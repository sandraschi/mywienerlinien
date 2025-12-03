"""
Multi-city management service.
Phase 4 Enhancement: Support for multiple Austrian and international cities.

Manages GTFS data, routing, and features across different cities.
"""

import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class CityManager:
    """Manages multi-city transit data and configurations."""

    def __init__(self, db_manager, config_dir: Optional[Path] = None):
        """Initialize city manager.

        Args:
            db_manager: Database manager instance
            config_dir: Directory for city configurations
        """
        self.db = db_manager
        self.config_dir = config_dir or Path(__file__).parent.parent / "data" / "cities"
        self.config_dir.mkdir(parents=True, exist_ok=True)

        self.current_city = "vienna"  # Default
        self.loaded_cities = {}

        self._create_tables()

    def _create_tables(self):
        """Create multi-city management tables."""
        try:
            # Cities table
            self.db.execute_query("""
            CREATE TABLE IF NOT EXISTS cities (
                id SERIAL PRIMARY KEY,
                city_code VARCHAR(50) UNIQUE NOT NULL,
                city_name VARCHAR(200) NOT NULL,
                country VARCHAR(100),
                timezone VARCHAR(100),
                language VARCHAR(10),
                gtfs_url TEXT,
                map_center_lat FLOAT,
                map_center_lng FLOAT,
                map_zoom INTEGER,
                enabled BOOLEAN DEFAULT TRUE,
                gtfs_last_updated TIMESTAMP,
                data_loaded BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)

            # City-specific routing preferences
            self.db.execute_query("""
            CREATE TABLE IF NOT EXISTS city_preferences (
                id SERIAL PRIMARY KEY,
                city_code VARCHAR(50) REFERENCES cities(city_code),
                preference_key VARCHAR(100),
                preference_value TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(city_code, preference_key)
            )
            """)

            # Initialize Vienna as default city
            self._initialize_default_cities()

            logger.info("City management tables created/verified")

        except Exception as e:
            logger.error(f"Error creating city tables: {e}", exc_info=True)

    def _initialize_default_cities(self):
        """Initialize default cities in database."""
        try:
            # Import city configurations
            import sys
            from pathlib import Path

            sys.path.insert(0, str(Path(__file__).parent.parent.parent))
            from scripts.city_config import CITIES

            for city_code, config in CITIES.items():
                query = """
                INSERT INTO cities
                (city_code, city_name, country, timezone, language, gtfs_url,
                 map_center_lat, map_center_lng, map_zoom, enabled)
                VALUES (:code, :name, :country, :timezone, :language, :url,
                        :lat, :lng, :zoom, TRUE)
                ON CONFLICT (city_code) DO UPDATE SET
                    gtfs_url = EXCLUDED.gtfs_url,
                    map_center_lat = EXCLUDED.map_center_lat,
                    map_center_lng = EXCLUDED.map_center_lng,
                    map_zoom = EXCLUDED.map_zoom
                """

                # Extract country from city name
                country = (
                    "Austria"
                    if city_code in ["vienna", "graz", "linz", "salzburg", "innsbruck", "oebb"]
                    else "Unknown"
                )

                params = {
                    "code": city_code,
                    "name": config.name,
                    "country": country,
                    "timezone": config.timezone,
                    "language": config.language,
                    "url": config.gtfs_url,
                    "lat": config.map_center[0] if config.map_center else None,
                    "lng": config.map_center[1] if config.map_center else None,
                    "zoom": config.map_zoom,
                }

                self.db.execute_query(query, params)

            logger.info(f"Initialized {len(CITIES)} cities in database")

        except Exception as e:
            logger.warning(f"Error initializing cities: {e}")

    def get_active_city(self) -> str:
        """Get currently active city code."""
        return self.current_city

    def switch_city(self, city_code: str) -> bool:
        """Switch to a different city.

        Args:
            city_code: City code to switch to

        Returns:
            True if switch successful
        """
        try:
            # Check if city exists
            query = "SELECT city_code, data_loaded FROM cities WHERE city_code = :code AND enabled = TRUE"
            results = self.db.execute_query(query, {"code": city_code})

            if not results:
                logger.warning(f"City {city_code} not found or disabled")
                return False

            city_data = results[0]

            if not city_data["data_loaded"]:
                logger.warning(f"City {city_code} data not loaded yet")
                # Still allow switch, but note that data needs loading

            self.current_city = city_code
            logger.info(f"Switched to city: {city_code}")
            return True

        except Exception as e:
            logger.error(f"Error switching city: {e}", exc_info=True)
            return False

    def get_available_cities(self) -> list[dict]:
        """Get list of available cities.

        Returns:
            List of city information dictionaries
        """
        try:
            query = """
            SELECT
                city_code,
                city_name,
                country,
                timezone,
                language,
                map_center_lat,
                map_center_lng,
                map_zoom,
                data_loaded,
                gtfs_last_updated
            FROM cities
            WHERE enabled = TRUE
            ORDER BY
                CASE
                    WHEN country = 'Austria' THEN 1
                    ELSE 2
                END,
                city_name
            """

            results = self.db.execute_query(query)

            cities = []
            for row in results:
                cities.append(
                    {
                        "code": row["city_code"],
                        "name": row["city_name"],
                        "country": row["country"],
                        "timezone": row["timezone"],
                        "language": row["language"],
                        "map_center": {"lat": row["map_center_lat"], "lng": row["map_center_lng"]}
                        if row["map_center_lat"]
                        else None,
                        "map_zoom": row["map_zoom"],
                        "data_loaded": row["data_loaded"],
                        "last_updated": row["gtfs_last_updated"].isoformat()
                        if row["gtfs_last_updated"]
                        else None,
                    }
                )

            return cities

        except Exception as e:
            logger.error(f"Error getting cities: {e}", exc_info=True)
            return []

    def get_city_info(self, city_code: Optional[str] = None) -> Optional[dict]:
        """Get detailed information about a city.

        Args:
            city_code: City code (defaults to current city)

        Returns:
            City information dictionary
        """
        if city_code is None:
            city_code = self.current_city

        cities = self.get_available_cities()
        for city in cities:
            if city["code"] == city_code:
                return city

        return None

    def mark_city_data_loaded(self, city_code: str) -> bool:
        """Mark city data as loaded after GTFS import.

        Args:
            city_code: City code

        Returns:
            True if successful
        """
        try:
            query = """
            UPDATE cities
            SET data_loaded = TRUE,
                gtfs_last_updated = NOW()
            WHERE city_code = :code
            """

            self.db.execute_query(query, {"code": city_code})
            logger.info(f"Marked {city_code} data as loaded")
            return True

        except Exception as e:
            logger.error(f"Error marking city loaded: {e}", exc_info=True)
            return False

    def get_city_statistics(self, city_code: Optional[str] = None) -> dict:
        """Get statistics for a city.

        Args:
            city_code: City code (defaults to current)

        Returns:
            Statistics dictionary
        """
        if city_code is None:
            city_code = self.current_city

        try:
            # Count routes, stops, trips for this city
            # Note: Current schema doesn't separate by city
            # Future enhancement: Add city_code to GTFS tables

            stats = {
                "city": city_code,
                "routes": 0,
                "stops": 0,
                "trips": 0,
                "message": "Multi-city separation pending - all data currently shared",
            }

            return stats

        except Exception as e:
            logger.error(f"Error getting city stats: {e}", exc_info=True)
            return {}


# Singleton
_city_manager: Optional[CityManager] = None


def get_city_manager(db_manager) -> CityManager:
    """Get or create city manager instance."""
    global _city_manager
    if _city_manager is None:
        _city_manager = CityManager(db_manager)
    return _city_manager
