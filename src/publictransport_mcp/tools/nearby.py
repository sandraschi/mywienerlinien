"""Nearby stops tool for Vienna Transit MCP."""

import math
from typing import Annotated

from fastmcp import FastMCP
from mcp.types import ToolAnnotations
from pydantic import BaseModel, Field


class NearbyStop(BaseModel):
    """A stop near the specified location."""

    name: str = Field(..., description="Stop name")
    rbl: str | None = Field(None, description="RBL code")
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
    radius_earth = 6371000  # Earth's radius in meters

    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lng2 - lng1)

    a = math.sin(delta_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return radius_earth * c


def register_nearby_stops_tool(mcp: FastMCP) -> None:
    """Register the nearby_stops tool with the MCP server."""

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True, openWorldHint=True))
    async def nearby_stops(
        lat: Annotated[
            float,
            Field(description="Search center latitude (e.g. 48.2082 for Vienna center). Must be within 48.1-48.35."),
        ],
        lng: Annotated[
            float,
            Field(description="Search center longitude (e.g. 16.3738 for Vienna center). Must be within 16.1-16.6."),
        ],
        radius: Annotated[int, Field(description="Search radius in meters, 50-2000.", ge=50, le=2000)] = 500,
        limit: Annotated[int, Field(description="Maximum stops to return, 1-50.", ge=1, le=50)] = 10,
    ) -> NearbyStopsResponse:
        """Find transit stops near a location.

        Searches for metro stations, tram stops, and bus stops within the
        specified radius of the given coordinates. Results are sorted by
        distance from closest to farthest.

        ## Return Format
        {"lat": float, "lng": float, "radius_meters": int, "stops": [{"name": str, "rbl": str | None, "type": "metro|tram|bus", "distance_meters": int, "lat": float, "lng": float, "lines": list[str]}], "count": int}

        ## Examples
        nearby_stops(lat=48.2082, lng=16.3738)
        nearby_stops(lat=48.2082, lng=16.3738, radius=300)
        nearby_stops(lat=48.2082, lng=16.3738, radius=1000, limit=5)
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

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True, openWorldHint=True))
    async def find_nearby_stations(
        latitude: Annotated[float, Field(description="Location latitude (e.g. 48.2082 for Vienna center).")],
        longitude: Annotated[float, Field(description="Location longitude (e.g. 16.3738 for Vienna center).")],
        radius_km: Annotated[float, Field(description="Search radius in kilometers.", ge=0.05, le=2.0)] = 1.0,
        max_results: Annotated[int, Field(description="Maximum stations to return.", ge=1, le=50)] = 10,
    ) -> NearbyStopsResponse:
        """Find transit stations near a specific location.

        Legacy-compatible alias for nearby_stops using kilometers for the
        radius. Converts the radius to meters and delegates to nearby_stops.

        ## Return Format
        {"lat": float, "lng": float, "radius_meters": int, "stops": [{"name": str, "rbl": str | None, "type": "metro|tram|bus", "distance_meters": int, "lat": float, "lng": float, "lines": list[str]}], "count": int}

        ## Examples
        find_nearby_stations(latitude=48.2082, longitude=16.3738)
        find_nearby_stations(latitude=48.2082, longitude=16.3738, radius_km=0.5, max_results=5)
        """
        return await nearby_stops(lat=latitude, lng=longitude, radius=int(radius_km * 1000), limit=max_results)
