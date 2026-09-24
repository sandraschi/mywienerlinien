"""MCP tool for journey planning.
Phase 3A Enhancement: Real GTFS-based routing with multi-leg journey support.
"""

import logging
from datetime import datetime
from typing import Annotated

from fastmcp import FastMCP
from fastmcp.tools.tool import ToolAnnotations
from pydantic import Field

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

    from wienerlinien_mcp.models.journey import JourneyPlan, JourneySegment
    from wienerlinien_mcp.routing_service import JourneyPlanner
    from wienerlinien_mcp.utils import find_station_by_name

logger = logging.getLogger(__name__)

# Initialize journey planner (lazy loading)
_journey_planner = None


def get_journey_planner():
    """Get or create journey planner instance."""
    global _journey_planner
    if _journey_planner is None:
        _journey_planner = JourneyPlanner(db)
    return _journey_planner


def _resolve_stop_id(station: dict) -> str:
    """Resolve a GTFS stop_id for a station dict from find_station_by_name.

    The station dict carries the Wiener Linien RBL (monitor id); the routing
    graph is keyed by GTFS stop_id, matched here via the DB station catalog
    (stop_code holds the RBL, comma-separated). Falls back to the RBL itself
    when the DB is unreachable so the planner can still attempt a match.
    """
    rbl = str(station.get("rbl") or "")
    name = station.get("name") or ""
    try:
        for row in db.get_stations():
            codes = [c.strip() for c in str(row.get("rbl") or "").split(",")]
            if rbl and rbl in codes and row.get("id"):
                return str(row["id"])
            if name and row.get("name") == name and row.get("id"):
                return str(row["id"])
    except Exception:
        logger.warning("Stop-id catalog lookup failed; falling back to RBL", exc_info=True)
    return rbl or name


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

    @mcp.tool(
        annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True, openWorldHint=True)
    )
    async def journey_planner(
        from_station: Annotated[str, Field(description="Origin station name, full or partial. Examples: Stephansplatz, Hauptbahnhof, Stephans.")],
        to_station: Annotated[str, Field(description="Destination station name, full or partial. Examples: Praterstern, Karlsplatz.")],
        departure_time: Annotated[str | None, Field(description="Departure time in ISO 8601 (e.g. 2025-01-15T14:30:00Z). Omit for now.")] = None,
    ) -> JourneyPlan:
        """Plan optimal journey between Vienna stations.

        Calculates the best route from an origin station to a destination
        station using Vienna's public transport network. Considers metro,
        tram, and bus connections, and provides information about transfers,
        travel time, and estimated fare. Supports immediate and future
        departure times using scheduled service availability.

        ## Return Format
        {"from_station": str, "to_station": str, "departure_time": datetime, "total_duration_minutes": int, "segments": [{"line": str, "from_station": str, "to_station": str, "departure_time": datetime, "arrival_time": datetime, "duration_minutes": int, "vehicle_type": "metro|tram|bus"}], "transfers": int, "estimated_cost": str | None}

        ## Examples
        journey_planner(from_station="Stephansplatz", to_station="Praterstern")
        journey_planner(from_station="Stephansplatz", to_station="Praterstern", departure_time="2025-01-15T14:30:00Z")
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

            # Use GTFS-based routing service (graph is keyed by GTFS stop_id)
            planner = get_journey_planner()
            route_options = planner.plan_journey(
                _resolve_stop_id(from_info), _resolve_stop_id(to_info), dep_time
            )

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
            raise RuntimeError(f"Failed to plan journey: {e!s}") from e
