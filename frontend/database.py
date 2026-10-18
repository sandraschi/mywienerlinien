"""
Database module: PostgreSQL for app tables, SQLite snapshot for GTFS static data.

GTFS schedule reads (routes, stops, shapes, ...) run against the normalized
snapshot gtfs-mcp writes (<gtfs-mcp data_dir>/snapshots/<feed>.db, SPEC
delegation Phase 1) — no Postgres required for the map. App tables (vehicles,
api keys, notifications, ...) stay on PostgreSQL until the app.db migration.
"""

# Configure logging
import logging
import os
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, List, Optional

from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.pool import QueuePool

logger = logging.getLogger(__name__)


def resolve_snapshot_path(feed_id: str = "vienna") -> Path | None:
    """Locate the gtfs-mcp snapshot file (read-only for us, gtfs-mcp is sole writer).

    Precedence: explicit GTFS_SNAPSHOT_PATH env (read fresh, test-friendly),
    else a `gtfs-mcp` sibling of this repo carrying data/snapshots/<feed>.db,
    else None (callers refuse with guidance instead of failing obscurely).
    """
    explicit = os.environ.get("GTFS_SNAPSHOT_PATH", "").strip()
    if explicit:
        cand = Path(explicit).expanduser()
        return cand if cand.is_file() else None
    sibling = Path(__file__).resolve().parents[2] / "gtfs-mcp" / "data" / "snapshots" / f"{feed_id}.db"
    return sibling if sibling.is_file() else None


def _as_int(value):
    """Best-effort int for group_concat fragments (keeps the raw value if garbage)."""
    try:
        return int(value)
    except (TypeError, ValueError):
        return value


ROUTE_TYPE_NAMES = {
    0: "Tram",
    1: "Metro",
    2: "Rail",
    3: "Bus",
    4: "Ferry",
    5: "Cable Tram",
    6: "Aerial",
    7: "Funicular",
    11: "Trolleybus",
    12: "Monorail",
    800: "Bus",
}


class DatabaseManager:
    """
    Manages database connections and sessions.
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._initialized = True
        self.engine = None
        self.session_factory = None
        # GTFS snapshot connection (SQLite, read-only for us). Initialized
        # separately via init_snapshot: map reads must not require Postgres.
        self.snapshot_engine = None
        self.snapshot_factory = None
        self._default_color = "#3f51b5"

    def init_app(self, app):
        """Initialize the database connection using Flask app configuration."""
        # Always initialize database, even in development mode
        # dev_mode = os.getenv("APP_ENV", "").lower() in ("development", "dev")
        # if dev_mode:
        #     logger.info("Development mode: skipping database initialization")
        #     return

        if self.engine is not None:
            return

        # Get database URL from environment or use default
        db_url = os.getenv("DATABASE_URL", "postgresql://wienerlinien:wienerlinien@db:5432/wienerlinien")

        # Configure the SQLAlchemy engine with connection pooling
        self.engine = create_engine(
            db_url,
            poolclass=QueuePool,
            pool_size=5,
            max_overflow=10,
            pool_timeout=30,
            pool_recycle=1800,  # Recycle connections after 30 minutes
            pool_pre_ping=True,  # Enable connection liveness checks
            connect_args={
                "connect_timeout": 10,
                "keepalives": 1,
                "keepalives_idle": 30,
                "keepalives_interval": 10,
                "keepalives_count": 5,
            },
        )

        # Create a scoped session factory
        self.session_factory = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=self.engine))

        # Test the connection
        self._test_connection()

    def _test_connection(self):
        """Test the database connection."""
        try:
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info("Successfully connected to the database")
        except Exception as e:
            logger.error(f"Failed to connect to the database: {e!s}")
            raise

    def get_session(self):
        """Get a new database session."""
        if not self.session_factory:
            raise RuntimeError("Database not initialized. Call init_app first.")
        return self.session_factory()

    def init_snapshot(self, snapshot_path=None):
        """Connect GTFS static reads to a gtfs-mcp snapshot SQLite file.

        Resolves via resolve_snapshot_path() (GTFS_SNAPSHOT_PATH env, else the
        gtfs-mcp sibling checkout). Idempotent; raises RuntimeError with
        guidance when no snapshot file exists.
        """
        if self.snapshot_engine is not None:
            return
        path = Path(snapshot_path).expanduser() if snapshot_path else resolve_snapshot_path()
        if path is None or not path.is_file():
            raise RuntimeError(
                "GTFS snapshot not found. Export a feed from gtfs-mcp (it writes "
                "<data_dir>/snapshots/<feed>.db) or set GTFS_SNAPSHOT_PATH to the file."
            )
        self.snapshot_engine = create_engine(f"sqlite:///{path}", connect_args={"check_same_thread": False})
        self.snapshot_factory = scoped_session(
            sessionmaker(autocommit=False, autoflush=False, bind=self.snapshot_engine)
        )
        logger.info(f"GTFS snapshot connected: {path}")

    def execute_snapshot_query(self, query: str, params: dict | None = None, fetch_one: bool = False) -> Any:
        """Run a read against the GTFS snapshot (same shape as execute_query).

        fetch_one=True returns the first row dict (or None) instead of a list —
        the shared-manager callers already pass this kwarg.
        """
        if not self.snapshot_factory:
            raise RuntimeError("Snapshot database not initialized. Call init_snapshot first.")
        session = self.snapshot_factory()
        try:
            result = session.execute(text(query), params or {})
            rows = [dict(row._mapping) for row in result]
            return rows[0] if fetch_one and rows else (None if fetch_one else rows)
        except SQLAlchemyError as e:
            logger.error(f"Error executing snapshot query: {e!s}")
            session.rollback()
            raise
        finally:
            self.snapshot_factory.remove()

    def close_session(self, exception=None):
        """Close the current database session."""
        if self.session_factory:
            self.session_factory.remove()

    def execute_query(self, query: str, params: dict | None = None) -> list[dict]:
        """
        Execute a raw SQL query and return the results as a list of dictionaries.

        Args:
            query: The SQL query to execute
            params: Optional parameters for the query

        Returns:
            List of dictionaries representing the query results
        """
        session = self.get_session()
        try:
            result = session.execute(text(query), params or {})
            return [dict(row._mapping) for row in result]
        except SQLAlchemyError as e:
            logger.error(f"Error executing query: {e!s}")
            session.rollback()
            raise
        finally:
            self.close_session()

    @staticmethod
    def _to_float(value: Any) -> float | None:
        if value is None:
            return None
        if isinstance(value, (float, int)):
            return float(value)
        if isinstance(value, Decimal):
            return float(value)
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    def _normalize_color(self, color: str | None) -> str:
        if not color:
            return self._default_color
        value = color.strip()
        if not value:
            return self._default_color
        if not value.startswith("#"):
            value = f"#{value}"
        if len(value) == 4:
            return value.upper()
        if len(value) == 7:
            return value.upper()
        # Truncate to 6 hex digits if longer
        if len(value) > 7:
            value = value[:7]
        return value.upper()

    def get_vehicles(self, line_number: str | None = None) -> list[dict]:
        """
        Get vehicle positions from the database.

        Args:
            line_number: Optional line number to filter by

        Returns:
            List of vehicle positions
        """
        query = """
        SELECT
            v.vehicle_id,
            v.line_number,
            v.direction,
            v.latitude,
            v.longitude,
            v.last_update,
            v.delay,
            v.vehicle_type
        FROM
            vehicles v
        """

        if line_number:
            query += " WHERE v.line_number = :line_number"

        query += " ORDER BY v.last_update DESC"

        return self.execute_query(query, {"line_number": line_number})

    def get_routes(self) -> list[dict]:
        """
        Get all routes from the database.

        Returns:
            List of routes with their details
        """
        query = """
        SELECT
            r.route_id,
            r.route_short_name,
            r.route_long_name,
            r.route_type,
            r.route_color,
            r.route_text_color,
            a.agency_name,
            COUNT(DISTINCT t.trip_id) as trip_count,
            COUNT(DISTINCT st.stop_id) as stop_count
        FROM
            routes r
        LEFT JOIN
            agencies a ON r.agency_id = a.agency_id
        LEFT JOIN
            trips t ON r.route_id = t.route_id
        LEFT JOIN
            stop_times st ON t.trip_id = st.trip_id
        GROUP BY
            r.route_id, a.agency_name
        ORDER BY
            r.route_type, r.route_short_name
        """

        return self.execute_snapshot_query(query)

    def get_line_overview(self, line_name: str) -> dict | None:
        """Return high-level information about a specific line."""
        query = """
        SELECT
            r.route_id,
            r.route_short_name,
            r.route_long_name,
            r.route_type,
            r.route_color,
            r.route_text_color,
            COUNT(DISTINCT t.trip_id) AS trip_count,
            COUNT(DISTINCT st.stop_id) AS stop_count
        FROM
            routes r
        LEFT JOIN
            trips t ON t.route_id = r.route_id
        LEFT JOIN
            stop_times st ON st.trip_id = t.trip_id
        WHERE
            LOWER(r.route_short_name) = LOWER(:line_name)
        GROUP BY
            r.route_id
        ORDER BY
            stop_count DESC
        """

        rows = self.execute_snapshot_query(query, {"line_name": line_name})
        if not rows:
            return None

        primary = rows[0]
        variants = []
        for row in rows:
            variants.append(
                {
                    "route_id": row["route_id"],
                    "trip_count": int(row.get("trip_count") or 0),
                    "stop_count": int(row.get("stop_count") or 0),
                }
            )

        return {
            "route_id": primary["route_id"],
            "line": primary["route_short_name"],
            "name": primary.get("route_long_name"),
            "route_type": primary.get("route_type"),
            "route_type_name": ROUTE_TYPE_NAMES.get(primary.get("route_type"), "Unknown"),
            "color": self._normalize_color(primary.get("route_color")),
            "text_color": self._normalize_color(primary.get("route_text_color")),
            "trip_count": int(primary.get("trip_count") or 0),
            "stop_count": int(primary.get("stop_count") or 0),
            "variants": variants,
        }

    def get_line_route_data(self, line_name: str) -> dict | None:
        """Return route geometry (segments) for a given line."""
        routes = self.execute_snapshot_query(
            """
            SELECT
                r.route_id,
                r.route_short_name,
                r.route_long_name,
                r.route_type,
                r.route_color,
                r.route_text_color
            FROM
                routes r
            WHERE
                LOWER(r.route_short_name) = LOWER(:line_name)
            ORDER BY
                r.route_id
            """,
            {"line_name": line_name},
        )

        if not routes:
            return None

        segments: list[dict[str, Any]] = []
        for route in routes:
            # DISTINCT ON is Postgres-only: window + filter is portable SQLite.
            # NULL directions sort last to match NULLS LAST semantics.
            shapes = self.execute_snapshot_query(
                """
                SELECT shape_id, direction_id FROM (
                    SELECT
                        shape_id,
                        direction_id,
                        ROW_NUMBER() OVER (
                            PARTITION BY shape_id
                            ORDER BY direction_id IS NULL, direction_id, trip_id
                        ) AS rn
                    FROM trips
                    WHERE route_id = :route_id AND shape_id IS NOT NULL
                )
                WHERE rn = 1
                LIMIT 4
                """,
                {"route_id": route["route_id"]},
            )

            for shape in shapes:
                points = self.execute_snapshot_query(
                    """
                    SELECT
                        shape_pt_lat,
                        shape_pt_lon,
                        shape_pt_sequence
                    FROM
                        shapes
                    WHERE
                        shape_id = :shape_id
                    ORDER BY
                        shape_pt_sequence
                    """,
                    {"shape_id": shape["shape_id"]},
                )

                if not points:
                    continue

                coordinates = [
                    [self._to_float(point["shape_pt_lat"]), self._to_float(point["shape_pt_lon"])]
                    for point in points
                    if self._to_float(point["shape_pt_lat"]) is not None
                    and self._to_float(point["shape_pt_lon"]) is not None
                ]

                if not coordinates:
                    continue

                segments.append(
                    {
                        "route_id": route["route_id"],
                        "shape_id": shape["shape_id"],
                        "direction_id": shape.get("direction_id"),
                        "coordinates": coordinates,
                    }
                )

        overview = self.get_line_overview(line_name)
        type_code = overview["route_type"] if overview else routes[0].get("route_type")
        type_name = (
            overview["route_type_name"] if overview else ROUTE_TYPE_NAMES.get(routes[0].get("route_type"), "Unknown")
        )

        return {
            "line": overview["line"] if overview else routes[0]["route_short_name"],
            "name": overview["name"] if overview else routes[0].get("route_long_name"),
            "type": type_name,
            "type_code": type_code,
            "type_name": type_name,
            "color": overview["color"] if overview else self._normalize_color(routes[0].get("route_color")),
            "text_color": overview["text_color"]
            if overview
            else self._normalize_color(routes[0].get("route_text_color")),
            "segments": segments,
            "stops": self.get_line_stations(line_name),
            "overview": overview,
        }

    def get_line_stations(self, line_name: str) -> list[dict]:
        """Return ordered stations for the given line."""
        query = """
        WITH matched_routes AS (
            SELECT route_id
            FROM routes
            WHERE LOWER(route_short_name) = LOWER(:line_name)
        ), ordered_stops AS (
            SELECT
                s.stop_id,
                s.stop_name,
                s.stop_code,
                s.stop_lat,
                s.stop_lon,
                st.stop_sequence,
                t.direction_id,
                ROW_NUMBER() OVER (PARTITION BY s.stop_id ORDER BY st.stop_sequence) AS rn
            FROM matched_routes mr
            JOIN trips t ON t.route_id = mr.route_id
            JOIN stop_times st ON st.trip_id = t.trip_id
            JOIN stops s ON s.stop_id = st.stop_id
        )
        SELECT
            stop_id,
            stop_name,
            stop_code,
            stop_lat,
            stop_lon,
            stop_sequence,
            direction_id
        FROM ordered_stops
        WHERE rn = 1
        ORDER BY stop_sequence
        """

        rows = self.execute_snapshot_query(query, {"line_name": line_name})
        stations: list[dict[str, Any]] = []
        for row in rows:
            stations.append(
                {
                    "id": row["stop_id"],
                    "name": row["stop_name"],
                    "rbl": row["stop_code"],
                    "lat": self._to_float(row["stop_lat"]),
                    "lng": self._to_float(row["stop_lon"]),
                    "sequence": int(row["stop_sequence"]) if row.get("stop_sequence") is not None else None,
                    "direction": int(row["direction_id"]) if row.get("direction_id") is not None else None,
                }
            )
        return stations

    def get_stations(self) -> list[dict]:
        """
        Get all stations from the database.

        Returns:
            List of stations with their details
        """
        query = """
        SELECT
            s.stop_id as id,
            s.stop_name as name,
            s.stop_code as rbl,
            CASE
                WHEN s.location_type = 1 THEN 'station'
                WHEN s.wheelchair_boarding = 1 THEN 'accessible'
                ELSE 'stop'
            END as type,
            s.zone_id as zone,
            s.stop_lat as lat,
            s.stop_lon as lng
        FROM
            stops s
        WHERE
            s.location_type = 1 OR s.parent_station IS NULL OR s.parent_station = ''
        ORDER BY
            s.stop_name
        """

        return self.execute_snapshot_query(query)

    def get_stops(self, route_id: str | None = None) -> list[dict]:
        """
        Get stops from the database, optionally filtered by route.

        Args:
            route_id: Optional route ID to filter stops by

        Returns:
            List of stops with their details
        """
        query = """
        SELECT DISTINCT
            s.stop_id,
            s.stop_name,
            s.stop_lat as latitude,
            s.stop_lon as longitude,
            s.wheelchair_boarding,
            s.location_type,
            s.parent_station,
            group_concat(DISTINCT r.route_short_name) as route_numbers,
            group_concat(DISTINCT r.route_type) as route_types
        FROM
            stops s
        LEFT JOIN
            stop_times st ON s.stop_id = st.stop_id
        LEFT JOIN
            trips t ON st.trip_id = t.trip_id
        LEFT JOIN
            routes r ON t.route_id = r.route_id
        """

        params = {}
        if route_id:
            query += " WHERE t.route_id = :route_id"
            params["route_id"] = route_id

        query += """
        GROUP BY
            s.stop_id, s.stop_name, s.stop_lat, s.stop_lon,
            s.wheelchair_boarding, s.location_type, s.parent_station
        ORDER BY
            s.stop_name
        """

        rows = self.execute_snapshot_query(query, params)
        # Engine-independent shape: Postgres array_agg returns lists, SQLite
        # group_concat returns comma strings — normalize to lists here so
        # callers never see the difference.
        for row in rows:
            row["route_numbers"] = [v for v in str(row.get("route_numbers") or "").split(",") if v]
            row["route_types"] = [_as_int(v) for v in str(row.get("route_types") or "").split(",") if v]
        return rows

    def get_route_stops(self, route_id: str, direction_id: int | None = None) -> list[dict]:
        """
        Get all stops for a specific route and optional direction.

        Args:
            route_id: The route ID
            direction_id: Optional direction ID (0 or 1)

        Returns:
            List of stops in order for the route
        """
        query = """
        WITH route_trips AS (
            SELECT DISTINCT t.trip_id
            FROM trips t
            WHERE t.route_id = :route_id
        )
        SELECT
            s.stop_id,
            s.stop_name,
            s.stop_lat as latitude,
            s.stop_lon as longitude,
            st.stop_sequence,
            t.direction_id
        FROM
            stops s
        JOIN
            stop_times st ON s.stop_id = st.stop_id
        JOIN
            route_trips rt ON st.trip_id = rt.trip_id
        JOIN
            trips t ON st.trip_id = t.trip_id
        WHERE
            t.route_id = :route_id
        """

        params = {"route_id": route_id}

        if direction_id is not None:
            query += " AND t.direction_id = :direction_id"
            params["direction_id"] = direction_id

        query += """
        ORDER BY
            t.direction_id, st.stop_sequence
        """

        return self.execute_snapshot_query(query, params)


# Create a singleton instance
db = DatabaseManager()


def init_db(app):
    """Initialize the database with the Flask app."""
    db.init_app(app)

    # Register teardown handler
    @app.teardown_appcontext
    def shutdown_session(exception=None):
        db.close_session(exception)

    return db
