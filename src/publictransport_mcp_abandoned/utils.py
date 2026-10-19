"""Shared utilities for MCP server tools."""

import sys
from pathlib import Path

# Add frontend to path for backend imports
_project_root = Path(__file__).parent.parent.parent
_frontend_path = _project_root / "frontend"
if str(_frontend_path) not in sys.path:
    sys.path.insert(0, str(_frontend_path))

from data_loader import data_loader


def find_station_by_name(query: str) -> dict | None:
    """Find a station by name (fuzzy matching).

    Args:
        query: Station name to search for

    Returns:
        Station dict with name, rbl, type, zone, lat, lng, or None if not found
    """
    stations = data_loader.load_stations()
    query_lower = query.lower().strip()

    # Exact match
    for station in stations:
        if station.name.lower() == query_lower:
            return {
                "name": station.name,
                "rbl": station.rbl,
                "type": station.type,
                "zone": station.zone,
                "lat": station.lat,
                "lng": station.lng,
            }

    # Partial match
    for station in stations:
        if query_lower in station.name.lower() or station.name.lower() in query_lower:
            return {
                "name": station.name,
                "rbl": station.rbl,
                "type": station.type,
                "zone": station.zone,
                "lat": station.lat,
                "lng": station.lng,
            }

    return None
