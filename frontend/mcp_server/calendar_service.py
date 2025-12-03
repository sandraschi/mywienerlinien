"""
Calendar Integration Service
Phase 5: Travel time calculations and departure reminders for appointments

Integrates with calendar systems (Outlook, Google Calendar) to:
- Calculate travel time to appointments
- Suggest departure times
- Send reminders
- Auto-plan journeys
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class Appointment:
    """Calendar appointment/event."""

    event_id: str
    title: str
    location: str
    start_time: datetime
    end_time: datetime
    timezone: str
    organizer: Optional[str] = None
    attendees: list[str] = None


@dataclass
class TravelPlan:
    """Travel plan for an appointment."""

    appointment: Appointment
    origin_station: str
    destination_station: str
    travel_time_minutes: int
    departure_time: datetime
    arrival_time: datetime
    buffer_minutes: int
    route_segments: list[dict]
    reminder_times: list[datetime]


class CalendarIntegrationService:
    """Integrates transit planning with calendar systems."""

    # Default buffer times
    DEFAULT_BUFFER_MINUTES = 10  # Arrive 10 minutes early
    REMINDER_OFFSETS = [15, 30, 60]  # Remind 15, 30, 60 minutes before departure

    def __init__(self, db_manager, journey_planner):
        """Initialize calendar integration.

        Args:
            db_manager: Database manager
            journey_planner: Journey planning service
        """
        self.db = db_manager
        self.journey_planner = journey_planner
        self._create_tables()

    def _create_tables(self):
        """Create calendar integration tables."""
        try:
            # Appointments table
            self.db.execute_query("""
            CREATE TABLE IF NOT EXISTS calendar_appointments (
                id SERIAL PRIMARY KEY,
                event_id VARCHAR(200) UNIQUE,
                user_id VARCHAR(100),
                title VARCHAR(500),
                location VARCHAR(500),
                start_time TIMESTAMP,
                end_time TIMESTAMP,
                timezone VARCHAR(100),
                origin_station VARCHAR(200),
                destination_station VARCHAR(200),
                travel_plan TEXT,  -- JSON
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                synced BOOLEAN DEFAULT FALSE
            )
            """)

            # Travel reminders table
            self.db.execute_query("""
            CREATE TABLE IF NOT EXISTS travel_reminders (
                id SERIAL PRIMARY KEY,
                event_id VARCHAR(200),
                reminder_time TIMESTAMP,
                reminder_type VARCHAR(50),
                message TEXT,
                sent BOOLEAN DEFAULT FALSE,
                sent_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)

            logger.info("Calendar tables created/verified")

        except Exception as e:
            logger.error(f"Error creating calendar tables: {e}", exc_info=True)

    def calculate_travel_plan(
        self,
        appointment: Appointment,
        origin_station: str,
        buffer_minutes: int = DEFAULT_BUFFER_MINUTES,
    ) -> Optional[TravelPlan]:
        """Calculate complete travel plan for an appointment.

        Args:
            appointment: Calendar appointment
            origin_station: Starting station name
            buffer_minutes: Extra time buffer

        Returns:
            Complete travel plan with timing
        """
        try:
            # Find destination station near appointment location
            # For now, use appointment location as station name
            # Future: Geocoding service to find nearest station
            destination_station = appointment.location

            # Calculate required arrival time (with buffer)
            required_arrival = appointment.start_time - timedelta(minutes=buffer_minutes)

            # Plan journey
            from mcp_server.utils import find_station_by_name

            from_info = find_station_by_name(origin_station)
            to_info = find_station_by_name(destination_station)

            if not from_info or not to_info:
                logger.warning(
                    f"Could not find stations: {origin_station} or {destination_station}"
                )
                return None

            # Get route options
            routes = self.journey_planner.plan_journey(
                from_info["id"],
                to_info["id"],
                required_arrival - timedelta(minutes=30),  # Search 30 min before required
                num_alternatives=3,
            )

            if not routes:
                return None

            # Use fastest route
            best_route = routes[0]

            # Calculate departure time
            departure_time = required_arrival - timedelta(minutes=best_route.total_duration_minutes)

            # Generate reminder times
            reminders = [
                departure_time - timedelta(minutes=offset)
                for offset in self.REMINDER_OFFSETS
                if departure_time - timedelta(minutes=offset) > datetime.now()
            ]

            travel_plan = TravelPlan(
                appointment=appointment,
                origin_station=origin_station,
                destination_station=destination_station,
                travel_time_minutes=best_route.total_duration_minutes,
                departure_time=departure_time,
                arrival_time=required_arrival,
                buffer_minutes=buffer_minutes,
                route_segments=[
                    {
                        "line": seg.line,
                        "from": seg.from_stop_name,
                        "to": seg.to_stop_name,
                        "duration": seg.duration_minutes,
                        "vehicle_type": seg.vehicle_type,
                    }
                    for seg in best_route.segments
                ],
                reminder_times=reminders,
            )

            logger.info(
                f"Travel plan created for {appointment.title}: depart {departure_time.strftime('%H:%M')}"
            )

            return travel_plan

        except Exception as e:
            logger.error(f"Error calculating travel plan: {e}", exc_info=True)
            return None

    def create_reminders(self, travel_plan: TravelPlan) -> bool:
        """Create departure reminders for an appointment.

        Args:
            travel_plan: Complete travel plan

        Returns:
            True if reminders created
        """
        try:
            for reminder_time in travel_plan.reminder_times:
                offset_minutes = int(
                    (travel_plan.departure_time - reminder_time).total_seconds() / 60
                )

                message = (
                    f"🚇 Departure reminder for {travel_plan.appointment.title}\n"
                    f"Leave in {offset_minutes} minutes from {travel_plan.origin_station}\n"
                    f"Take {travel_plan.route_segments[0]['line']} towards {travel_plan.destination_station}\n"
                    f"Arrive at {travel_plan.arrival_time.strftime('%H:%M')} (on time for {travel_plan.appointment.start_time.strftime('%H:%M')})"
                )

                self.db.execute_query(
                    """
                INSERT INTO travel_reminders
                (event_id, reminder_time, reminder_type, message)
                VALUES (:event_id, :reminder_time, :type, :message)
                """,
                    {
                        "event_id": travel_plan.appointment.event_id,
                        "reminder_time": reminder_time,
                        "type": f"departure_{offset_minutes}min",
                        "message": message,
                    },
                )

            logger.info(f"Created {len(travel_plan.reminder_times)} reminders")
            return True

        except Exception as e:
            logger.error(f"Error creating reminders: {e}", exc_info=True)
            return False

    def get_pending_reminders(self) -> list[dict]:
        """Get reminders that should be sent now.

        Returns:
            List of pending reminders
        """
        try:
            query = """
            SELECT *
            FROM travel_reminders
            WHERE sent = FALSE
                AND reminder_time <= NOW()
                AND reminder_time > NOW() - INTERVAL '5 minutes'
            ORDER BY reminder_time
            """

            return self.db.execute_query(query)

        except Exception as e:
            logger.error(f"Error getting reminders: {e}", exc_info=True)
            return []


# Singleton
_calendar_service: Optional[CalendarIntegrationService] = None


def get_calendar_service(db_manager, journey_planner) -> CalendarIntegrationService:
    """Get or create calendar service instance."""
    global _calendar_service
    if _calendar_service is None:
        _calendar_service = CalendarIntegrationService(db_manager, journey_planner)
    return _calendar_service
