"""FastAPI application entrypoint for the Wiener Linien Live Map."""

from __future__ import annotations

import logging
import os
from dataclasses import asdict
from datetime import datetime, timedelta
from pathlib import Path
import socketio
from cachetools import TTLCache
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

try:
    from .data_loader import data_loader
    from .database import db
    from .disruption_alerts import disruption_monitor
    from .gtfs_manager import manager as gtfs_manager
    from .vehicle_service import clear_vehicle_cache, collect_vehicle_data, get_vehicle_summary
    from .websocket_manager import get_websocket_manager, init_websocket_manager
except ImportError:  # pragma: no cover - runtime fallback when package context missing
    from data_loader import data_loader  # type: ignore
    from database import db  # type: ignore
    from disruption_alerts import disruption_monitor  # type: ignore
    from gtfs_manager import manager as gtfs_manager  # type: ignore
    from vehicle_service import clear_vehicle_cache, collect_vehicle_data, get_vehicle_summary  # type: ignore
    from websocket_manager import get_websocket_manager, init_websocket_manager  # type: ignore


BASE_DIR = Path(__file__).parent
TEMPLATES = Jinja2Templates(directory=BASE_DIR / "templates")
STATIC_DIR = BASE_DIR / "static"
DATA_DIR = BASE_DIR / "data"

LOGS_DIR = BASE_DIR / "logs"
LOGS_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler(LOGS_DIR / "app.log")],
)

logger = logging.getLogger(__name__)


TEST_MODE = os.getenv("WIENER_LINIEN_TEST_MODE", "").strip() == "1"

sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins="*")
websocket_manager = init_websocket_manager(sio)

fastapi_app = FastAPI(
    title="Wiener Linien Live Map",
    version="2.0.0",
    default_response_class=JSONResponse,
)
fastapi_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

if STATIC_DIR.exists():
    fastapi_app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


ROUTES_CACHE = TTLCache(maxsize=1, ttl=300)


def _normalize_line_identifier(line_name: str) -> str:
    return line_name.strip()


@fastapi_app.on_event("startup")
async def on_startup() -> None:
    logger.info("Starting FastAPI application")
    initialize_app()
    if not TEST_MODE:
        websocket_manager.start()


@fastapi_app.on_event("shutdown")
async def on_shutdown() -> None:
    if not TEST_MODE:
        websocket_manager.stop()


@fastapi_app.get("/", response_class=HTMLResponse)
async def read_index(request: Request) -> HTMLResponse:
    return TEMPLATES.TemplateResponse("index.html", {"request": request})


@fastapi_app.get("/about", response_class=HTMLResponse)
async def read_about(request: Request) -> HTMLResponse:
    return TEMPLATES.TemplateResponse("about.html", {"request": request})


@fastapi_app.get("/status", response_class=HTMLResponse)
async def commuter_status_page(request: Request) -> HTMLResponse:
    return TEMPLATES.TemplateResponse("status.html", {"request": request})


@fastapi_app.get("/line/{line_name}", response_class=HTMLResponse)
async def read_line_info(request: Request, line_name: str) -> HTMLResponse:
    return TEMPLATES.TemplateResponse("line_info.html", {"request": request, "line_name": line_name})


@fastapi_app.get("/api/vehicles")
async def get_vehicles(request: Request) -> JSONResponse:
    vehicle_type = request.query_params.get("type", "all")
    station = request.query_params.get("station")
    line = request.query_params.get("line")
    line_filters: set[str] = set()

    for raw_value in request.query_params.getlist("lines"):
        if not raw_value:
            continue
        for piece in raw_value.split(","):
            cleaned = piece.strip()
            if cleaned:
                line_filters.add(cleaned)

    if line:
        line_filters.add(line)

    lines = sorted(line_filters)

    logger.info(
        "Fetching vehicles: type=%s lines=%s station=%s",
        vehicle_type,
        lines,
        station,
    )

    result = collect_vehicle_data(
        vehicle_type=vehicle_type,
        station=station,
        lines=lines if lines else None,
    )
    if not result["vehicles"]:
        logger.warning("No vehicles found matching the criteria")

    payload = {
        "vehicles": result["vehicles"],
        "timestamp": datetime.utcnow().isoformat(),
        "successful_requests": result["successful_requests"],
        "failed_requests": result["failed_requests"],
    }
    return JSONResponse(payload)


@fastapi_app.get("/api/lines")
async def get_lines() -> JSONResponse:
    try:
        line_data = data_loader.get_gtfs_line_catalog()
        if not line_data:
            fallback_lines = data_loader.load_lines()
            line_data = [
                {
                    "name": line.name,
                    "type": line.type,
                    "color": line.color,
                    "description": line.description,
                    "frequency": line.frequency,
                    "operating_hours": line.operating_hours,
                }
                for line in fallback_lines
            ]
        return JSONResponse({"lines": line_data})
    except Exception as exc:
        logger.error("Error in get_lines: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@fastapi_app.get("/api/lines/{line_name}")
async def get_line_overview(line_name: str) -> JSONResponse:
    normalized_name = _normalize_line_identifier(line_name)
    logger.info("Fetching overview for line %s", normalized_name, extra={"route_short_name": normalized_name})

    try:
        line_info = data_loader.get_line_by_name(normalized_name)
        overview = db.get_line_overview(normalized_name)

        if line_info is None and overview is None:
            raise HTTPException(status_code=404, detail="Line not found")

        response = {
            "line": asdict(line_info) if line_info else {"name": normalized_name},
            "overview": overview,
        }
        return JSONResponse(response)
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Error fetching overview for line %s: %s", normalized_name, exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch line overview")


@fastapi_app.get("/api/lines/{line_name}/route")
async def get_line_route(line_name: str) -> JSONResponse:
    normalized_name = _normalize_line_identifier(line_name)
    logger.info(
        "Fetching route geometry for line %s",
        normalized_name,
        extra={"route_short_name": normalized_name},
    )

    try:
        route_data = data_loader.get_gtfs_route(normalized_name)
        if not route_data:
            raise HTTPException(status_code=404, detail="Route not found for line")
        return JSONResponse({"route": route_data})
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Error fetching route for line %s: %s", normalized_name, exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch route data")


@fastapi_app.get("/api/lines/{line_name}/stations")
async def get_line_stations(line_name: str) -> JSONResponse:
    normalized_name = _normalize_line_identifier(line_name)
    logger.info("Fetching stations for line %s", normalized_name, extra={"route_short_name": normalized_name})

    try:
        stations = data_loader.get_gtfs_line_stations(normalized_name)
        return JSONResponse({
            "line": normalized_name,
            "stations": stations,
        })
    except Exception as exc:
        logger.error("Error fetching stations for line %s: %s", normalized_name, exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch stations")


@fastapi_app.get("/api/arrivals")
async def get_arrivals(request: Request) -> JSONResponse:
    """Return next departures/vehicles for a stop by RBL or for a set of lines."""
    try:
        rbl = request.query_params.get("rbl")
        lines_param = request.query_params.get("lines")
        vehicle_type = request.query_params.get("type", "all")

        lines = None
        if lines_param:
            lines = [piece.strip().upper() for piece in lines_param.split(",") if piece.strip()]

        if not rbl and not lines:
            raise HTTPException(status_code=400, detail="Provide rbl or lines")

        result = collect_vehicle_data(
            vehicle_type=vehicle_type,
            station=rbl,
            lines=lines,
        )
        return JSONResponse(result)
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Error in get_arrivals: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@fastapi_app.get("/api/traffic-info")
async def get_traffic_info() -> JSONResponse:
    """Fetch traffic disruptions and alerts from Wiener Linien /trafficInfo endpoint."""
    try:
        import requests
        
        # Cache for 5 minutes
        # Check cache
        cached_data = getattr(get_traffic_info, '_cache', None)
        cache_time = getattr(get_traffic_info, '_cache_time', None)
        
        if cached_data and cache_time:
            if datetime.now() - cache_time < timedelta(minutes=5):
                return JSONResponse(cached_data)
        
        # Fetch from Wiener Linien API
        url = "https://www.wienerlinien.at/ogd_realtime/trafficInfoList"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        # Transform to our format
        alerts = []
        if isinstance(data, dict) and 'data' in data:
            for item in data.get('data', []):
                if 'attributes' in item:
                    attrs = item['attributes']
                    alert = {
                        'id': item.get('id', ''),
                        'title': attrs.get('title', ''),
                        'description': attrs.get('description', ''),
                        'severity': attrs.get('severity', 'info'),
                        'lines': attrs.get('relatedLines', []),
                        'start_time': attrs.get('startTime', ''),
                        'end_time': attrs.get('endTime', ''),
                        'type': attrs.get('type', ''),
                    }
                    alerts.append(alert)
        
        result = {
            'alerts': alerts,
            'timestamp': datetime.utcnow().isoformat(),
            'count': len(alerts)
        }
        
        # Cache the result
        get_traffic_info._cache = result
        get_traffic_info._cache_time = datetime.now()
        
        return JSONResponse(result)
    except Exception as exc:
        logger.error("Error fetching traffic info: %s", exc, exc_info=True)
        # Return empty result on error
        return JSONResponse({
            'alerts': [],
            'timestamp': datetime.utcnow().isoformat(),
            'count': 0,
            'error': str(exc)
        })


@fastapi_app.get("/api/stops/nearby")
async def get_stops_nearby(request: Request) -> JSONResponse:
    """Return nearest stops to a lat/lon with distance and RBL when available."""
    try:
        lat_raw = request.query_params.get("lat")
        lon_raw = request.query_params.get("lon")
        limit_raw = request.query_params.get("limit", "10")

        if lat_raw is None or lon_raw is None:
            raise HTTPException(status_code=400, detail="lat and lon are required")

        try:
            lat = float(lat_raw)
            lon = float(lon_raw)
            limit = max(1, min(50, int(limit_raw)))
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid lat/lon/limit")

        # Fetch all stops and compute distances (fallback without PostGIS function)
        stops = db.get_stations()  # expected to include name, rbl, type, lat, lng
        def haversine(a_lat: float, a_lon: float, b_lat: float, b_lon: float) -> float:
            from math import radians, sin, cos, asin, sqrt
            R = 6371000.0
            d_lat = radians(b_lat - a_lat)
            d_lon = radians(b_lon - a_lon)
            la1 = radians(a_lat)
            la2 = radians(b_lat)
            h = sin(d_lat/2)**2 + cos(la1) * cos(la2) * sin(d_lon/2)**2
            return 2 * R * asin(sqrt(h))

        enriched = []
        for stop in stops:
            s_lat = stop.get("lat")
            s_lon = stop.get("lng")
            if isinstance(s_lat, (int, float)) and isinstance(s_lon, (int, float)):
                distance = haversine(lat, lon, float(s_lat), float(s_lon))
                enriched.append({
                    "name": stop.get("name"),
                    "rbl": stop.get("rbl"),
                    "type": stop.get("type"),
                    "lat": s_lat,
                    "lng": s_lon,
                    "distance_m": round(distance, 1),
                })

        enriched.sort(key=lambda x: x["distance_m"])
        return JSONResponse({"stops": enriched[:limit], "origin": {"lat": lat, "lon": lon}})
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Error in get_stops_nearby: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@fastapi_app.get("/api/stations")
async def get_stations() -> JSONResponse:
    try:
        stations = db.get_stations()
        station_data = [
            {
                "name": station["name"],
                "rbl": station["rbl"],
                "type": station["type"],
                "zone": station["zone"],
                "lat": station["lat"],
                "lng": station["lng"],
            }
            for station in stations
        ]
        return JSONResponse({"stations": station_data})
    except Exception as exc:
        logger.error("Error in get_stations: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@fastapi_app.get("/api/routes")
async def get_routes() -> JSONResponse:
    cache_key = "routes"
    cached = ROUTES_CACHE.get(cache_key)
    if cached:
        return JSONResponse(cached)

    try:
        routes = db.get_routes()
        response = {
            "status": "success",
            "data": routes,
            "count": len(routes),
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
        ROUTES_CACHE[cache_key] = response
        return JSONResponse(response)
    except Exception as exc:
        logger.error("Error in get_routes: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch routes")


@fastapi_app.get("/api/disruptions")
async def get_disruptions(request: Request) -> JSONResponse:
    try:
        line_filter = request.query_params.get("line")
        severity_filter = request.query_params.get("severity")
        
        if line_filter:
            disruptions = disruption_monitor.get_disruptions_by_line(line_filter)
        elif severity_filter:
            from disruption_alerts import DisruptionSeverity

            disruptions = disruption_monitor.get_disruptions_by_severity(DisruptionSeverity(severity_filter))
        else:
            disruptions = disruption_monitor.get_active_disruptions()
        
        disruption_data = [
            {
                "id": disruption.id,
                "line": disruption.line,
                "type": disruption.type.value,
                "severity": disruption.severity.value,
                "status": disruption.status.value,
                "title": disruption.title,
                "description": disruption.description,
                "affected_stations": disruption.affected_stations,
                "affected_lines": disruption.affected_lines,
                "start_time": disruption.start_time.isoformat(),
                "end_time": disruption.end_time.isoformat() if disruption.end_time else None,
                "created_at": disruption.created_at.isoformat(),
                "updated_at": disruption.updated_at.isoformat(),
            }
            for disruption in disruptions
        ]
        return JSONResponse({"disruptions": disruption_data})
    except Exception as exc:
        logger.error("Error in get_disruptions: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@fastapi_app.get("/api/disruptions/summary")
async def get_disruption_summary() -> JSONResponse:
    try:
        summary = disruption_monitor.get_disruption_summary()
        return JSONResponse(summary)
    except Exception as exc:
        logger.error("Error in get_disruption_summary: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
        

@fastapi_app.get("/api/status")
async def get_system_status() -> JSONResponse:
    try:
        ws_manager = get_websocket_manager()
        active_disruptions = disruption_monitor.get_active_disruptions()
        filter_summary = ws_manager.get_filters_summary() if ws_manager else {
            "clients": 0,
            "line_filters": 0,
            "type_filters": 0,
        }
        status = {
            "websocket_clients": ws_manager.get_connected_clients_count() if ws_manager else 0,
            "active_disruptions": len(active_disruptions),
            "vehicle_count": ws_manager.get_vehicle_count() if ws_manager else 0,
            "vehicle_total": ws_manager.get_vehicle_total_count() if ws_manager else 0,
            "filters": filter_summary,
            "data_cache_status": data_loader.get_cache_status(),
            "last_api_check": disruption_monitor.last_check.isoformat() if disruption_monitor.last_check else None,
            "timestamp": datetime.utcnow().isoformat(),
        }
        return JSONResponse(status)
    except Exception as exc:
        logger.error("Error in get_system_status: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@fastapi_app.get("/api/status/summary")
async def get_status_summary() -> JSONResponse:
    try:
        vehicle_summary = get_vehicle_summary()
        disruption_summary = disruption_monitor.get_disruption_summary()
        heartbeat_path = Path(os.getenv("GTFS_HEARTBEAT_PATH", "/app/data/gtfs_loader_heartbeat.json"))
        heartbeat_info = None
        if heartbeat_path.exists():
            heartbeat_info = {
                "path": str(heartbeat_path),
                "updated_at": datetime.utcfromtimestamp(heartbeat_path.stat().st_mtime).isoformat() + "Z",
            }
        # Read last GTFS refresh marker
        try:
            marker_path = LOGS_DIR / "gtfs_last_success.txt"
            last_gtfs_refresh = marker_path.read_text(encoding="utf-8").strip() if marker_path.exists() else None
        except Exception:
            last_gtfs_refresh = None
        payload = {
            "vehicles": vehicle_summary,
            "disruptions": disruption_summary,
            "heartbeat": heartbeat_info,
            "last_gtfs_refresh": last_gtfs_refresh,
        }
        return JSONResponse(payload)
    except Exception as exc:
        logger.error("Error building status summary: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to build status summary")


@fastapi_app.get("/data/{path:path}")
async def serve_data_file(path: str) -> FileResponse:
    candidate_dirs = [
        DATA_DIR,
        Path("/data"),
        BASE_DIR / "data",
    ]
    for directory in candidate_dirs:
        file_path = directory / path
        if file_path.exists() and file_path.suffix.lower() == ".md":
            return FileResponse(file_path, media_type="text/markdown")
    raise HTTPException(status_code=404, detail="File not found")


@fastapi_app.get("/routes", response_class=HTMLResponse)
async def list_routes() -> HTMLResponse:
    entries = []
    for route in fastapi_app.routes:
        methods = ",".join(sorted(route.methods or []))
        entries.append(f"{route.name}: {route.path} [{methods}]")
    entries.sort()
    body = "<br>".join(entries)
    return HTMLResponse(body)


def initialize_app() -> None:
    logger.info("Initializing Wiener Linien Live Map application")
    (BASE_DIR / "logs").mkdir(exist_ok=True)

    if not TEST_MODE and db.engine is None:
        try:
            db.init_app(fastapi_app)
        except Exception as exc:  # pragma: no cover - startup critical
            logger.error("Database initialization failed: %s", exc, exc_info=True)
            raise

    if not TEST_MODE:
        try:
            gtfs_manager.ensure_data_ready()
        except Exception as exc:  # pragma: no cover - startup critical
            logger.error("GTFS bootstrap failed: %s", exc, exc_info=True)
            raise

    data_loader.load_lines()
    data_loader.load_stations()
    data_loader.load_routes()
    clear_vehicle_cache()


socket_app = socketio.ASGIApp(sio, other_asgi_app=fastapi_app, socketio_path="/ws/socket.io")
app = socket_app


if __name__ == "__main__":  # pragma: no cover - manual execution helper
    import uvicorn

    uvicorn.run("app:app", host="0.0.0.0", port=3080, reload=True)

