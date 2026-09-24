"""MCP tool for searching stations."""

import logging
from typing import Annotated

from fastmcp import FastMCP
from fastmcp.tools.tool import ToolAnnotations
from pydantic import Field

try:
    from ...data_loader import data_loader
    from ..models.stations import Station, StationSearchResponse
except ImportError:
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from data_loader import data_loader

    from wienerlinien_mcp.models.stations import Station, StationSearchResponse

logger = logging.getLogger(__name__)


def register_station_search_tool(mcp: FastMCP) -> None:
    """Register the station_search tool with the MCP server.

    This tool provides station search functionality for Vienna's public transport
    network. It searches through all stations (metro, tram, bus) and returns
    matching results with station details including coordinates and types.

    Args:
        mcp: FastMCP server instance to register the tool with
    """

    @mcp.tool(
        annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True, openWorldHint=True)
    )
    async def station_search(
        query: Annotated[str, Field(description="Search query: full name, partial name, or abbreviation. Examples: Stephans, Hauptbahnhof, HBF. Case-insensitive.")],
        limit: Annotated[int, Field(description="Maximum results to return, 1-20.", ge=1, le=20)] = 10,
    ) -> StationSearchResponse:
        """Find Vienna transit stations by name or location.

        Searches Vienna's public transport network for stations matching the
        query string. Supports partial matching, so users can search with
        incomplete station names. Results are prioritized by exact matches
        first, then partial matches. Case-insensitive, works with German
        and English names plus common abbreviations.

        ## Return Format
        {"query": str, "results": [{"name": str, "rbl": str | None, "type": "metro|tram|bus", "zone": str | None, "lat": float | None, "lng": float | None}], "count": int}

        ## Examples
        station_search(query="Stephans")
        station_search(query="Hauptbahnhof", limit=5)
        station_search(query="HBF")
        """
        try:
            # Validate limit
            limit = max(1, min(20, limit))

            # Load all stations
            all_stations = data_loader.load_stations()
            query_lower = query.lower().strip()

            # Search stations
            matches = []
            for station in all_stations:
                station_name_lower = station.name.lower()

                # Exact match gets highest priority
                if station_name_lower == query_lower:
                    matches.insert(0, station)
                # Partial match
                elif query_lower in station_name_lower or station_name_lower.startswith(query_lower[:3]):
                    matches.append(station)

            # Convert to Station models
            results = []
            for station in matches[:limit]:
                station_model = Station(
                    name=station.name,
                    rbl=station.rbl,
                    type=station.type,
                    zone=station.zone,
                    lat=station.lat,
                    lng=station.lng,
                )
                results.append(station_model)

            return StationSearchResponse(
                query=query,
                results=results,
                count=len(results),
            )

        except Exception as e:
            logger.error(f"Error searching stations: {e}", exc_info=True)
            raise RuntimeError(f"Failed to search stations: {e!s}") from e
