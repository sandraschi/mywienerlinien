"""MCP tool for searching stations."""

import logging

from fastmcp import FastMCP

try:
    from ...data_loader import data_loader
    from ..models.stations import Station, StationSearchResponse
except ImportError:
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from data_loader import data_loader
    from mcp_server.models.stations import Station, StationSearchResponse

logger = logging.getLogger(__name__)


def register_station_search_tool(mcp: FastMCP) -> None:
    """Register the station_search tool with the MCP server.

    This tool provides station search functionality for Vienna's public transport
    network. It searches through all stations (metro, tram, bus) and returns
    matching results with station details including coordinates and types.

    Args:
        mcp: FastMCP server instance to register the tool with
    """

    @mcp.tool()
    async def station_search(query: str, limit: int = 10) -> StationSearchResponse:
        """Find Vienna transit stations by name or location.

        Searches Vienna's public transport network for stations matching the
        query string. Supports partial matching, so users can search with
        incomplete station names. Results are prioritized by exact matches
        first, then partial matches.

        The search is case-insensitive and works with both German and English
        station names. Common abbreviations are also supported (e.g., "HBF"
        for "Hauptbahnhof").

        Args:
            query (str): Search query string. Can be a full station name, partial
                name, or abbreviation. Examples: "Stephans", "Hauptbahnhof",
                "Schweden", "HBF", "Stephansplatz".
            limit (int): Maximum number of results to return. Must be between 1
                and 20. Default is 10. Higher limits provide more options but
                may include less relevant matches.

        Returns:
            StationSearchResponse: Response containing:
                - query (str): The original search query
                - results (List[Station]): List of Station objects with:
                    * name (str): Full station name
                    * rbl (str, optional): RBL code (Vienna-specific station identifier)
                    * type (str): Station type (metro, tram, bus)
                    * zone (str, optional): Fare zone (typically "100" for most of Vienna)
                    * lat (float, optional): Latitude coordinate
                    * lng (float, optional): Longitude coordinate
                - count (int): Number of results returned

        Raises:
            RuntimeError: If search fails or data cannot be loaded.

        Example:
            >>> result = await station_search("Stephans", limit=5)
            >>> print(f"Found {result.count} stations matching '{result.query}'")
            Found 2 stations matching 'Stephans'
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
                elif query_lower in station_name_lower or station_name_lower.startswith(
                    query_lower[:3]
                ):
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
            raise RuntimeError(f"Failed to search stations: {str(e)}") from e
