import os
import sys
import logging
from pathlib import Path
from datetime import datetime
import pandas as pd
from sqlalchemy.orm import sessionmaker
from tqdm import tqdm

# Add project root to path
project_root = str(Path(__file__).parent.parent)
sys.path.append(project_root)

# Import our models
from models.gtfs_models import engine, init_db, Agency, Route, Stop, Trip, StopTime, SessionLocal

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_gtfs_to_db(gtfs_path, chunk_size=1000):
    """
    Load GTFS data from a zip file into the database.
    
    Args:
        gtfs_path (str): Path to the GTFS zip file
        chunk_size (int): Number of records to process in each chunk
    """
    try:
        import gtfs_kit as gk
    except ImportError:
        logger.error("gtfs_kit not found. Please install it with: pip install gtfs-kit")
        sys.exit(1)
    
    # Initialize database
    logger.info("Initializing database...")
    init_db()
    
    # Load the GTFS feed
    logger.info(f"Loading GTFS feed from {gtfs_path}...")
    feed = gk.read_feed(gtfs_path, dist_units='km')
    
    # Create a session
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Load agencies
        logger.info("Loading agencies...")
        for _, row in tqdm(feed.agencies.iterrows(), total=len(feed.agencies)):
            agency = Agency(
                agency_id=row.get('agency_id', ''),
                agency_name=row.get('agency_name', ''),
                agency_url=row.get('agency_url', ''),
                agency_timezone=row.get('agency_timezone', 'Europe/Vienna'),
                agency_lang=row.get('agency_lang', 'de'),
                agency_phone=row.get('agency_phone', '')
            )
            session.merge(agency)
        session.commit()
        
        # Load stops
        logger.info("Loading stops...")
        for _, row in tqdm(feed.stops.iterrows(), total=len(feed.stops)):
            stop = Stop(
                stop_id=row['stop_id'],
                stop_code=row.get('stop_code', ''),
                stop_name=row.get('stop_name', ''),
                stop_desc=row.get('stop_desc', ''),
                stop_lat=row.get('stop_lat'),
                stop_lon=row.get('stop_lon'),
                zone_id=row.get('zone_id'),
                stop_url=row.get('stop_url'),
                location_type=row.get('location_type', 0),
                parent_station=row.get('parent_station'),
                wheelchair_boarding=row.get('wheelchair_boarding')
            )
            session.merge(stop)
        session.commit()
        
        # Load routes
        logger.info("Loading routes...")
        for _, row in tqdm(feed.routes.iterrows(), total=len(feed.routes)):
            route = Route(
                route_id=row['route_id'],
                agency_id=row.get('agency_id', ''),
                route_short_name=row.get('route_short_name', ''),
                route_long_name=row.get('route_long_name', ''),
                route_desc=row.get('route_desc', ''),
                route_type=row.get('route_type', 3),  # Default to bus
                route_url=row.get('route_url'),
                route_color=row.get('route_color', 'FFFFFF'),
                route_text_color=row.get('route_text_color', '000000')
            )
            session.merge(route)
        session.commit()
        
        # Load trips and stop times in chunks
        logger.info("Loading trips and stop times...")
        
        # Process trips in chunks
        for i in tqdm(range(0, len(feed.trips), chunk_size)):
            chunk = feed.trips.iloc[i:i + chunk_size]
            
            # Process trips in this chunk
            for _, trip_row in chunk.iterrows():
                trip = Trip(
                    trip_id=trip_row['trip_id'],
                    route_id=trip_row.get('route_id'),
                    service_id=trip_row.get('service_id', ''),
                    trip_headsign=trip_row.get('trip_headsign'),
                    trip_short_name=trip_row.get('trip_short_name'),
                    direction_id=trip_row.get('direction_id'),
                    block_id=trip_row.get('block_id'),
                    shape_id=trip_row.get('shape_id'),
                    wheelchair_accessible=trip_row.get('wheelchair_accessible', 0),
                    bikes_allowed=trip_row.get('bikes_allowed', 0)
                )
                session.merge(trip)
                
                # Get stop times for this trip
                stop_times = feed.stop_times[feed.stop_times['trip_id'] == trip_row['trip_id']]
                
                for _, st_row in stop_times.iterrows():
                    stop_time = StopTime(
                        trip_id=st_row['trip_id'],
                        arrival_time=st_row.get('arrival_time', ''),
                        departure_time=st_row.get('departure_time', ''),
                        stop_id=st_row.get('stop_id'),
                        stop_sequence=st_row.get('stop_sequence', 0),
                        stop_headsign=st_row.get('stop_headsign'),
                        pickup_type=st_row.get('pickup_type', 0),
                        drop_off_type=st_row.get('drop_off_type', 0),
                        shape_dist_traveled=st_row.get('shape_dist_traveled'),
                        timepoint=st_row.get('timepoint', 1)
                    )
                    session.merge(stop_time)
            
            # Commit after each chunk
            session.commit()
        
        logger.info("Data loading completed successfully!")
        
    except Exception as e:
        logger.error(f"Error loading GTFS data: {str(e)}", exc_info=True)
        session.rollback()
        raise
    finally:
        session.close()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Load GTFS data into the database')
    parser.add_argument('gtfs_path', help='Path to the GTFS zip file')
    parser.add_argument('--chunk-size', type=int, default=1000,
                       help='Number of records to process in each chunk (default: 1000)')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.gtfs_path):
        logger.error(f"GTFS file not found: {args.gtfs_path}")
        sys.exit(1)
    
    load_gtfs_to_db(args.gtfs_path, args.chunk_size)
