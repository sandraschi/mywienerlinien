"""
Download and process Wiener Linien GTFS data.

This script downloads the latest GTFS data from Wiener Linien and processes it
to generate accurate route and station information.
"""

import os
import sys
import zipfile
import csv
import json
import signal
import time
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError as FutureTimeoutError
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

# Timeout for network operations (seconds)
DOWNLOAD_TIMEOUT = 30
PROCESSING_TIMEOUT = 60

# Configuration
GTFS_URL = "https://www.wienerlinien.at/ogd_realtime/doku/ogd/gtfs/gtfs.zip"
DATA_DIR = Path(__file__).parent.parent / "frontend" / "data"
GTFS_DIR = Path(__file__).parent / "gtfs_data"
GTFS_ZIP = GTFS_DIR / "wienerlinien-gtfs.zip"
GTFS_EXTRACT_DIR = GTFS_DIR  # Use the same directory for extracted files

# Ensure directories exist
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(GTFS_DIR, exist_ok=True)

# How old (in days) the GTFS data can be before we consider it stale
GTFS_MAX_AGE_DAYS = 7

def is_gtfs_fresh(gtfs_zip: Path) -> bool:
    """Check if the GTFS data is still fresh."""
    if not gtfs_zip.exists():
        return False
        
    # Get file age in days
    file_age = (datetime.now() - datetime.fromtimestamp(gtfs_zip.stat().st_mtime)).days
    return file_age < GTFS_MAX_AGE_DAYS

def download_with_timeout(url: str, output_path: Path, timeout: int) -> Tuple[bool, str]:
    """Download helper function that runs in a separate thread with timeout."""
    import urllib.request
    import socket
    
    # Define start_time here so it's in scope for report_progress
    start_time = time.time()
    
    def report_progress(count, block_size, total_size):
        nonlocal start_time  # Ensure we can modify the outer scope variable
        if time.time() - start_time > 0:  # Avoid division by zero
            percent = min(int(count * block_size * 100 / total_size), 100)
            sys.stdout.write(f"\rProgress: {percent}%")
            sys.stdout.flush()
    
    try:
        urllib.request.urlretrieve(
            url, 
            output_path,
            reporthook=report_progress
        )
        return True, "Success"
    except (urllib.error.URLError, socket.timeout, socket.gaierror) as e:
        return False, f"Network error downloading {url}: {str(e)}"
    except Exception as e:
        return False, f"Unexpected error downloading {url}: {str(e)}"

def download_file(url: str, output_path: Path, force: bool = False) -> Tuple[bool, str]:
    """Download a file from a URL to the specified path with timeout."""
    import threading
    
    # Skip download if file exists and we're not forcing
    if output_path.exists() and not force:
        return True, "File already exists"
    
    print(f"Downloading {url}...")
    start_time = time.time()
    
    # Create a shared variable to store the result
    result = None
    
    def download_thread():
        nonlocal result
        result = download_with_timeout(url, output_path, DOWNLOAD_TIMEOUT)
    
    # Start the download in a separate thread
    thread = threading.Thread(target=download_thread)
    thread.start()
    
    # Wait for the thread to complete or timeout
    thread.join(timeout=DOWNLOAD_TIMEOUT + 5)  # Add some buffer time
    
    if thread.is_alive():
        # Thread is still running after timeout
        return False, f"Download timed out after {DOWNLOAD_TIMEOUT} seconds"
    
    if result is None:
        return False, "Download failed - no result returned"
    
    success, message = result
    
    if success:
        print(f"\nDownloaded to {output_path} in {time.time() - start_time:.1f} seconds")
    else:
        print(f"\n{message}")
    
    return success, message

def extract_gtfs(gtfs_zip: Path, output_dir: Path, force: bool = False) -> Tuple[bool, str]:
    """Extract GTFS zip file to the specified directory with progress and timeout."""
    import threading
    
    print(f"Extracting {gtfs_zip} to {output_dir}...")
    start_time = time.time()
    
    # Check if we already have extracted files that are fresh
    required_files = ['routes.txt', 'trips.txt', 'stops.txt', 'stop_times.txt']
    all_files_exist = all((output_dir / f).exists() for f in required_files)
    
    if all_files_exist and not force:
        print("  • Using existing extracted files (use --force to re-extract)")
        return True, "Using existing extracted files"
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Shared variable to store the result
    result = None
    
    def extract_thread():
        nonlocal result
        try:
            with zipfile.ZipFile(gtfs_zip, 'r') as zip_ref:
                # Get list of files to extract
                file_list = zip_ref.namelist()
                total_files = len(file_list)
                
                # Extract files one by one with progress
                for i, file in enumerate(file_list, 1):
                    try:
                        zip_ref.extract(file, output_dir)
                        if i % 10 == 0 or i == total_files:
                            print(f"\r  • Extracted {i}/{total_files} files...", end="")
                    except Exception as e:
                        print(f"\n  • Warning: Failed to extract {file}: {e}")
                        continue
                
                print(f"\n  • Extraction completed in {time.time() - start_time:.1f} seconds")
                result = (True, f"Extracted {total_files} files")
                
        except zipfile.BadZipFile as e:
            result = (False, f"Invalid zip file: {e}")
        except Exception as e:
            result = (False, f"Error extracting {gtfs_zip}: {e}")
    
    # Start the extraction in a separate thread
    thread = threading.Thread(target=extract_thread)
    thread.start()
    
    # Wait for the thread to complete or timeout
    thread.join(timeout=PROCESSING_TIMEOUT)
    
    if thread.is_alive():
        # Thread is still running after timeout
        return False, f"Extraction timed out after {PROCESSING_TIMEOUT} seconds"
    
    if result is None:
        return False, "Extraction failed - no result returned"
    
    success, message = result
    if not success:
        print(f"\n  • {message}")
    
    return success, message

def load_gtfs_data(gtfs_dir: Path) -> dict:
    """Load GTFS data from the extracted directory."""
    gtfs_data = {}
    
    # List of required GTFS files
    required_files = [
        'routes.txt', 'trips.txt', 'stops.txt', 'stop_times.txt'
    ]
    
    for file in required_files:
        file_path = gtfs_dir / file
        if not file_path.exists():
            print(f"Warning: Missing required GTFS file: {file}")
            continue
            
        print(f"Loading {file}...")
        try:
            with open(file_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                data = list(reader)
                gtfs_data[file] = data
                
                # Print debug info for stops.txt
                if file == 'stops.txt' and data:
                    print(f"  • Found {len(data)} stops")
                    print(f"  • First 3 stops: {[s.get('stop_name', 'N/A') for s in data[:3]]}")
                    
        except Exception as e:
            print(f"  • Error reading {file}: {e}")
            gtfs_data[file] = []
    
    return gtfs_data

def process_routes(gtfs_data: dict) -> dict:
    """Process routes from GTFS data."""
    routes = {}
    for route in gtfs_data.get('routes.txt', []):
        route_id = route['route_id']
        routes[route_id] = {
            'route_id': route_id,
            'route_short_name': route['route_short_name'],
            'route_long_name': route['route_long_name'],
            'route_type': int(route['route_type']),
            'route_color': f"#{route.get('route_color', '000000').lstrip('#')}",
            'route_text_color': f"#{route.get('route_text_color', 'FFFFFF').lstrip('#')}",
            'stops': []
        }
    return routes

def process_stops(gtfs_data: dict) -> dict:
    """Process stops data from GTFS."""
    stops = {}
    stops_data = gtfs_data.get('stops.txt', [])
    
    if not stops_data:
        print("  • Warning: No stops data found in GTFS")
        return {}
        
    print(f"  • Processing {len(stops_data)} stops...")
    
    for i, stop in enumerate(stops_data, 1):
        try:
            stop_id = stop.get('stop_id')
            if not stop_id:
                print(f"  • Warning: Missing stop_id in stop record: {stop}")
                continue
                
            stops[stop_id] = {
                'stop_id': stop_id,
                'stop_name': stop.get('stop_name', 'Unnamed Stop'),
                'stop_lat': float(stop.get('stop_lat', 0)),
                'stop_lon': float(stop.get('stop_lon', 0)),
                'zone_id': stop.get('zone_id', ''),
                'location_type': int(stop.get('location_type', 0)),
                'parent_station': stop.get('parent_station', '')
            }
            
            # Print progress for large datasets
            if i % 1000 == 0 or i == len(stops_data):
                print(f"  • Processed {i}/{len(stops_data)} stops")
                
        except Exception as e:
            print(f"  • Error processing stop {i}: {e}")
            continue
            
    print(f"  • Successfully processed {len(stops)} stops")
    return stops

def process_stop_times(gtfs_data: dict, routes: dict, trips: dict, stops: dict, max_entries: int = 100000):
    """Process stop times to build route sequences.
    
    Args:
        gtfs_data: Dictionary containing GTFS data
        routes: Dictionary of routes to populate with stops
        trips: Dictionary of trips (unused in this implementation)
        stops: Dictionary of all stops
        max_entries: Maximum number of entries to process (for testing)
    """
    print("  • Indexing trips by route...")
    # First, index trips by route
    route_trips = {}
    for trip in gtfs_data.get('trips.txt', []):
        route_id = trip['route_id']
        if route_id not in route_trips:
            route_trips[route_id] = set()
        route_trips[route_id].add(trip['trip_id'])
    
    print(f"  • Processing stop times (first {max_entries:,} entries)...")
    processed = 0
    stop_times = gtfs_data.get('stop_times.txt', [])
    total_entries = min(len(stop_times), max_entries)
    
    for i, stop_time in enumerate(stop_times):
        # Progress reporting
        if i % 10000 == 0 and i > 0:
            print(f"    - Processed {i:,}/{total_entries:,} entries...")
            
        if i >= max_entries:
            print(f"    - Reached maximum of {max_entries:,} entries")
            break
            
        trip_id = stop_time['trip_id']
        stop_id = stop_time['stop_id']
        
        # Skip if stop doesn't exist
        if stop_id not in stops:
            continue
            
        # Find which route this stop belongs to
        for route_id, trip_set in route_trips.items():
            if trip_id in trip_set and route_id in routes:
                # Check if this stop is already in the route's stops
                stop_exists = False
                for existing_stop in routes[route_id]['stops']:
                    if existing_stop['stop_id'] == stop_id:
                        stop_exists = True
                        break
                        
                if not stop_exists:
                    routes[route_id]['stops'].append({
                        'stop_id': stop_id,
                        'stop_name': stops[stop_id]['stop_name'],
                        'stop_sequence': int(stop_time['stop_sequence']),
                        'lat': stops[stop_id]['stop_lat'],
                        'lon': stops[stop_id]['stop_lon']
                    })
                    processed += 1
    
    # Sort stops by sequence for each route
    print("  • Sorting stops by sequence...")
    for route_id, route in routes.items():
        route['stops'].sort(key=lambda x: x['stop_sequence'])
        print(f"    - Route {route_id}: {len(route['stops'])} stops")
    
    print(f"  • Processed {processed} stop assignments")

def get_route_type_name(route_type: str) -> str:
    """Get the display name for a route type."""
    route_type_names = {
        'tram': 'Tram',
        'metro': 'Metro',
        'bus': 'Bus',
        'nightbus': 'Night Bus',
        'funicular': 'Funicular'
    }
    return route_type_names.get(route_type, 'Unknown')

def generate_markdown_files(routes: dict, stops: dict, output_dir: Path):
    """Generate markdown files for routes and stations."""
    # Define route types and their metadata
    route_types = {
        0: {'name': 'tram', 'title': 'Tram (Straßenbahn)', 'filename': 'tramroutes.md', 'station_file': 'tramstations.md'},
        1: {'name': 'metro', 'title': 'U-Bahn (Metro)', 'filename': 'tuberoutes.md', 'station_file': 'tramstations.md'},  # Using tramstations for metro
        3: {'name': 'bus', 'title': 'Bus', 'filename': 'busroutes.md', 'station_file': 'busstations.md'},
        7: {'name': 'funicular', 'title': 'Funicular', 'filename': 'funicularroutes.md', 'station_file': 'funicularstations.md'}
    }
    
    # Initialize data structures
    routes_by_type = {}
    station_data = {}
    
    # Process routes and collect station data
    for route in routes.values():
        route_type_info = route_types.get(route['route_type'])
        if not route_type_info:
            continue
            
        route_type = route_type_info['name']
        
        # Special handling for night buses (N-prefixed routes)
        if route_type == 'bus' and route['route_short_name'].startswith(('N', 'n')):
            route_type = 'nightbus'
            route_types[999] = {'name': 'nightbus', 'title': 'Night Bus', 'filename': 'nightbusroutes.md', 'station_file': 'nightbusstations.md'}
        
        # Initialize route type if not exists
        if route_type not in routes_by_type:
            routes_by_type[route_type] = []
            station_data[route_type] = set()
        
        routes_by_type[route_type].append(route)
        
        # Collect unique stations for this route type
        for stop in route['stops']:
            station_data[route_type].add((stop['stop_name'], stop['lat'], stop['lon']))
    
    # Generate files for each route type
    for route_type_id, type_info in route_types.items():
        route_type = type_info['name']
        
        # Skip if no routes of this type
        if route_type not in routes_by_type or not routes_by_type[route_type]:
            continue
        
        # Sort routes by short name
        type_routes = sorted(routes_by_type[route_type], key=lambda x: x['route_short_name'])
        
        # Generate route file
        with open(output_dir / type_info['filename'], 'w', encoding='utf-8') as f:
            f.write(f"# Vienna {type_info['title']} Routes\n\n")
            f.write("*Generated from official Wiener Linien GTFS data*  "
                  f"*Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n")
            
            for route in type_routes:
                f.write(f"## {route['route_short_name']} - {route['route_long_name']}\n")
                f.write(f"- **Line**: {route['route_short_name']}\n")
                f.write(f"- **Type**: {type_info['title']}\n")
                f.write(f"- **Color**: {route['route_color']}\n")
                f.write(f"- **Stops**: {len(route['stops'])}\n\n")
                
                f.write("### Stops\n")
                for i, stop in enumerate(route['stops'], 1):
                    f.write(f"{i}. **{stop['stop_name']}**  \n")
                    f.write(f"   - Coordinates: {stop['lat']:.6f}, {stop['lon']:.6f}\n")
                    f.write(f"   - Stop ID: {stop['stop_id']}\n\n")
                f.write("\n")
        
    # Generate unified stations.md file with all stations
    all_stations = {}
    
    # First, collect all stations with their types
    for route_type, stations in station_data.items():
        route_type_name = get_route_type_name(route_type)
        for station in stations:
            name, lat, lon = station
            if name not in all_stations:
                all_stations[name] = {
                    'lat': lat,
                    'lon': lon,
                    'types': set()
                }
            all_stations[name]['types'].add(route_type_name)
    
    if all_stations:
        with open(output_dir / 'stations.md', 'w', encoding='utf-8') as f:
            f.write("# Vienna Public Transport Stations\n\n")
            f.write("*Generated from official Wiener Linien GTFS data*  "
                  f"*Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n")
            
            f.write("## Station List\n\n")
            
            # Sort stations by name for consistency
            sorted_station_names = sorted(all_stations.keys())
            
            for i, name in enumerate(sorted_station_names, 1):
                station = all_stations[name]
                f.write(f"{i}. **{name}**  \n")
                f.write(f"   - Coordinates: {station['lat']:.6f}, {station['lon']:.6f}\n")
                f.write(f"   - Serves: {', '.join(sorted(station['types']))}\n\n")
    
    # Also generate individual station files for each route type
    for route_type, type_info in route_types.items():
        if route_type in station_data and station_data[route_type]:
            station_file = type_info['station_file']
            stations = sorted(station_data[route_type], key=lambda x: x[0])
            
            with open(output_dir / station_file, 'w', encoding='utf-8') as f:
                f.write(f"# Vienna {type_info['title']} Stations\n\n")
                f.write("*Generated from official Wiener Linien GTFS data*  "
                      f"*Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n")
                
                f.write("## Station List\n\n")
                
                for i, (name, lat, lon) in enumerate(stations, 1):
                    f.write(f"{i}. **{name}**  \n")
                    f.write(f"   - Coordinates: {lat:.6f}, {lon:.6f}\n")
                    f.write(f"   - Type: {type_info['title']}\n\n")

def process_with_timeout(func, *args, timeout=60, **kwargs):
    """Run a function with a timeout using ThreadPoolExecutor."""
    import concurrent.futures
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(func, *args, **kwargs)
        try:
            return future.result(timeout=timeout)
        except concurrent.futures.TimeoutError:
            print(f"\nError: {func.__name__} timed out after {timeout} seconds")
            return None

class ScriptError(Exception):
    """Custom exception for script errors."""
    pass

def parse_arguments():
    """Parse command line arguments."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Process Wiener Linien GTFS data.')
    parser.add_argument('--force-download', action='store_true',
                       help='Force download of GTFS data even if it exists')
    parser.add_argument('--force-extract', action='store_true',
                       help='Force extraction of GTFS data even if files exist')
    parser.add_argument('--debug', action='store_true',
                       help='Enable debug output')
    return parser.parse_args()

def main():
    """Main function to download and process GTFS data with error handling and timeouts."""
    args = parse_arguments()
    
    print("=" * 50)
    print("Wiener Linien GTFS Data Processor")
    print("=" * 50)
    print(f"Data directory: {DATA_DIR}")
    print(f"GTFS directory: {GTFS_DIR}")
    print("-" * 50)
    start_time = time.time()
    
    try:
        # Ensure directories exist
        print(f"\n[1/5] Setting up directories...")
        os.makedirs(DATA_DIR, exist_ok=True)
        os.makedirs(GTFS_DIR, exist_ok=True)
        print(f"  • Data directory: {DATA_DIR}")
        print(f"  • GTFS directory: {GTFS_DIR}")
        
        # Download GTFS data if needed
        print(f"\n[2/5] Checking GTFS data...")
        
        if not is_gtfs_fresh(GTFS_ZIP) or args.force_download:
            if GTFS_ZIP.exists():
                if args.force_download:
                    print("  • Forcing download of GTFS data...")
                else:
                    print(f"  • GTFS data is older than {GTFS_MAX_AGE_DAYS} days, downloading fresh copy...")
            else:
                print("  • GTFS data not found, downloading...")
                
            success, message = download_file(GTFS_URL, GTFS_ZIP, force=args.force_download)
            if not success:
                raise ScriptError(f"Failed to download GTFS data: {message}")
        else:
            print(f"  • Using existing GTFS data (less than {GTFS_MAX_AGE_DAYS} days old)")
        
        # Extract GTFS data
        print(f"\n[3/5] Extracting GTFS data...")
        
        success, message = extract_gtfs(GTFS_ZIP, GTFS_EXTRACT_DIR, force=args.force_extract)
        if not success:
            raise ScriptError(f"Failed to extract GTFS data: {message}")
            
        # Verify required files exist
        required_files = ['routes.txt', 'trips.txt', 'stops.txt', 'stop_times.txt']
        missing_files = [f for f in required_files if not (GTFS_EXTRACT_DIR / f).exists()]
        if missing_files:
            raise ScriptError(f"Missing required GTFS files: {', '.join(missing_files)}")
        
        # Load and process GTFS data with timeout
        print(f"\n[4/5] Processing GTFS data...")
        gtfs_data = process_with_timeout(load_gtfs_data, GTFS_EXTRACT_DIR, timeout=PROCESSING_TIMEOUT)
        
        if not gtfs_data:
            raise ScriptError("No GTFS data loaded - check the GTFS files for errors")
        
        # Process the data with timeouts
        print("  • Processing routes...")
        routes = process_with_timeout(process_routes, gtfs_data, timeout=PROCESSING_TIMEOUT)
        
        print("  • Processing stops...")
        stops = process_with_timeout(process_stops, gtfs_data, timeout=PROCESSING_TIMEOUT)
        
        print("  • Processing stop times...")
        # Process a limited number of entries initially for testing (set to 100,000 for now)
        # Once verified, we can increase this or set to None to process all
        max_entries = 100000  # Start with a reasonable number for testing
        process_with_timeout(process_stop_times, gtfs_data, routes, {}, stops, max_entries, timeout=PROCESSING_TIMEOUT)
        
        # Generate markdown files
        print(f"\n[5/5] Generating markdown files in {DATA_DIR}...")
        generate_markdown_files(routes, stops, DATA_DIR)
        
        # List generated files
        print("\n" + "=" * 50)
        print("PROCESSING COMPLETE")
        print("=" * 50)
        print(f"Total time: {time.time() - start_time:.1f} seconds\n")
        
        print("Generated files:")
        for pattern in ["*routes.md", "*stations.md"]:
            for file in sorted(DATA_DIR.glob(pattern)):
                file_size = os.path.getsize(file) / 1024  # Size in KB
                print(f"  • {file.name} ({file_size:.1f} KB)")
        
        # Verify stations.md was created
        stations_file = DATA_DIR / "stations.md"
        if not stations_file.exists():
            print("\nWARNING: stations.md was not generated!")
            return 1
            
        return 0
        
    except ScriptError as e:
        print(f"\nERROR: {str(e)}")
        return 1
    except Exception as e:
        print(f"\nUNEXPECTED ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
