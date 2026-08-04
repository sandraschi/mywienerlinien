"""FastAPI application entrypoint for the Wiener Linien Live Map."""

from __future__ import annotations

import asyncio
import logging
import os
from contextlib import asynccontextmanager
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
from pydantic import BaseModel
import subprocess

try:
    from .api.analytics import router as analytics_router
    from .api.public_api import router as public_api_router
    from .data_loader import data_loader
    from .database import db
    from .disruption_alerts import disruption_monitor
    from .gtfs_manager import manager as gtfs_manager
    from .vehicle_service import (
        clear_vehicle_cache,
        collect_vehicle_data,
        get_vehicle_summary,
    )
    from .websocket_manager import get_websocket_manager, init_websocket_manager
except ImportError:  # pragma: no cover - runtime fallback when package context missing
    from data_loader import data_loader  # type: ignore
    from database import db  # type: ignore
    from disruption_alerts import disruption_monitor  # type: ignore
    from gtfs_manager import manager as gtfs_manager  # type: ignore
    from vehicle_service import (  # type: ignore
        clear_vehicle_cache,
        collect_vehicle_data,
        get_vehicle_summary,
    )
    from websocket_manager import get_websocket_manager, init_websocket_manager  # type: ignore

    try:
        from api.analytics import router as analytics_router  # type: ignore
        from api.public_api import router as public_api_router  # type: ignore
    except ImportError:
        analytics_router = None
        public_api_router = None

try:
    import sys
    from pathlib import Path

    _root = Path(__file__).parent.parent
    sys.path.insert(0, str(_root))
    sys.path.insert(0, str(_root / "src"))
    from scripts.city_config import get_city_config, list_cities  # type: ignore
except ImportError:
    # Fallback if city_config is not available
    def list_cities():
        return {}

    def get_city_config(city_name: str):
        return None


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


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager (replaces deprecated @app.on_event)."""
    logger.info("Starting FastAPI application")
    initialize_app()
    if not TEST_MODE:
        websocket_manager.start()

    yield

    if not TEST_MODE:
        websocket_manager.stop()


fastapi_app = FastAPI(
    title="Wiener Linien Live Map",
    version="2.0.0",
    default_response_class=JSONResponse,
    lifespan=lifespan,  # Modern lifespan management
)
fastapi_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

if STATIC_DIR.exists():
    fastapi_app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Register analytics router (Phase 3C)
if analytics_router:
    try:
        fastapi_app.include_router(analytics_router)
        logger.info("Analytics router registered")
    except Exception as e:
        logger.warning(f"Failed to register analytics router: {e}")

# Register public API router (Phase 4)
if public_api_router:
    try:
        fastapi_app.include_router(public_api_router)
        logger.info("Public API router registered")
    except Exception as e:
        logger.warning(f"Failed to register public API router: {e}")

ROUTES_CACHE = TTLCache(maxsize=1, ttl=300)


def _normalize_line_identifier(line_name: str) -> str:
    return line_name.strip()


@fastapi_app.get("/", response_class=HTMLResponse)
async def read_index(request: Request) -> HTMLResponse:
    return TEMPLATES.TemplateResponse("index.html", {"request": request})


@fastapi_app.get("/about", response_class=HTMLResponse)
async def read_about(request: Request) -> HTMLResponse:
    return TEMPLATES.TemplateResponse("about.html", {"request": request})


@fastapi_app.get("/status", response_class=HTMLResponse)
async def commuter_status_page(request: Request) -> HTMLResponse:
    return TEMPLATES.TemplateResponse("status.html", {"request": request})


@fastapi_app.get("/analytics", response_class=HTMLResponse)
async def analytics_dashboard_page(request: Request) -> HTMLResponse:
    """Analytics dashboard page - Phase 3C."""
    return TEMPLATES.TemplateResponse("analytics.html", {"request": request})


@fastapi_app.get("/community", response_class=HTMLResponse)
async def community_dashboard_page(request: Request) -> HTMLResponse:
    """Community dashboard page - Phase 5."""
    return TEMPLATES.TemplateResponse("community.html", {"request": request})


# Multi-City API (Phase 4) - NOTE: actual route handlers defined later using city_config


@fastapi_app.get("/line/{line_name}", response_class=HTMLResponse)
async def read_line_info(request: Request, line_name: str) -> HTMLResponse:
    return TEMPLATES.TemplateResponse(
        "line_info.html", {"request": request, "line_name": line_name}
    )


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

    result = await asyncio.to_thread(
        collect_vehicle_data,
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
            # Fallback: convert Line objects to dict format
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
    logger.info(
        "Fetching overview for line %s",
        normalized_name,
        extra={"route_short_name": normalized_name},
    )

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
        logger.error(
            "Error fetching overview for line %s: %s",
            normalized_name,
            exc,
            exc_info=True,
        )
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
        logger.error(
            "Error fetching route for line %s: %s", normalized_name, exc, exc_info=True
        )
        raise HTTPException(status_code=500, detail="Failed to fetch route data")


@fastapi_app.get("/api/lines/{line_name}/stations")
async def get_line_stations(line_name: str) -> JSONResponse:
    normalized_name = _normalize_line_identifier(line_name)
    logger.info(
        "Fetching stations for line %s",
        normalized_name,
        extra={"route_short_name": normalized_name},
    )

    try:
        stations = data_loader.get_gtfs_line_stations(normalized_name)
        return JSONResponse(
            {
                "line": normalized_name,
                "stations": stations,
            }
        )
    except Exception as exc:
        logger.error(
            "Error fetching stations for line %s: %s",
            normalized_name,
            exc,
            exc_info=True,
        )
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
            lines = [
                piece.strip().upper()
                for piece in lines_param.split(",")
                if piece.strip()
            ]

        if not rbl and not lines:
            raise HTTPException(status_code=400, detail="Provide rbl or lines")

        result = await asyncio.to_thread(
            collect_vehicle_data,
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
        cached_data = getattr(get_traffic_info, "_cache", None)
        cache_time = getattr(get_traffic_info, "_cache_time", None)

        if cached_data and cache_time:
            if datetime.now() - cache_time < timedelta(minutes=5):
                return JSONResponse(cached_data)

        # Fetch from Wiener Linien API
        url = "https://www.wienerlinien.at/ogd_realtime/trafficInfoList"
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        data = response.json()

        # WL API V1.4 trafficInfoList response shape:
        # {"data": {"trafficInfos": [...], "trafficInfoCategories": [...]}}
        # Each trafficInfo has: name, priority, owner, ownerFormatted,
        #   title, description, descriptionHTML, time, attributes, references
        alerts = []
        if isinstance(data, dict) and "data" in data:
            traffic_infos = data["data"].get("trafficInfos") or []
            for item in traffic_infos:
                attrs = item.get("attributes") or {}
                refs = item.get("references") or {}
                # Collect related line names
                related_lines = []
                for line_ref in (refs.get("lines") or []):
                    name = line_ref.get("name") or line_ref.get("shortName") or ""
                    if name:
                        related_lines.append(name)
                time_info = item.get("time") or {}
                alert = {
                    "id": item.get("name", ""),
                    "title": item.get("title", ""),
                    "description": item.get("description", ""),
                    "description_html": item.get("descriptionHTML", ""),
                    "severity": attrs.get("severity", "info"),
                    "status": item.get("attributes", {}).get("status", ""),
                    "lines": related_lines,
                    "start_time": time_info.get("start", ""),
                    "end_time": time_info.get("end", ""),
                    "created": time_info.get("created", ""),
                    "last_update": time_info.get("lastupdate", ""),
                    "type": item.get("owner", ""),
                    "priority": item.get("priority", ""),
                }
                alerts.append(alert)

        result = {
            "alerts": alerts,
            "timestamp": datetime.utcnow().isoformat(),
            "count": len(alerts),
        }

        # Cache the result
        get_traffic_info._cache = result
        get_traffic_info._cache_time = datetime.now()

        return JSONResponse(result)
    except Exception as exc:
        logger.error("Error fetching traffic info: %s", exc, exc_info=True)
        # Return empty result on error
        return JSONResponse(
            {
                "alerts": [],
                "timestamp": datetime.utcnow().isoformat(),
                "count": 0,
                "error": str(exc),
            }
        )


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
            from math import asin, cos, radians, sin, sqrt

            R = 6371000.0
            d_lat = radians(b_lat - a_lat)
            d_lon = radians(b_lon - a_lon)
            la1 = radians(a_lat)
            la2 = radians(b_lat)
            h = sin(d_lat / 2) ** 2 + cos(la1) * cos(la2) * sin(d_lon / 2) ** 2
            return 2 * R * asin(sqrt(h))

        enriched = []
        for stop in stops:
            s_lat = stop.get("lat")
            s_lon = stop.get("lng")
            if isinstance(s_lat, (int, float)) and isinstance(s_lon, (int, float)):
                distance = haversine(lat, lon, float(s_lat), float(s_lon))
                enriched.append(
                    {
                        "name": stop.get("name"),
                        "rbl": stop.get("rbl"),
                        "type": stop.get("type"),
                        "lat": s_lat,
                        "lng": s_lon,
                        "distance_m": round(distance, 1),
                    }
                )

        enriched.sort(key=lambda x: x["distance_m"])
        return JSONResponse(
            {"stops": enriched[:limit], "origin": {"lat": lat, "lon": lon}}
        )
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

            disruptions = disruption_monitor.get_disruptions_by_severity(
                DisruptionSeverity(severity_filter)
            )
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
                "end_time": disruption.end_time.isoformat()
                if disruption.end_time
                else None,
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
        filter_summary = (
            ws_manager.get_filters_summary()
            if ws_manager
            else {
                "clients": 0,
                "line_filters": 0,
                "type_filters": 0,
            }
        )
        status = {
            "websocket_clients": ws_manager.get_connected_clients_count()
            if ws_manager
            else 0,
            "active_disruptions": len(active_disruptions),
            "vehicle_count": ws_manager.get_vehicle_count() if ws_manager else 0,
            "vehicle_total": ws_manager.get_vehicle_total_count() if ws_manager else 0,
            "filters": filter_summary,
            "data_cache_status": data_loader.get_cache_status(),
            "last_api_check": disruption_monitor.last_check.isoformat()
            if disruption_monitor.last_check
            else None,
            "timestamp": datetime.utcnow().isoformat(),
        }
        return JSONResponse(status)
    except Exception as exc:
        logger.error("Error in get_system_status: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@fastapi_app.get("/api/health")
async def get_health_status() -> JSONResponse:
    """Fast health check endpoint for container health checks."""
    return JSONResponse({"status": "healthy", "service": "mywienerlinien"})


class LaunchRequest(BaseModel):
    repo_path: str


@fastapi_app.post("/api/fleet/launch")
async def launch_app(request: LaunchRequest):
    """Launch another MCP app via its start.ps1 script."""
    path = Path(request.repo_path)
    if not path.exists():
        raise HTTPException(
            status_code=404, detail=f"Path {request.repo_path} does not exist"
        )

    # Security check
    allowed_base = Path("D:/Dev/repos")
    try:
        path.relative_to(allowed_base)
    except ValueError:
        raise HTTPException(status_code=403, detail="Access denied")

    start_script = path / "web_sota" / "start.ps1"
    if not start_script.exists():
        start_script = path / "web" / "start.ps1"
        if not start_script.exists():
            # Fallback for older repos
            start_script = path / "start.ps1"
            if not start_script.exists():
                raise HTTPException(status_code=400, detail="No start.ps1 found")

    try:
        subprocess.Popen(
            [
                "powershell.exe",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(start_script),
            ],
            cwd=str(path),
            creationflags=subprocess.CREATE_NEW_CONSOLE,
        )
        return {"success": True, "message": f"Launched {path.name}"}
    except Exception as e:
        logger.error(f"Launch failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@fastapi_app.get("/api/status/summary")
async def get_status_summary() -> JSONResponse:
    try:
        vehicle_summary = get_vehicle_summary()
        disruption_summary = disruption_monitor.get_disruption_summary()
        heartbeat_path = Path(
            os.getenv("GTFS_HEARTBEAT_PATH", "/app/data/gtfs_loader_heartbeat.json")
        )
        heartbeat_info = None
        if heartbeat_path.exists():
            heartbeat_info = {
                "path": str(heartbeat_path),
                "updated_at": datetime.utcfromtimestamp(
                    heartbeat_path.stat().st_mtime
                ).isoformat()
                + "Z",
            }
        # Read last GTFS refresh marker
        try:
            marker_path = LOGS_DIR / "gtfs_last_success.txt"
            last_gtfs_refresh = (
                marker_path.read_text(encoding="utf-8").strip()
                if marker_path.exists()
                else None
            )
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


@fastapi_app.get("/api/cities")
async def get_cities() -> JSONResponse:
    """Get list of available cities with their configurations."""
    try:
        cities_dict = list_cities()
        cities_list = []
        for city_key, city_config in cities_dict.items():
            city_data = {
                "key": city_key,
                "name": city_config.name,
                "description": city_config.description,
                "timezone": city_config.timezone,
                "language": city_config.language,
            }
            if city_config.map_center:
                city_data["map_center"] = {
                    "lat": city_config.map_center[0],
                    "lng": city_config.map_center[1],
                }
                city_data["map_zoom"] = city_config.map_zoom
            cities_list.append(city_data)
        return JSONResponse({"cities": cities_list})
    except Exception as exc:
        logger.error("Error fetching cities: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch cities")


@fastapi_app.get("/api/cities/{city_key}")
async def get_city_info(city_key: str) -> JSONResponse:
    """Get configuration for a specific city."""
    try:
        city_config = get_city_config(city_key)
        if not city_config:
            raise HTTPException(status_code=404, detail="City not found")

        city_data = {
            "key": city_key,
            "name": city_config.name,
            "description": city_config.description,
            "timezone": city_config.timezone,
            "language": city_config.language,
            "enable_rbl_mapping": city_config.enable_rbl_mapping,
        }
        if city_config.map_center:
            city_data["map_center"] = {
                "lat": city_config.map_center[0],
                "lng": city_config.map_center[1],
            }
            city_data["map_zoom"] = city_config.map_zoom
        return JSONResponse(city_data)
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Error fetching city info: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch city info")


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


# Favorites API (localStorage-based, no authentication)
# In the future, this can be extended with user accounts and database storage
@fastapi_app.get("/api/favorites")
async def get_favorites(request: Request) -> JSONResponse:
    """
    Get favorite stations. Currently returns empty list as favorites are stored client-side.
    Future enhancement: Support for server-side storage with user accounts.
    """
    return JSONResponse(
        {
            "favorites": [],
            "message": "Favorites are stored locally in your browser. Use localStorage API from frontend.",
        }
    )


@fastapi_app.post("/api/favorites")
async def add_favorite(request: Request) -> JSONResponse:
    """
    Add a favorite station. Currently handled client-side via localStorage.
    Future enhancement: Support for server-side storage with user accounts.
    """
    try:
        data = await request.json()
        station_id = data.get("station_id")
        station_name = data.get("station_name")

        if not station_id or not station_name:
            raise HTTPException(
                status_code=400, detail="station_id and station_name are required"
            )

        return JSONResponse(
            {
                "success": True,
                "message": "Favorite added (client-side storage)",
                "station": {"id": station_id, "name": station_name},
            }
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Error adding favorite: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@fastapi_app.delete("/api/favorites/{station_id}")
async def remove_favorite(station_id: str) -> JSONResponse:
    """
    Remove a favorite station. Currently handled client-side via localStorage.
    Future enhancement: Support for server-side storage with user accounts.
    """
    return JSONResponse(
        {
            "success": True,
            "message": f"Favorite {station_id} removed (client-side storage)",
        }
    )


# Journey Planning & Route Comparison API (Phase 3B)
@fastapi_app.get("/api/journey/plan")
async def plan_journey(request: Request) -> JSONResponse:
    """Plan journey with multiple route options and real-time delays.

    Phase 3B Enhancement: A* pathfinding with delay-adjusted routing.

    Query Parameters:
        from: Origin station name or ID
        to: Destination station name or ID
        time: Optional departure time (ISO format)
        alternatives: Number of alternative routes (1-5, default: 3)
        include_delays: Include real-time delay adjustments (default: true)

    Returns:
        Multiple route options with segments, transfers, delays
    """
    try:
        from_station = request.query_params.get("from")
        to_station = request.query_params.get("to")
        departure_time_str = request.query_params.get("time")
        alternatives = min(
            5, max(1, int(request.query_params.get("alternatives", "3")))
        )
        include_delays = (
            request.query_params.get("include_delays", "true").lower() != "false"
        )

        if not from_station or not to_station:
            raise HTTPException(
                status_code=400, detail="Both 'from' and 'to' parameters are required"
            )

        # Parse departure time
        if departure_time_str:
            try:
                departure_time = datetime.fromisoformat(
                    departure_time_str.replace("Z", "+00:00")
                )
            except:
                departure_time = datetime.now()
        else:
            departure_time = datetime.now()

        # Import routing services
        try:
            from wienerlinien_mcp.routing_service import RouteSegment
            from wienerlinien_mcp.utils import find_station_by_name
        except ImportError:
            from frontend.wienerlinien_mcp.utils import find_station_by_name

        # Find stations
        from_info = find_station_by_name(from_station)
        to_info = find_station_by_name(to_station)

        if not from_info:
            raise HTTPException(
                status_code=404, detail=f"Origin station '{from_station}' not found"
            )
        if not to_info:
            raise HTTPException(
                status_code=404, detail=f"Destination station '{to_station}' not found"
            )

        # Get journey planner (lazy loaded with A* support)
        from wienerlinien_mcp.tools.journey import get_journey_planner

        planner = get_journey_planner()

        # Plan journey with multiple alternatives
        route_options = planner.plan_journey(
            from_info["id"],
            to_info["id"],
            departure_time,
            num_alternatives=alternatives,
        )

        if not route_options:
            raise HTTPException(
                status_code=404, detail="No routes found between these stations"
            )

        # Adjust for real-time delays if requested
        if include_delays:
            try:
                import vehicle_service
                from wienerlinien_mcp.realtime_service import get_realtime_service

                realtime_svc = get_realtime_service(vehicle_service)
                realtime_updates = realtime_svc.get_realtime_updates()

                # Adjust each route for delays
                adjusted_routes = []
                for route in route_options:
                    adjusted = realtime_svc.adjust_route_for_delays(
                        route, realtime_updates
                    )
                    adjusted_routes.append(adjusted)

                # Re-rank by reliability
                ranked = realtime_svc.rank_routes_by_reliability(
                    adjusted_routes, realtime_updates
                )
                route_options = [route for route, score in ranked]

                logger.info(
                    f"Applied real-time delay adjustments to {len(route_options)} routes"
                )
            except Exception as e:
                logger.warning(f"Could not apply delay adjustments: {e}")

        # Convert to JSON-serializable format
        routes_data = []
        for route in route_options:
            segments_data = []
            for seg in route.segments:
                segments_data.append(
                    {
                        "line": seg.line,
                        "from_station": seg.from_stop_name,
                        "to_station": seg.to_stop_name,
                        "departure_time": seg.departure_time.isoformat(),
                        "arrival_time": seg.arrival_time.isoformat(),
                        "duration_minutes": seg.duration_minutes,
                        "vehicle_type": seg.vehicle_type,
                        "distance_meters": round(seg.distance_meters)
                        if seg.distance_meters
                        else None,
                        "is_walking": seg.line == "WALK",
                    }
                )

            routes_data.append(
                {
                    "from_station": from_info["name"],
                    "to_station": to_info["name"],
                    "departure_time": route.departure_time.isoformat(),
                    "arrival_time": route.arrival_time.isoformat(),
                    "total_duration_minutes": route.total_duration_minutes,
                    "transfers": route.transfers,
                    "total_distance_meters": round(route.total_distance_meters),
                    "estimated_cost": route.estimated_cost,
                    "segments": segments_data,
                }
            )

        return JSONResponse(
            {
                "routes": routes_data,
                "origin": {"id": from_info["id"], "name": from_info["name"]},
                "destination": {"id": to_info["id"], "name": to_info["name"]},
                "query_time": departure_time.isoformat(),
                "delays_included": include_delays,
                "timestamp": datetime.now().isoformat(),
            }
        )

    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Error planning journey: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Journey planning failed: {str(exc)}"
        )


def initialize_app() -> None:
    logger.info("Initializing Wiener Linien Live Map application")
    (BASE_DIR / "logs").mkdir(exist_ok=True)

    # In development mode, database is optional
    dev_mode = os.getenv("APP_ENV", "").lower() in ("development", "dev") or TEST_MODE

    # Initialize database even in development mode
    logger.info("Initializing database connection")
    try:
        db.init_app(None)  # Initialize database connection
        logger.info("Database connection initialized successfully")
    except Exception as exc:
        logger.error("Database initialization failed: %s", exc, exc_info=True)
        if not dev_mode:
            raise

    if not TEST_MODE:
        try:
            gtfs_manager.ensure_data_ready()
        except Exception as exc:  # pragma: no cover - startup critical
            if dev_mode:
                logger.warning(
                    "GTFS bootstrap failed (continuing in dev mode): %s", exc
                )
                # Don't raise in dev mode - allow app to start without GTFS data
            else:
                logger.error("GTFS bootstrap failed: %s", exc, exc_info=True)
                raise

    # Data loading is now lazy - only load when first requested
    # This speeds up startup from ~67 seconds to ~1 second
    # data_loader.load_lines()  # Commented out for lazy loading
    # data_loader.load_stations()  # Commented out for lazy loading
    # data_loader.load_routes()  # Commented out for lazy loading
    try:
        clear_vehicle_cache()
    except Exception as exc:
        if dev_mode:
            logger.warning(
                "Vehicle cache clear failed (continuing in dev mode): %s", exc
            )
        else:
            raise


# For development without Socket.IO, use FastAPI app directly
dev_mode = os.getenv("APP_ENV", "").lower() in ("development", "dev")
if dev_mode:
    app = fastapi_app
    logger.info("Running in development mode without Socket.IO")
else:
    socket_app = socketio.ASGIApp(
        sio, other_asgi_app=fastapi_app, socketio_path="/ws/socket.io"
    )
    app = socket_app


if __name__ == "__main__":  # pragma: no cover - manual execution helper
    import uvicorn

    port = int(os.environ.get("PORT", "10722"))
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=True)
