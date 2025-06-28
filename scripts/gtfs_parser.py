"""
GTFS Parser using pygtfs

This script demonstrates how to parse and query GTFS data using the pygtfs library.
"""
import os
import sys
import logging
import sqlalchemy
from pathlib import Path
import pygtfs

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

def setup_database(gtfs_zip_path: Path, db_path: str = ':memory:') -> pygtfs.Schedule:
    """
    Set up a SQLite database and load GTFS data into it.
    
    Args:
        gtfs_zip_path: Path to the GTFS zip file
        db_path: Path to SQLite database (default: in-memory)
        
    Returns:
        pygtfs.Schedule: Loaded GTFS schedule
    """
    logger.info(f"Setting up database from {gtfs_zip_path}")
    
    # Handle database path
    db_url = 'sqlite:///:memory:'
    if db_path != ':memory:':
        # Ensure directory exists
        db_path = Path(db_path).absolute()
        db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Convert to string and normalize path for SQLite
        db_path_str = str(db_path).replace('\\', '/')
        db_url = f'sqlite:///{db_path_str}'
        
        logger.info(f"Using database at: {db_url}")
    
    # Create a new GTFS database and load the feed
    try:
        logger.info("Creating database schema...")
        schedule = pygtfs.Schedule(db_url)
        
        logger.info("Loading GTFS data...")
        pygtfs.append_feed(schedule, str(gtfs_zip_path))
        
        logger.info("GTFS data loaded successfully")
        return schedule
    except Exception as e:
        logger.error(f"Error loading GTFS data: {e}", exc_info=True)
        raise

def print_route_info(schedule: pygtfs.Schedule) -> None:
    """Print basic information about routes in the GTFS data."""
    print("\n=== Routes ===")
    # Get all routes, ordered by route_short_name
    routes = schedule.session.query(pygtfs.gtfs_entities.Route).order_by(
        pygtfs.gtfs_entities.Route.route_short_name
    ).all()
    
    for route in routes:
        print(f"{route.route_short_name}: {route.route_long_name} (Type: {route.route_type})")

def print_stop_info(schedule: pygtfs.Schedule, route_short_name: str) -> None:
    """Print information about stops for a specific route."""
    print(f"\n=== Stops for Route {route_short_name} ===")
    
    # Find the route by short name
    route = schedule.session.query(pygtfs.gtfs_entities.Route).filter_by(
        route_short_name=route_short_name
    ).first()
    
    if not route:
        print(f"Route {route_short_name} not found")
        return
    
    # Get all trips for this route
    trips = schedule.session.query(pygtfs.gtfs_entities.Trip).filter_by(
        route_id=route.route_id
    ).limit(1).all()  # Just get one trip for demonstration
    
    if not trips:
        print(f"No trips found for route {route_short_name}")
        return
    
    # Get stop times for the first trip
    trip = trips[0]
    print(f"\nTrip: {trip.trip_headsign or trip.trip_id}")
    
    # Get stop times ordered by stop_sequence
    stop_times = schedule.session.query(pygtfs.gtfs_entities.StopTime).filter_by(
        trip_id=trip.trip_id
    ).order_by(pygtfs.gtfs_entities.StopTime.stop_sequence).all()
    
    for st in stop_times:
        # Get the stop information
        stop = schedule.session.query(pygtfs.gtfs_entities.Stop).get(st.stop_id)
        print(f"  {st.stop_sequence:2d}. {stop.stop_name} ({st.arrival_time})")

def main():
    """Main function to demonstrate GTFS parsing."""
    try:
        # Get the script directory
        script_dir = Path(__file__).parent.resolve()
        
        # Path to the GTFS zip file
        gtfs_zip_path = script_dir / "gtfs_data" / "gtfs.zip"
        
        if not gtfs_zip_path.exists():
            logger.error(f"GTFS file not found at {gtfs_zip_path}")
            return
        
        # Set up the database and load GTFS data
        db_path = script_dir / "gtfs_data" / "gtfs.sqlite"
        logger.info(f"Creating database at: {db_path}")
        
        # Remove existing database if it exists
        if db_path.exists():
            logger.info("Removing existing database file")
            db_path.unlink()
            
        schedule = setup_database(gtfs_zip_path, str(db_path))
        
        # Print some basic information
        routes_count = schedule.session.query(pygtfs.gtfs_entities.Route).count()
        stops_count = schedule.session.query(pygtfs.gtfs_entities.Stop).count()
        
        print(f"\nLoaded GTFS data with {routes_count} routes and {stops_count} stops")
        
        # Show route information (first 10 routes)
        print_route_info(schedule)
        
        # Show stops for a specific route (e.g., U1 for subway)
        print("\n" + "="*50)
        print("Example: Stops for U1 (U-Bahn)")
        print("="*50)
        print_stop_info(schedule, "U1")
        
        # Also show a tram line example
        print("\n" + "="*50)
        print("Example: Stops for D (Tram)")
        print("="*50)
        print_stop_info(schedule, "D")
        
    except Exception as e:
        logger.error(f"Error processing GTFS data: {e}", exc_info=True)
    finally:
        if 'schedule' in locals():
            schedule.session.close()

if __name__ == "__main__":
    main()
