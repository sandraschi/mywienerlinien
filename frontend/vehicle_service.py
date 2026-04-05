"""Shared utilities for fetching and aggregating vehicle and traffic data.

API: Wiener Linien OGD Realtime V1.4 (09.02.2026)
  - /monitor?stopId=<id>  → next-70-min departures per stop (no sender needed)
  - /trafficInfoList      → service disruptions

Vehicle GPS positions are NOT available from the WL API. We approximate them
by querying the departure countdown at every stop of a line, then linearly
interpolating each vehicle between the two consecutive stops that bracket
its current countdown value.
"""

from __future__ import annotations

import logging
import re
import threading
import time
from collections.abc import Iterable
from datetime import datetime
from typing import Any

import requests

try:
    from .data_loader import data_loader
    from .database import db
except ImportError:  # pragma: no cover - runtime fallback when package context missing
    from data_loader import data_loader  # type: ignore
    from database import db  # type: ignore

logger = logging.getLogger(__name__)

VEHICLE_CACHE_TTL = 30  # seconds
MAX_RBLS_PER_LINE = 30  # enough to cover a full line
_vehicle_snapshot_cache: dict[str, dict[str, Any]] = {}
_vehicle_cache_lock = threading.Lock()

# V1.4 API base — no sender param required
_WL_BASE = "http://www.wienerlinien.at/ogd_realtime"


# ---------------------------------------------------------------------------
# Low-level API helpers
# ---------------------------------------------------------------------------

def _get(url: str, params: dict | None = None, timeout: int = 10) -> dict | None:
    """GET with basic error handling. Returns parsed JSON or None."""
    try:
        r = requests.get(url, params=params, timeout=timeout)
        r.raise_for_status()
        return r.json()
    except requests.RequestException as exc:
        logger.error("WL API request failed %s %s: %s", url, params, exc)
        return None


def fetch_vehicle_data(rbl_number: str) -> dict[str, Any] | None:
    """Fetch departure monitor for one stop by RBL number (backward-compat)."""
    return _get(f"{_WL_BASE}/monitor", params={"rbl": rbl_number,
                                                "activateTrafficInfo": "stoerungkurz"})


def fetch_stop_departures(stop_id: str | int) -> dict[str, Any] | None:
    """Fetch departure monitor using the current V1.4 stopId parameter."""
    return _get(f"{_WL_BASE}/monitor", params={"stopId": str(stop_id),
                                                "activateTrafficInfo": "stoerungkurz"})


def fetch_traffic_info() -> dict[str, Any] | None:
    return _get(f"{_WL_BASE}/trafficInfoList")


def fetch_news() -> dict[str, Any] | None:
    return _get(f"{_WL_BASE}/newsList")


# ---------------------------------------------------------------------------
# Cache helpers
# ---------------------------------------------------------------------------

def vehicle_cache_key(station: str | None, lines: Iterable[str] | None) -> str:
    if station:
        return f"station:{station}"
    if lines:
        normalized = ",".join(sorted({str(l).strip().upper() for l in lines if l}))
        if normalized:
            return f"lines:{normalized}"
    return "__default__"


def clear_vehicle_cache() -> None:
    with _vehicle_cache_lock:
        _vehicle_snapshot_cache.clear()


# ---------------------------------------------------------------------------
# Schedule-interpolated pseudo-position logic
# ---------------------------------------------------------------------------

def _lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def _guess_vehicle_type(line_name: str) -> str:
    u = line_name.upper()
    if re.match(r"^U\d", u):
        return "metro"
    if re.match(r"^[1-9]$|^[1-9][0-9]$|^[A-EORWZ]$", u):
        return "tram"
    if re.match(r"^[SNRCE]\d|^WLB", u):
        return "rail"
    return "buscity"


def _interpolate_vehicles_for_line(line_name: str) -> list[dict[str, Any]]:
    """
    Build pseudo-realtime vehicle positions for *line_name*.

    Algorithm:
      1. Load ordered stops from the DB (with lat/lon).
      2. For each stop that has an RBL, query the /monitor endpoint.
      3. Collect the minimum countdown for line_name at each stop index.
      4. For each consecutive stop pair (N, N+1) that has countdowns,
         compute how far between them a vehicle is using linear interpolation.
      5. Return one vehicle dict per inferred in-transit segment.

    This is intentionally approximate. Multiple vehicles on the same line
    are not tracked individually — only the nearest departure at each stop
    is used. Good enough for a visual "something is moving" indicator.
    """
    try:
        stops = db.get_line_stations(line_name)
    except Exception as exc:
        logger.warning("Cannot load stops for line %s: %s", line_name, exc)
        return []

    if not stops:
        logger.info("No stops found for line %s", line_name)
        return []

    stop_countdowns: dict[int, float] = {}
    stop_coords: dict[int, tuple[float, float]] = {}
    stop_names: dict[int, str] = {}

    for idx, stop in enumerate(stops):
        lat = stop.get("lat")
        lng = stop.get("lng")
        if lat is None or lng is None:
            continue
        stop_coords[idx] = (float(lat), float(lng))
        stop_names[idx] = stop.get("name", "")

        rbl_raw = str(stop.get("rbl") or stop.get("stop_code") or "").strip()
        if not rbl_raw:
            continue
        rbl_token = re.split(r"[,\s;]+", rbl_raw)[0].strip()
        if not rbl_token:
            continue

        data = fetch_vehicle_data(rbl_token)
        if not data or "data" not in data:
            time.sleep(0.05)
            continue

        min_cd: float | None = None
        for monitor in data["data"].get("monitors", []):
            for line_data in monitor.get("lines", []):
                if line_data.get("name", "").upper() != line_name.upper():
                    continue
                for dep in (line_data.get("departures") or {}).get("departure", []):
                    cd = dep.get("departureTime", {}).get("countdown")
                    if cd is not None:
                        if min_cd is None or float(cd) < min_cd:
                            min_cd = float(cd)

        if min_cd is not None:
            stop_countdowns[idx] = min_cd

        time.sleep(0.05)  # be gentle

    if len(stop_countdowns) < 2:
        logger.info("Insufficient countdown data for line %s (%d stops)", line_name,
                    len(stop_countdowns))
        return []

    vehicles: list[dict[str, Any]] = []
    sorted_idx = sorted(stop_countdowns.keys())

    for i in range(len(sorted_idx) - 1):
        n = sorted_idx[i]
        n1 = sorted_idx[i + 1]
        cd_n = stop_countdowns[n]
        cd_n1 = stop_countdowns[n1]

        # Travel time for this segment in minutes
        travel_time = cd_n1 - cd_n
        if travel_time <= 0:
            continue  # stops out of sequence or same vehicle hasn't moved

        # A vehicle is between N and N+1 when it has already left N
        # (cd_n <= 0) and hasn't yet reached N+1 (cd_n1 > 0).
        # Negative countdown means it departed that many minutes ago.
        if cd_n <= 0 and cd_n1 > 0:
            fraction = min(1.0, max(0.0, (-cd_n) / travel_time))
        else:
            continue

        if n not in stop_coords or n1 not in stop_coords:
            continue

        lat_a, lng_a = stop_coords[n]
        lat_b, lng_b = stop_coords[n1]

        vehicles.append({
            "id": f"{line_name}_seg{n}_{n1}",
            "type": _guess_vehicle_type(line_name),
            "line": line_name,
            "routeId": line_name,
            "lat": round(_lerp(lat_a, lat_b, fraction), 6),
            "lng": round(_lerp(lng_a, lng_b, fraction), 6),
            "coordinates": [round(_lerp(lng_a, lng_b, fraction), 6),
                            round(_lerp(lat_a, lat_b, fraction), 6)],
            "direction": "H",
            "towards": stop_names.get(n1, ""),
            "next_station": stop_names.get(n1, ""),
            "delay": 0,
            "countdown": int(cd_n1),
            "timestamp": datetime.utcnow().isoformat(),
            "platform": "",
            "barrier_free": True,
            "interpolated": True,
            "segment_from": stop_names.get(n, ""),
            "segment_to": stop_names.get(n1, ""),
            "segment_fraction": round(fraction, 3),
        })

    logger.info("Interpolated %d pseudo-vehicles for line %s", len(vehicles), line_name)
    return vehicles


# ---------------------------------------------------------------------------
# Shared response parser
# ---------------------------------------------------------------------------

def _calculate_delay(departure_time: dict[str, Any]) -> int:
    try:
        planned = departure_time.get("timePlanned")
        real = departure_time.get("timeReal")
        if planned and real:
            p = datetime.fromisoformat(planned.replace("Z", "+00:00"))
            r = datetime.fromisoformat(real.replace("Z", "+00:00"))
            return int((r - p).total_seconds() / 60)
        return 0
    except Exception:
        return 0


def _parse_monitor_response(
    data: dict[str, Any],
    line_filter: str | None,
    out: list[dict[str, Any]],
) -> None:
    """Parse a /monitor JSON response into vehicle dicts, appending to `out`."""
    for monitor in data.get("data", {}).get("monitors", []):
        coords = (monitor.get("locationStop", {})
                  .get("geometry", {})
                  .get("coordinates", [0, 0]))
        props = monitor.get("locationStop", {}).get("properties", {})
        stop_name = props.get("title", "")
        rbl_id = props.get("attributes", {}).get("rbl", "?")

        for line_data in monitor.get("lines", []):
            line_name = line_data.get("name", "")
            if line_filter and line_name.upper() != line_filter.upper():
                continue
            line_type = line_data.get("type", "unknown")
            for dep in (line_data.get("departures") or {}).get("departure", []):
                dep_time = dep.get("departureTime", {})
                out.append({
                    "id": f"{line_name}_{rbl_id}_{len(out)}",
                    "type": line_type.replace("pt", "").lower(),
                    "line": line_name,
                    "routeId": line_name,
                    "lat": coords[1] if len(coords) > 1 else 0,
                    "lng": coords[0] if coords else 0,
                    "coordinates": [coords[0] if coords else 0,
                                    coords[1] if len(coords) > 1 else 0],
                    "direction": line_data.get("direction", "H"),
                    "towards": line_data.get("towards", ""),
                    "next_station": stop_name,
                    "delay": _calculate_delay(dep_time),
                    "timestamp": datetime.utcnow().isoformat(),
                    "countdown": dep_time.get("countdown", 0),
                    "platform": line_data.get("platform", ""),
                    "barrier_free": line_data.get("barrierFree", False),
                    "interpolated": False,
                })


# ---------------------------------------------------------------------------
# RBL resolution helper
# ---------------------------------------------------------------------------

def _determine_rbls_for_lines(line_filters: set[str] | None) -> list[str]:
    if not line_filters:
        return []
    rbls: list[str] = []
    for line_name in line_filters:
        try:
            stations = db.get_line_stations(line_name)
        except Exception as exc:
            logger.warning("Failed to load stations for line %s: %s", line_name, exc)
            continue
        for st in stations:
            rbl_code = st.get("rbl") or st.get("stop_code")
            if not rbl_code:
                continue
            for part in re.split(r"[,\s;]+", str(rbl_code)):
                r = part.strip()
                if r and r not in rbls:
                    rbls.append(r)
        if len(rbls) >= MAX_RBLS_PER_LINE:
            break
    return rbls[:MAX_RBLS_PER_LINE]


# ---------------------------------------------------------------------------
# Snapshot refresh
# ---------------------------------------------------------------------------

def _refresh_vehicle_snapshot(
    station: str | None,
    line_filters: set[str] | None,
) -> dict[str, Any]:
    """
    Primary mode (line_filters set): interpolate pseudo-positions along the
    full line route, falling back to raw monitor data if interpolation fails.

    Station mode: departure board for a single stop.

    Default mode: coarse sample of a few major stops for a map overview.
    """
    vehicles: list[dict[str, Any]] = []
    successful = 0
    failed = 0

    if line_filters:
        for line_name in sorted(line_filters):
            line_veh = _interpolate_vehicles_for_line(line_name)
            if line_veh:
                vehicles.extend(line_veh)
                successful += 1
            else:
                # Fallback: raw departure board for first few stops
                rbls = _determine_rbls_for_lines({line_name})
                for rbl in rbls[:6]:
                    data = fetch_vehicle_data(rbl)
                    if data and "data" in data:
                        _parse_monitor_response(data, line_name, vehicles)
                        successful += 1
                    else:
                        failed += 1
                    time.sleep(0.1)

    elif station:
        data = fetch_vehicle_data(station)
        if data and "data" in data:
            _parse_monitor_response(data, None, vehicles)
            successful += 1
        else:
            failed += 1

    else:
        all_stations = data_loader.load_stations()
        sample_rbls: list[str] = []
        for st in all_stations:
            if not st.rbl:
                continue
            for token in re.split(r"[,\s;]+", st.rbl):
                t = token.strip()
                if t and t not in sample_rbls:
                    sample_rbls.append(t)
            if len(sample_rbls) >= 8:
                break
        for rbl in sample_rbls:
            data = fetch_vehicle_data(rbl)
            if data and "data" in data:
                _parse_monitor_response(data, None, vehicles)
                successful += 1
            else:
                failed += 1
            time.sleep(0.1)

    return {
        "vehicles": vehicles,
        "successful_requests": successful,
        "failed_requests": failed,
        "fetched_at": time.monotonic(),
    }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def collect_vehicle_data(
    vehicle_type: str = "all",
    line: str | None = None,
    station: str | None = None,
    lines: list[str] | None = None,
    use_cache_only: bool = False,
) -> dict[str, Any]:
    normalized_lines: list[str] = []
    if lines:
        normalized_lines = sorted({v.strip().upper() for v in lines if v})
    if line:
        normalized_lines = sorted({*normalized_lines, line.strip().upper()})

    cache_key = vehicle_cache_key(station, normalized_lines)

    with _vehicle_cache_lock:
        snapshot = _vehicle_snapshot_cache.get(cache_key)
        age = (time.monotonic() - snapshot["fetched_at"]) if snapshot else VEHICLE_CACHE_TTL + 1

    if age > VEHICLE_CACHE_TTL and not use_cache_only:
        raw_snapshot = _refresh_vehicle_snapshot(
            station, set(normalized_lines) if normalized_lines else None
        )
        with _vehicle_cache_lock:
            _vehicle_snapshot_cache[cache_key] = raw_snapshot
    elif snapshot:
        raw_snapshot = snapshot
    else:
        raw_snapshot = {"vehicles": [], "successful_requests": 0,
                        "failed_requests": 0, "fetched_at": time.monotonic()}

    vehicles = raw_snapshot["vehicles"]

    if vehicle_type and vehicle_type != "all":
        vt = vehicle_type.lower()
        vehicles = [v for v in vehicles if v.get("type", "").lower() == vt]

    if normalized_lines:
        lf = set(normalized_lines)
        vehicles = [v for v in vehicles if v.get("line", "").upper() in lf]

    logger.info("Vehicle snapshot: %d returned (type=%s lines=%s)",
                len(vehicles), vehicle_type, normalized_lines or "all")
    if not vehicles:
        logger.warning("Returning 0 vehicles")

    return {
        "vehicles": vehicles,
        "successful_requests": raw_snapshot["successful_requests"],
        "failed_requests": raw_snapshot["failed_requests"],
    }


def get_vehicle_summary(
    lines: Iterable[str] | None = None,
    station: str | None = None,
) -> dict[str, Any]:
    snapshot = collect_vehicle_data(
        vehicle_type="all",
        line=None,
        station=station,
        lines=list(lines) if lines else None,
    )
    vehicles = snapshot["vehicles"]

    per_type: dict[str, int] = {}
    lines_seen: dict[str, int] = {}
    delayed: list[dict[str, Any]] = []

    for v in vehicles:
        vt = v.get("type", "unknown").lower() or "unknown"
        per_type[vt] = per_type.get(vt, 0) + 1
        ln = v.get("line", "unknown")
        lines_seen[ln] = lines_seen.get(ln, 0) + 1
        delay = v.get("delay") or 0
        if delay > 0:
            delayed.append({"line": ln, "next_station": v.get("next_station", ""),
                            "delay": delay, "countdown": v.get("countdown"),
                            "timestamp": v.get("timestamp"), "type": vt})

    delayed.sort(key=lambda e: e["delay"], reverse=True)

    line_catalog = data_loader.get_gtfs_line_catalog() or []
    try:
        fallback = data_loader.load_lines()
        if not line_catalog:
            line_catalog = [{"name": l.name, "type": l.type, "color": l.color}
                            for l in fallback]
    except Exception:
        pass
    catalog = {str(item.get("name", "")).upper(): item for item in line_catalog}

    line_details = []
    for ln, count in sorted(lines_seen.items(), key=lambda x: x[1], reverse=True):
        lk = catalog.get(ln.upper()) or {}
        line_details.append({"name": ln, "count": count,
                              "type": lk.get("type", "Unknown"),
                              "color": f"#{lk.get('color', '2F855A')}"})

    return {
        "vehicles_total": len(vehicles),
        "vehicles_per_type": per_type,
        "vehicles_per_line": lines_seen,
        "line_details": line_details,
        "delayed": delayed[:10],
        "successful_requests": snapshot["successful_requests"],
        "failed_requests": snapshot["failed_requests"],
        "generated_at": datetime.utcnow().isoformat() + "Z",
    }


__all__ = [
    "collect_vehicle_data",
    "fetch_vehicle_data",
    "fetch_stop_departures",
    "fetch_traffic_info",
    "fetch_news",
    "clear_vehicle_cache",
    "vehicle_cache_key",
    "VEHICLE_CACHE_TTL",
]
