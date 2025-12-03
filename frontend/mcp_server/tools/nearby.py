"""Nearby stops tool for Vienna Transit MCP."""

import math
from typing import Optional

from fastmcp import FastMCP
from pydantic import BaseModel, Field


class NearbyStop(BaseModel):
    """A stop near the specified location."""

    name: str = Field(..., description="Stop name")
    rbl: Optional[str] = Field(None, description="RBL code")
    type: str = Field(..., description="Stop type (metro, tram, bus)")
    distance_meters: int = Field(..., description="Distance from search point in meters")
    lat: float = Field(..., description="Latitude")
    lng: float = Field(..., description="Longitude")
    lines: list[str] = Field(default_factory=list, description="Lines serving this stop")


class NearbyStopsResponse(BaseModel):
    """Response containing nearby stops."""

    lat: float = Field(..., description="Search latitude")
    lng: float = Field(..., description="Search longitude")
    radius_meters: int = Field(..., description="Search radius used")
    stops: list[NearbyStop] = Field(..., description="Nearby stops sorted by distance")
    count: int = Field(..., description="Number of stops found")


def _haversine_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Calculate distance between two coordinates in meters."""
    R = 6371000  # Earth's radius in meters

    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lng2 - lng1)

    a = (
        math.sin(delta_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c


def register_nearby_stops_tool(mcp: FastMCP) -> None:
    """Register the nearby_stops tool with the MCP server."""

    @mcp.tool()
    async def nearby_stops(
        lat: float,
        lng: float,
        radius: int = 500,
        limit: int = 10,
    ) -> NearbyStopsResponse:
        """Find transit stops near a location.

        Searches for metro stations, tram stops, and bus stops within the
        specified radius of the given coordinates. Results are sorted by
        distance from closest to farthest.

        Args:
            lat: Latitude of search center (e.g., 48.2082 for Vienna center)
            lng: Longitude of search center (e.g., 16.3738 for Vienna center)
            radius: Search radius in meters (default 500, max 2000)
            limit: Maximum stops to return (default 10, max 50)

        Returns:
            NearbyStopsResponse containing:
                - lat/lng: Search coordinates used
                - radius_meters: Search radius used
                - stops: List of nearby stops with distance
                - count: Number of stops found

        Raises:
            ValueError: If coordinates are outside Vienna area

        Example:
            >>> result = await nearby_stops(48.2082, 16.3738, radius=300)
            >>> for stop in result.stops[:3]:
            ...     print(f"{stop.name}: {stop.distance_meters}m")
            Stephansplatz: 50m
            Stephansplatz: 65m
            Graben: 180m
        """
        # Validate coordinates (rough Vienna bounding box)
        if not (48.1 <= lat <= 48.35 and 16.1 <= lng <= 16.6):
            raise ValueError(
                f"Coordinates ({lat}, {lng}) appear to be outside Vienna. "
                "Vienna coordinates are approximately lat: 48.1-48.35, lng: 16.1-16.6"
            )

        # Clamp radius and limit
        radius = max(50, min(2000, radius))
        limit = max(1, min(50, limit))

        # Load stations from database
        try:
            from data_loader import data_loader

            all_stations = data_loader.load_stations()
        except Exception as e:
            raise RuntimeError(f"Failed to load station data: {e}")

        # Find stops within radius
        nearby = []
        for station in all_stations:
            if station.lat is None or station.lng is None:
                continue

            distance = _haversine_distance(lat, lng, station.lat, station.lng)
            if distance <= radius:
                nearby.append(
                    NearbyStop(
                        name=station.name,
                        rbl=station.rbl,
                        type=station.type,
                        distance_meters=int(distance),
                        lat=station.lat,
                        lng=station.lng,
                        lines=[],  # TODO: Add line info from GTFS
                    )
                )

        # Sort by distance and limit
        nearby.sort(key=lambda s: s.distance_meters)
        nearby = nearby[:limit]

        return NearbyStopsResponse(
            lat=lat,
            lng=lng,
            radius_meters=radius,
            stops=nearby,
            count=len(nearby),
        )
