"""MCP tool for journey planning.
Phase 3A Enhancement: Real GTFS-based routing with multi-leg journey support.
"""

import logging
from datetime import datetime

from fastmcp import FastMCP

try:
    from ...database import db
    from ..models.journey import JourneyPlan, JourneySegment
    from ..routing_service import JourneyPlanner
    from ..utils import find_station_by_name
except ImportError:
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from database import db
    from mcp_server.models.journey import JourneyPlan, JourneySegment
    from mcp_server.routing_service import JourneyPlanner
    from mcp_server.utils import find_station_by_name

logger = logging.getLogger(__name__)

# Initialize journey planner (lazy loading)
_journey_planner = None


def get_journey_planner():
    """Get or create journey planner instance."""
    global _journey_planner
    if _journey_planner is None:
        _journey_planner = JourneyPlanner(db)
    return _journey_planner


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
        from_station: str, to_station: str, departure_time: str | None = None
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
                except ValueError:
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

            # Use GTFS-based routing service
            planner = get_journey_planner()
            route_options = planner.plan_journey(from_info["id"], to_info["id"], dep_time)

            if not route_options:
                # Fallback if no routes found
                logger.warning(f"No routes found between {from_info['name']} and {to_info['name']}")
                return JourneyPlan(
                    from_station=from_info["name"],
                    to_station=to_info["name"],
                    departure_time=dep_time,
                    total_duration_minutes=0,
                    segments=[],
                    transfers=0,
                    estimated_cost="€2.40",
                )

            # Use the best (first) route option
            best_route = route_options[0]

            # Convert routing service segments to MCP model segments
            mcp_segments = []
            for seg in best_route.segments:
                mcp_seg = JourneySegment(
                    line=seg.line,
                    from_station=seg.from_stop_name,
                    to_station=seg.to_stop_name,
                    departure_time=seg.departure_time,
                    arrival_time=seg.arrival_time,
                    duration_minutes=seg.duration_minutes,
                    vehicle_type=seg.vehicle_type,
                )
                mcp_segments.append(mcp_seg)

            journey = JourneyPlan(
                from_station=from_info["name"],
                to_station=to_info["name"],
                departure_time=dep_time,
                total_duration_minutes=best_route.total_duration_minutes,
                segments=mcp_segments,
                transfers=best_route.transfers,
                estimated_cost=best_route.estimated_cost,
            )

            logger.info(
                f"Journey planned: {from_info['name']} -> {to_info['name']}, "
                f"{journey.total_duration_minutes} min, {journey.transfers} transfers"
            )

            return journey

        except ValueError as e:
            logger.warning(f"Journey planning error: {e}")
            raise
        except Exception as e:
            logger.error(f"Error planning journey: {e}", exc_info=True)
            raise RuntimeError(f"Failed to plan journey: {str(e)}") from e
