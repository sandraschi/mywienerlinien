"""
Data Loader Module for Wiener Linien Live Map

This module provides functions to load and parse structured data files
containing information about lines, stations, routes, and disruptions.
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


def _normalize_hex_color(value: Optional[str]) -> str:
    if not value:
        return "#3F51B5"
    cleaned = str(value).strip().lstrip("#")
    if not cleaned:
        return "#3F51B5"
    if len(cleaned) not in {3, 6}:
        cleaned = cleaned[:6].ljust(6, "0")
    return f"#{cleaned.upper()}"


@dataclass
class Station:
    """Represents a transport station/stop."""

    name: str
    rbl: str
    type: str
    zone: str
    lat: Optional[float] = None
    lng: Optional[float] = None


@dataclass
class Line:
    """Represents a transport line."""

    name: str
    type: str
    color: str
    length: str
    stations: int
    description: str
    frequency: str
    operating_hours: str


@dataclass
class Route:
    """Represents a transport route."""

    line: str
    type: str
    color: str
    length: str
    stations: int
    description: str
    coordinates: List[List[float]]
    stops: List[Dict[str, Any]]


@dataclass
class Disruption:
    """Represents a service disruption."""

    id: str
    line: str
    type: str
    severity: str
    description: str
    affected_stations: List[str]
    start_time: datetime
    end_time: Optional[datetime]
    status: str


class DataLoader:
    """Main data loader class for parsing structured data files."""

    def __init__(self, data_dir: str = "data"):
        """Initialize the data loader (data_dir kept for backward compatibility but not used)."""
        self.data_dir = data_dir
        self._lines_cache = None
        self._stations_cache = None
        self._routes_cache = None
        self._disruptions_cache = None
        self._last_loaded = {}

    def load_lines(self, force_reload: bool = False) -> List[Line]:
        """Load all transport lines from the database."""
        if not force_reload and self._lines_cache is not None:
            return self._lines_cache

        db_target = None
        try:
            from .database import ROUTE_TYPE_NAMES as route_type_names
            from .database import db as db_rel

            db_target = db_rel
        except Exception:
            try:
                from database import ROUTE_TYPE_NAMES as route_type_names
                from database import db as db_abs  # type: ignore

                db_target = db_abs
            except Exception as exc:
                logger.error("Database unavailable for loading lines: %s", exc)
                self._lines_cache = []
                return self._lines_cache

        try:
            routes = db_target.get_routes()
            lines = []
            seen_names = set()

            for route in routes:
                short_name = (route.get("route_short_name") or "").strip()
                if not short_name or short_name.upper() in seen_names:
                    continue
                seen_names.add(short_name.upper())

                route_type_code = route.get("route_type", 3)
                route_type_name = route_type_names.get(route_type_code, "Unknown")
                color = _normalize_hex_color(route.get("route_color"))
                description = route.get("route_long_name") or ""

                lines.append(
                    Line(
                        name=short_name,
                        type=route_type_name,
                        color=color,
                        length="",  # Not available in GTFS
                        stations=int(route.get("stop_count") or 0),
                        description=description,
                        frequency="",  # Not available in GTFS
                        operating_hours="",  # Not available in GTFS
                    )
                )

            self._lines_cache = lines
            self._last_loaded["lines"] = datetime.now()
            logger.info(f"Loaded {len(self._lines_cache)} lines from database")
        except Exception as exc:
            logger.error("Failed to load lines from database: %s", exc)
            self._lines_cache = []

        return self._lines_cache

    def get_line_by_name(self, line_name: str) -> Optional[Line]:
        """Return a line definition by its short name from the database."""
        if not line_name:
            return None

        normalized = line_name.strip().lower()
        for line in self.load_lines():
            if line.name.lower() == normalized:
                return line
        return None

    def get_gtfs_line_catalog(self) -> List[Dict[str, Any]]:
        """Return line catalog merged with GTFS metadata from the database."""
        ROUTE_TYPE_NAMES_local = None
        db_local = None

        try:
            from .database import ROUTE_TYPE_NAMES as route_type_names_rel
            from .database import db as db_rel

            ROUTE_TYPE_NAMES_local = route_type_names_rel
            db_local = db_rel
        except Exception:
            try:
                from database import ROUTE_TYPE_NAMES as route_type_names_abs  # type: ignore
                from database import db as db_abs

                ROUTE_TYPE_NAMES_local = route_type_names_abs
                db_local = db_abs
            except Exception as exc:  # pragma: no cover - defensive
                logger.warning("GTFS catalog unavailable: %s", exc)
                return []

        try:
            routes = db_local.get_routes()
        except Exception as exc:
            logger.error("Failed to load routes from database: %s", exc)
            return []

        catalog: List[Dict[str, Any]] = []
        seen: set[str] = set()

        for route in routes:
            short_name = (route.get("route_short_name") or "").strip()
            if not short_name:
                continue
            key = short_name.upper()
            if key in seen:
                continue
            seen.add(key)

            route_type_code = route.get("route_type")
            route_type_name = ROUTE_TYPE_NAMES_local.get(route_type_code, "Unknown")

            description = route.get("route_long_name") or ""
            color = route.get("route_color") or "#3F51B5"

            catalog.append(
                {
                    "name": short_name,
                    "type": route_type_name,
                    "type_code": route_type_code,
                    "color": _normalize_hex_color(color),
                    "description": description,
                    "agency": route.get("agency_name"),
                    "trip_count": int(route.get("trip_count") or 0),
                    "stop_count": int(route.get("stop_count") or 0),
                }
            )

        return sorted(catalog, key=lambda entry: entry["name"])

    def get_gtfs_route(self, line_name: str) -> Optional[Dict[str, Any]]:
        db_target = None
        try:
            from .database import db as db_rel

            db_target = db_rel
        except Exception:
            try:
                from database import db as db_abs  # type: ignore

                db_target = db_abs
            except Exception:
                db_target = None
        if db_target is None:
            logger.warning("GTFS route unavailable: database module missing")
            return None

        try:
            return db_target.get_line_route_data(line_name)
        except Exception as exc:
            logger.error("Failed to load route data for %s: %s", line_name, exc)
            return None

    def get_gtfs_line_stations(self, line_name: str) -> List[Dict[str, Any]]:
        db_target = None
        try:
            from .database import db as db_rel

            db_target = db_rel
        except Exception:
            try:
                from database import db as db_abs  # type: ignore

                db_target = db_abs
            except Exception:
                db_target = None
        if db_target is None:
            logger.warning("GTFS station lookup unavailable: database module missing")
            return []

        try:
            return db_target.get_line_stations(line_name)
        except Exception as exc:
            logger.error("Failed to load stations for %s: %s", line_name, exc)
            return []

    def load_stations(self, force_reload: bool = False) -> List[Station]:
        """Load station data from the database."""
        if not force_reload and self._stations_cache is not None:
            return self._stations_cache

        logger.info("Loading stations from database...")

        db_target = None
        try:
            from .database import db as db_rel

            db_target = db_rel
        except Exception:
            try:
                from database import db as db_abs  # type: ignore

                db_target = db_abs
            except Exception as exc:
                logger.error("Database unavailable for loading stations: %s", exc)
                self._stations_cache = []
                return self._stations_cache

        try:
            db_stations = db_target.get_stations()
            stations = []

            for db_station in db_stations:
                # Parse RBL from stop_code (can be comma-separated)
                rbl = db_station.get("rbl") or ""
                if isinstance(rbl, str):
                    rbl = rbl.strip()

                station_type = db_station.get("type", "Unknown")
                zone = db_station.get("zone") or "100"
                lat = db_station.get("lat")
                lng = db_station.get("lng")

                stations.append(
                    Station(
                        name=db_station.get("name", ""),
                        rbl=str(rbl) if rbl else "",
                        type=station_type,
                        zone=str(zone),
                        lat=float(lat) if lat is not None else None,
                        lng=float(lng) if lng is not None else None,
                    )
                )

            self._stations_cache = stations
            self._last_loaded["stations"] = datetime.now()
            logger.info(f"Loaded {len(stations)} stations from database")
        except Exception as exc:
            logger.error("Failed to load stations from database: %s", exc)
            self._stations_cache = []

        return self._stations_cache

    def load_routes(self, force_reload: bool = False) -> List[Route]:
        """Load all routes from the database."""
        if not force_reload and self._routes_cache is not None:
            return self._routes_cache

        db_target = None
        try:
            from .database import ROUTE_TYPE_NAMES as route_type_names
            from .database import db as db_rel

            db_target = db_rel
        except Exception:
            try:
                from database import ROUTE_TYPE_NAMES as route_type_names
                from database import db as db_abs  # type: ignore

                db_target = db_abs
            except Exception as exc:
                logger.error("Database unavailable for loading routes: %s", exc)
                self._routes_cache = []
                return self._routes_cache

        try:
            db_routes = db_target.get_routes()
            routes = []
            seen_names = set()

            for db_route in db_routes:
                short_name = (db_route.get("route_short_name") or "").strip()
                if not short_name or short_name.upper() in seen_names:
                    continue
                seen_names.add(short_name.upper())

                # Get route geometry and stops
                route_data = db_target.get_line_route_data(short_name)
                if not route_data:
                    continue

                route_type_code = db_route.get("route_type", 3)
                route_type_name = route_type_names.get(route_type_code, "Unknown")
                color = _normalize_hex_color(db_route.get("route_color"))
                description = db_route.get("route_long_name") or ""

                # Extract coordinates from segments
                coordinates = []
                for segment in route_data.get("segments", []):
                    coordinates.extend(segment.get("coordinates", []))

                # Get stops
                stops = route_data.get("stops", [])

                routes.append(
                    Route(
                        line=short_name,
                        type=route_type_name,
                        color=color,
                        length="",  # Not available in GTFS
                        stations=len(stops),
                        description=description,
                        coordinates=coordinates,
                        stops=stops,
                    )
                )

            self._routes_cache = routes
            self._last_loaded["routes"] = datetime.now()
            logger.info(f"Loaded {len(self._routes_cache)} routes from database")
        except Exception as exc:
            logger.error("Failed to load routes from database: %s", exc)
            self._routes_cache = []

        return self._routes_cache

    def get_station_by_rbl(self, rbl: str) -> Optional[Station]:
        """Get a specific station by RBL number."""
        stations = self.load_stations()
        for station in stations:
            if station.rbl == rbl:
                return station
        return None

    def get_route_by_line(self, line_name: str) -> Optional[Route]:
        """Get a specific route by line name."""
        routes = self.load_routes()
        for route in routes:
            if route.line == line_name:
                return route
        return None

    def get_lines_by_type(self, line_type: str) -> List[Line]:
        """Get all lines of a specific type."""
        lines = self.load_lines()
        return [line for line in lines if line.type.lower() == line_type.lower()]

    def get_stations_by_type(self, station_type: str) -> List[Station]:
        """Get all stations of a specific type."""
        stations = self.load_stations()
        return [station for station in stations if station.type.lower() == station_type.lower()]

    def clear_cache(self):
        """Clear all cached data."""
        self._lines_cache = None
        self._stations_cache = None
        self._routes_cache = None
        self._disruptions_cache = None
        self._last_loaded = {}
        logger.info("Data cache cleared")

    def get_cache_status(self) -> Dict[str, Any]:
        """Get the status of cached data."""
        serialized_last_loaded = {
            key: value.isoformat() if isinstance(value, datetime) else value
            for key, value in self._last_loaded.items()
        }
        return {
            "lines_loaded": self._lines_cache is not None,
            "stations_loaded": self._stations_cache is not None,
            "routes_loaded": self._routes_cache is not None,
            "disruptions_loaded": self._disruptions_cache is not None,
            "last_loaded": serialized_last_loaded,
        }


# Global data loader instance
data_loader = DataLoader()
