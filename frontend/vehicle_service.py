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
from zoneinfo import ZoneInfo

import requests

try:
    from .data_loader import data_loader
    from .database import db
except ImportError:  # pragma: no cover - runtime fallback when package context missing
    from data_loader import data_loader  # type: ignore
    from database import db  # type: ignore

logger = logging.getLogger(__name__)

# GTFS stop_times are published in local time (Europe/Vienna for this feed).
_VIENNA_TZ = ZoneInfo("Europe/Vienna")


def _now_local() -> datetime:
    """Current wall-clock time in the feed's local timezone."""
    return datetime.now(_VIENNA_TZ)

VEHICLE_CACHE_TTL = 60  # seconds
MAX_RBLS_PER_LINE = 30  # enough to cover a full line
# Lines shown by default (no line filter): schedule-interpolated pseudo
# vehicles. Trams with frequent headways look best "in motion".
DEFAULT_PSEUDO_LINES = ["12", "26", "1", "2", "D", "71"]
# Per-line cap so the default map stays light (multiple service variants can
# double-count the same corridor).
MAX_VEHICLES_PER_LINE = 60
_vehicle_snapshot_cache: dict[str, dict[str, Any]] = {}
_vehicle_cache_lock = threading.Lock()
_refresh_locks: dict[str, threading.Lock] = {}

# V1.4 API base - no sender param required
_WL_BASE = "http://www.wienerlinien.at/ogd_realtime"


# ---------------------------------------------------------------------------
# Low-level API helpers
# ---------------------------------------------------------------------------

def _get(url: str, params: dict | None = None, timeout: int = 6) -> dict | None:
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


def _parse_gtfs_seconds(t: str) -> int | None:
    """Parse GTFS HH:MM:SS (or H:MM:SS) to seconds-of-day.

    Times >= 24:00:00 (midnight-crossing trips) return None - those trips are
    excluded from schedule interpolation (v1 limitation).
    """
    try:
        parts = [int(p) for p in str(t).strip().split(":")]
        if len(parts) != 3:
            return None
        h, m, s = parts
        if h >= 24:
            return None
        return h * 3600 + m * 60 + s
    except (ValueError, TypeError):
        return None


def _schedule_pseudo_vehicles(line_name: str, now: datetime | None = None) -> list[dict[str, Any]]:
    """Interpolate pseudo-live vehicle markers from the GTFS schedule itself.

    There is no real-time GPS signal from the vehicles. But the schedule tells
    us exactly when each trip is supposed to depart each stop, so for every
    trip that is "on the road right now" (its previous stop was departed and
    its next stop has not been reached), we place a marker linearly between
    the two bracketing stops. One marker per active trip - correct for any
    headway, including frequent lines like tram 12.

    Returns the same payload shape as the countdown-based interpolation.
    """
    now = now or _now_local()
    now_s = now.hour * 3600 + now.minute * 60 + now.second

    # Push a time window into SQL so the 6.1M-row stop_times table is not
    # scanned in full: only rows whose bracket can contain "now" are fetched.
    # departure_time/arrival_time are "HH:MM:SS" strings - lexicographic
    # comparison is valid for times within the same day.
    def _fmt(seconds: int) -> str:
        seconds = max(0, min(seconds, 86399))
        return f"{seconds // 3600:02d}:{(seconds % 3600) // 60:02d}:{seconds % 60:02d}"

    win_start = _fmt(now_s - 2700)   # 45 min back
    win_end = _fmt(now_s + 3600)     # 60 min ahead

    rows = db.execute_query(
        """
        SELECT t.trip_id, t.trip_headsign, t.direction_id,
               st.stop_sequence, st.arrival_time, st.departure_time,
               s.stop_id, s.stop_name, s.stop_lat, s.stop_lon
        FROM routes r
        JOIN trips t ON t.route_id = r.route_id
        JOIN stop_times st ON st.trip_id = t.trip_id
        JOIN stops s ON s.stop_id = st.stop_id
        WHERE LOWER(r.route_short_name) = LOWER(:line)
          AND s.stop_lat IS NOT NULL AND s.stop_lon IS NOT NULL
          AND st.departure_time <= :win_end
          AND st.arrival_time >= :win_start
        ORDER BY t.trip_id, st.stop_sequence
        """,
        {"line": line_name, "win_start": win_start, "win_end": win_end},
    )
    if not rows:
        logger.info("No schedule rows for line %s", line_name)
        return []

    # Group rows by trip, preserving stop_sequence order
    trips: dict[str, list[dict]] = {}
    for row in rows:
        trips.setdefault(row["trip_id"], []).append(row)

    vehicles: list[dict[str, Any]] = []
    for trip_id, stops in trips.items():
        stops = sorted(stops, key=lambda r: int(r.get("stop_sequence") or 0))
        if len(stops) < 2:
            continue

        headsign = stops[0].get("trip_headsign") or ""
        direction_id = stops[0].get("direction_id")

        for i in range(len(stops) - 1):
            dep_s = _parse_gtfs_seconds(stops[i].get("departure_time") or "")
            arr_s = _parse_gtfs_seconds(stops[i + 1].get("arrival_time") or "")
            if dep_s is None or arr_s is None or arr_s <= dep_s:
                continue
            # Vehicle is on this segment when it has departed stop i
            # and has not yet arrived at stop i+1.
            if dep_s <= now_s < arr_s:
                fraction = min(1.0, max(0.0, (now_s - dep_s) / (arr_s - dep_s)))
                a = stops[i]
                b = stops[i + 1]
                lat = _lerp(float(a["stop_lat"]), float(b["stop_lat"]), fraction)
                lng = _lerp(float(a["stop_lon"]), float(b["stop_lon"]), fraction)
                vehicles.append({
                    "id": f"{line_name}_{trip_id[:12]}_{i}",
                    "type": _guess_vehicle_type(line_name),
                    "line": line_name,
                    "routeId": line_name,
                    "trip_id": trip_id,
                    "lat": round(lat, 6),
                    "lng": round(lng, 6),
                    "coordinates": [round(lng, 6), round(lat, 6)],
                    "direction": "R" if direction_id in (1, "1") else "H",
                    "towards": headsign or b["stop_name"],
                    "next_station": b["stop_name"],
                    "delay": 0,
                    "countdown": max(0, (arr_s - now_s) // 60),
                    "timestamp": now.isoformat(),
                    "platform": "",
                    "barrier_free": True,
                    "interpolated": True,
                    "schedule_based": True,
                    "segment_from": a["stop_name"],
                    "segment_to": b["stop_name"],
                    "segment_fraction": round(fraction, 3),
                })
                break  # one marker per trip

    if vehicles:
        logger.info("Schedule-interpolated %d pseudo-vehicles for line %s",
                    len(vehicles), line_name)
    return vehicles


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

    Preferred source: the GTFS schedule (stop_times in Postgres). For each
    trip that is between two stops right now, place a marker interpolated
    between the bracketing stop coordinates. This works at any headway.

    Fallback: query the live OGD /monitor countdown at every stop of the line
    and interpolate between stops with bracketing countdowns (best-effort for
    sparse service; unreliable at frequent headways because the monitor shows
    the next vehicle at each stop).
    """
    schedule = _schedule_pseudo_vehicles(line_name)
    if schedule:
        return schedule
    logger.info("Schedule interpolation empty for %s - falling back to countdowns", line_name)
    return _countdown_pseudo_vehicles(line_name)


def _countdown_pseudo_vehicles(line_name: str) -> list[dict[str, Any]]:
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
    are not tracked individually - only the nearest departure at each stop
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
    full line route from the GTFS schedule (stop_times in Postgres) - no
    dependency on the live WL API.

    Default mode (no filters): schedule-interpolated pseudo-vehicles for the
    DEFAULT_PSEUDO_LINES set. The Wiener Linien OGD API provides no vehicle
    positions (only incidents/blockages), so raw monitor scraping is NOT used
    for the map's vehicle layer.

    Station mode: departure board for a single stop (uses the OGD monitor
    API - requires the API key in production).
    """
    vehicles: list[dict[str, Any]] = []
    successful = 0
    failed = 0

    if line_filters:
        for line_name in sorted(line_filters):
            line_veh = _schedule_pseudo_vehicles(line_name)
            if line_veh:
                vehicles.extend(line_veh)
                successful += 1
            else:
                line_veh = _countdown_pseudo_vehicles(line_name)
                if line_veh:
                    vehicles.extend(line_veh)
                    successful += 1
                else:
                    failed += 1

    elif station:
        data = fetch_vehicle_data(station)
        if data and "data" in data:
            _parse_monitor_response(data, None, vehicles)
            successful += 1
        else:
            failed += 1

    else:
        for line_name in DEFAULT_PSEUDO_LINES:
            line_veh = _schedule_pseudo_vehicles(line_name)
            if line_veh:
                vehicles.extend(line_veh[:MAX_VEHICLES_PER_LINE])
                successful += 1
            else:
                failed += 1

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
        # Serialize refreshes per key: concurrent callers wait on one
        # computation instead of each scanning the schedule themselves.
        refresh_lock = _refresh_locks.setdefault(cache_key, threading.Lock())
        with refresh_lock:
            with _vehicle_cache_lock:
                snapshot = _vehicle_snapshot_cache.get(cache_key)
                age = (time.monotonic() - snapshot["fetched_at"]) if snapshot else VEHICLE_CACHE_TTL + 1
            if age > VEHICLE_CACHE_TTL:
                raw_snapshot = _refresh_vehicle_snapshot(
                    station, set(normalized_lines) if normalized_lines else None
                )
                with _vehicle_cache_lock:
                    _vehicle_snapshot_cache[cache_key] = raw_snapshot
            else:
                raw_snapshot = snapshot
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
