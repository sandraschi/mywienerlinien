"""
Smart notification service for transit alerts.
Phase 3C Enhancement: Intelligent notifications based on predictions and favorites.

Sends notifications for:
- Predicted delays on favorite lines
- Service disruptions
- Alternative route suggestions
- Departure reminders
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional

logger = logging.getLogger(__name__)


class NotificationType(Enum):
    """Types of notifications."""

    DELAY_ALERT = "delay_alert"
    DISRUPTION = "disruption"
    ALTERNATIVE_ROUTE = "alternative_route"
    DEPARTURE_REMINDER = "departure_reminder"
    SERVICE_CHANGE = "service_change"


class NotificationPriority(Enum):
    """Notification priority levels."""

    LOW = 1
    MEDIUM = 2
    HIGH = 3
    URGENT = 4


@dataclass
class Notification:
    """A notification to be sent to user."""

    notification_id: str
    notification_type: NotificationType
    priority: NotificationPriority
    title: str
    message: str
    line: Optional[str]
    station: Optional[str]
    action_url: Optional[str]
    created_at: datetime
    expires_at: Optional[datetime]

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.notification_id,
            "type": self.notification_type.value,
            "priority": self.priority.value,
            "title": self.title,
            "message": self.message,
            "line": self.line,
            "station": self.station,
            "action_url": self.action_url,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
        }


class SmartNotificationService:
    """Intelligent notification service for transit alerts."""

    # Notification thresholds
    DELAY_THRESHOLD_MINUTES = 5  # Notify if predicted delay >= 5 min
    DISRUPTION_THRESHOLD = "moderate"  # Notify for moderate+ disruptions

    def __init__(self, db_manager, prediction_service, historical_collector):
        """Initialize notification service.

        Args:
            db_manager: Database manager
            prediction_service: ML prediction service
            historical_collector: Historical data collector
        """
        self.db = db_manager
        self.predictor = prediction_service
        self.collector = historical_collector
        self.notifications: list[Notification] = []
        self._create_table()

    def _create_table(self):
        """Create notifications table."""
        try:
            self.db.execute_query("""
            CREATE TABLE IF NOT EXISTS notifications (
                id SERIAL PRIMARY KEY,
                notification_id VARCHAR(100) UNIQUE,
                notification_type VARCHAR(50),
                priority INTEGER,
                title VARCHAR(200),
                message TEXT,
                line VARCHAR(10),
                station VARCHAR(200),
                action_url VARCHAR(500),
                created_at TIMESTAMP,
                expires_at TIMESTAMP,
                sent BOOLEAN DEFAULT FALSE,
                sent_at TIMESTAMP
            )
            """)

            self.db.execute_query("""
            CREATE INDEX IF NOT EXISTS idx_notifications_created
            ON notifications(created_at DESC)
            """)

        except Exception as e:
            logger.error(f"Error creating notifications table: {e}", exc_info=True)

    def check_favorite_lines(self, favorite_stations: list[dict]) -> list[Notification]:
        """Check favorite stations and generate notifications for predicted delays.

        Args:
            favorite_stations: List of user's favorite stations

        Returns:
            List of notifications generated
        """
        notifications = []

        # Get unique lines from favorite stations
        lines = set()
        for station in favorite_stations:
            # Query lines serving this station
            try:
                query = """
                SELECT DISTINCT r.route_short_name
                FROM routes r
                JOIN trips t ON r.route_id = t.route_id
                JOIN stop_times st ON t.trip_id = st.trip_id
                JOIN stops s ON st.stop_id = s.stop_id
                WHERE s.stop_name = :station_name
                LIMIT 5
                """
                results = self.db.execute_query(query, {"station_name": station.get("name")})
                for row in results:
                    lines.add(row["route_short_name"])
            except:
                pass

        # Check predictions for each line
        for line in lines:
            try:
                prediction = self.predictor.predict_delay(line, datetime.now())

                if (
                    prediction
                    and prediction.predicted_delay_minutes >= self.DELAY_THRESHOLD_MINUTES
                ):
                    notification = self._create_delay_notification(prediction)
                    notifications.append(notification)

            except Exception as e:
                logger.error(f"Error checking {line}: {e}")

        return notifications

    def _create_delay_notification(self, prediction) -> Notification:
        """Create notification for predicted delay."""
        notification_id = f"delay_{prediction.line}_{datetime.now().strftime('%Y%m%d%H%M')}"

        # Determine priority based on delay severity
        delay = prediction.predicted_delay_minutes
        if delay >= 15:
            priority = NotificationPriority.URGENT
            title = f"⚠️ Severe Delay Predicted on {prediction.line}"
        elif delay >= 8:
            priority = NotificationPriority.HIGH
            title = f"⚠️ Significant Delay on {prediction.line}"
        elif delay >= 5:
            priority = NotificationPriority.MEDIUM
            title = f"ℹ️ Delay Expected on {prediction.line}"
        else:
            priority = NotificationPriority.LOW
            title = f"Minor delay on {prediction.line}"

        message = (
            f"Expected delay: {delay:.0f} minutes\n"
            f"Confidence: {prediction.confidence * 100:.0f}%\n"
            f"Consider alternative routes."
        )

        return Notification(
            notification_id=notification_id,
            notification_type=NotificationType.DELAY_ALERT,
            priority=priority,
            title=title,
            message=message,
            line=prediction.line,
            station=None,
            action_url=f"/line/{prediction.line}",
            created_at=datetime.now(),
            expires_at=datetime.now() + timedelta(hours=1),
        )

    def create_alternative_route_notification(
        self, original_line: str, alternative_line: str, time_saved_minutes: int
    ) -> Notification:
        """Create notification suggesting alternative route."""
        notification_id = f"alt_{original_line}_{datetime.now().strftime('%Y%m%d%H%M')}"

        notification = Notification(
            notification_id=notification_id,
            notification_type=NotificationType.ALTERNATIVE_ROUTE,
            priority=NotificationPriority.MEDIUM,
            title="💡 Better Route Available",
            message=(
                f"{original_line} has delays. "
                f"Take {alternative_line} instead - saves {time_saved_minutes} minutes!"
            ),
            line=original_line,
            station=None,
            action_url=None,
            created_at=datetime.now(),
            expires_at=datetime.now() + timedelta(minutes=30),
        )

        return notification

    def send_notification(self, notification: Notification) -> bool:
        """Send notification and store in database.

        Args:
            notification: Notification to send

        Returns:
            True if sent successfully
        """
        try:
            # Store in database
            query = """
            INSERT INTO notifications
            (notification_id, notification_type, priority, title, message,
             line, station, action_url, created_at, expires_at, sent, sent_at)
            VALUES (:notification_id, :notification_type, :priority, :title, :message,
                    :line, :station, :action_url, :created_at, :expires_at, TRUE, NOW())
            ON CONFLICT (notification_id) DO NOTHING
            """

            data = {
                "notification_id": notification.notification_id,
                "notification_type": notification.notification_type.value,
                "priority": notification.priority.value,
                "title": notification.title,
                "message": notification.message,
                "line": notification.line,
                "station": notification.station,
                "action_url": notification.action_url,
                "created_at": notification.created_at,
                "expires_at": notification.expires_at,
            }

            self.db.execute_query(query, data)

            # TODO: Integrate with push notification service (Web Push API)
            # For now, just log
            logger.info(f"Notification sent: {notification.title}")

            return True

        except Exception as e:
            logger.error(f"Error sending notification: {e}", exc_info=True)
            return False

    def get_active_notifications(
        self, user_favorites: Optional[list[str]] = None
    ) -> list[Notification]:
        """Get active notifications for user.

        Args:
            user_favorites: Optional list of favorite station/line IDs

        Returns:
            List of active notifications
        """
        try:
            query = """
            SELECT *
            FROM notifications
            WHERE (expires_at IS NULL OR expires_at > NOW())
                AND created_at > NOW() - INTERVAL '2 hours'
            """

            params = {}

            if user_favorites:
                query += " AND (line = ANY(:favorites) OR station = ANY(:favorites))"
                params["favorites"] = user_favorites

            query += " ORDER BY priority DESC, created_at DESC LIMIT 20"

            results = self.db.execute_query(query, params)

            notifications = []
            for row in results:
                notif = Notification(
                    notification_id=row["notification_id"],
                    notification_type=NotificationType(row["notification_type"]),
                    priority=NotificationPriority(row["priority"]),
                    title=row["title"],
                    message=row["message"],
                    line=row["line"],
                    station=row["station"],
                    action_url=row["action_url"],
                    created_at=row["created_at"],
                    expires_at=row["expires_at"],
                )
                notifications.append(notif)

            return notifications

        except Exception as e:
            logger.error(f"Error getting notifications: {e}", exc_info=True)
            return []


# Singleton
_notification_service: Optional[SmartNotificationService] = None


def get_notification_service(db_manager, prediction_service, historical_collector):
    """Get or create notification service instance."""
    global _notification_service
    if _notification_service is None:
        _notification_service = SmartNotificationService(
            db_manager, prediction_service, historical_collector
        )
    return _notification_service
