"""
Historical data collection and management service.
Phase 3C Enhancement: Collects journey times, delays, and patterns for ML training.

This module continuously logs actual transit performance data to build
a historical dataset for delay prediction and analytics.
"""

import json
import logging
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class VehicleSnapshot:
    """Snapshot of vehicle state at a point in time."""

    vehicle_id: str
    line: str
    station: str
    delay_minutes: int
    latitude: float
    longitude: float
    timestamp: datetime
    direction: str
    vehicle_type: str

    def to_dict(self) -> dict:
        """Convert to dictionary for storage."""
        data = asdict(self)
        data["timestamp"] = self.timestamp.isoformat()
        return data


@dataclass
class JourneyRecord:
    """Record of a completed journey with actual timing."""

    journey_id: str
    from_station_id: str
    to_station_id: str
    planned_duration_minutes: int
    actual_duration_minutes: int | None
    transfers: int
    lines_used: list[str]
    departure_time: datetime
    arrival_time: datetime | None
    delays_encountered: list[dict]
    route_segments: list[dict]
    timestamp: datetime

    def to_dict(self) -> dict:
        """Convert to dictionary for storage."""
        data = asdict(self)
        data["departure_time"] = self.departure_time.isoformat()
        data["arrival_time"] = self.arrival_time.isoformat() if self.arrival_time else None
        data["timestamp"] = self.timestamp.isoformat()
        return data


@dataclass
class DelayPattern:
    """Identified delay pattern for a line/time/day combination."""

    line: str
    day_of_week: int  # 0=Monday, 6=Sunday
    hour: int  # 0-23
    average_delay_minutes: float
    max_delay_minutes: float
    sample_count: int
    reliability_score: float  # 0-100
    last_updated: datetime

    def to_dict(self) -> dict:
        """Convert to dictionary for storage."""
        data = asdict(self)
        data["last_updated"] = self.last_updated.isoformat()
        return data


class HistoricalDataCollector:
    """Collects and manages historical transit data."""

    def __init__(self, db_manager, storage_dir: Path | None = None):
        """Initialize historical data collector.

        Args:
            db_manager: Database manager instance
            storage_dir: Directory for JSON storage (fallback if DB unavailable)
        """
        self.db = db_manager
        self.storage_dir = storage_dir or Path(__file__).parent.parent / "data" / "historical"
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        # In-memory buffer for batch inserts
        self.vehicle_buffer: list[VehicleSnapshot] = []
        self.journey_buffer: list[JourneyRecord] = []
        self.buffer_size = 100  # Flush after 100 records

        self._create_tables()

    def _create_tables(self):
        """Create historical data tables if they don't exist."""
        try:
            # Vehicle snapshots table
            self.db.execute_query(
                """
            CREATE TABLE IF NOT EXISTS historical_vehicles (
                id SERIAL PRIMARY KEY,
                vehicle_id VARCHAR(100),
                line VARCHAR(10),
                station VARCHAR(200),
                delay_minutes INTEGER,
                latitude FLOAT,
                longitude FLOAT,
                direction VARCHAR(50),
                vehicle_type VARCHAR(20),
                timestamp TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
            )

            # Create indexes for common queries
            self.db.execute_query(
                """
            CREATE INDEX IF NOT EXISTS idx_historical_vehicles_line_time
            ON historical_vehicles(line, timestamp)
            """
            )

            self.db.execute_query(
                """
            CREATE INDEX IF NOT EXISTS idx_historical_vehicles_timestamp
            ON historical_vehicles(timestamp DESC)
            """
            )

            # Journey records table
            self.db.execute_query(
                """
            CREATE TABLE IF NOT EXISTS historical_journeys (
                id SERIAL PRIMARY KEY,
                journey_id VARCHAR(100) UNIQUE,
                from_station_id VARCHAR(50),
                to_station_id VARCHAR(50),
                planned_duration_minutes INTEGER,
                actual_duration_minutes INTEGER,
                transfers INTEGER,
                lines_used TEXT,  -- JSON array
                departure_time TIMESTAMP,
                arrival_time TIMESTAMP,
                delays_encountered TEXT,  -- JSON array
                route_segments TEXT,  -- JSON array
                timestamp TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
            )

            self.db.execute_query(
                """
            CREATE INDEX IF NOT EXISTS idx_historical_journeys_route
            ON historical_journeys(from_station_id, to_station_id, timestamp)
            """
            )

            # Delay patterns table (for ML predictions)
            self.db.execute_query(
                """
            CREATE TABLE IF NOT EXISTS delay_patterns (
                id SERIAL PRIMARY KEY,
                line VARCHAR(10),
                day_of_week INTEGER,
                hour INTEGER,
                average_delay_minutes FLOAT,
                max_delay_minutes FLOAT,
                sample_count INTEGER,
                reliability_score FLOAT,
                last_updated TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(line, day_of_week, hour)
            )
            """
            )

            logger.info("Historical data tables created/verified")

        except Exception as e:
            logger.error(f"Error creating historical tables: {e}", exc_info=True)

    def record_vehicle_snapshot(self, vehicle_data: dict):
        """Record a vehicle snapshot for historical analysis.

        Args:
            vehicle_data: Vehicle data from API
        """
        try:
            snapshot = VehicleSnapshot(
                vehicle_id=vehicle_data.get("id", "unknown"),
                line=vehicle_data.get("line", "unknown"),
                station=vehicle_data.get("station", "unknown"),
                delay_minutes=vehicle_data.get("delay_minutes", 0),
                latitude=vehicle_data.get("latitude", 0.0),
                longitude=vehicle_data.get("longitude", 0.0),
                direction=vehicle_data.get("direction", "unknown"),
                vehicle_type=vehicle_data.get("vehicle_type", "unknown"),
                timestamp=datetime.now(),
            )

            self.vehicle_buffer.append(snapshot)

            # Flush if buffer full
            if len(self.vehicle_buffer) >= self.buffer_size:
                self._flush_vehicle_buffer()

        except Exception as e:
            logger.error(f"Error recording vehicle snapshot: {e}", exc_info=True)

    def record_journey(
        self,
        journey_id: str,
        from_station_id: str,
        to_station_id: str,
        planned_duration: int,
        actual_duration: int | None,
        transfers: int,
        lines_used: list[str],
        departure_time: datetime,
        arrival_time: datetime | None,
        delays: list[dict],
        segments: list[dict],
    ):
        """Record a completed journey for historical analysis.

        Args:
            journey_id: Unique journey identifier
            from_station_id: Origin station ID
            to_station_id: Destination station ID
            planned_duration: Planned duration in minutes
            actual_duration: Actual duration if completed
            transfers: Number of transfers
            lines_used: List of line names used
            departure_time: Departure time
            arrival_time: Actual arrival time
            delays: List of delays encountered
            segments: Journey segments
        """
        try:
            record = JourneyRecord(
                journey_id=journey_id,
                from_station_id=from_station_id,
                to_station_id=to_station_id,
                planned_duration_minutes=planned_duration,
                actual_duration_minutes=actual_duration,
                transfers=transfers,
                lines_used=lines_used,
                departure_time=departure_time,
                arrival_time=arrival_time,
                delays_encountered=delays,
                route_segments=segments,
                timestamp=datetime.now(),
            )

            self.journey_buffer.append(record)

            # Flush if buffer full
            if len(self.journey_buffer) >= self.buffer_size:
                self._flush_journey_buffer()

        except Exception as e:
            logger.error(f"Error recording journey: {e}", exc_info=True)

    def _flush_vehicle_buffer(self):
        """Flush vehicle snapshots to database."""
        if not self.vehicle_buffer:
            return

        try:
            # Try database insert
            query = """
            INSERT INTO historical_vehicles
            (vehicle_id, line, station, delay_minutes, latitude, longitude,
             direction, vehicle_type, timestamp)
            VALUES (:vehicle_id, :line, :station, :delay_minutes, :latitude,
                    :longitude, :direction, :vehicle_type, :timestamp)
            """

            for snapshot in self.vehicle_buffer:
                self.db.execute_query(query, snapshot.to_dict())

            logger.info(f"Flushed {len(self.vehicle_buffer)} vehicle snapshots to database")
            self.vehicle_buffer.clear()

        except Exception as e:
            logger.warning(f"Database flush failed, saving to file: {e}")
            self._flush_to_file("vehicles", self.vehicle_buffer)
            self.vehicle_buffer.clear()

    def _flush_journey_buffer(self):
        """Flush journey records to database."""
        if not self.journey_buffer:
            return

        try:
            query = """
            INSERT INTO historical_journeys
            (journey_id, from_station_id, to_station_id, planned_duration_minutes,
             actual_duration_minutes, transfers, lines_used, departure_time,
             arrival_time, delays_encountered, route_segments, timestamp)
            VALUES (:journey_id, :from_station_id, :to_station_id, :planned_duration_minutes,
                    :actual_duration_minutes, :transfers, :lines_used, :departure_time,
                    :arrival_time, :delays_encountered, :route_segments, :timestamp)
            ON CONFLICT (journey_id) DO UPDATE SET
                actual_duration_minutes = EXCLUDED.actual_duration_minutes,
                arrival_time = EXCLUDED.arrival_time
            """

            for record in self.journey_buffer:
                data = record.to_dict()
                data["lines_used"] = json.dumps(data["lines_used"])
                data["delays_encountered"] = json.dumps(data["delays_encountered"])
                data["route_segments"] = json.dumps(data["route_segments"])
                self.db.execute_query(query, data)

            logger.info(f"Flushed {len(self.journey_buffer)} journey records to database")
            self.journey_buffer.clear()

        except Exception as e:
            logger.warning(f"Database flush failed, saving to file: {e}")
            self._flush_to_file("journeys", self.journey_buffer)
            self.journey_buffer.clear()

    def _flush_to_file(self, data_type: str, buffer: list):
        """Flush buffer to JSON file as fallback."""
        try:
            filename = f"{data_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            filepath = self.storage_dir / filename

            data = [item.to_dict() for item in buffer]
            with open(filepath, "w") as f:
                json.dump(data, f, indent=2)

            logger.info(f"Saved {len(buffer)} {data_type} to {filepath}")
        except Exception as e:
            logger.error(f"Failed to save to file: {e}", exc_info=True)

    def get_delay_history(self, line: str | None = None, days: int = 30) -> list[dict]:
        """Get historical delay data for analysis.

        Args:
            line: Filter by line (None for all)
            days: Number of days to look back

        Returns:
            List of delay records
        """
        try:
            query = """
            SELECT
                line,
                station,
                delay_minutes,
                timestamp,
                EXTRACT(DOW FROM timestamp) as day_of_week,
                EXTRACT(HOUR FROM timestamp) as hour
            FROM historical_vehicles
            WHERE timestamp > NOW() - INTERVAL ':days days'
            """

            params = {"days": days}

            if line:
                query += " AND line = :line"
                params["line"] = line

            query += " ORDER BY timestamp DESC LIMIT 10000"

            return self.db.execute_query(query, params)

        except Exception as e:
            logger.error(f"Error fetching delay history: {e}", exc_info=True)
            return []

    def analyze_delay_patterns(self, line: str | None = None) -> list[DelayPattern]:
        """Analyze historical data to identify delay patterns.

        Args:
            line: Filter by line (None for all)

        Returns:
            List of identified delay patterns
        """
        try:
            query = """
            SELECT
                line,
                EXTRACT(DOW FROM timestamp)::INTEGER as day_of_week,
                EXTRACT(HOUR FROM timestamp)::INTEGER as hour,
                AVG(delay_minutes) as avg_delay,
                MAX(delay_minutes) as max_delay,
                COUNT(*) as sample_count,
                100 - (AVG(delay_minutes) * 5) as reliability_score
            FROM historical_vehicles
            WHERE timestamp > NOW() - INTERVAL '30 days'
                AND delay_minutes IS NOT NULL
            """

            params = {}
            if line:
                query += " AND line = :line"
                params["line"] = line

            query += """
            GROUP BY line, day_of_week, hour
            HAVING COUNT(*) >= 10  -- Minimum sample size
            ORDER BY line, day_of_week, hour
            """

            results = self.db.execute_query(query, params)

            patterns = []
            for row in results:
                pattern = DelayPattern(
                    line=row["line"],
                    day_of_week=row["day_of_week"],
                    hour=row["hour"],
                    average_delay_minutes=float(row["avg_delay"]),
                    max_delay_minutes=float(row["max_delay"]),
                    sample_count=row["sample_count"],
                    reliability_score=max(0, min(100, float(row["reliability_score"]))),
                    last_updated=datetime.now(),
                )
                patterns.append(pattern)

            # Store patterns in database
            self._store_patterns(patterns)

            logger.info(f"Analyzed {len(patterns)} delay patterns")
            return patterns

        except Exception as e:
            logger.error(f"Error analyzing delay patterns: {e}", exc_info=True)
            return []

    def _store_patterns(self, patterns: list[DelayPattern]):
        """Store delay patterns in database for quick lookup."""
        try:
            query = """
            INSERT INTO delay_patterns
            (line, day_of_week, hour, average_delay_minutes, max_delay_minutes,
             sample_count, reliability_score, last_updated)
            VALUES (:line, :day_of_week, :hour, :average_delay_minutes,
                    :max_delay_minutes, :sample_count, :reliability_score, :last_updated)
            ON CONFLICT (line, day_of_week, hour) DO UPDATE SET
                average_delay_minutes = EXCLUDED.average_delay_minutes,
                max_delay_minutes = EXCLUDED.max_delay_minutes,
                sample_count = EXCLUDED.sample_count,
                reliability_score = EXCLUDED.reliability_score,
                last_updated = EXCLUDED.last_updated
            """

            for pattern in patterns:
                self.db.execute_query(query, pattern.to_dict())

            logger.info(f"Stored {len(patterns)} delay patterns")

        except Exception as e:
            logger.error(f"Error storing patterns: {e}", exc_info=True)

    def get_pattern_for_time(self, line: str, target_time: datetime) -> DelayPattern | None:
        """Get delay pattern for a specific line and time.

        Args:
            line: Line name
            target_time: Target datetime

        Returns:
            Delay pattern if available
        """
        try:
            day_of_week = target_time.weekday()
            hour = target_time.hour

            query = """
            SELECT *
            FROM delay_patterns
            WHERE line = :line
                AND day_of_week = :day_of_week
                AND hour = :hour
            ORDER BY last_updated DESC
            LIMIT 1
            """

            results = self.db.execute_query(
                query, {"line": line, "day_of_week": day_of_week, "hour": hour}
            )

            if results:
                row = results[0]
                return DelayPattern(
                    line=row["line"],
                    day_of_week=row["day_of_week"],
                    hour=row["hour"],
                    average_delay_minutes=row["average_delay_minutes"],
                    max_delay_minutes=row["max_delay_minutes"],
                    sample_count=row["sample_count"],
                    reliability_score=row["reliability_score"],
                    last_updated=row["last_updated"],
                )

            return None

        except Exception as e:
            logger.error(f"Error getting pattern: {e}", exc_info=True)
            return None

    def get_line_reliability_stats(self, days: int = 30) -> dict[str, dict]:
        """Get reliability statistics for all lines.

        Args:
            days: Number of days to analyze

        Returns:
            Dictionary of line stats
        """
        try:
            query = """
            SELECT
                line,
                COUNT(*) as total_samples,
                AVG(delay_minutes) as avg_delay,
                STDDEV(delay_minutes) as stddev_delay,
                MAX(delay_minutes) as max_delay,
                PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY delay_minutes) as median_delay,
                PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY delay_minutes) as p95_delay,
                100 - (AVG(delay_minutes) * 5) as reliability_score
            FROM historical_vehicles
            WHERE timestamp > NOW() - INTERVAL ':days days'
                AND delay_minutes IS NOT NULL
            GROUP BY line
            ORDER BY reliability_score DESC
            """

            results = self.db.execute_query(query, {"days": days})

            stats = {}
            for row in results:
                stats[row["line"]] = {
                    "total_samples": row["total_samples"],
                    "average_delay": float(row["avg_delay"]),
                    "stddev_delay": float(row["stddev_delay"]) if row["stddev_delay"] else 0,
                    "max_delay": float(row["max_delay"]),
                    "median_delay": float(row["median_delay"]),
                    "p95_delay": float(row["p95_delay"]),
                    "reliability_score": max(0, min(100, float(row["reliability_score"]))),
                }

            return stats

        except Exception as e:
            logger.error(f"Error getting reliability stats: {e}", exc_info=True)
            return {}

    def cleanup_old_data(self, days_to_keep: int = 90):
        """Remove historical data older than specified days.

        Args:
            days_to_keep: Number of days of data to retain
        """
        try:
            # Clean vehicle snapshots
            self.db.execute_query(
                """
            DELETE FROM historical_vehicles
            WHERE timestamp < NOW() - INTERVAL ':days days'
            """,
                {"days": days_to_keep},
            )

            # Clean journey records
            self.db.execute_query(
                """
            DELETE FROM historical_journeys
            WHERE timestamp < NOW() - INTERVAL ':days days'
            """,
                {"days": days_to_keep},
            )

            logger.info(f"Cleaned data older than {days_to_keep} days")

        except Exception as e:
            logger.error(f"Error cleaning old data: {e}", exc_info=True)

    def export_training_data(self, output_file: Path | None = None) -> Path:
        """Export historical data for ML training.

        Args:
            output_file: Output file path (auto-generated if None)

        Returns:
            Path to exported file
        """
        if output_file is None:
            output_file = (
                self.storage_dir / f"training_data_{datetime.now().strftime('%Y%m%d')}.json"
            )

        try:
            # Get comprehensive dataset
            data = {
                "vehicle_snapshots": self.get_delay_history(days=90),
                "delay_patterns": [p.to_dict() for p in self.analyze_delay_patterns()],
                "line_reliability": self.get_line_reliability_stats(days=90),
                "export_date": datetime.now().isoformat(),
                "record_count": {
                    "vehicles": len(self.get_delay_history(days=90)),
                    "patterns": len(self.analyze_delay_patterns()),
                },
            }

            with open(output_file, "w") as f:
                json.dump(data, f, indent=2, default=str)

            logger.info(f"Exported training data to {output_file}")
            return output_file

        except Exception as e:
            logger.error(f"Error exporting training data: {e}", exc_info=True)
            raise


# Singleton instance
_collector: HistoricalDataCollector | None = None


def get_historical_collector(db_manager) -> HistoricalDataCollector:
    """Get or create historical data collector instance."""
    global _collector
    if _collector is None:
        _collector = HistoricalDataCollector(db_manager)
    return _collector
