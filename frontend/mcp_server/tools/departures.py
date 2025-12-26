"""MCP tool for getting next departures from stations."""

import logging
from datetime import datetime

from fastmcp import FastMCP

try:
    from ...data_loader import data_loader
    from ...vehicle_service import collect_vehicle_data
    from ..models.departures import Departure, DepartureResponse
    from ..utils import find_station_by_name
except ImportError:
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from data_loader import data_loader
    from mcp_server.models.departures import Departure, DepartureResponse
    from mcp_server.utils import find_station_by_name
    from vehicle_service import collect_vehicle_data

logger = logging.getLogger(__name__)


def register_departures_tool(mcp: FastMCP) -> None:
    """Register the next_departures tool with the MCP server.

    This tool provides real-time departure information for Vienna public transport
    stations. It queries the Wiener Linien API and returns upcoming departures with
    line numbers, destinations, departure times, delays, and vehicle types.

    Args:
        mcp: FastMCP server instance to register the tool with
    """

    @mcp.tool()
    async def next_departures(station: str, max_results: int = 5) -> DepartureResponse:
        """Get next departures from a Vienna transit station.

        Retrieves real-time departure information for the specified station, including
        metro (U-Bahn), tram, bus, and night bus services. Results are sorted by
        departure time and include countdown timers, delays, and vehicle types.

        The tool supports fuzzy station name matching, so partial names work well.
        For example, "Stephans" will match "Stephansplatz" and "Stephansdom".

        Args:
            station (str): Station name (supports German/English, partial matching).
                Examples: "Stephansplatz", "Schwedenplatz", "Hauptbahnhof",
                "Stephans" (partial match), "HBF" (common abbreviation).
            max_results (int): Maximum departures to return. Must be between 1 and 10.
                Default is 5. Higher values provide more options but may include
                departures further in the future.

        Returns:
            DepartureResponse: Response containing:
                - station_name (str): Full name of the matched station
                - station_rbl (str, optional): RBL code (Vienna-specific station identifier)
                - departures (List[Departure]): List of Departure objects with:
                    * line (str): Line identifier (e.g., "U1", "D", "13A", "N25")
                    * destination (str): Next station or final destination
                    * departure_time (datetime): Scheduled departure datetime (UTC)
                    * countdown_minutes (int): Minutes until departure
                    * delay_minutes (int, optional): Delay in minutes (None if on time)
                    * platform (str, optional): Platform/track number (if available)
                    * vehicle_type (str): Type of vehicle (metro, tram, bus, nightbus)
                - timestamp (datetime): Response generation timestamp

        Raises:
            ValueError: If station name cannot be found or matched. Includes
                suggestions for similar station names.
            RuntimeError: If API request fails or data cannot be processed.

        Example:
            >>> result = await next_departures("Stephansplatz", max_results=3)
            >>> print(f"Next {len(result.departures)} departures from {result.station_name}")
            Next 3 departures from Stephansplatz
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
            raise RuntimeError(f"Failed to fetch departures: {str(e)}") from e
