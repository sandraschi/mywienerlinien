"""MCP tool for getting detailed information about transit routes."""

import logging
from typing import Optional

from fastmcp import FastMCP
from pydantic import BaseModel, Field

try:
    from ..database import db
except ImportError:
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from database import db

logger = logging.getLogger(__name__)


class RouteStop(BaseModel):
    """Information about a stop on a route."""

    name: str = Field(..., description="Stop name")
    latitude: float = Field(..., description="Stop latitude")
    longitude: float = Field(..., description="Stop longitude")
    zone: Optional[str] = Field(None, description="Fare zone")
    directions: list[str] = Field(
        default_factory=list, description="Available directions from this stop"
    )


class RouteSchedule(BaseModel):
    """Basic schedule information for a route."""

    first_departure: str = Field(..., description="First scheduled departure")
    last_arrival: str = Field(..., description="Last scheduled arrival")
    total_trips: int = Field(..., description="Total scheduled trips for today")


class RouteInfoResponse(BaseModel):
    """Detailed information about a transit route."""

    line: str = Field(..., description="Line identifier (e.g., U4, 5, 13A)")
    name: str = Field(..., description="Full route name")
    type: str = Field(..., description="Vehicle type (Metro, Tram, Bus, etc.)")
    color: str = Field(..., description="Hex color code for the route")
    text_color: str = Field(..., description="Hex color code for text on the route color")
    stops: list[RouteStop] = Field(..., description="List of stops on this route")
    total_stops: int = Field(..., description="Number of stops")
    schedule: RouteSchedule = Field(..., description="Schedule summary")


def register_routes_tool(mcp: FastMCP) -> None:
    """Register the get_route_info tool with the MCP server."""

    @mcp.tool()
    async def get_route_info(line: str) -> RouteInfoResponse:
        """Get detailed information about a specific transit route/line.

        Retrieves the full list of stops, vehicle type, route colors, and
        service span (first/last service) for a given line.

        Args:
            line: Route/line identifier (e.g., "U4", "5", "68A")

        Returns:
            RouteInfoResponse with detailed route information
        """
        try:
            line_upper = line.upper().strip()

            # Get route basic info
            route_query = """
                SELECT
                    r.route_short_name,
                    r.route_long_name,
                    r.route_type,
                    CASE
                        WHEN r.route_type = 0 THEN 'Tram'
                        WHEN r.route_type = 1 THEN 'Metro'
                        WHEN r.route_type = 2 THEN 'Rail'
                        WHEN r.route_type = 3 THEN 'Bus'
                        ELSE 'Other'
                    END as vehicle_type,
                    r.route_color,
                    r.route_text_color
                FROM routes r
                WHERE UPPER(r.route_short_name) = ?
            """

            # Use ? for sqlite parameter placeholder (assuming sqlite based on db.py)
            route_result = db.execute_query(route_query, (line_upper,))
            if not route_result:
                # Try partial match if exact match fails
                route_query_fuzzy = """
                    SELECT r.route_short_name, r.route_long_name, r.route_type,
                           CASE WHEN r.route_type = 0 THEN 'Tram' WHEN r.route_type = 1 THEN 'Metro'
                                WHEN r.route_type = 2 THEN 'Rail' WHEN r.route_type = 3 THEN 'Bus'
                                ELSE 'Other' END as vehicle_type,
                           r.route_color, r.route_text_color
                    FROM routes r
                    WHERE UPPER(r.route_short_name) LIKE ?
                    LIMIT 1
                """
                route_result = db.execute_query(route_query_fuzzy, (f"%{line_upper}%",))

            if not route_result:
                raise ValueError(f"Route '{line}' not found")

            route_info = route_result[0]
            canonical_line = route_info["route_short_name"]

            # Get stops for this route
            # Grouped by stop to get directions
            stops_query = """
                SELECT
                    s.stop_name,
                    s.stop_lat,
                    s.stop_lon,
                    s.zone_id,
                    GROUP_CONCAT(DISTINCT t.trip_headsign) as directions_str
                FROM routes r
                JOIN trips t ON r.route_id = t.route_id
                JOIN stop_times st ON t.trip_id = st.trip_id
                JOIN stops s ON st.stop_id = s.stop_id
                WHERE r.route_short_name = ?
                GROUP BY s.stop_name
                ORDER BY MIN(st.stop_sequence)
            """

            stops_result = db.execute_query(stops_query, (canonical_line,))

            stops = []
            for row in stops_result:
                directions = row["directions_str"].split(",") if row["directions_str"] else []
                stops.append(
                    RouteStop(
                        name=row["stop_name"],
                        latitude=row["stop_lat"],
                        longitude=row["stop_lon"],
                        zone=row["zone_id"],
                        directions=[d.strip() for d in directions if d.strip()],
                    )
                )

            # Get schedule info
            schedule_query = """
                SELECT
                    MIN(st.departure_time) as first_departure,
                    MAX(st.arrival_time) as last_arrival,
                    COUNT(DISTINCT t.trip_id) as total_trips
                FROM routes r
                JOIN trips t ON r.route_id = t.route_id
                JOIN stop_times st ON t.trip_id = st.trip_id
                WHERE r.route_short_name = ?
            """

            schedule_result = db.execute_query(schedule_query, (canonical_line,))
            schedule_row = schedule_result[0] if schedule_result else {}

            return RouteInfoResponse(
                line=route_info["route_short_name"],
                name=route_info["route_long_name"] or route_info["route_short_name"],
                type=route_info["vehicle_type"],
                color=f"#{route_info['route_color'] or '666666'}",
                text_color=f"#{route_info['route_text_color'] or 'FFFFFF'}",
                stops=stops,
                total_stops=len(stops),
                schedule=RouteSchedule(
                    first_departure=str(schedule_row.get("first_departure", "N/A")),
                    last_arrival=str(schedule_row.get("last_arrival", "N/A")),
                    total_trips=schedule_row.get("total_trips", 0),
                ),
            )

        except ValueError as e:
            logger.warning(f"Route info request error: {e}")
            raise
        except Exception as e:
            logger.error(f"Error fetching route info: {e}", exc_info=True)
            raise RuntimeError(f"Failed to fetch route info for '{line}': {str(e)}") from e
