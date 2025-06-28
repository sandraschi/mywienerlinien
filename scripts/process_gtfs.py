"""
Process GTFS data and generate markdown files for Wiener Linien routes and stations.
"""

import os
import sys
import csv
import zipfile
import urllib.request
import logging
from collections import defaultdict
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Set, Optional, Any
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError as FutureTimeoutError

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class TimeoutException(Exception):
    """Custom exception for timeouts."""
    pass

def timeout_handler(signum, frame):
    """Handle timeouts."""
    raise TimeoutException("Operation timed out")

class GTFSProcessor:
    """Process GTFS data and generate markdown files."""
    
    def __init__(self, data_dir: Path, gtfs_dir: Path):
        """Initialize with directories."""
        self.data_dir = data_dir
        self.gtfs_dir = gtfs_dir
        self.gtfs_url = "https://www.wienerlinien.at/ogd_realtime/doku/ogd/gtfs/gtfs.zip"
        
        # Ensure directories exist
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.gtfs_dir.mkdir(parents=True, exist_ok=True)
        
        # Route type definitions
        self.route_types = {
            0: {'name': 'tram', 'title': 'Tram (Straßenbahn)', 'filename': 'tramroutes.md', 'station_file': 'tramstations.md'},
            1: {'name': 'metro', 'title': 'U-Bahn (Metro)', 'filename': 'tuberoutes.md', 'station_file': 'tramstations.md'},
            3: {'name': 'bus', 'title': 'Bus', 'filename': 'busroutes.md', 'station_file': 'busstations.md'},
            7: {'name': 'funicular', 'title': 'Funicular', 'filename': 'funicularroutes.md', 'station_file': 'funicularstations.md'}
        }
    
    def download_file(self, url: str, output_path: Path, timeout: int = 60) -> bool:
        """
        Download a file with timeout and progress tracking.
        
        Args:
            url: The URL to download from
            output_path: Path to save the downloaded file
            timeout: Timeout in seconds (default: 60)
            
        Returns:
            bool: True if download was successful, False otherwise
        """
        import urllib.request
        import socket
        from tqdm import tqdm
        
        class DownloadProgressBar(tqdm):
            def update_to(self, b=1, bsize=1, tsize=None):
                if tsize is not None:
                    self.total = tsize
                self.update(b * bsize - self.n)
        
        try:
            logger.info(f"Starting download from {url}")
            logger.info(f"Saving to: {output_path}")
            
            # Ensure parent directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Set socket timeout
            socket.setdefaulttimeout(timeout)
            
            # Download with progress bar
            with DownloadProgressBar(unit='B', unit_scale=True, miniters=1, 
                                  desc=output_path.name) as t:
                try:
                    urllib.request.urlretrieve(
                        url, 
                        filename=output_path, 
                        reporthook=t.update_to,
                        data=None
                    )
                except socket.timeout:
                    logger.error(f"Download timed out after {timeout} seconds")
                    if output_path.exists():
                        output_path.unlink()  # Clean up partial download
                    return False
                except Exception as e:
                    logger.error(f"Download error: {e}")
                    if output_path.exists():
                        output_path.unlink()  # Clean up partial download
                    return False
            
            # Verify download
            if output_path.exists() and output_path.stat().st_size > 0:
                logger.info(f"Successfully downloaded {output_path.name} ({output_path.stat().st_size / (1024*1024):.2f} MB)")
                return True
            else:
                logger.error("Downloaded file is empty or missing")
                if output_path.exists():
                    output_path.unlink()
                return False
                
        except Exception as e:
            logger.error(f"Error in download_file: {e}", exc_info=True)
            if output_path.exists():
                output_path.unlink()
            return False
    
    def extract_zip(self, zip_path: Path, extract_to: Path) -> bool:
        """Extract a zip file with error handling."""
        try:
            logger.info(f"Extracting {zip_path} to {extract_to}")
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_to)
            return True
        except Exception as e:
            logger.error(f"[EXTRACT] Error extracting {zip_path}: {e}")
            return False
    
    def load_gtfs_data(self, gtfs_dir: Path) -> Dict[str, Any]:
        """
        Load GTFS data from extracted files in the extracted/ subdirectory.
        Optimized to handle large files like stop_times.txt efficiently.
        """
        logger.info(f"[LOAD] Starting to load GTFS data from: {gtfs_dir}")
        extracted_dir = gtfs_dir / "extracted"
        logger.info(f"[LOAD] Extracted directory: {extracted_dir}")
        logger.info(f"[LOAD] Extracted directory exists: {extracted_dir.exists()}")
        
        if not extracted_dir.exists():
            logger.error(f"[LOAD] Extracted directory does not exist: {extracted_dir}")
            return {}
            
        data = {}
        file_handles = []  # Track open file handles for cleanup
        
        # Define file loading order to ensure dependencies are loaded first
        files_to_load = [
            'routes.txt',
            'trips.txt',
            'stops.txt',
            'stop_times.txt',
            'calendar.txt',
            'calendar_dates.txt',
            'shapes.txt'
        ]
        
        logger.info(f"[LOAD] Will attempt to load files: {files_to_load}")
        
        # Define required files and their processing methods
        file_configs = {
            'routes.txt': {'chunked': False, 'required': True},
            'trips.txt': {'chunked': False, 'required': True},
            'stops.txt': {'chunked': False, 'required': True},
            'stop_times.txt': {'chunked': True, 'chunk_size': 100000, 'required': True},
            'calendar.txt': {'chunked': False, 'required': False},
            'calendar_dates.txt': {'chunked': False, 'required': False},
            'shapes.txt': {'chunked': False, 'required': False},
            'agency.txt': {'chunked': False, 'required': False}
        }
        
        extracted_dir = gtfs_dir / 'extracted'
        
        def load_file(file_path, chunked=False, chunk_size=None, file_handle=None):
            """
            Helper to load a file, optionally in chunks.
            
            Args:
                file_path: Path to the file to load
                chunked: Whether to read the file in chunks
                chunk_size: Size of chunks for chunked reading
                file_handle: Optional file handle to use (for chunked reading)
                
            Returns:
                For non-chunked: List of records
                For chunked: Dict with reader and file handle
            """
            if not file_path.exists() or not file_path.is_file():
                return None
                
            try:
                if file_handle is None:
                    # Open new file handle if not provided
                    file_handle = open(file_path, 'r', encoding='utf-8-sig')
                    file_handles.append(file_handle)  # Track for cleanup
                
                reader = csv.DictReader(file_handle)
                
                if not chunked:
                    # For non-chunked reading, read all records and close the file
                    try:
                        records = list(reader)
                        logger.info(f"Loaded {len(records)} records from {file_path}")
                        if records:
                            logger.debug(f"Sample record from {file_path.name}: {records[0]}")
                        return records
                    finally:
                        if file_handle not in file_handles:  # Don't close if tracked for chunked reading
                            file_handle.close()
                else:
                    # For chunked reading, return the reader and keep the file open
                    first_row = next(reader, None)
                    if first_row:
                        logger.info(f"Initialized chunked reading for {file_path}")
                        logger.debug(f"Sample record from {file_path.name}: {first_row}")
                        
                        # Reset file position to beginning
                        file_handle.seek(0)
                        # Skip header
                        next(reader)
                        
                        # Return a dict with the reader and chunk size
                        return {
                            'reader': reader,
                            'chunk_size': chunk_size,
                            'file_handle': file_handle  # Keep reference to keep file open
                        }
                    return None
                    
            except Exception as e:
                logger.error(f"Error loading {file_path}: {e}", exc_info=True)
                if file_handle and file_handle not in file_handles:
                    file_handle.close()
                return None
        
        # Check if extracted directory exists
        if not extracted_dir.exists() or not extracted_dir.is_dir():
            logger.error(f"GTFS extracted directory not found: {extracted_dir}")
            logger.info(f"Available directories: {[d.name for d in gtfs_dir.iterdir() if d.is_dir()]}")
            return {}
        
        # Check for required files
        missing_required = []
        for file, config in file_configs.items():
            if config['required']:
                file_path = extracted_dir / file
                if not file_path.exists() or not file_path.is_file():
                    missing_required.append(file)
                    logger.error(f"Missing required GTFS file: {file_path}")
        
        if missing_required:
            logger.error(f"Missing {len(missing_required)} required GTFS files: {', '.join(missing_required)}")
            available_files = [f.name for f in extracted_dir.glob('*') if f.is_file()]
            logger.info(f"Available files in {extracted_dir}: {', '.join(available_files) if available_files else 'None'}")
            return {}
        
        # Load each file
        for file_name in files_to_load:
            if file_name not in file_configs:
                logger.warning(f"Skipping unknown file: {file_name}")
                continue
                
            config = file_configs[file_name]
            file_path = extracted_dir / file_name
            
            if not file_path.exists():
                if config['required']:
                    logger.error(f"Required file not found: {file_path}")
                    return {}
                logger.warning(f"Optional file not found, skipping: {file_path}")
                continue
                
            logger.info(f"Loading {file_name}...")
            file_data = load_file(
                file_path,
                chunked=config.get('chunked', False),
                chunk_size=config.get('chunk_size')
            )
            
            if file_data is not None or not config['required']:
                data[file_name] = file_data
            else:
                logger.error(f"Failed to load required file: {file_name}")
        
        # Verify required fields in each file
        required_fields = {
            'routes.txt': ['route_id', 'route_short_name', 'route_type'],
            'trips.txt': ['trip_id', 'route_id', 'direction_id'],
            'stops.txt': ['stop_id', 'stop_name', 'stop_lat', 'stop_lon'],
            'stop_times.txt': ['trip_id', 'stop_id', 'stop_sequence']
        }
        
        for file, fields in required_fields.items():
            if file not in data:
                continue
                
            if isinstance(data[file], dict) and 'reader' in data[file]:
                # For chunked files, we can't check all rows, so just log a warning
                logger.warning(f"Skipping field validation for chunked file: {file}")
                continue
                
            if not data[file]:
                logger.warning(f"No data in {file} to validate fields")
                continue
                
            missing_fields = [f for f in fields if f not in data[file][0]]
            if missing_fields:
                logger.error(f"Missing required fields in {file}: {', '.join(missing_fields)}")
                logger.info(f"Available fields in {file}: {', '.join(data[file][0].keys())}")
                return {}
        logger.info("GTFS data loaded successfully")
        return data
    
    def process_gtfs_data(self, data: Dict) -> Dict:
        """Process GTFS data into routes, stops, and station variants."""
        logger.info("Starting to process GTFS data...")
        routes = {}
        stops = {}
        trips = {}
        stop_times = []
        station_variants = defaultdict(list)  # Maps stop_name to list of stop variants
        
        # Process routes
        logger.info("Processing routes...")
        routes_data = data.get('routes.txt', [])
        for route in routes_data:
            route_id = route['route_id']
            routes[route_id] = {
                'route_id': route_id,
                'route_short_name': route['route_short_name'],
                'route_long_name': route.get('route_long_name', ''),
                'route_type': int(route['route_type']),
                'route_color': f"#{route.get('route_color', '000000').lstrip('#')}",
                'directions': defaultdict(dict)  # direction_id -> {trip_id, stops}
            }
        
        logger.info(f"Processed {len(routes)} routes")
        
        # Process stops
        logger.info("Processing stops...")
        stops_data = data.get('stops.txt', [])
        for stop in stops_data:
            stop_id = stop['stop_id']
            stop_name = stop['stop_name'].strip()
            
            stops[stop_id] = {
                'stop_id': stop_id,
                'stop_name': stop_name,
                'lat': float(stop.get('stop_lat', 0)),
                'lon': float(stop.get('stop_lon', 0)),
                'routes': defaultdict(set)  # route_id -> set of direction_ids
            }
            
            # Initialize station variant tracking
            station_variants[stop_name].append(stop_id)
        
        logger.info(f"Processed {len(stops)} stops")
        
        # Process trips
        logger.info("Processing trips...")
        trips_data = data.get('trips.txt', [])
        route_trips = defaultdict(list)  # route_id -> list of trips
        
        for trip in trips_data:
            trip_id = trip['trip_id']
            route_id = trip['route_id']
            direction_id = trip.get('direction_id', '0')
            
            if route_id not in routes:
                logger.warning(f"Trip {trip_id} references unknown route {route_id}")
                continue
                
            trips[trip_id] = {
                'trip_id': trip_id,
                'route_id': route_id,
                'direction_id': direction_id,
                'service_id': trip.get('service_id', ''),
                'trip_headsign': trip.get('trip_headsign', '')
            }
            
            route_trips[route_id].append(trip_id)
        
        logger.info(f"Processed {len(trips)} trips")
        
        # Process stop times (chunked if needed)
        logger.info("Processing stop times...")
        stop_times_data = data.get('stop_times.txt', [])
        
        if isinstance(stop_times_data, dict) and 'reader' in stop_times_data:
            # Process stop_times in chunks
            reader = stop_times_data['reader']
            chunk_size = stop_times_data.get('chunk_size', 100000)
            chunk = []
            processed_count = 0
            
            for row in reader:
                chunk.append(row)
                if len(chunk) >= chunk_size:
                    self._process_stop_times_chunk(chunk, trips, stops, routes, stop_times)
                    processed_count += len(chunk)
                    logger.info(f"Processed {processed_count} stop times...")
                    chunk = []
            
            # Process remaining rows in the last chunk
            if chunk:
                self._process_stop_times_chunk(chunk, trips, stops, routes, stop_times)
                processed_count += len(chunk)
            
            logger.info(f"Processed {processed_count} stop times in total")
        else:
            # Process all stop times at once (for small files)
            self._process_stop_times_chunk(stop_times_data, trips, stops, routes, stop_times)
            logger.info(f"Processed {len(stop_times_data)} stop times")
        
        # Build route directions based on stop sequences
        self._build_route_directions(routes, trips, stop_times, stops)
        
        return {
            'routes': routes,
            'stops': stops,
            'trips': trips,
            'stop_times': stop_times,
            'station_variants': station_variants
        }
    
    def _process_stop_times_chunk(self, chunk, trips, stops, routes, stop_times_list):
        """Process a chunk of stop times and update the data structures."""
        for stop_time in chunk:
            trip_id = stop_time['trip_id']
            stop_id = stop_time['stop_id']
            
            # Skip if trip or stop is not found
            if trip_id not in trips or stop_id not in stops:
                continue
                
            # Add stop time to the list
            stop_times_list.append({
                'trip_id': trip_id,
                'stop_id': stop_id,
                'stop_sequence': int(stop_time['stop_sequence']),
                'arrival_time': stop_time.get('arrival_time', ''),
                'departure_time': stop_time.get('departure_time', '')
            })
            
            # Update stop's route information
            trip = trips[trip_id]
            route_id = trip['route_id']
            direction_id = trip['direction_id']
            stops[stop_id]['routes'][route_id].add(direction_id)
    
    def _build_route_directions(self, routes, trips, stop_times, stops, station_variants=None):
        """Build route directions based on stop sequences.
        
        Args:
            routes: Dictionary of routes
            trips: Dictionary of trips
            stop_times: List of stop times
            stops: Dictionary of stops
            station_variants: Dictionary mapping station names to variant stop IDs (optional)
        """
        if station_variants is None:
            station_variants = {}
        logger.info("Building route directions...")
        
        # Group stop times by trip
        stop_times_by_trip = defaultdict(list)
        for stop_time in stop_times:
            stop_times_by_trip[stop_time['trip_id']].append(stop_time)
        
        # Sort stop times by sequence
        for trip_id, trip_stop_times in stop_times_by_trip.items():
            trip_stop_times.sort(key=lambda x: int(x['stop_sequence']))
        
        # Process each trip
        for trip_id, trip in trips.items():
            if trip_id not in stop_times_by_trip:
                continue
                
            route_id = trip['route_id']
            direction_id = trip['direction_id']
            
            if route_id not in routes:
                continue
                
            # Get the stop sequence for this trip
            trip_stop_times = stop_times_by_trip[trip_id]
            
            # Initialize direction info if not exists
            if direction_id not in routes[route_id]['directions']:
                routes[route_id]['directions'][direction_id] = {
                    'stops': [],
                    'trip_ids': set()
                }
                
            direction_info = routes[route_id]['directions'][direction_id]
            
            # Add this trip to the direction
            direction_info['trip_ids'].add(trip_id)
            
            # Process each stop time for this trip
            for stop_time in trip_stop_times:
                stop_id = stop_time.get('stop_id')
                if not stop_id or stop_id not in stops:
                    continue
                
                # Add stop to direction if not already present
                if stop_id not in direction_info['stops']:
                    direction_info['stops'].append(stop_id)
                
                # Initialize routes in stop if needed
                if 'routes' not in stops[stop_id]:
                    stops[stop_id]['routes'] = {}
                
                # Add this route and direction to the stop's routes
                if route_id not in stops[stop_id]['routes']:
                    stops[stop_id]['routes'][route_id] = set()
                stops[stop_id]['routes'][route_id].add(direction_id)
        
        # No need to sort stops here since we maintain the order when adding them
        # based on the stop_sequence from the GTFS data
        
        # Add station variant information to stops if provided
        if station_variants:
            for stop_name, variant_ids in station_variants.items():
                if len(variant_ids) > 1:
                    for stop_id in variant_ids:
                        stops[stop_id]['is_variant'] = True
                        stops[stop_id]['variants'] = variant_ids
        
        return {
            'routes': routes,
            'stops': stops,
            'station_variants': station_variants
        }
    
    def generate_markdown(self, data: Dict, output_dir: Path):
        """Generate markdown files from processed GTFS data."""
        logger.info(f"[DEBUG] Starting markdown generation in directory: {output_dir.absolute()}")
        
        # Ensure output directory exists
        output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"[DEBUG] Output directory exists: {output_dir.exists()}")
        logger.info(f"[DEBUG] Output directory is writable: {os.access(str(output_dir), os.W_OK)}")
        
        routes = data.get('routes', {})
        stops = data.get('stops', {})
        station_variants = data.get('station_variants', {})
        
        logger.info(f"[DEBUG] Processing {len(routes)} routes")
        logger.info(f"[DEBUG] Processing {len(stops)} stops")
        logger.info(f"[DEBUG] Processing {len(station_variants)} station variants")
        
        # Log the first few routes and stops for debugging
        for i, (route_id, route) in enumerate(list(routes.items())[:3]):
            logger.info(f"[DEBUG] Route {i+1}: {route_id} - {route.get('route_short_name')} ({route.get('route_long_name')})")
            
        for i, (stop_id, stop) in enumerate(list(stops.items())[:3]):
            logger.info(f"[DEBUG] Stop {i+1}: {stop_id} - {stop.get('stop_name')}")
            
        logger.info(f"[DEBUG] Route types: {self.route_types}")
        
        # Group routes by type
        routes_by_type = {}
        
        for route_id, route in routes.items():
            route_type_id = route.get('route_type')
            route_type_info = self.route_types.get(route_type_id, {})
            route_type = route_type_info.get('name')
            
            if not route_type:
                logger.warning(f"Unknown route type: {route_type_id} for route {route.get('route_short_name', route_id)}")
                continue
                
            # Special handling for night buses
            route_short_name = str(route.get('route_short_name', ''))
            if route_type == 'bus' and route_short_name.startswith(('N', 'n')):
                route_type = 'nightbus'
                self.route_types[999] = {
                    'name': 'nightbus',
                    'title': 'Night Bus',
                    'filename': 'nightbusroutes.md',
                    'station_file': 'nightbusstations.md'
                }
            
            if route_type not in routes_by_type:
                routes_by_type[route_type] = {}
            routes_by_type[route_type][route_id] = route
        
        # Generate route files for each route type
        for route_type, type_info in self.route_types.items():
            filename = type_info['filename']
            output_file = output_dir / filename
            logger.info(f"Generating route file: {output_file}")
            
            # Skip if no routes of this type
            type_routes = routes_by_type.get(type_info['name'], {})
            route_count = len(type_routes)
            logger.info(f"Found {route_count} routes of type {type_info['name']}")
            
            if route_count == 0:
                logger.warning(f"No routes found for type: {type_info['name']}")
                continue
                
            # Use the routes for this specific type
            routes = type_routes
            
            if route_count == 0:
                logger.warning(f"No routes found for type: {type_info['name']}")
                continue
            
            routes = [r for r in data['routes'].values() if r['route_type'] == route_type]
            logger.info(f"Found {len(routes)} routes for type {type_info['name']}")
            
            if not routes:
                logger.warning(f"No routes found for {type_info['name']}")
                continue
                
            logger.info(f"Will write to route file: {output_file}")
            
            # Sort routes by short name
            sorted_routes = sorted(routes.values(), key=lambda x: x.get('route_short_name', ''))
            
            # Generate route file
            try:
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(f"# Vienna {type_info['title']} Routes\n\n")
                    f.write("*Generated from official Wiener Linien GTFS data*  "
                          f"*Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n")
                    
                    for route in sorted_routes:
                        route_name = route.get('route_short_name', 'Unknown')
                        route_long_name = route.get('route_long_name', '')
                        route_color = route.get('route_color', 'N/A')
                        
                        f.write(f"## {route_name} - {route_long_name}\n")
                        f.write(f"- **Line**: {route_name}\n")
                        f.write(f"- **Type**: {type_info['title']}\n")
                        f.write(f"- **Color**: {route_color}\n")
                        
                        # Count stops across all directions
                        total_stops = sum(len(direction['stops']) for direction in route.get('directions', {}).values())
                        f.write(f"- **Stops**: {total_stops}\n\n")
                        
                        # List directions
                        for direction_id, direction in sorted(route.get('directions', {}).items()):
                            dir_name = "Inbound" if direction_id == '0' else "Outbound"
                            trip_id = next(iter(direction.get('trip_ids', [])), 'N/A')
                            
                            f.write(f"### Direction: {dir_name} (Trip ID: {trip_id})\n")
                            f.write(f"- **Stops**: {len(direction.get('stops', []))}\n\n")
                            
                            f.write("#### Stops\n")
                            for i, stop_id in enumerate(direction.get('stops', []), 1):
                                if stop_id not in stops:
                                    continue
                                    
                                stop = stops[stop_id]
                                stop_name = stop.get('stop_name', 'Unknown')
                                variant_note = " (Variant)" if stop.get('is_variant') else ""
                                
                                f.write(f"{i}. **{stop_name}{variant_note}**  \n")
                                f.write(f"   - Coordinates: {stop.get('stop_lat', 'N/A')}, {stop.get('stop_lon', 'N/A')}\n")
                                f.write(f"   - Stop ID: {stop_id}\n\n")
                
                logger.info(f"Generated {output_file}")
                
            except Exception as e:
                logger.error(f"Error generating {output_file}: {e}", exc_info=True)
        
        # Generate station files
        logger.info("Generating station files...")
        self._generate_station_files(routes, stops, station_variants, output_dir)
        logger.info("Station file generation completed")
    
    def _generate_station_files(self, routes: Dict, stops: Dict, station_variants: Dict, output_dir: Path):
        """Generate station markdown files for each route type."""
        logger.info("Generating station files...")
        
        # Group routes by type
        routes_by_type = defaultdict(list)
        for route in routes.values():
            routes_by_type[route['route_type']].append(route)
            
        logger.info(f"Routes grouped into {len(routes_by_type)} route types")
        
        # Map route type to display names
        type_display_names = {
            'tram': 'Tram (Straßenbahn)',
            'metro': 'U-Bahn (Metro)',
            'bus': 'Bus',
            'nightbus': 'Night Bus',
            'funicular': 'Funicular'
        }
        
        # Group stops by route type
        stops_by_type = defaultdict(list)
        
        for stop_id, stop in stops.items():
            # Find all route types this stop is associated with
            for route_id in stop['routes'].keys():
                if route_id in routes:
                    route_type = self.route_types.get(routes[route_id]['route_type'], {}).get('name')
                    if route_type:
                        stops_by_type[route_type].append(stop_id)
        
        # Generate station files for each route type
        logger.info(f"Processing stops by type: {list(stops_by_type.keys())}")
        
        try:
            for route_type, stop_ids in stops_by_type.items():
                logger.info(f"Processing route type: {route_type} with {len(stop_ids)} stops")
                
                type_info = next((v for k, v in self.route_types.items() if v.get('name') == route_type), None)
                if not type_info or 'station_file' not in type_info:
                    logger.warning(f"No type info or station_file for route type: {route_type}")
                    continue
                    
                logger.info(f"Found type info for {route_type}: {type_info}")
                    
                station_file = output_dir / type_info['station_file']
                # Get unique station names and their variants
                station_names = set(stops[stop_id]['stop_name'] for stop_id in stop_ids)
                
                with open(station_file, 'w', encoding='utf-8') as f:
                    # Use the display name for the station type
                    display_name = type_display_names.get(route_type, type_info['title'])
                    f.write(f"# Vienna {display_name} Stations\n\n")
                    f.write("*Generated from official Wiener Linien GTFS data*  "
                          f"*Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n")
                    
                    f.write("## Station List\n\n")
                    
                    # Sort stops by name and write to file
                    for i, stop_id in enumerate(sorted(stops.keys()), 1):
                        stop = stops[stop_id]
                        stop_name = stop.get('stop_name', 'Unknown')
                        variant_note = " (Variant)" if stop.get('is_variant') else ""
                        
                        f.write(f"{i}. **{stop_name}{variant_note}**  \n")
                        f.write(f"   - Coordinates: {stop.get('stop_lat', 'N/A')}, {stop.get('stop_lon', 'N/A')}\n")
                        f.write(f"   - Stop ID: {stop_id}\n\n")
                
                logger.info(f"Generated {station_file}")
            
            # Generate station files after all route types are processed
            logger.info("Generating station files...")
            self._generate_station_files(routes, stops, station_variants, output_dir)
            logger.info("Station file generation completed")
                
        except Exception as e:
            logger.error(f"Error generating station files: {e}", exc_info=True)

    def _generate_station_files(self, routes: Dict, stops: Dict, station_variants: Dict, output_dir: Path):
        """Generate station markdown files for each route type."""
        logger.info("Generating station files...")
    
        # Group stops by route type
        stops_by_type = defaultdict(set)
        
        # Track which routes serve each stop
        for route_id, route in routes.items():
            route_type = route.get('route_type')
            if route_type is None:
                continue
                
            for direction in route.get('directions', {}).values():
                for stop_id in direction.get('stops', []):
                    if stop_id in stops:
                        stops_by_type[route_type].add(stop_id)
        
        # Generate a station file for each route type
        for route_type, type_info in self.route_types.items():
            route_type_name = type_info.get('name')
            if not route_type_name:
                continue
                
            # Get stops for this route type
            type_stop_ids = stops_by_type.get(route_type, set())
            if not type_stop_ids:
                logger.info(f"No stops found for route type: {route_type_name}")
                continue
                
            # Get station file path
            station_file = output_dir / type_info['station_file']
            logger.info(f"Generating station file for {route_type_name}: {station_file}")
            
            try:
                with open(station_file, 'w', encoding='utf-8') as f:
                    # Write header
                    f.write(f"# Vienna {type_info['title']} Stations\n\n")
                    f.write("*Generated from official Wiener Linien GTFS data*  "
                          f"*Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n")
                    
                    # Group stops by name (handling variants)
                    stops_by_name = defaultdict(list)
                    for stop_id in type_stop_ids:
                        stop = stops.get(stop_id, {})
                        stop_name = stop.get('stop_name', 'Unknown')
                        stops_by_name[stop_name].append(stop)
                    
                    # Sort stops by name
                    for stop_name in sorted(stops_by_name.keys()):
                        stop_group = stops_by_name[stop_name]
                        f.write(f"## {stop_name}\n\n")
                        
                        for stop in stop_group:
                            variant_note = " (Variant)" if stop.get('is_variant') else ""
                            f.write(f"- **Stop ID**: {stop.get('stop_id', 'N/A')}{variant_note}  \n")
                            f.write(f"  - Coordinates: {stop.get('stop_lat', 'N/A')}, {stop.get('stop_lon', 'N/A')}  \n")
                            
                            # List routes that serve this stop
                            route_list = []
                            for route_id, directions in stop.get('routes', {}).items():
                                if route_id in routes:
                                    route_name = routes[route_id].get('route_short_name', route_id)
                                    dirs = ['In' if d == '0' else 'Out' for d in directions]
                                    route_list.append(f"{route_name} ({', '.join(sorted(dirs))})")
                            
                            if route_list:
                                f.write(f"  - **Routes**: {', '.join(sorted(route_list))}  \n")
                            
                            f.write("\n")
                
                logger.info(f"Generated {station_file}")
                
            except Exception as e:
                logger.error(f"Error generating {station_file}: {e}", exc_info=True)


def main():
    try:
        # Configure logging to file
        log_file = Path(__file__).parent / 'gtfs_processor.log'
        file_handler = logging.FileHandler(log_file, mode='w')
        file_handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        logger.info("Starting GTFS data processing...")
        logger.info(f"Python version: {sys.version}")
        logger.info(f"Current working directory: {os.getcwd()}")
        
        # Set up directories
        base_dir = Path(__file__).parent.parent
        data_dir = base_dir / "frontend" / "data"
        gtfs_dir = base_dir / "scripts" / "gtfs_data"
        
        logger.info(f"Base directory: {base_dir}")
        logger.info(f"Data directory: {data_dir}")
        logger.info(f"GTFS directory: {gtfs_dir}")
        
        # Ensure directories exist
        data_dir.mkdir(parents=True, exist_ok=True)
        gtfs_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize processor
        logger.info("Initializing GTFSProcessor...")
        processor = GTFSProcessor(data_dir, gtfs_dir)
        
        # Set the path to the extracted GTFS files
        extracted_dir = gtfs_dir / "extracted"
        logger.info(f"Using GTFS data from: {extracted_dir}")
        
        # Check if extracted files exist
        required_files = ["routes.txt", "trips.txt", "stops.txt", "stop_times.txt"]
        missing_files = [f for f in required_files if not (extracted_dir / f).exists()]
        
        if missing_files:
            logger.error(f"Missing required GTFS files: {', '.join(missing_files)}")
            logger.error(f"Please ensure the GTFS files are extracted to: {extracted_dir}")
            return 1
        
        # Load GTFS data
        logger.info("Loading GTFS data...")
        gtfs_data = processor.load_gtfs_data(gtfs_dir)
        if not gtfs_data:
            logger.error("Failed to load GTFS data")
            return 1
            
        logger.info(f"Loaded GTFS data with {len(gtfs_data.get('routes.txt', []))} routes")
        
        # Process GTFS data
        logger.info("Processing GTFS data...")
        try:
            processed_data = processor.process_gtfs_data(gtfs_data)
            if not processed_data:
                logger.error("Failed to process GTFS data")
                return 1
            
            logger.info(f"Processed data: {len(processed_data.get('routes', {}))} routes, "
                       f"{len(processed_data.get('stops', {}))} stops")
            
            # Generate markdown files
            logger.info("Generating markdown files...")
            processor.generate_markdown(processed_data, data_dir)
            
            # List generated files
            output_files = list(data_dir.glob("*.md"))
            if output_files:
                logger.info(f"Generated {len(output_files)} markdown files: {[f.name for f in output_files]}")
            else:
                logger.warning("No markdown files were generated")
                # Check directory contents
                logger.info(f"Directory contents: {list(data_dir.glob('*'))}")
            
            logger.info("GTFS data processing completed successfully!")
            return 0
            
        except Exception as e:
            logger.error(f"Error during processing: {e}", exc_info=True)
            return 1
        
    except Exception as e:
        logger.error(f"Error in main: {e}", exc_info=True)
        return 1
    finally:
        logger.info("Script execution finished")

def test_gtfs_processing():
    """Test GTFS processing with a small subset of data."""
    logger.info("Starting GTFS processing test...")
    
    # Set up test data
    test_data = {
        'routes.txt': [
            {
                'route_id': '1',
                'route_short_name': 'U1',
                'route_long_name': 'U-Bahn Line 1',
                'route_type': '1',
                'route_color': 'FF0000'
            }
        ],
        'stops.txt': [
            {'stop_id': '1', 'stop_name': 'Station A', 'stop_lat': '48.1', 'stop_lon': '16.1'},
            {'stop_id': '2', 'stop_name': 'Station B', 'stop_lat': '48.2', 'stop_lon': '16.2'}
        ],
        'trips.txt': [
            {'trip_id': 'T1', 'route_id': '1', 'direction_id': '0'},
            {'trip_id': 'T2', 'route_id': '1', 'direction_id': '1'}
        ],
        'stop_times.txt': [
            {'trip_id': 'T1', 'stop_id': '1', 'stop_sequence': '1', 'arrival_time': '08:00:00', 'departure_time': '08:00:00'},
            {'trip_id': 'T1', 'stop_id': '2', 'stop_sequence': '2', 'arrival_time': '08:05:00', 'departure_time': '08:05:00'},
            {'trip_id': 'T2', 'stop_id': '2', 'stop_sequence': '1', 'arrival_time': '09:00:00', 'departure_time': '09:00:00'},
            {'trip_id': 'T2', 'stop_id': '1', 'stop_sequence': '2', 'arrival_time': '09:05:00', 'departure_time': '09:05:00'}
        ]
    }
    
    # Create a test processor
    processor = GTFSProcessor(Path('test_data'), Path('test_gtfs'))
    
    try:
        # Process the test data
        processed_data = processor.process_gtfs_data(test_data)
        
        # Verify the results
        assert 'routes' in processed_data, "Missing 'routes' in processed data"
        assert 'stops' in processed_data, "Missing 'stops' in processed data"
        assert 'trips' in processed_data, "Missing 'trips' in processed data"
        assert 'stop_times' in processed_data, "Missing 'stop_times' in processed data"
        
        # Check routes
        routes = processed_data['routes']
        assert len(routes) == 1, f"Expected 1 route, got {len(routes)}"
        assert '1' in routes, "Route '1' not found in processed data"
        
        # Check stops
        stops = processed_data['stops']
        assert len(stops) == 2, f"Expected 2 stops, got {len(stops)}"
        
        # Check trips
        trips = processed_data['trips']
        assert len(trips) == 2, f"Expected 2 trips, got {len(trips)}"
        
        # Check stop times
        stop_times = processed_data['stop_times']
        assert len(stop_times) == 4, f"Expected 4 stop times, got {len(stop_times)}"
        
        # Check route directions
        route = routes['1']
        assert 'directions' in route, "Missing 'directions' in route"
        assert '0' in route['directions'], "Direction '0' not found in route"
        assert '1' in route['directions'], "Direction '1' not found in route"
        
        logger.info("GTFS processing test passed successfully!")
        return True
        
    except AssertionError as e:
        logger.error(f"Test failed: {e}")
        return False
    except Exception as e:
        logger.error(f"Error during test: {e}", exc_info=True)
        return False

if __name__ == "__main__":
    # Run tests first
    if test_gtfs_processing():
        logger.info("All tests passed. Running main processing...")
        sys.exit(main())
    else:
        logger.error("Tests failed. Aborting main processing.")
        sys.exit(1)
