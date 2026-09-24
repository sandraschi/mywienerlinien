"""MCP tool for getting next departures from stations."""

import logging
from datetime import UTC, datetime
from typing import Annotated

from fastmcp import FastMCP
from mcp.types import ToolAnnotations
from pydantic import Field

try:
    from data_loader import data_loader
    from vehicle_service import collect_vehicle_data

    from ..models.departures import Departure, DepartureResponse
    from ..utils import find_station_by_name
except ImportError:
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from data_loader import data_loader
    from vehicle_service import collect_vehicle_data

    from wienerlinien_mcp.models.departures import Departure, DepartureResponse
    from wienerlinien_mcp.utils import find_station_by_name

logger = logging.getLogger(__name__)


def register_departures_tool(mcp: FastMCP) -> None:
    """Register the next_departures tool with the MCP server.

    This tool provides real-time departure information for Vienna public transport
    stations. It queries the Wiener Linien API and returns upcoming departures with
    line numbers, destinations, departure times, delays, and vehicle types.

    Args:
        mcp: FastMCP server instance to register the tool with
    """

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True, openWorldHint=True))
    async def next_departures(
        station: Annotated[
            str,
            Field(
                description="Station name with fuzzy matching. Examples: Stephansplatz, Hauptbahnhof, Stephans (partial), HBF (abbreviation)."
            ),
        ],
        max_results: Annotated[int, Field(description="Maximum departures to return, 1-10.", ge=1, le=10)] = 5,
    ) -> DepartureResponse:
        """Get next departures from a Vienna transit station.

        Retrieves real-time departure information for the specified station, including
        metro (U-Bahn), tram, bus, and night bus services. Results are sorted by
        departure time and include countdown timers, delays, and vehicle types.
        Supports fuzzy station name matching, so partial names work well.

        ## Return Format
        {"station_name": str, "station_rbl": str | None, "departures": [{"line": str, "destination": str, "departure_time": datetime, "countdown_minutes": int, "delay_minutes": int | None, "platform": str | None, "vehicle_type": "metro|tram|bus|nightbus"}], "timestamp": datetime}

        ## Examples
        next_departures(station="Stephansplatz")
        next_departures(station="Hauptbahnhof", max_results=10)
        next_departures(station="Schweden", max_results=3)
        """
        try:
            # Validate max_results
            max_results = max(1, min(10, max_results))

            # Find station
            station_info = find_station_by_name(station)
            if not station_info:
                # Use elicitation for ambiguous station names
                stations = data_loader.load_stations()
                suggestions = [
                    s.name
                    for s in stations
                    if station.lower() in s.name.lower() or s.name.lower().startswith(station.lower()[:3])
                ][:5]

                error_msg = f"Station '{station}' not found."
                if suggestions:
                    error_msg += f" Did you mean: {', '.join(suggestions)}?"

                raise ValueError(error_msg)

            # Get departures using existing vehicle service
            result = collect_vehicle_data(
                vehicle_type="all",
                station=station_info.get("rbl"),
                lines=None,
            )

            vehicles = result.get("vehicles", [])

            # Convert to Departure models
            departures = []
            now = datetime.now(UTC)

            for vehicle in vehicles[:max_results]:
                # Calculate countdown
                timestamp = vehicle.get("timestamp")
                if timestamp:
                    if isinstance(timestamp, str):
                        try:
                            vehicle_time = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                        except ValueError:
                            vehicle_time = now
                    else:
                        vehicle_time = timestamp
                else:
                    vehicle_time = now

                countdown = int((vehicle_time - now).total_seconds() / 60)
                if countdown < 0:
                    countdown = 0

                departure = Departure(
                    line=vehicle.get("line", "?"),
                    destination=vehicle.get("next_station", "Unknown"),
                    departure_time=vehicle_time,
                    countdown_minutes=countdown,
                    delay_minutes=vehicle.get("delay"),
                    platform=None,  # Not available in current API
                    vehicle_type=vehicle.get("type", "unknown").lower(),
                )
                departures.append(departure)

            return DepartureResponse(
                station_name=station_info["name"],
                station_rbl=station_info.get("rbl"),
                departures=departures,
            )

        except ValueError as e:
            logger.warning(f"Station search error: {e}")
            raise
        except Exception as e:
            logger.error(f"Error fetching departures: {e}", exc_info=True)
            raise RuntimeError(f"Failed to fetch departures: {e!s}") from e


async def get_next_departures_internal(station_name: str, max_results: int = 5) -> list[dict]:
    """Internal helper for public API compatibility.

    Args:
        station_name: Station to search for
        max_results: Max results to return

    Returns:
        List of dicts containing departure info
    """
    from ..utils import find_station_by_name

    station_info = find_station_by_name(station_name)
    if not station_info:
        return []

    # Simple mock/proxy call to vehicles
    # In a real scenario, this would call the same logic as the tool
    # but return plain dicts instead of Pydantic models (if needed)
    from vehicle_service import collect_vehicle_data

    result = collect_vehicle_data(
        vehicle_type="all",
        station=station_info.get("rbl"),
        lines=None,
    )
    return result.get("vehicles", [])[:max_results]
