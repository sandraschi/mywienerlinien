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
from database import db

from wienerlinien_mcp.models.departures import Departure, DepartureResponse, TimetableResponse
from wienerlinien_mcp.models.disruptions import Disruption, DisruptionResponse, DisruptionSummaryResponse
from wienerlinien_mcp.utils import find_station_by_name

# Import disruption monitor
try:
    from disruption_alerts import disruption_monitor
except ImportError:
    disruption_monitor = None

logger = logging.getLogger(__name__)


def register_departures_tool(mcp: FastMCP) -> None:
    """Register departures-related tools with the MCP server."""

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

    @mcp.tool()
    async def get_timetable(
        station: str,
        line: str = None,
        start_time: str = None,
        end_time: str = None
    ) -> TimetableResponse:
        """Get scheduled timetable for a station between specific times.

        Args:
            station: Station name (supports German/English, partial matching)
                   Examples: "Friedensbrücke", "Stephansplatz", "Hauptbahnhof"
            line: Optional line filter (e.g., "U4", "5", "68A") - leave empty for all lines
            start_time: Start time in HH:MM format (default: current time)
            end_time: End time in HH:MM format (default: start_time + 1 hour)

        Returns:
            Scheduled departures timetable organized by line with departure times and directions
        """
        try:
            # Parse start time
            if start_time:
                try:
                    # Parse HH:MM format
                    start_hour, start_minute = map(int, start_time.split(':'))
                    start_seconds = start_hour * 3600 + start_minute * 60
                except:
                    raise ValueError("start_time must be in HH:MM format (e.g., '06:00')")
            else:
                # Use current time
                now = datetime.now()
                start_seconds = now.hour * 3600 + now.minute * 60

            # Parse end time
            if end_time:
                try:
                    # Parse HH:MM format
                    end_hour, end_minute = map(int, end_time.split(':'))
                    end_seconds = end_hour * 3600 + end_minute * 60
                except:
                    raise ValueError("end_time must be in HH:MM format (e.g., '07:00')")
            else:
                # Default to start_time + 1 hour
                end_seconds = start_seconds + 3600

            # Validate time range
            if end_seconds <= start_seconds:
                raise ValueError("end_time must be after start_time")
            if end_seconds - start_seconds > 4 * 3600:  # Max 4 hours
                raise ValueError("Time range cannot exceed 4 hours")

            # Find station
            station_info = find_station_by_name(station)
            if not station_info:
                raise ValueError(f"Station '{station}' not found")

            # Build time range strings
            start_time_str = f"{start_seconds//3600:02d}:{(start_seconds%3600)//60:02d}:{start_seconds%60:02d}"
            end_time_str = f"{end_seconds//3600:02d}:{(end_seconds%3600)//60:02d}:{end_seconds%60:02d}"

            # Build query
            query = f"""
                SELECT
                    r.route_short_name as line,
                    t.trip_headsign as direction,
                    st.departure_time,
                    s.stop_name,
                    CASE
                        WHEN r.route_type = 0 THEN 'Tram'
                        WHEN r.route_type = 1 THEN 'Metro'
                        WHEN r.route_type = 2 THEN 'Rail'
                        WHEN r.route_type = 3 THEN 'Bus'
                        ELSE 'Other'
                    END as vehicle_type
                FROM stop_times st
                JOIN stops s ON st.stop_id = s.stop_id
                JOIN trips t ON st.trip_id = t.trip_id
                JOIN routes r ON t.route_id = r.route_id
                WHERE s.stop_name = '{station_info["name"]}'
                  AND st.departure_time >= '{start_time_str}'
                  AND st.departure_time < '{end_time_str}'
            """

            if line:
                query += f" AND r.route_short_name = '{line.upper()}'"

            query += " ORDER BY st.departure_time, r.route_short_name"

            # Execute query
            result = db.execute_query(query)

            # Group by line for better display
            timetable = {}
            for row in result:
                line_name = row['line']
                if line_name not in timetable:
                    timetable[line_name] = {
                        'line': line_name,
                        'vehicle_type': row['vehicle_type'],
                        'departures': []
                    }

                timetable[line_name]['departures'].append({
                    'time': str(row['departure_time'])[:5],  # HH:MM format
                    'direction': row['direction']
                })

            # Convert to response format
            lines = list(timetable.values())

            return TimetableResponse(
                station=station_info["name"],
                lines=lines,
                time_window=f"{start_time or 'now'} to {end_time or f'{((start_seconds + 3600)//3600):02d}:{(((start_seconds + 3600)%3600)//60):02d}'}"
            )

        except ValueError as e:
            logger.warning(f"Timetable validation error: {e}")
            raise
        except Exception as e:
            logger.error(f"Error fetching timetable: {e}", exc_info=True)
            raise RuntimeError(f"Failed to fetch timetable: {str(e)}") from e

    @mcp.tool()
    async def get_disruptions(
        line: str = None,
        station: str = None,
        severity: str = None,
        max_results: int = 10
    ) -> DisruptionResponse:
        """Get current service disruptions in Vienna's transit system.

        Args:
            line: Optional line filter (e.g., "U4", "5", "68A")
            station: Optional station filter (e.g., "Friedensbrücke", "Karlsplatz")
            severity: Optional severity filter ("low", "medium", "high", "critical")
            max_results: Maximum disruptions to return (1-50, default: 10)

        Returns:
            Current service disruptions with details
        """
        try:
            if not disruption_monitor:
                raise RuntimeError("Disruption monitoring not available")

            # Validate inputs
            max_results = max(1, min(50, max_results))

            # Get disruptions based on filters
            disruptions = []

            if line:
                disruptions = disruption_monitor.get_disruptions_by_line(line)
            elif station:
                disruptions = disruption_monitor.get_disruptions_by_station(station)
            elif severity:
                from disruption_alerts import DisruptionSeverity
                try:
                    sev_enum = DisruptionSeverity(severity.lower())
                    disruptions = disruption_monitor.get_disruptions_by_severity(sev_enum)
                except ValueError:
                    raise ValueError(f"Invalid severity: {severity}. Must be: low, medium, high, critical")
            else:
                disruptions = disruption_monitor.get_active_disruptions()

            # Convert to Disruption models
            disruption_models = []
            for disruption in disruptions[:max_results]:
                disruption_models.append(Disruption(
                    id=disruption.id,
                    title=disruption.title,
                    description=disruption.description,
                    line=disruption.line,
                    type=disruption.type.value,
                    severity=disruption.severity.value,
                    status=disruption.status.value,
                    affected_stations=disruption.affected_stations,
                    affected_lines=disruption.affected_lines,
                    start_time=disruption.start_time,
                    end_time=disruption.end_time,
                    created_at=disruption.created_at,
                    updated_at=disruption.updated_at,
                ))

            return DisruptionResponse(
                disruptions=disruption_models,
                count=len(disruption_models),
            )

        except ValueError as e:
            logger.warning(f"Disruption validation error: {e}")
            raise
        except Exception as e:
            logger.error(f"Error fetching disruptions: {e}", exc_info=True)
            raise RuntimeError(f"Failed to fetch disruptions: {str(e)}") from e

    @mcp.tool()
    async def get_service_status() -> DisruptionSummaryResponse:
        """Get current service status summary for Vienna's transit system.

        Returns:
            Summary of active disruptions and service status
        """
        try:
            if not disruption_monitor:
                raise RuntimeError("Disruption monitoring not available")

            summary = disruption_monitor.get_disruption_summary()

            return DisruptionSummaryResponse(
                total_active=summary.get("total_active", 0),
                by_severity=summary.get("by_severity", {}),
                by_type=summary.get("by_type", {}),
                most_affected_lines=summary.get("most_affected_lines", []),
                last_updated=datetime.utcnow(),
            )

        except Exception as e:
            logger.error(f"Error fetching service status: {e}", exc_info=True)
            raise RuntimeError(f"Failed to fetch service status: {str(e)}") from e

    @mcp.tool()
    async def find_nearby_stations(
        latitude: float,
        longitude: float,
        radius_km: float = 1.0,
        max_results: int = 10
    ) -> dict:
        """Find transit stations near a specific location.

        Args:
            latitude: Latitude of the location
            longitude: Longitude of the location
            radius_km: Search radius in kilometers (default: 1.0)
            max_results: Maximum stations to return (1-20, default: 10)

        Returns:
            Nearby transit stations with distance and available lines
        """
        try:
            # Validate inputs
            max_results = max(1, min(20, max_results))
            radius_km = max(0.1, min(5.0, radius_km))

            # Query for nearby stations
            query = f"""
                SELECT
                    s.stop_name,
                    s.stop_lat,
                    s.stop_lon,
                    s.zone_id,
                    array_agg(DISTINCT r.route_short_name) as lines,
                    ST_Distance(
                        ST_Transform(ST_SetSRID(ST_MakePoint(%s, %s), 4326), 3857),
                        ST_Transform(ST_SetSRID(ST_MakePoint(s.stop_lon, s.stop_lat), 4326), 3857)
                    ) / 1000 as distance_km
                FROM stops s
                LEFT JOIN stop_times st ON s.stop_id = st.stop_id
                LEFT JOIN trips t ON st.trip_id = t.trip_id
                LEFT JOIN routes r ON t.route_id = r.route_id
                WHERE ST_DWithin(
                    ST_Transform(ST_SetSRID(ST_MakePoint(s.stop_lon, s.stop_lat), 4326), 3857),
                    ST_Transform(ST_SetSRID(ST_MakePoint(%s, %s), 4326), 3857),
                    %s
                )
                GROUP BY s.stop_id, s.stop_name, s.stop_lat, s.stop_lon, s.zone_id
                ORDER BY distance_km
                LIMIT %s
            """

            # Convert radius to meters for PostGIS
            radius_meters = radius_km * 1000

            result = db.execute_query(query, (longitude, latitude, longitude, latitude, radius_meters, max_results))

            stations = []
            for row in result:
                stations.append({
                    "name": row["stop_name"],
                    "latitude": row["stop_lat"],
                    "longitude": row["stop_lon"],
                    "zone": row["zone_id"],
                    "lines": row["lines"] or [],
                    "distance_km": round(row["distance_km"], 2),
                })

            return {
                "stations": stations,
                "search_location": {"lat": latitude, "lng": longitude},
                "search_radius_km": radius_km,
                "count": len(stations),
            }

        except Exception as e:
            logger.error(f"Error finding nearby stations: {e}", exc_info=True)
            raise RuntimeError(f"Failed to find nearby stations: {str(e)}") from e

    @mcp.tool()
    async def get_route_info(line: str) -> dict:
        """Get detailed information about a specific transit route/line.

        Args:
            line: Route/line identifier (e.g., "U4", "5", "68A")

        Returns:
            Route information including stops, type, and schedule details
        """
        try:
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
                WHERE r.route_short_name = %s
            """

            route_result = db.execute_query(route_query, (line.upper(),))
            if not route_result:
                raise ValueError(f"Route '{line}' not found")

            route_info = route_result[0]

            # Get stops for this route
            stops_query = """
                SELECT DISTINCT
                    s.stop_name,
                    s.stop_lat,
                    s.stop_lon,
                    s.zone_id,
                    array_agg(DISTINCT t.trip_headsign) as directions
                FROM routes r
                JOIN trips t ON r.route_id = t.route_id
                JOIN stop_times st ON t.trip_id = st.trip_id
                JOIN stops s ON st.stop_id = s.stop_id
                WHERE r.route_short_name = %s
                GROUP BY s.stop_id, s.stop_name, s.stop_lat, s.stop_lon, s.zone_id
                ORDER BY min(st.stop_sequence)
            """

            stops_result = db.execute_query(stops_query, (line.upper(),))

            stops = []
            for row in stops_result:
                stops.append({
                    "name": row["stop_name"],
                    "latitude": row["stop_lat"],
                    "longitude": row["stop_lon"],
                    "zone": row["zone_id"],
                    "directions": row["directions"] or [],
                })

            # Get schedule info
            schedule_query = """
                SELECT
                    min(st.departure_time) as first_departure,
                    max(st.arrival_time) as last_arrival,
                    count(DISTINCT t.trip_id) as total_trips
                FROM routes r
                JOIN trips t ON r.route_id = t.route_id
                JOIN stop_times st ON t.trip_id = st.trip_id
                WHERE r.route_short_name = %s
            """

            schedule_result = db.execute_query(schedule_query, (line.upper(),))
            schedule_info = schedule_result[0] if schedule_result else {}

            return {
                "line": route_info["route_short_name"],
                "name": route_info["route_long_name"],
                "type": route_info["vehicle_type"],
                "color": f"#{route_info['route_color'] or '666666'}",
                "text_color": f"#{route_info['route_text_color'] or 'FFFFFF'}",
                "stops": stops,
                "total_stops": len(stops),
                "schedule": {
                    "first_departure": str(schedule_info.get("first_departure", "N/A")),
                    "last_arrival": str(schedule_info.get("last_arrival", "N/A")),
                    "total_trips": schedule_info.get("total_trips", 0),
                },
            }

        except ValueError as e:
            logger.warning(f"Route info validation error: {e}")
            raise
        except Exception as e:
            logger.error(f"Error fetching route info: {e}", exc_info=True)
            raise RuntimeError(f"Failed to fetch route info: {str(e)}") from e
