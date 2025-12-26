"""MCP tool for getting next departures from stations."""

import logging
import sys
from datetime import datetime
from pathlib import Path

from fastmcp import FastMCP

# Add frontend to path for backend imports
_project_root = Path(__file__).parent.parent.parent.parent
_frontend_path = _project_root / "frontend"
if str(_frontend_path) not in sys.path:
    sys.path.insert(0, str(_frontend_path))

from data_loader import data_loader
from vehicle_service import collect_vehicle_data

from wienerlinien_mcp.models.departures import Departure, DepartureResponse
from wienerlinien_mcp.utils import find_station_by_name

logger = logging.getLogger(__name__)


def register_departures_tool(mcp: FastMCP) -> None:
    """Register the next_departures tool with the MCP server."""

    @mcp.tool()
    async def next_departures(station: str, max_results: int = 5) -> DepartureResponse:
        """Get next departures from a Vienna transit station.

        Args:
            station: Station name (supports German/English, partial matching)
                   Examples: "Stephansplatz", "Schwedenplatz", "Hauptbahnhof"
            max_results: Maximum departures to return (1-10, default: 5)

        Returns:
            List of departures with line, destination, time, delay, platform
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
                    if station.lower() in s.name.lower()
                    or s.name.lower().startswith(station.lower()[:3])
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
            now = datetime.utcnow()

            for vehicle in vehicles[:max_results]:
                # Calculate countdown
                timestamp = vehicle.get("timestamp")
                if timestamp:
                    if isinstance(timestamp, str):
                        try:
                            vehicle_time = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                        except:
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
            raise RuntimeError(f"Failed to fetch departures: {str(e)}") from e
