"""
Database module for handling PostgreSQL operations.

This module provides a database session factory and common database operations
for the Wiener Linien application.
"""
import os
from typing import List, Dict, Any, Optional
from datetime import datetime

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.pool import QueuePool

# Configure logging
import logging
logger = logging.getLogger(__name__)

class DatabaseManager:
    """
    Manages database connections and sessions.
    """
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self._initialized = True
        self.engine = None
        self.session_factory = None
    
    def init_app(self, app):
        """Initialize the database connection using Flask app configuration."""
        if self.engine is not None:
            return
            
        # Get database URL from environment or use default
        db_url = os.getenv('DATABASE_URL', 'postgresql://wienerlinien:wienerlinien@db:5432/wienerlinien')
        
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
                'connect_timeout': 10,
                'keepalives': 1,
                'keepalives_idle': 30,
                'keepalives_interval': 10,
                'keepalives_count': 5
            }
        )
        
        # Create a scoped session factory
        self.session_factory = scoped_session(
            sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine
            )
        )
        
        # Test the connection
        self._test_connection()
    
    def _test_connection(self):
        """Test the database connection."""
        try:
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info("Successfully connected to the database")
        except Exception as e:
            logger.error(f"Failed to connect to the database: {str(e)}")
            raise
    
    def get_session(self):
        """Get a new database session."""
        if not self.session_factory:
            raise RuntimeError("Database not initialized. Call init_app first.")
        return self.session_factory()
    
    def close_session(self, exception=None):
        """Close the current database session."""
        if self.session_factory:
            self.session_factory.remove()
    
    def execute_query(self, query: str, params: Optional[Dict] = None) -> List[Dict]:
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
            logger.error(f"Error executing query: {str(e)}")
            session.rollback()
            raise
        finally:
            self.close_session()
    
    def get_vehicles(self, line_number: Optional[str] = None) -> List[Dict]:
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
        
        return self.execute_query(query, {'line_number': line_number})
    
    def get_routes(self) -> List[Dict]:
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
        
        return self.execute_query(query)
    
    def get_stops(self, route_id: Optional[str] = None) -> List[Dict]:
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
            array_agg(DISTINCT r.route_short_name) as route_numbers,
            array_agg(DISTINCT r.route_type) as route_types
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
            params['route_id'] = route_id
            
        query += """
        GROUP BY 
            s.stop_id, s.stop_name, s.stop_lat, s.stop_lon, 
            s.wheelchair_boarding, s.location_type, s.parent_station
        ORDER BY 
            s.stop_name
        """
        
        return self.execute_query(query, params)
    
    def get_route_stops(self, route_id: str, direction_id: Optional[int] = None) -> List[Dict]:
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
        
        params = {'route_id': route_id}
        
        if direction_id is not None:
            query += " AND t.direction_id = :direction_id"
            params['direction_id'] = direction_id
            
        query += """
        ORDER BY 
            t.direction_id, st.stop_sequence
        """
        
        return self.execute_query(query, params)

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
