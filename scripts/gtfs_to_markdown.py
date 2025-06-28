"""
Generate clean markdown files from GTFS data using pygtfs.

This script generates markdown files for routes and stations
using the official GTFS data through the pygtfs library.
"""

# Test print to verify script execution
print("Script started successfully!")
print(f"Python version: {__import__('sys').version}")
print(f"Python executable: {__import__('sys').executable}")


import os
import sys
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Set, Tuple, Optional

import pygtfs
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('gtfs_to_markdown')

class GTFSMarkdownGenerator:
    """Generate markdown files from GTFS data using pygtfs."""
    
    def __init__(self, gtfs_db_path: str, output_dir: Path):
        """Initialize with path to GTFS SQLite database and output directory."""
        logger.info("="*80)
        logger.info("Initializing GTFSMarkdownGenerator")
        logger.info("="*80)
        
        # Convert string path to Path object if needed
        gtfs_db_path = Path(gtfs_db_path) if isinstance(gtfs_db_path, str) else gtfs_db_path
        self.gtfs_db_path = gtfs_db_path.resolve()
        
        logger.info(f"GTFS Database Path: {self.gtfs_db_path}")
        logger.info(f"Database exists: {self.gtfs_db_path.exists()}")
        
        if not self.gtfs_db_path.exists():
            raise FileNotFoundError(f"GTFS database not found at: {self.gtfs_db_path}")
        
        # Ensure output directory exists
        self.output_dir = Path(output_dir).resolve()
        logger.info(f"\nOutput Directory: {self.output_dir}")
        
        try:
            self.output_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Output directory ready: {self.output_dir}")
            
            # Test writing to the directory
            test_file = self.output_dir / "test_write.tmp"
            test_file.write_text("test")
            test_file.unlink()
            logger.info("Write test to output directory successful")
            
        except Exception as e:
            logger.error(f"Failed to initialize output directory: {e}")
            raise
            
        logger.info("-" * 80)
        logger.info("")
        
        # Initialize database connection
        self._init_database()
        
        # Route type mappings
        self.route_types = {
            '0': {'name': 'Tram', 'filename': 'tramroutes.md', 'station_file': 'tramstations.md'},
            '1': {'name': 'Metro', 'filename': 'tuberoutes.md', 'station_file': 'tubestations.md'},
            '3': {'name': 'Bus', 'filename': 'busroutes.md', 'station_file': 'busstations.md'},
            '7': {'name': 'Funicular', 'filename': 'funicularroutes.md', 'station_file': 'funicularstations.md'},
        }
        
        # Initialize database connection
        self.engine = create_engine(f'sqlite:///{gtfs_db_path}')
        self.Session = sessionmaker(bind=self.engine)
        self.session = self.Session()
    
    def get_routes_by_type(self) -> Dict[str, List[pygtfs.gtfs_entities.Route]]:
        """Get routes grouped by their type."""
        routes_by_type = {}
        for route in self.schedule.routes:
            route_type = str(route.route_type)
            if route_type not in routes_by_type:
                routes_by_type[route_type] = []
            routes_by_type[route_type].append(route)
        return routes_by_type
    
    def get_stop_sequence(self, trip: pygtfs.gtfs_entities.Trip) -> List[pygtfs.gtfs_entities.Stop]:
        """Get the sequence of stops for a trip."""
        stop_times = self.session.query(pygtfs.gtfs_entities.StopTime)\
            .filter_by(trip_id=trip.trip_id)\
            .order_by(pygtfs.gtfs_entities.StopTime.stop_sequence)\
            .all()
        return [st.stop for st in stop_times]
    
    def generate_route_markdown(self, route_type: str, routes: List[pygtfs.gtfs_entities.Route]) -> str:
        """Generate markdown content for routes of a specific type."""
        if not routes:
            return ""
            
        route_type_info = self.route_types.get(route_type, {
            'name': f'Type {route_type}',
            'filename': f'type_{route_type}_routes.md',
            'station_file': f'type_{route_type}_stations.md'
        })
        
        lines = [
            f"# Vienna {route_type_info['name']} Routes",
            f"\n*Generated from official Wiener Linien GTFS data*  *Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n"
        ]
        
        for route in sorted(routes, key=lambda r: r.route_short_name):
            # Get one trip for this route to get the stop sequence
            trip = self.session.query(pygtfs.gtfs_entities.Trip)\
                .filter_by(route_id=route.route_id)\
                .first()
                
            if not trip:
                logger.warning(f"No trips found for route {route.route_short_name}")
                continue
                
            stops = self.get_stop_sequence(trip)
            
            lines.extend([
                f"## {route.route_short_name} - {route.route_long_name}",
                f"- **Line**: {route.route_short_name}",
                f"- **Type**: {route_type_info['name']}",
                f"- **Color**: {getattr(route, 'route_color', '#000000')}",
                f"- **Stops**: {len(stops)}\n",
                "### Stops:",
                *[f"1. {stop.stop_name} (ID: {stop.stop_id})" for stop in stops],
                ""
            ])
        
        return "\n".join(lines)
    
    def generate_station_markdown(self) -> str:
        """Generate markdown content for all stations."""
        # Group stops by their parent station or use the stop itself
        stations = {}
        for stop in self.schedule.stops:
            parent_id = getattr(stop, 'parent_station', None) or stop.stop_id
            if parent_id not in stations:
                stations[parent_id] = {
                    'name': stop.stop_name,
                    'routes': set(),
                    'location': (stop.stop_lat, stop.stop_lon) if stop.stop_lat and stop.stop_lon else None
                }
            
            # Add routes that serve this stop
            for route in self.session.query(pygtfs.gtfs_entities.Route)\
                .join(pygtfs.gtfs_entities.Trip)\
                .join(pygtfs.gtfs_entities.StopTime)\
                .filter(pygtfs.gtfs_entities.StopTime.stop_id == stop.stop_id)\
                .distinct():
                stations[parent_id]['routes'].add((route.route_short_name, route.route_type))
        
        # Sort stations by name
        sorted_stations = sorted(stations.items(), key=lambda x: x[1]['name'])
        
        # Generate markdown
        lines = [
            "# Vienna Public Transport Stations",
            f"\n*Generated from official Wiener Linien GTFS data*  *Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n"
        ]
        
        for station_id, data in sorted_stations:
            route_list = ", ".join(
                f"{route_num} ({self.route_types.get(str(route_type), {}).get('name', 'Unknown')})"
                for route_num, route_type in sorted(data['routes'])
            )
            
            location = f"{data['location'][0]:.6f}, {data['location'][1]:.6f}" if data['location'] else "Location not available"
            
            lines.extend([
                f"## {data['name']}",
                f"- **Station ID**: {station_id}",
                f"- **Location**: {location}",
                f"- **Served by**: {route_list or 'No routes found'}",
                ""
            ])
        
        return "\n".join(lines)
    
    def generate_all(self):
        """Generate all markdown files."""
        # Generate route files by type
        routes_by_type = self.get_routes_by_type()
        
        for route_type, routes in routes_by_type.items():
            route_type_info = self.route_types.get(route_type, {})
            if not route_type_info:
                logger.warning(f"No configuration found for route type {route_type}")
                continue
                
            content = self.generate_route_markdown(route_type, routes)
            output_file = self.output_dir / route_type_info['filename']
            output_file.write_text(content, encoding='utf-8')
            logger.info(f"Generated {output_file}")
        
        # Generate stations file
        stations_content = self.generate_station_markdown()
        stations_file = self.output_dir / 'stations.md'
        stations_file.write_text(stations_content, encoding='utf-8')
        logger.info(f"Generated {stations_file}")

    def _init_database(self):
        """Initialize database connection and verify schema."""
        logger.info("Initializing database connection...")
        
        try:
            # Create SQLAlchemy engine
            db_url = f'sqlite:///{self.gtfs_db_path}'
            logger.info(f"Database URL: {db_url}")
            
            self.engine = create_engine(db_url)
            self.Session = sessionmaker(bind=self.engine)
            self.session = self.Session()
            
            # Test connection
            with self.engine.connect() as conn:
                # Use text() for raw SQL queries
                from sqlalchemy import text
                result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table';"))
                tables = [row[0] for row in result]
                logger.info(f"Found {len(tables)} tables in database")
                
                required_tables = {'agency', 'stops', 'routes', 'trips', 'stop_times'}
                missing_tables = required_tables - set(tables)
                
                if missing_tables:
                    raise ValueError(f"Missing required tables: {missing_tables}")
                
                # Log table counts
                for table in required_tables:
                    if table in tables:
                        # Use text() for raw SQL queries with parameters
                        count = conn.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
                        logger.info(f"Table '{table}': {count} rows")
            
            # Initialize pygtfs schedule with the database URL string
            logger.info("Initializing pygtfs Schedule...")
            self.schedule = pygtfs.Schedule(f'sqlite:///{self.gtfs_db_path}')
            
            # Log basic stats
            logger.info(f"Agencies: {len(self.schedule.agencies)}")
            logger.info(f"Routes: {len(self.schedule.routes)}")
            logger.info(f"Stops: {len(self.schedule.stops)}")
            logger.info(f"Trips: {len(self.schedule.trips)}")
            
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}", exc_info=True)
            raise

    def generate_trip_markdown(self, route_type: str, routes: List[pygtfs.gtfs_entities.Route]) -> str:
        """Generate markdown content for trips of a specific route type."""
        if not routes:
            return ""
            
        route_type_info = self.route_types.get(route_type, {
            'name': f'Type {route_type}',
            'filename': f'type_{route_type}_routes.md',
            'station_file': f'type_{route_type}_stations.md',
            'trip_file': f'type_{route_type}_trips.md'
        })
        
        lines = [
            f"# Vienna {route_type_info['name']} Trips",
            f"\n*Generated from official Wiener Linien GTFS data*  *Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n"
        ]
        
        for route in sorted(routes, key=lambda r: r.route_short_name):
            # Get all trips for this route
            trips = self.session.query(pygtfs.gtfs_entities.Trip)\
                .filter_by(route_id=route.route_id)\
                .order_by(pygtfs.gtfs_entities.Trip.trip_headsign)\
                .all()
                
            if not trips:
                logger.warning(f"No trips found for route {route.route_short_name}")
                continue
                
            # Group trips by headsign
            trips_by_headsign = {}
            for trip in trips:
                headsign = trip.trip_headsign or "Unknown Destination"
                if headsign not in trips_by_headsign:
                    trips_by_headsign[headsign] = []
                trips_by_headsign[headsign].append(trip)
            
            lines.extend([
                f"## Route {route.route_short_name} - {route.route_long_name}",
                f"- **Route Type**: {route_type_info['name']}",
                f"- **Number of Trips**: {len(trips)}",
                f"- **Number of Directions**: {len(trips_by_headsign)}\n"
            ])
            
            for headsign, trips in trips_by_headsign.items():
                lines.append(f"### To: {headsign}")
                
                # Get stop sequence from the first trip
                if trips:
                    stops = self.get_stop_sequence(trips[0])
                    lines.append("#### Stops:")
                    lines.extend([f"{i+1}. {stop.stop_name}" for i, stop in enumerate(stops)])
                    lines.append("")
                
                # Show trip times for this headsign
                lines.append("#### Sample Departure Times:")
                for trip in sorted(trips[:5], key=lambda t: t.departure_time if hasattr(t, 'departure_time') else ''):
                    dep_time = getattr(trip, 'departure_time', 'N/A')
                    lines.append(f"- {dep_time}")
                if len(trips) > 5:
                    lines.append(f"- ... and {len(trips) - 5} more trips")
                lines.append("")
        
        return "\n".join(lines)

    def generate_all(self):
        """Generate all markdown files."""
        logger.info("\n" + "="*80)
        logger.info("Starting markdown generation")
        logger.info("="*80 + "\n")
        
        try:
            # Generate route files by type
            routes_by_type = self.get_routes_by_type()
            logger.info(f"Found routes in {len(routes_by_type)} route types")
            
            for route_type, routes in routes_by_type.items():
                route_type_info = self.route_types.get(route_type, {
                    'name': f'Type {route_type}',
                    'filename': f'type_{route_type}_routes.md',
                    'station_file': f'type_{route_type}_stations.md',
                    'trip_file': f'type_{route_type}_trips.md'
                })
                
                logger.info(f"\nProcessing {route_type_info['name']} routes...")
                logger.info(f"Found {len(routes)} routes of type {route_type}")
                
                # Generate route markdown
                route_content = self.generate_route_markdown(route_type, routes)
                route_file = self.output_dir / route_type_info['filename']
                
                logger.info(f"Writing {len(route_content)} characters to {route_file}")
                route_file.write_text(route_content, encoding='utf-8')
                logger.info(f"Successfully wrote {route_file}")
                
                # Generate trip markdown
                trip_content = self.generate_trip_markdown(route_type, routes)
                trip_file = self.output_dir / route_type_info.get('trip_file', f'type_{route_type}_trips.md')
                
                logger.info(f"Writing {len(trip_content)} characters to {trip_file}")
                trip_file.write_text(trip_content, encoding='utf-8')
                logger.info(f"Successfully wrote {trip_file}")
            
            # Generate stations file
            logger.info("\nGenerating stations markdown...")
            stations_content = self.generate_station_markdown()
            stations_file = self.output_dir / 'stations.md'
            
            logger.info(f"Writing {len(stations_content)} characters to {stations_file}")
            stations_file.write_text(stations_content, encoding='utf-8')
            logger.info(f"Successfully wrote {stations_file}")
            
            logger.info("\n" + "="*80)
            logger.info("Markdown generation completed successfully")
            logger.info("="*80)
            
        except Exception as e:
            logger.error(f"Error during markdown generation: {e}", exc_info=True)
            raise

def setup_logging():
    """Set up logging configuration."""
    try:
        script_dir = Path(__file__).parent.resolve()
        log_file = script_dir / 'gtfs_to_markdown.log'
        
        # Print log file location
        print(f"Log file will be created at: {log_file}")
        
        # Clear any existing log handlers to avoid duplicate logs
        for handler in logging.root.handlers[:]:
            logging.root.removeHandler(handler)
        
        # Set up file handler with explicit file mode
        file_handler = logging.FileHandler(log_file, mode='w', encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        
        # Set up console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Create formatter and add it to the handlers
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # Create logger
        logger = logging.getLogger('gtfs_to_markdown')
        logger.setLevel(logging.DEBUG)
        
        # Add handlers to logger
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        # Log startup information
        logger.info("="*80)
        logger.info("Starting GTFS to Markdown Conversion")
        logger.info(f"Script directory: {script_dir}")
        logger.info(f"Log file: {log_file}")
        logger.info("="*80)
        
        return script_dir, logger
        
    except Exception as e:
        print(f"Error setting up logging: {e}", file=sys.stderr)
        raise

def main():
    """Main function to run the markdown generation."""
    script_dir, logger = setup_logging()
    
    
    try:
        # Path to the GTFS SQLite database
        script_dir = Path(__file__).parent.resolve()
        logger.info(f"Script directory: {script_dir}")
        
        gtfs_db = script_dir / 'gtfs_data' / 'gtfs.sqlite'
        gtfs_db = gtfs_db.resolve()
        logger.info(f"GTFS database path: {gtfs_db}")
        
        if not gtfs_db.exists():
            error_msg = f"GTFS database not found at {gtfs_db}"
            logger.error(error_msg)
            logger.info("Please run gtfs_parser.py first to create the database.")
            return 1
        
        # Output directory
        output_dir = script_dir.parent / 'frontend' / 'data'
        output_dir = output_dir.resolve()
        logger.info(f"Output directory: {output_dir}")
        
        # Ensure output directory exists
        output_dir.mkdir(parents=True, exist_ok=True)
        if not output_dir.exists():
            error_msg = f"Failed to create output directory: {output_dir}"
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)
        
        logger.info("\n" + "-"*80)
        logger.info("Initializing GTFSMarkdownGenerator")
        logger.info("-"*80)
        
        generator = GTFSMarkdownGenerator(str(gtfs_db), output_dir)
        
        logger.info("\n" + "-"*80)
        logger.info("Starting markdown generation")
        logger.info("-"*80 + "\n")
        
        generator.generate_all()
        
        logger.info("\n" + "="*80)
        logger.info("GTFS to Markdown conversion completed successfully")
        logger.info("="*80)
        
        return 0
        
    except Exception as e:
        logger.error(f"\nError in main: {str(e)}", exc_info=True)
        logger.error("="*80)
        logger.error("GTFS to Markdown conversion failed")
        logger.error("="*80)
        return 1
    finally:
        logging.shutdown()

if __name__ == "__main__":
    sys.exit(main())
