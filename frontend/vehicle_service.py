"""Shared utilities for fetching and aggregating vehicle and traffic data."""

from __future__ import annotations

import logging
import re
import threading
import time
from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional, Set

import requests

try:
    from .data_loader import data_loader
    from .database import db
except ImportError:  # pragma: no cover - runtime fallback when package context missing
    from data_loader import data_loader  # type: ignore
    from database import db  # type: ignore

logger = logging.getLogger(__name__)

VEHICLE_CACHE_TTL = 30  # seconds
MAX_RBLS_PER_LINE = 12
_vehicle_snapshot_cache: Dict[str, Dict[str, Any]] = {}
_vehicle_cache_lock = threading.Lock()


def vehicle_cache_key(station: Optional[str], lines: Optional[Iterable[str]]) -> str:
    if station:
        return f"station:{station}"
    if lines:
        normalized = ",".join(sorted({str(line).strip().upper() for line in lines if line}))
        if normalized:
            return f"lines:{normalized}"
    return "__default__"


def clear_vehicle_cache() -> None:
    with _vehicle_cache_lock:
        _vehicle_snapshot_cache.clear()


def fetch_vehicle_data(rbl_number: str) -> Optional[Dict[str, Any]]:
    """Fetch vehicle data from the Wiener Linien API for a specific RBL."""

    try:
        url = "https://www.wienerlinien.at/ogd_realtime/monitor"
        params = {
            "rbl": rbl_number,
            "sender": "mywienerlinien.live-map@example.com",
        }
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as exc:
        logger.error("API request failed for RBL %s: %s", rbl_number, exc)
        return None


def fetch_traffic_info() -> Optional[Dict[str, Any]]:
    try:
        url = "https://www.wienerlinien.at/ogd_realtime/trafficInfo"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as exc:
        logger.error("Error fetching traffic info: %s", exc)
        return None


def fetch_news() -> Optional[Dict[str, Any]]:
    try:
        url = "https://www.wienerlinien.at/ogd_realtime/news"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as exc:
        logger.error("Error fetching news: %s", exc)
        return None


def _calculate_delay(departure_time: Dict[str, Any]) -> int:
    try:
        planned_time = departure_time.get("timePlanned")
        real_time = departure_time.get("timeReal")
        if planned_time and real_time:
            planned = datetime.fromisoformat(planned_time.replace("Z", "+00:00"))
            real = datetime.fromisoformat(real_time.replace("Z", "+00:00"))
            delay_seconds = (real - planned).total_seconds()
            return int(delay_seconds / 60)
        return 0
    except Exception:
        return 0


def collect_vehicle_data(
    vehicle_type: str = "all",
    line: Optional[str] = None,
    station: Optional[str] = None,
    lines: Optional[List[str]] = None,
) -> Dict[str, Any]:
    normalized_lines: List[str] = []
    if lines:
        normalized_lines = sorted({value.strip().upper() for value in lines if value})

    if line:
        normalized_lines = sorted({*normalized_lines, line.strip().upper()})

    cache_key = vehicle_cache_key(station, normalized_lines)

    with _vehicle_cache_lock:
        snapshot = _vehicle_snapshot_cache.get(cache_key)
        if snapshot:
            age = time.monotonic() - snapshot["fetched_at"]
        else:
            age = VEHICLE_CACHE_TTL + 1

        if age > VEHICLE_CACHE_TTL:
            raw_snapshot = _refresh_vehicle_snapshot(station, set(normalized_lines) if normalized_lines else None)
            _vehicle_snapshot_cache[cache_key] = raw_snapshot
        else:
            raw_snapshot = snapshot  # type: ignore[assignment]

    vehicles = raw_snapshot["vehicles"]

    if vehicle_type and vehicle_type != "all":
        vehicle_type_normalized = vehicle_type.lower()
        vehicles = [
            vehicle for vehicle in vehicles if vehicle["type"].lower() == vehicle_type_normalized
        ]

    line_filters: set[str] = set(normalized_lines)

    if line_filters:
        vehicles = [
            vehicle
            for vehicle in vehicles
            if vehicle.get("line", "").upper() in line_filters
        ]

    logger.info(
        "Vehicle snapshot filtered",
        extra={
            "vehicle_type": vehicle_type,
            "station": station,
            "line_filters": sorted(line_filters) if line_filters else None,
            "total_available": len(raw_snapshot["vehicles"]),
            "total_returned": len(vehicles),
        },
    )

    return {
        "vehicles": vehicles,
        "successful_requests": raw_snapshot["successful_requests"],
        "failed_requests": raw_snapshot["failed_requests"],
    }


def get_vehicle_summary(
    lines: Optional[Iterable[str]] = None,
    station: Optional[str] = None,
) -> Dict[str, Any]:
    """Return aggregated statistics for dashboards."""
    snapshot = collect_vehicle_data(
        vehicle_type="all",
        line=None,
        station=station,
        lines=list(lines) if lines else None,
    )
    vehicles = snapshot["vehicles"]

    per_type: Dict[str, int] = {}
    lines_seen: Dict[str, int] = {}
    delayed: List[Dict[str, Any]] = []

    for vehicle in vehicles:
        vehicle_type = vehicle.get("type", "unknown").lower() or "unknown"
        per_type[vehicle_type] = per_type.get(vehicle_type, 0) + 1

        line_name = vehicle.get("line", "unknown")
        lines_seen[line_name] = lines_seen.get(line_name, 0) + 1

        delay = vehicle.get("delay") or 0
        if delay and delay > 0:
            delayed.append(
                {
                    "line": line_name,
                    "next_station": vehicle.get("next_station", ""),
                    "delay": delay,
                    "countdown": vehicle.get("countdown"),
                    "timestamp": vehicle.get("timestamp"),
                    "type": vehicle_type,
                }
            )

    delayed.sort(key=lambda entry: entry["delay"], reverse=True)

    line_catalog = data_loader.get_gtfs_line_catalog()
    if not line_catalog:
        fallback_lines = data_loader.load_lines()
        line_catalog = [
            {
                "name": line.name,
                "type": line.type,
                "color": line.color,
            }
            for line in fallback_lines
        ]
    catalog_lookup = {str(item.get("name", "")).upper(): item for item in line_catalog}

    line_details = []
    for line_name, count in sorted(lines_seen.items(), key=lambda item: item[1], reverse=True):
        lookup = catalog_lookup.get(line_name.upper()) or {}
        line_details.append(
            {
                "name": line_name,
                "count": count,
                "type": lookup.get("type", "Unknown"),
                "color": f"#{lookup.get('color', '2F855A')}",
            }
        )

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


def _refresh_vehicle_snapshot(station: Optional[str], line_filters: Optional[Set[str]]) -> Dict[str, Any]:
    vehicles: List[Dict[str, Any]] = []
    successful_requests = 0
    failed_requests = 0

    if station:
        stations_to_query = [station]
    else:
        stations_to_query = _determine_rbls_for_lines(line_filters)

    if not stations_to_query:
        all_stations = data_loader.load_stations()
        major_stations: List[str] = []
        for station_info in all_stations:
            if not station_info.rbl:
                continue
            for token in re.split(r"[,\s;]+", station_info.rbl):
                rbl_token = token.strip()
                if rbl_token and rbl_token not in major_stations:
                    major_stations.append(rbl_token)
            if len(major_stations) >= MAX_RBLS_PER_LINE:
                break
        stations_to_query = major_stations[:MAX_RBLS_PER_LINE]

    logger.debug(
        "Refreshing vehicle snapshot",
        extra={
            "station": station,
            "line_filters": sorted(line_filters) if line_filters else None,
            "rbl_count": len(stations_to_query),
        },
    )

    for idx, rbl in enumerate(stations_to_query):
        data = fetch_vehicle_data(rbl)
        if data and "data" in data and "monitors" in data["data"]:
            matched_requested_line = False
            for monitor in data["data"]["monitors"]:
                lines = monitor.get("lines") or []
                for line_data in lines:
                    line_name = line_data.get("name", "")
                    if line_filters and line_name.upper() not in line_filters:
                        continue
                    matched_requested_line = True
                    line_type = line_data.get("type", "unknown")
                    departures = line_data.get("departures", {}).get("departure", [])
                    if not isinstance(departures, list):
                        departures = [departures] if departures else []
                    for departure in departures:
                        vehicle_info = departure.get("vehicle")
                        if not vehicle_info:
                            continue
                        departure_time = departure.get("departureTime", {})
                        coordinates = (
                            monitor.get("locationStop", {})
                            .get("geometry", {})
                            .get("coordinates", [0, 0])
                        )
                        properties = monitor.get("locationStop", {}).get("properties", {})
                        vehicle_entry = {
                            "id": f"{line_name}_{rbl}_{len(vehicles)}",
                            "type": line_type.replace("pt", "").lower(),
                            "line": line_name,
                            "lat": coordinates[1] if len(coordinates) > 1 else 0,
                            "lng": coordinates[0] if coordinates else 0,
                            "direction": vehicle_info.get("towards", ""),
                            "next_station": properties.get("title", ""),
                            "delay": _calculate_delay(departure_time),
                            "timestamp": datetime.utcnow().isoformat(),
                            "countdown": departure_time.get("countdown", 0),
                            "platform": vehicle_info.get("platform", ""),
                            "barrier_free": vehicle_info.get("barrierFree", False),
                        }
                        vehicles.append(vehicle_entry)
            if matched_requested_line:
                successful_requests += 1
            else:
                failed_requests += 1
        else:
            failed_requests += 1
        if idx != len(stations_to_query) - 1:
            time.sleep(0.2)
        if (line_filters and successful_requests >= 3) or len(vehicles) >= 50:
            break

    return {
        "vehicles": vehicles,
        "successful_requests": successful_requests,
        "failed_requests": failed_requests,
        "fetched_at": time.monotonic(),
    }


def _determine_rbls_for_lines(line_filters: Optional[Set[str]]) -> List[str]:
    if not line_filters:
        return []

    rbls: List[str] = []

    for line_name in line_filters:
        try:
            stations = db.get_line_stations(line_name)
        except Exception as exc:
            logger.warning("Failed to load stations for line %s: %s", line_name, exc)
            continue

        for station in stations:
            rbl_code = station.get("rbl") or station.get("stop_code")
            if not rbl_code:
                continue
            parts = re.split(r"[,\s;]+", str(rbl_code))
            for part in parts:
                rbl = part.strip()
                if rbl and rbl not in rbls:
                    rbls.append(rbl)

        if len(rbls) >= MAX_RBLS_PER_LINE:
            break

    limited = rbls[:MAX_RBLS_PER_LINE]
    if limited:
        logger.debug(
            "Derived RBLs for lines",
            extra={"lines": sorted(line_filters), "rbl_sample": limited[:5], "total": len(limited)},
        )
    else:
        logger.info(
            "No RBLs resolved for requested lines; falling back to major stations",
            extra={"lines": sorted(line_filters)},
        )
    return limited


__all__ = [
    "collect_vehicle_data",
    "fetch_vehicle_data",
    "fetch_traffic_info",
    "fetch_news",
    "clear_vehicle_cache",
    "vehicle_cache_key",
    "VEHICLE_CACHE_TTL",
]

