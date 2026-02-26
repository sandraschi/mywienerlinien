"""
Social Features Service
Phase 5: Community-driven features for commuters

Enables users to:
- Report real-time disruptions
- Share tips and station photos
- Rate transit lines
- Create commuter communities
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional

logger = logging.getLogger(__name__)


class ReportType(Enum):
    """Types of user reports."""

    DELAY = "delay"
    CROWDING = "crowding"
    DISRUPTION = "disruption"
    CLEANLINESS = "cleanliness"
    SAFETY = "safety"
    ACCESSIBILITY = "accessibility"
    OTHER = "other"


class ReportSeverity(Enum):
    """Severity of user reports."""

    INFO = 1
    MINOR = 2
    MODERATE = 3
    SEVERE = 4


@dataclass
class UserReport:
    """User-generated report about transit conditions."""

    report_id: str
    user_id: str
    report_type: ReportType
    severity: ReportSeverity
    line: Optional[str]
    station: Optional[str]
    description: str
    timestamp: datetime
    votes_helpful: int = 0
    votes_not_helpful: int = 0
    verified: bool = False


@dataclass
class StationTip:
    """User tip about a station."""

    tip_id: str
    user_id: str
    station: str
    tip_text: str
    category: str  # "navigation", "accessibility", "amenities", "connection"
    helpful_votes: int
    timestamp: datetime


class SocialService:
    """Community-driven features service."""

    def __init__(self, db_manager):
        """Initialize social service.

        Args:
            db_manager: Database manager instance
        """
        self.db = db_manager
        self._create_tables()

    def _create_tables(self):
        """Create social features tables."""
        try:
            # User reports table
            self.db.execute_query("""
            CREATE TABLE IF NOT EXISTS user_reports (
                id SERIAL PRIMARY KEY,
                report_id VARCHAR(100) UNIQUE,
                user_id VARCHAR(100),
                report_type VARCHAR(50),
                severity INTEGER,
                line VARCHAR(10),
                station VARCHAR(200),
                description TEXT,
                votes_helpful INTEGER DEFAULT 0,
                votes_not_helpful INTEGER DEFAULT 0,
                verified BOOLEAN DEFAULT FALSE,
                timestamp TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)

            # Station tips table
            self.db.execute_query("""
            CREATE TABLE IF NOT EXISTS station_tips (
                id SERIAL PRIMARY KEY,
                tip_id VARCHAR(100) UNIQUE,
                user_id VARCHAR(100),
                station VARCHAR(200),
                tip_text TEXT,
                category VARCHAR(50),
                helpful_votes INTEGER DEFAULT 0,
                timestamp TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)

            # Line ratings table
            self.db.execute_query("""
            CREATE TABLE IF NOT EXISTS line_ratings (
                id SERIAL PRIMARY KEY,
                user_id VARCHAR(100),
                line VARCHAR(10),
                rating INTEGER CHECK (rating >= 1 AND rating <= 5),
                comment TEXT,
                timestamp TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, line)
            )
            """)

            # Station photos table
            self.db.execute_query("""
            CREATE TABLE IF NOT EXISTS station_photos (
                id SERIAL PRIMARY KEY,
                photo_id VARCHAR(100) UNIQUE,
                user_id VARCHAR(100),
                station VARCHAR(200),
                photo_url VARCHAR(500),
                caption TEXT,
                likes INTEGER DEFAULT 0,
                timestamp TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)

            logger.info("Social features tables created/verified")

        except Exception as e:
            logger.error(f"Error creating social tables: {e}", exc_info=True)

    def submit_report(
        self,
        user_id: str,
        report_type: ReportType,
        severity: ReportSeverity,
        description: str,
        line: Optional[str] = None,
        station: Optional[str] = None,
    ) -> Optional[UserReport]:
        """Submit a user report about transit conditions.

        Args:
            user_id: User identifier
            report_type: Type of report
            severity: Severity level
            description: Description text
            line: Affected line (optional)
            station: Affected station (optional)

        Returns:
            UserReport object if successful
        """
        try:
            import secrets

            report_id = f"report_{secrets.token_hex(8)}"

            report = UserReport(
                report_id=report_id,
                user_id=user_id,
                report_type=report_type,
                severity=severity,
                line=line,
                station=station,
                description=description,
                timestamp=datetime.now(),
            )

            # Store in database
            self.db.execute_query(
                """
            INSERT INTO user_reports
            (report_id, user_id, report_type, severity, line, station,
             description, timestamp)
            VALUES (:report_id, :user_id, :report_type, :severity, :line,
                    :station, :description, :timestamp)
            """,
                {
                    "report_id": report.report_id,
                    "user_id": report.user_id,
                    "report_type": report.report_type.value,
                    "severity": report.severity.value,
                    "line": report.line,
                    "station": report.station,
                    "description": report.description,
                    "timestamp": report.timestamp,
                },
            )

            logger.info(f"User report submitted: {report_id} ({report_type.value})")
            return report

        except Exception as e:
            logger.error(f"Error submitting report: {e}", exc_info=True)
            return None

    def get_recent_reports(
        self, line: Optional[str] = None, station: Optional[str] = None, hours: int = 2
    ) -> list[dict]:
        """Get recent user reports.

        Args:
            line: Filter by line
            station: Filter by station
            hours: Hours to look back

        Returns:
            List of recent reports
        """
        try:
            query = """
            SELECT *
            FROM user_reports
            WHERE timestamp > NOW() - INTERVAL ':hours hours'
            """

            params = {"hours": hours}

            if line:
                query += " AND line = :line"
                params["line"] = line

            if station:
                query += " AND station = :station"
                params["station"] = station

            query += " ORDER BY timestamp DESC, votes_helpful DESC LIMIT 20"

            return self.db.execute_query(query, params)

        except Exception as e:
            logger.error(f"Error getting reports: {e}", exc_info=True)
            return []

    def submit_station_tip(
        self, user_id: str, station: str, tip_text: str, category: str = "general"
    ) -> Optional[StationTip]:
        """Submit a helpful tip about a station.

        Args:
            user_id: User identifier
            station: Station name
            tip_text: Tip content
            category: Tip category

        Returns:
            StationTip object if successful
        """
        try:
            import secrets

            tip_id = f"tip_{secrets.token_hex(8)}"

            tip = StationTip(
                tip_id=tip_id,
                user_id=user_id,
                station=station,
                tip_text=tip_text,
                category=category,
                helpful_votes=0,
                timestamp=datetime.now(),
            )

            self.db.execute_query(
                """
            INSERT INTO station_tips
            (tip_id, user_id, station, tip_text, category, timestamp)
            VALUES (:tip_id, :user_id, :station, :tip_text, :category, :timestamp)
            """,
                {
                    "tip_id": tip.tip_id,
                    "user_id": tip.user_id,
                    "station": tip.station,
                    "tip_text": tip.tip_text,
                    "category": tip.category,
                    "timestamp": tip.timestamp,
                },
            )

            logger.info(f"Station tip submitted: {tip_id} for {station}")
            return tip

        except Exception as e:
            logger.error(f"Error submitting tip: {e}", exc_info=True)
            return None

    def get_station_tips(self, station: str, limit: int = 10) -> list[dict]:
        """Get tips for a station.

        Args:
            station: Station name
            limit: Maximum tips to return

        Returns:
            List of station tips
        """
        try:
            query = """
            SELECT *
            FROM station_tips
            WHERE station = :station
            ORDER BY helpful_votes DESC, timestamp DESC
            LIMIT :limit
            """

            return self.db.execute_query(query, {"station": station, "limit": limit})

        except Exception as e:
            logger.error(f"Error getting station tips: {e}", exc_info=True)
            return []

    def vote_helpful(self, item_id: str, item_type: str = "report") -> bool:
        """Vote an item as helpful.

        Args:
            item_id: Report ID or Tip ID
            item_type: "report" or "tip"

        Returns:
            True if successful
        """
        try:
            if item_type == "report":
                self.db.execute_query(
                    """
                UPDATE user_reports
                SET votes_helpful = votes_helpful + 1
                WHERE report_id = :id
                """,
                    {"id": item_id},
                )
            elif item_type == "tip":
                self.db.execute_query(
                    """
                UPDATE station_tips
                SET helpful_votes = helpful_votes + 1
                WHERE tip_id = :id
                """,
                    {"id": item_id},
                )

            return True

        except Exception as e:
            logger.error(f"Error voting: {e}", exc_info=True)
            return False

    def get_line_community_rating(self, line: str) -> Optional[dict]:
        """Get community rating for a line.

        Args:
            line: Line code

        Returns:
            Rating statistics
        """
        try:
            query = """
            SELECT
                COUNT(*) as total_ratings,
                AVG(rating) as average_rating,
                STDDEV(rating) as stddev,
                MAX(rating) as max_rating,
                MIN(rating) as min_rating
            FROM line_ratings
            WHERE line = :line
            """

            results = self.db.execute_query(query, {"line": line})

            if results and results[0]["total_ratings"] > 0:
                return {
                    "line": line,
                    "average_rating": float(results[0]["average_rating"]),
                    "total_ratings": results[0]["total_ratings"],
                    "stddev": float(results[0]["stddev"]) if results[0]["stddev"] else 0,
                }

            return None

        except Exception as e:
            logger.error(f"Error getting line rating: {e}", exc_info=True)
            return None


# Singleton
_social_service: Optional[SocialService] = None


def get_social_service(db_manager) -> SocialService:
    """Get or create social service instance."""
    global _social_service
    if _social_service is None:
        _social_service = SocialService(db_manager)
    return _social_service
