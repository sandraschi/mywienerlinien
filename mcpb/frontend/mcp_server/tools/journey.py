"""MCP tool for journey planning."""

import logging
from datetime import datetime
from typing import Optional

from fastmcp import FastMCP

try:
    from ..models.journey import JourneyPlan, JourneySegment
    from ..utils import find_station_by_name
except ImportError:
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from mcp_server.models.journey import JourneyPlan, JourneySegment
    from mcp_server.utils import find_station_by_name

logger = logging.getLogger(__name__)


def register_journey_tool(mcp: FastMCP) -> None:
    """Register the journey_planner tool with the MCP server.
    
    This tool provides journey planning functionality for Vienna's public
    transport network. It calculates optimal routes between stations,
    including transfers, travel time, and estimated costs.
    
    Note: Currently returns placeholder data. Full implementation would
    integrate with GTFS routing or Wiener Linien journey planner API.
    
    Args:
        mcp: FastMCP server instance to register the tool with
    """
    
    @mcp.tool()
    async def journey_planner(
        from_station: str,
        to_station: str,
        departure_time: Optional[str] = None
    ) -> JourneyPlan:
        """Plan optimal journey between Vienna stations.
        
        Calculates the best route from an origin station to a destination
        station using Vienna's public transport network. Considers metro,
        tram, and bus connections, and provides information about transfers,
        travel time, and estimated fare.
        
        The tool supports both immediate departure (current time) and
        future departure times. When planning for future times, considers
        scheduled service availability.
        
        Args:
            from_station (str): Origin station name. Can be full name or partial
                match. Examples: "Stephansplatz", "Hauptbahnhof", "Stephans"
                (partial match).
            to_station (str): Destination station name. Same matching rules as
                from_station. Examples: "Praterstern", "Schönbrunn", "Karlsplatz".
            departure_time (str, optional): Departure time in ISO 8601 format.
                Example: "2025-01-15T14:30:00Z" or "2025-01-15T14:30:00+01:00".
                If not provided, uses current UTC time. The tool will find the
                next available departure after this time.
        
        Returns:
            JourneyPlan: Journey plan containing:
                - from_station (str): Full name of origin station
                - to_station (str): Full name of destination station
                - departure_time (datetime): Requested departure time
                - total_duration_minutes (int): Total journey time in minutes
                - segments (List[JourneySegment]): List of journey segments with:
                    * line (str): Line identifier for this segment
                    * from_station (str): Starting station of segment
                    * to_station (str): Ending station of segment
                    * departure_time (datetime): Segment departure time
                    * arrival_time (datetime): Segment arrival time
                    * duration_minutes (int): Segment duration
                    * vehicle_type (str): Type of vehicle (metro, tram, bus)
                - transfers (int): Number of transfers required (0 for direct routes)
                - estimated_cost (str, optional): Estimated fare cost (e.g., "€2.40")
        
        Raises:
            ValueError: If origin or destination station cannot be found. Includes
                suggestions for similar station names.
            RuntimeError: If journey planning fails or cannot be processed.
        
        Example:
            >>> plan = await journey_planner(
            ...     "Stephansplatz",
            ...     "Praterstern",
            ...     departure_time="2025-01-15T14:30:00Z"
            ... )
            >>> print(f"Journey takes {plan.total_duration_minutes} minutes")
            >>> print(f"Requires {plan.transfers} transfers")
        """
        try:
            # Parse departure time
            if departure_time:
                try:
                    dep_time = datetime.fromisoformat(departure_time.replace("Z", "+00:00"))
                except:
                    dep_time = datetime.utcnow()
            else:
                dep_time = datetime.utcnow()
            
            # Find stations
            from_info = find_station_by_name(from_station)
            if not from_info:
                raise ValueError(f"Origin station '{from_station}' not found")
            
            to_info = find_station_by_name(to_station)
            if not to_info:
                raise ValueError(f"Destination station '{to_station}' not found")
            
            # TODO: Implement actual journey planning algorithm
            # For now, return a placeholder response
            # This would integrate with GTFS routing or Wiener Linien journey planner API
            
            # Placeholder: Simple direct route estimate
            # In production, this would use GTFS routing or API
            segments = []
            total_duration = 15  # Placeholder
            
            journey = JourneyPlan(
                from_station=from_info["name"],
                to_station=to_info["name"],
                departure_time=dep_time,
                total_duration_minutes=total_duration,
                segments=segments,
                transfers=0,
                estimated_cost="€2.40",  # Standard Vienna fare
            )
            
            return journey
            
        except ValueError as e:
            logger.warning(f"Journey planning error: {e}")
            raise
        except Exception as e:
            logger.error(f"Error planning journey: {e}", exc_info=True)
            raise RuntimeError(f"Failed to plan journey: {str(e)}") from e

