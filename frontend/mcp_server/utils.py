"""Shared utilities for MCP server tools."""

try:
    from ..data_loader import data_loader
except ImportError:
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).parent.parent))
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
