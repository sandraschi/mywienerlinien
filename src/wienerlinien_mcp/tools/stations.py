"""MCP tool for searching stations."""

import logging
import sys
from pathlib import Path

from fastmcp import FastMCP

# Add frontend to path for backend imports
_project_root = Path(__file__).parent.parent.parent.parent
_frontend_path = _project_root / "frontend"
if str(_frontend_path) not in sys.path:
    sys.path.insert(0, str(_frontend_path))

from wienerlinien_mcp.models.stations import Station, StationSearchResponse
from data_loader import data_loader

logger = logging.getLogger(__name__)


def register_station_search_tool(mcp: FastMCP) -> None:
    """Register the station_search tool with the MCP server."""
    
    @mcp.tool()
    async def station_search(
        query: str,
        limit: int = 10
    ) -> StationSearchResponse:
        """Find Vienna transit stations by name or location.
        
        Args:
            query: Search query (station name, partial match supported)
                 Examples: "Stephans", "Hauptbahnhof", "Schweden"
            limit: Maximum results to return (1-20, default: 10)
        
        Returns:
            List of matching stations with name, RBL, coordinates, type
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
            raise RuntimeError(f"Failed to search stations: {str(e)}") from e



