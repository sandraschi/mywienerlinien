"""
GTFS Data Analyzer for Wiener Linien

This script analyzes GTFS data to extract accurate route and station information
for Vienna's public transport system (U-Bahn, trams, and buses).
"""

import csv
import os
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Set, Tuple, Optional
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('gtfs_analysis.log', mode='w', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

# Path to GTFS data directory
GTFS_DIR = os.path.join(os.path.dirname(__file__), 'gtfs_data', 'extracted')

# Output directory for generated files
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), '..', 'frontend', 'data')

# Route types in GTFS (https://developers.google.com/transit/gtfs/reference#routestxt)
ROUTE_TYPES = {
    '0': 'tram',
    '1': 'metro',
    '2': 'rail',
    '3': 'bus',
    '4': 'ferry',
    '5': 'cable_tram',
    '6': 'aerial',
    '7': 'funicular',
    '11': 'trolleybus',
    '12': 'monorail'
}

@dataclass
class Stop:
    """Represents a GTFS stop with additional route and direction context."""
    stop_id: str
    stop_name: str
    lat: float
    lon: float
    routes: Dict[str, Set[int]] = field(default_factory=lambda: defaultdict(set))  # route_id -> set of direction_ids

@dataclass
class Route:
    """Represents a transport route with its stops and directions."""
    route_id: str
    route_short_name: str
    route_long_name: str
    route_type: str  # Using the GTFS route_type code
    route_color: str = ""
    route_text_color: str = ""
    directions: Dict[int, Dict] = field(default_factory=dict)  # direction_id -> {trip_id, stop_sequence: [stops]}

def load_stops(gtfs_dir: str) -> Dict[str, Stop]:
    """Load all stops from stops.txt."""
    stops = {}
    stops_file = os.path.join(gtfs_dir, 'stops.txt')
    
    try:
        with open(stops_file, 'r', encoding='utf-8-sig') as f:  # Handle BOM if present
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    stop = Stop(
                        stop_id=row['stop_id'].strip(),
                        stop_name=row['stop_name'].strip(),
                        lat=float(row['stop_lat']),
                        lon=float(row['stop_lon'])
                    )
                    stops[stop.stop_id] = stop
                except (KeyError, ValueError) as e:
                    logger.warning(f"Invalid stop entry: {row}. Error: {e}")
                    continue
        
        logger.info(f"Loaded {len(stops)} stops")
        return stops
    
    except FileNotFoundError:
        logger.error(f"stops.txt not found in {gtfs_dir}")
        return {}
    except Exception as e:
        logger.error(f"Error loading stops: {e}")
        return {}

def load_routes(gtfs_dir: str) -> Dict[str, Route]:
    """Load all routes from routes.txt."""
    routes = {}
    routes_file = os.path.join(gtfs_dir, 'routes.txt')
    
    try:
        with open(routes_file, 'r', encoding='utf-8-sig') as f:  # Handle BOM if present
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    route = Route(
                        route_id=row['route_id'].strip(),
                        route_short_name=row['route_short_name'].strip(),
                        route_long_name=row['route_long_name'].strip(),
                        route_type=row['route_type'],
                        route_color=row.get('route_color', '').strip() or '000000',
                        route_text_color=row.get('route_text_color', '').strip() or 'FFFFFF'
                    )
                    routes[route.route_id] = route
                except (KeyError, ValueError) as e:
                    logger.warning(f"Invalid route entry: {row}. Error: {e}")
                    continue
        
        logger.info(f"Loaded {len(routes)} routes")
        return routes
    
    except FileNotFoundError:
        logger.error(f"routes.txt not found in {gtfs_dir}")
        return {}
    except Exception as e:
        logger.error(f"Error loading routes: {e}")
        return {}

def load_trips(gtfs_dir: str, routes: Dict[str, Route]) -> Dict[str, Dict]:
    """Load trips and associate them with routes."""
    trips_file = os.path.join(gtfs_dir, 'trips.txt')
    trips_data = {}
    
    try:
        with open(trips_file, 'r', encoding='utf-8-sig') as f:  # Handle BOM if present
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    route_id = row['route_id'].strip()
                    if route_id not in routes:
                        continue
                        
                    trip_id = row['trip_id'].strip()
                    direction_id = int(row.get('direction_id', '0'))
                    shape_id = row.get('shape_id', '').strip()
                    
                    # Store trip data
                    trips_data[trip_id] = {
                        'route_id': route_id,
                        'direction_id': direction_id,
                        'shape_id': shape_id,
                        'trip_headsign': row.get('trip_headsign', '').strip(),
                        'service_id': row.get('service_id', '').strip()
                    }
                    
                    # Initialize direction in route if not exists
                    if direction_id not in routes[route_id].directions:
                        routes[route_id].directions[direction_id] = {
                            'trip_id': trip_id,
                            'stop_sequence': []
                        }
                        
                except (KeyError, ValueError) as e:
                    logger.warning(f"Invalid trip entry: {row}. Error: {e}")
                    continue
        
        logger.info(f"Loaded {len(trips_data)} trips")
        return trips_data
    
    except FileNotFoundError:
        logger.error(f"trips.txt not found in {gtfs_dir}")
        return {}
    except Exception as e:
        logger.error(f"Error loading trips: {e}")
        return {}

def process_stop_times(gtfs_dir: str, stops: Dict[str, Stop], routes: Dict[str, Route], trips: Dict[str, Dict]) -> None:
    """Process stop_times.txt to build stop sequences for each trip."""
    stop_times_file = os.path.join(gtfs_dir, 'stop_times.txt')
    
    try:
        # Track stop sequences for each trip
        trip_stop_sequences = defaultdict(list)
        total_rows = 0
        processed_rows = 0
        
        # First pass: count total rows for progress tracking
        logger.info("Counting rows in stop_times.txt...")
        with open(stop_times_file, 'r', encoding='utf-8-sig') as f:
            total_rows = sum(1 for _ in f) - 1  # Subtract 1 for header
        
        logger.info(f"Processing {total_rows} stop time entries...")
        
        # Second pass: collect stop sequences
        with open(stop_times_file, 'r', encoding='utf-8-sig') as f:  # Handle BOM if present
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    processed_rows += 1
                    if processed_rows % 100000 == 0:
                        progress = (processed_rows / total_rows) * 100
                        logger.info(f"Progress: {progress:.1f}% ({processed_rows}/{total_rows} rows)")
                    
                    trip_id = row['trip_id'].strip()
                    if trip_id not in trips:
                        continue
                        
                    stop_sequence = int(row['stop_sequence'])
                    stop_id = row['stop_id'].strip()
                    
                    if stop_id not in stops:
                        logger.debug(f"Stop ID {stop_id} not found in stops.txt")
                        continue
                        
                    trip_stop_sequences[trip_id].append((stop_sequence, stop_id))
                    
                except (KeyError, ValueError) as e:
                    logger.warning(f"Invalid stop_time entry: {row}. Error: {e}")
                    continue
        
        logger.info(f"Collected stop sequences for {len(trip_stop_sequences)} trips")
        
        # Process collected stop sequences
        logger.info("Processing stop sequences and updating routes...")
        processed_trips = 0
        total_trips = len(trip_stop_sequences)
        
        for trip_id, stop_sequence in trip_stop_sequences.items():
            processed_trips += 1
            if processed_trips % 1000 == 0:
                progress = (processed_trips / total_trips) * 100
                logger.info(f"Progress: {progress:.1f}% ({processed_trips}/{total_trips} trips)")
            
            if not stop_sequence:
                continue
                
            trip_info = trips.get(trip_id, {})
            route_id = trip_info.get('route_id')
            direction_id = trip_info.get('direction_id', 0)
            
            if not route_id or route_id not in routes:
                continue
                
            # Sort by stop_sequence
            stop_sequence.sort(key=lambda x: x[0])
            
            # Get the stop IDs in order
            ordered_stop_ids = [stop_id for _, stop_id in stop_sequence]
            
            # Initialize direction if it doesn't exist
            if direction_id not in routes[route_id].directions:
                routes[route_id].directions[direction_id] = {
                    'trip_id': trip_id,
                    'stop_sequence': []
                }
            
            # Update the route's direction with this stop sequence
            # Only update if this is a longer sequence than what we have
            current_sequence = routes[route_id].directions[direction_id]['stop_sequence']
            if len(ordered_stop_ids) > len(current_sequence):
                routes[route_id].directions[direction_id]['stop_sequence'] = ordered_stop_ids
                routes[route_id].directions[direction_id]['trip_id'] = trip_id
            
            # Update each stop with the route and direction information
            for stop_id in ordered_stop_ids:
                if stop_id in stops:
                    stops[stop_id].routes[route_id].add(direction_id)
        
        logger.info("Successfully processed stop times and updated routes")
    
    except FileNotFoundError:
        logger.error(f"stop_times.txt not found in {gtfs_dir}")
    except Exception as e:
        logger.error(f"Error processing stop times: {e}")

def generate_route_markdown(routes: Dict[str, Route], route_type: str, output_dir: str) -> None:
    """Generate markdown file with route information for a specific route type."""
    logger.info(f"Generating markdown for route type: {route_type}")
    route_type_name = ROUTE_TYPES.get(route_type, f"type_{route_type}")
    output_file = os.path.join(output_dir, f"{route_type_name}routes.md")
    
    # Debug: Log all routes and their types
    for route_id, route in routes.items():
        logger.debug(f"Route ID: {route_id}, Type: {route.route_type}, Name: {route.route_short_name}")
    
    # Filter routes by type and log the results
    filtered_routes = [r for r in routes.values() if r.route_type == route_type]
    logger.info(f"Found {len(filtered_routes)} routes of type {route_type} ({route_type_name})")
    
    for route in filtered_routes:
        logger.info(f"Processing route: {route.route_short_name} ({route.route_id}), Directions: {len(route.directions)}")
        for dir_id, direction in route.directions.items():
            logger.debug(f"  Direction {dir_id}: {len(direction.get('stop_sequence', []))} stops")
    
    # Filter routes by type and ensure they have directions
    filtered_routes = [r for r in routes.values() 
                      if r.route_type == route_type and r.directions]
    
    # Sort routes by short name
    try:
        sorted_routes = sorted(filtered_routes, key=lambda x: (
            # Try to sort numerically if possible, otherwise sort as string
            int(x.route_short_name) if x.route_short_name.isdigit() else float('inf'),
            x.route_short_name
        ))
    except Exception as e:
        logger.error(f"Error sorting routes: {e}")
        logger.error(f"Problematic route data: {[(r.route_short_name, r.route_id) for r in filtered_routes]}")
        sorted_routes = filtered_routes  # Use unsorted if sorting fails
    
    # Map route type to display name
    type_display = {
        '0': 'Tram (Straßenbahn)',
        '1': 'U-Bahn (Metro)',
        '3': 'Bus',
    }.get(route_type, f'Type {route_type}')
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f"# Vienna {type_display} Routes\n\n")
        f.write(f"*Generated from official Wiener Linien GTFS data*  *Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n")
        
        if not sorted_routes:
            f.write("*No route information available for this transport type.*\n")
            return
        
        for route in sorted_routes:
            f.write(f"## {route.route_short_name} - {route.route_long_name}\n")
            f.write(f"- **Line**: {route.route_short_name}\n")
            f.write(f"- **Type**: {type_display}\n")
            f.write(f"- **Route ID**: {route.route_id}\n")
            
            if route.route_color:
                f.write(f"- **Color**: #{route.route_color}\n")
            
            # Process each direction
            for direction_id, direction_info in route.directions.items():
                stop_sequence = direction_info.get('stop_sequence', [])
                f.write(f"\n### Direction {direction_id}")
                if 'trip_headsign' in direction_info:
                    f.write(f" - {direction_info['trip_headsign']}")
                f.write("\n")
                
                f.write(f"- **Number of stops**: {len(stop_sequence)}\n")
                
                # Show first and last few stops
                if stop_sequence:
                    first_stop = stop_sequence[0]
                    last_stop = stop_sequence[-1] if len(stop_sequence) > 1 else None
                    
                    f.write(f"- **From**: {first_stop}  \n")
                    if last_stop and last_stop != first_stop:
                        f.write(f"- **To**: {last_stop}  \n")
            
            f.write("\n---\n\n")
    
    logger.info(f"Generated tram routes markdown at {output_file}")

def generate_station_markdown(stops: Dict[str, Stop], route_type: str, output_dir: str) -> None:
    """Generate markdown file with station information for a specific route type."""
    route_type_name = ROUTE_TYPES.get(route_type, f"type_{route_type}")
    output_file = os.path.join(output_dir, f"{route_type_name}stations.md")
    
    # Filter stops that have routes of the specified type
    filtered_stops = []
    for stop in stops.values():
        # Check if this stop serves any routes of the specified type
        if any(route_id.split('-')[0] == route_type for route_id in stop.routes.keys()):
            filtered_stops.append(stop)
    
    # Sort stops by name
    sorted_stops = sorted(filtered_stops, key=lambda x: x.stop_name)
    
    # Map route type to display name
    type_display = {
        '0': 'Tram (Straßenbahn)',
        '1': 'U-Bahn (Metro)',
        '3': 'Bus',
    }.get(route_type, f'Type {route_type}')
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f"# Vienna {type_display} Stations\n\n")
        f.write(f"*Generated from official Wiener Linien GTFS data*  *Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n")
        f.write(f"Total stations: {len(sorted_stops)}\n\n")
        
        if not sorted_stops:
            f.write("*No station information available for this transport type.*\n")
            return
        
        for stop in sorted_stops:
            f.write(f"## {stop.stop_name}\n")
            f.write(f"- **Stop ID**: {stop.stop_id}  \n")
            f.write(f"- **Coordinates**: {stop.lat}, {stop.lon}  \n")
            
            # List routes that serve this stop
            if stop.routes:
                f.write("- **Served by routes**: ")
                route_list = []
                for route_id, directions in stop.routes.items():
                    route_info = f"{route_id} (Directions: {', '.join(map(str, sorted(directions)))})"
                    route_list.append(route_info)
                f.write(", ".join(route_list) + "\n")
            
            f.write("\n---\n\n")

def main():
    """Main function to process GTFS data and generate route and station information."""
    start_time = datetime.now()
    logger.info(f"Starting GTFS data analysis at {start_time}")
    
    # Create output directory if it doesn't exist
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Set up file handler for logging
    file_handler = logging.FileHandler('gtfs_analysis.log', mode='w', encoding='utf-8')
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    logger.addHandler(file_handler)
    
    # Load GTFS data
    logger.info("Loading GTFS data...")
    stops = load_stops(GTFS_DIR)
    routes = load_routes(GTFS_DIR)
    
    if not stops or not routes:
        logger.error("Failed to load required GTFS data")
        return
    
    # Load trips and associate them with routes
    logger.info("Loading and processing trips...")
    trips = load_trips(GTFS_DIR, routes)
    
    if not trips:
        logger.error("Failed to load trip data")
        return
    
    # Process stop times to build stop sequences
    logger.info("Processing stop times...")
    process_stop_times(GTFS_DIR, stops, routes, trips)
    
    # Generate output files for different route types
    route_types = {
        '0': 'tram',
        '1': 'u_bahn',
        '3': 'bus'
    }
    
    for route_type, type_name in route_types.items():
        logger.info(f"Generating {type_name} route information...")
        generate_route_markdown(routes, route_type, OUTPUT_DIR)
        
        logger.info(f"Generating {type_name} station information...")
        generate_station_markdown(stops, route_type, OUTPUT_DIR)
    
    logger.info("GTFS data analysis complete")

if __name__ == "__main__":
    main()
