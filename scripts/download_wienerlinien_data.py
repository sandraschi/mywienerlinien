"""
Download and process GTFS data for any city.

This script downloads GTFS data from any transit agency and processes it
to generate accurate route and station information. Supports multiple cities
via city configuration or direct GTFS URL.
"""

import os
import sys
import zipfile
import csv
import time
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, Tuple, Optional

try:
    from .city_config import get_city_config, get_gtfs_filename, list_cities, CityConfig
except ImportError:
    from city_config import get_city_config, get_gtfs_filename, list_cities, CityConfig  # type: ignore

# Timeout for network operations (seconds)
DOWNLOAD_TIMEOUT = 120  # Increased from 30
PROCESSING_TIMEOUT = 600  # Increased from 60 (10 minutes) to handle large GTFS datasets

# Default configuration (Vienna for backward compatibility)
DEFAULT_CITY = "vienna"
DEFAULT_GTFS_URL = "https://www.wienerlinien.at/ogd_realtime/doku/ogd/gtfs/gtfs.zip"

# In Docker, use /app/data; locally, use ../frontend/data
if Path("/app/data").exists():
    DATA_DIR = Path("/app/data")
else:
    DATA_DIR = Path(__file__).parent.parent / "frontend" / "data"
GTFS_DIR = Path(__file__).parent / "gtfs_data"
GTFS_EXTRACT_DIR = GTFS_DIR  # Use the same directory for extracted files


def get_gtfs_path(city_name: Optional[str] = None, gtfs_url: Optional[str] = None) -> Path:
    """Get the GTFS zip file path based on city or URL."""
    if city_name:
        filename = get_gtfs_filename(city_name)
    elif gtfs_url:
        # Extract filename from URL or use generic name
        filename = gtfs_url.split("/")[-1]
        if not filename.endswith(".zip"):
            filename = "gtfs.zip"
    else:
        filename = "wienerlinien-gtfs.zip"  # Default for backward compatibility
    return GTFS_DIR / filename

# Ensure directories exist (only if we have write permission)
try:
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(GTFS_DIR, exist_ok=True)
except (PermissionError, OSError):
    # Directory creation will happen when actually needed
    pass

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
    """Process routes from GTFS data.
    
    Args:
        gtfs_data: Dictionary containing GTFS data with 'routes.txt' key
        
    Returns:
        Dictionary mapping route IDs to route data with empty stops list
    """
    routes = {}
    seen_route_keys = set()  # Track unique route identifiers to avoid duplicates
    
    for route in gtfs_data.get('routes.txt', []):
        try:
            route_id = route['route_id']
            route_short_name = route.get('route_short_name', '').strip()
            route_long_name = route.get('route_long_name', '').strip()
            route_type = int(route.get('route_type', -1))
            
            # Create a unique key for this route to detect duplicates
            route_key = (route_short_name, route_long_name, route_type)
            if route_key in seen_route_keys:
                print(f"  • Skipping duplicate route: {route_short_name} - {route_long_name} (Type: {route_type})")
                continue
                
            seen_route_keys.add(route_key)
            
            routes[route_id] = {
                'route_id': route_id,
                'route_short_name': route_short_name,
                'route_long_name': route_long_name,
                'route_type': route_type,
                'route_color': f"#{route.get('route_color', '000000').lstrip('#')}",
                'route_text_color': f"#{route.get('route_text_color', 'FFFFFF').lstrip('#')}",
                'stops': []
            }
            
        except (KeyError, ValueError) as e:
            print(f"  • Error processing route {route.get('route_id', 'unknown')}: {e}")
            continue
    
    print(f"  • Processed {len(routes)} unique routes")
    return routes

def process_stops(gtfs_data: dict, max_stops: int = None) -> dict:
    """Process stops data from GTFS.
    
    Args:
        gtfs_data: Dictionary containing GTFS data
        max_stops: Maximum number of stops to process (for testing)
    """
    stops = {}
    stops_data = gtfs_data.get('stops.txt', [])
    
    if not stops_data:
        print("  • Warning: No stops data found in GTFS")
        return {}
    
    # Limit the number of stops if max_stops is specified
    if max_stops and max_stops > 0:
        stops_data = stops_data[:max_stops]
        print(f"  • Processing first {max_stops:,} stops (limited for testing)...")
    else:
        print(f"  • Processing {len(stops_data):,} stops...")
    
    start_time = time.time()
    last_log_time = start_time
    
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
            
            # Log progress every 10,000 records or every 5 seconds
            current_time = time.time()
            if i % 10000 == 0 or (current_time - last_log_time) >= 5 or i == len(stops_data):
                elapsed = current_time - start_time
                rate = i / elapsed if elapsed > 0 else 0
                remaining = (len(stops_data) - i) / rate if rate > 0 else 0
                
                print((f"  • Processed {i:,}/{len(stops_data):,} stops "
                      f"({i/len(stops_data)*100:.1f}%, {rate:,.0f} stops/sec, "
                      f"ETA: {remaining/60:.1f} min remaining)"))
                last_log_time = current_time
                
        except Exception as e:
            print(f"  • Error processing stop {i}: {e}")
            continue
    
    elapsed = time.time() - start_time
    print((f"  • Successfully processed {len(stops):,} stops in "
           f"{elapsed:.1f} seconds ({len(stops)/elapsed:,.0f} stops/sec)"))
    
    return stops

def remove_consecutive_duplicates(sequence):
    """Remove consecutive duplicate stops from a sequence while preserving order.
    
    Args:
        sequence: List of stop dictionaries
        
    Returns:
        List with consecutive duplicates removed
    """
    if not sequence:
        return []
        
    result = [sequence[0]]
    for item in sequence[1:]:
        if item['stop_id'] != result[-1]['stop_id']:
            result.append(item)
    return result


def deduplicate_stops(sequence):
    """Remove duplicate stops (by stop_id) while preserving order."""
    seen_ids = set()
    deduped = []
    for item in sequence:
        stop_id = item.get('stop_id')
        if not stop_id:
            continue
        if stop_id in seen_ids:
            continue
        seen_ids.add(stop_id)
        deduped.append(item)
    return deduped

def process_stop_times(gtfs_data: dict, routes: dict, trips: dict, stops: dict, max_entries: int = None):
    """Process stop times to build route sequences.
    
    Args:
        gtfs_data: Dictionary containing GTFS data with 'stop_times.txt' and 'trips.txt'
        routes: Dictionary of routes to populate with stops
        trips: Dictionary mapping trip IDs to trip data
        stops: Dictionary of all stops
        max_entries: Maximum number of entries to process (None for all)
    """
    print("  • Indexing trips by route and direction...")
    
    # First, index trips by route and direction, and map trip_id to route_id/direction_id
    trip_to_route_direction = {}
    trips_data = gtfs_data.get('trips.txt', [])
    
    # Build a proper trip_id to route_id and direction_id mapping
    for trip in trips_data:
        route_id = trip.get('route_id')
        direction_id = str(trip.get('direction_id', '0'))  # Ensure string for consistency
        trip_id = trip.get('trip_id')
        
        if not route_id or not trip_id or route_id not in routes:
            continue
            
        # Map trip to route and direction
        trip_to_route_direction[trip_id] = (route_id, direction_id)
    
    # Process stop times with progress reporting
    stop_times = gtfs_data.get('stop_times.txt', [])
    
    # Limit the number of entries if specified
    if max_entries and max_entries > 0:
        stop_times = stop_times[:max_entries]
        print(f"  • Processing first {max_entries:,} stop time entries...")
    else:
        print(f"  • Processing {len(stop_times):,} stop time entries...")
    
    # Sort stop times by trip_id and stop_sequence to ensure correct order
    print("  • Sorting stop times by trip and sequence...")
    stop_times.sort(key=lambda x: (x.get('trip_id', ''), int(x.get('stop_sequence', 0))))
    
    total_entries = len(stop_times)
    processed = 0
    start_time = time.time()
    last_log_time = start_time
    
    # Structure to hold a canonical stop sequence for each route and direction
    route_direction_stops: Dict[str, Dict[str, list]] = {}

    def store_trip_sequence(trip_id: str, stops_sequence: list) -> None:
        """Keep the best (longest) canonical stop sequence per route/direction."""
        if not trip_id or not stops_sequence:
            return
        mapping = trip_to_route_direction.get(trip_id)
        if not mapping:
            return
        route_id, direction_id = mapping
        if route_id not in route_direction_stops:
            route_direction_stops[route_id] = {}
        canonical = deduplicate_stops(remove_consecutive_duplicates(stops_sequence))
        existing = route_direction_stops[route_id].get(direction_id)
        if not existing or len(canonical) > len(existing):
            route_direction_stops[route_id][direction_id] = canonical
    
    # First pass: Build complete stop sequences for each trip
    print("  • Building stop sequences for each trip...")
    current_trip = None
    current_stops = []
    
    for i, stop_time in enumerate(stop_times, 1):
        # Progress reporting
        current_time = time.time()
        if i % 100000 == 0 or (current_time - last_log_time) >= 5 or i == total_entries:
            elapsed = current_time - start_time
            rate = i / elapsed if elapsed > 0 else 0
            remaining = (total_entries - i) / rate if rate > 0 else 0
            
            print((f"    - Processed {i:,}/{total_entries:,} entries "
                  f"({i/total_entries*100:.1f}%, {rate:,.0f} entries/sec, "
                  f"ETA: {remaining/60:.1f} min remaining)"))
            last_log_time = current_time
        
        trip_id = stop_time.get('trip_id')
        stop_id = stop_time.get('stop_id')
        
        # Skip if trip_id or stop_id is missing or stop doesn't exist
        if not trip_id or not stop_id or stop_id not in stops:
            continue
            
        # If this is a new trip, process the previous one
        if trip_id != current_trip and current_trip is not None:
            store_trip_sequence(current_trip, current_stops)
            # Reset for the new trip
            current_stops = []
        
        # Set the current trip
        current_trip = trip_id
        
        # Add this stop to the current trip's stops
        try:
            stop_sequence = int(stop_time.get('stop_sequence', 0))
            current_stops.append({
                'stop_id': stop_id,
                'stop_name': stops[stop_id].get('stop_name', 'Unknown Stop'),
                'stop_sequence': stop_sequence,
                'lat': float(stops[stop_id].get('stop_lat', 0)),
                'lon': float(stops[stop_id].get('stop_lon', 0))
            })
            processed += 1
        except (ValueError, KeyError) as e:
            print(f"    • Error processing stop time: {e}")
            continue
    
    # Process the last trip
    if current_trip and current_stops:
        store_trip_sequence(current_trip, current_stops)
    
    # Now build the final route stops by finding the most common sequence for each route/direction
    print("  • Building final route stop sequences...")
    route_stop_sequences = {}
    
    for route_id, directions in route_direction_stops.items():
        if route_id not in routes:
            continue
            
        route_stop_sequences[route_id] = {}
        
        for direction_id, canonical_stops in directions.items():
            if canonical_stops:
                route_stop_sequences[route_id][direction_id] = canonical_stops
    
    # Now assign the stops to the routes
    print("  • Assigning stops to routes...")
    routes_with_stops = 0
    total_stops_assigned = 0
    
    for route_id, route in routes.items():
        route['stops'] = []
        if route_id in route_stop_sequences:
            directions = route_stop_sequences[route_id]
            print(f"    - Processing route {route_id} with {len(directions)} directions")
            
            for direction_id, stops_list in directions.items():
                # Sort stops by sequence number before adding to route
                sorted_stops = sorted(stops_list, key=lambda x: x.get('stop_sequence', 0))
                print(f"      - Direction {direction_id}: {len(sorted_stops)} stops")
                
                for stop in sorted_stops:
                    route['stops'].append({
                        'stop_id': stop['stop_id'],
                        'stop_name': stop['stop_name'],
                        'stop_sequence': stop.get('stop_sequence', len(route['stops']) + 1),
                        'direction_id': direction_id,
                        'lat': stop['lat'],
                        'lon': stop['lon']
                    })
                    total_stops_assigned += 1
            
            if route['stops']:
                routes_with_stops += 1
    
    print(f"  • Assigned {total_stops_assigned} stops to {routes_with_stops} out of {len(routes)} routes")
    
    # Sort stops by sequence for each route and direction
    print("  • Sorting stops by sequence and direction...")
    route_count = len(routes)
    
    for i, (route_id, route) in enumerate(routes.items(), 1):
        # Group stops by direction
        stops_by_direction = {}
        for stop in route['stops']:
            direction = stop.get('direction_id', '0')
            if direction not in stops_by_direction:
                stops_by_direction[direction] = []
            stops_by_direction[direction].append(stop)
        
        # Sort stops within each direction by sequence
        route_stops = []
        for direction, dir_stops in stops_by_direction.items():
            dir_stops_sorted = sorted(dir_stops, key=lambda x: x['stop_sequence'])
            route_stops.extend(dir_stops_sorted)
        
        route['stops'] = route_stops
        
        if i % 100 == 0 or i == route_count:
            directions = len(stops_by_direction)
            print(f"    - Sorted {i:,}/{route_count:,} routes: {route_id} has {len(route_stops)} stops ({directions} directions)")
    
    # Print summary of routes with stops
    routes_with_stops = sum(1 for route in routes.values() if route['stops'])
    total_stops = sum(len(route['stops']) for route in routes.values())
    
    elapsed = time.time() - start_time
    print((f"  • Processed {processed:,} stop time entries "
           f"in {elapsed/60:.1f} minutes ({processed/elapsed:,.0f} entries/sec)"))
    print(f"  • {routes_with_stops:,} out of {route_count:,} routes have stops assigned")
    
    # Sort stops by sequence for each route and direction
    print("  • Sorting stops by sequence and direction...")
    route_count = len(routes)
    
    for i, (route_id, route) in enumerate(routes.items(), 1):
        # Group stops by direction
        stops_by_direction = {}
        for stop in route['stops']:
            direction = stop.get('direction_id', '0')
            if direction not in stops_by_direction:
                stops_by_direction[direction] = []
            stops_by_direction[direction].append(stop)
        
        # Sort stops within each direction by sequence
        route_stops = []
        for direction, dir_stops in stops_by_direction.items():
            dir_stops_sorted = sorted(dir_stops, key=lambda x: x['stop_sequence'])
            route_stops.extend(dir_stops_sorted)
        
        route['stops'] = route_stops
        
        if i % 100 == 0 or i == route_count:
            directions = len(stops_by_direction)
            print(f"    - Sorted {i:,}/{route_count:,} routes: {route_id} has {len(route_stops)} stops ({directions} directions)")
    
    # Print summary of routes with stops
    routes_with_stops = sum(1 for route in routes.values() if route['stops'])
    total_stops = sum(len(route['stops']) for route in routes.values())
    
    elapsed = time.time() - start_time
    print((f"  • Processed {processed:,} stop time entries "
           f"in {elapsed/60:.1f} minutes ({processed/elapsed:,.0f} entries/sec)"))
    print(f"  • {routes_with_stops:,} out of {route_count:,} routes have stops assigned")
    print(f"  • Total stops assigned: {total_stops:,}")

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
    """Generate markdown files for routes and stations.
    
    Args:
        routes: Dictionary of routes with their stops
        stops: Dictionary of all stops with their details
        output_dir: Directory where markdown files will be saved
    """
    # Define route types and their metadata
    route_types = {
        0: {
            'name': 'tram', 
            'title': 'Tram (Straßenbahn)', 
            'filename': 'tramroutes.md', 
            'station_file': 'tramstations.md',
            'description': 'Vienna tram routes operated by Wiener Linien.'
        },
        1: {
            'name': 'metro', 
            'title': 'U-Bahn (Metro)', 
            'filename': 'tuberoutes.md', 
            'station_file': 'ubahnstations.md',
            'description': 'Vienna U-Bahn (metro) lines operated by Wiener Linien.'
        },
        3: {
            'name': 'bus', 
            'title': 'Bus', 
            'filename': 'busroutes.md', 
            'station_file': 'busstations.md',
            'description': 'Vienna bus routes operated by Wiener Linien.'
        },
        7: {
            'name': 'funicular', 
            'title': 'Funicular', 
            'filename': 'funicularroutes.md', 
            'station_file': 'funicularstations.md',
            'description': 'Funicular railway in Vienna.'
        },
        999: {
            'name': 'nightbus', 
            'title': 'Night Bus', 
            'filename': 'nightbusroutes.md', 
            'station_file': 'nightbusstations.md',
            'description': 'Vienna night bus routes operated by Wiener Linien.'
        }
    }
    
    # Initialize data structures
    routes_by_type = {}
    station_data = {}
    route_directions = {}  # Track directions for each route
    
    # Process routes and collect station data
    for route_id, route in routes.items():
        route_type_info = route_types.get(route['route_type'])
        
        # Special handling for night buses (N-prefixed routes)
        if (route_type_info and route_type_info['name'] == 'bus' and 
            route['route_short_name'].startswith(('N', 'n'))):
            route_type_info = route_types[999]  # Use nightbus type
        
        if not route_type_info:
            continue
            
        route_type = route_type_info['name']
        
        # Initialize route type if not exists
        if route_type not in routes_by_type:
            routes_by_type[route_type] = []
            station_data[route_type] = set()
            route_directions[route_type] = {}
        
        # Add route to the appropriate type
        routes_by_type[route_type].append(route)
        
        # Track directions for this route
        if route_id not in route_directions[route_type]:
            route_directions[route_type][route_id] = set()
        
        # Collect unique stations for this route type and track directions
        for stop in route['stops']:
            station_data[route_type].add((stop['stop_name'], stop['lat'], stop['lon']))
            if 'direction_id' in stop:
                route_directions[route_type][route_id].add(stop['direction_id'])
    
    # Generate files for each route type
    for route_type_id, type_info in route_types.items():
        route_type = type_info['name']
        
        # Skip if no routes of this type
        if route_type not in routes_by_type or not routes_by_type[route_type]:
            print(f"  • No routes found for type: {type_info['title']}")
            continue
        
        # Sort routes by short name (handle numeric and alphanumeric sorting)
        def route_sort_key(route):
            try:
                # Try to convert to int for proper numeric sorting
                return (0, int(route['route_short_name']))
            except (ValueError, TypeError):
                # Fall back to string comparison
                return (1, str(route['route_short_name']))
        
        type_routes = sorted(routes_by_type[route_type], key=route_sort_key)
        
        # Generate route file
        output_file = output_dir / type_info['filename']
        print(f"  • Generating {type_info['filename']} with {len(type_routes)} {type_info['title']} routes...")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            # Write header
            f.write(f"# Vienna {type_info['title']} Routes\n\n")
            f.write("*Generated from official Wiener Linien GTFS data*  "
                  f"*Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n")
            f.write(f"{type_info['description']}\n\n")
            
            # Write route index
            if len(type_routes) > 5:  # Only add TOC for larger files
                f.write("## Route Index\n\n")
                for route in type_routes:
                    route_name = f"{route['route_short_name']} - {route['route_long_name']}"
                    f.write(f"- [{route_name}](#{route['route_short_name'].lower().replace(' ', '-')}---{route['route_long_name'].lower().replace(' ', '-').replace('/', '')})\n")
                f.write("\n")
            
            # Write each route
            for route in type_routes:
                route_id = route['route_id']
                route_name = f"{route['route_short_name']} - {route['route_long_name']}"
                
                # Create URL-friendly anchor
                route_anchor = f"{route['route_short_name'].lower().replace(' ', '-')}---{route['route_long_name'].lower().replace(' ', '-').replace('/', '')}"
                f.write(f"## <a id=\"{route_anchor}\"></a>{route_name}\n")
                
                f.write(f"- **Line**: {route['route_short_name']}  \n")
                f.write(f"- **Type**: {type_info['title']}  \n")
                f.write(f"- **Color**: {route['route_color']}  \n")
                
                # Group stops by direction if available
                stops_by_direction = {}
                for stop in route['stops']:
                    direction = stop.get('direction_id', '0')
                    if direction not in stops_by_direction:
                        stops_by_direction[direction] = []
                    stops_by_direction[direction].append(stop)
                
                # Write direction information
                if len(stops_by_direction) > 1:
                    f.write("- **Directions**: ")
                    directions = []
                    for direction_id in sorted(stops_by_direction.keys()):
                        dir_stops = stops_by_direction[direction_id]
                        if dir_stops:
                            # Get first and last stop names for direction
                            first_stop = dir_stops[0].get('stop_name', 'Unknown')
                            last_stop = dir_stops[-1].get('stop_name', 'Unknown')
                            directions.append(f"Direction {direction_id}: {first_stop} → {last_stop}")
                    f.write("; ".join(directions) + "  \n")
                
                f.write(f"- **Total Stops**: {len(route['stops'])}\n\n")
                
                # Write stops section
                f.write("### Stops\n\n")
                
                # If we have multiple directions, group by direction
                if len(stops_by_direction) > 1:
                    for direction_id in sorted(stops_by_direction.keys()):
                        dir_stops = stops_by_direction[direction_id]
                        if not dir_stops:
                            continue
                            
                        # Get direction description
                        first_stop = dir_stops[0].get('stop_name', 'Start')
                        last_stop = dir_stops[-1].get('stop_name', 'End')
                        f.write(f"#### Direction {direction_id}: {first_stop} → {last_stop}\n\n")
                        
                        # List stops for this direction
                        for i, stop in enumerate(dir_stops, 1):
                            f.write(f"{i}. **{stop['stop_name']}**  \n")
                            f.write(f"   - Coordinates: {stop.get('lat', 0):.6f}, {stop.get('lon', 0):.6f}  \n")
                            f.write(f"   - Stop ID: {stop.get('stop_id', 'N/A')}  \n")
                            f.write(f"   - Sequence: {stop.get('stop_sequence', i)}\n\n")
                else:
                    # Single direction, simple list
                    for i, stop in enumerate(route['stops'], 1):
                        f.write(f"{i}. **{stop['stop_name']}**  \n")
                        f.write(f"   - Coordinates: {stop.get('lat', 0):.6f}, {stop.get('lon', 0):.6f}  \n")
                        f.write(f"   - Stop ID: {stop.get('stop_id', 'N/A')}  \n")
                        f.write(f"   - Sequence: {stop.get('stop_sequence', i)}\n\n")
                
                f.write("\n")
        
    # Generate unified stations.md file with all stations
    all_stations = {}
    
    # First, collect all stations with their types from the stops dictionary
    # This ensures we get all stops, not just those attached to routes
    for stop_id, stop in stops.items():
        name = stop.get('stop_name')
        if not name or not stop.get('lat') or not stop.get('lon'):
            continue
            
        # Get the route types that serve this stop by checking all routes
        stop_route_types = set()
        
        # Get location type (0=stop, 1=station, 2=entrance/exit, etc.)
        location_type = int(stop.get('location_type', '0'))
        
        # Check if this is a U-Bahn station (location_type = 1 and name ends with 'U' or contains 'U-Bahn')
        if (location_type == 1 and 
            (name.endswith('U') or 'U-Bahn' in name or ' U ' in f" {name} " or 
             any(word.startswith('U') and len(word) <= 3 for word in name.split()))):
            stop_route_types.add('metro')
        
        # Check all routes that serve this stop
        for route in routes.values():
            # Check if this stop is in the route's stops or if the route has this stop_id in its stops
            route_stops = route.get('stops', [])
            if any(s.get('stop_id') == stop_id for s in route_stops):
                route_type = route.get('route_type')
                route_short_name = route.get('route_short_name', '')
                
                if route_type == 0:  # Tram
                    stop_route_types.add('tram')
                elif route_type == 1:  # Metro
                    stop_route_types.add('metro')
                elif route_type == 3:  # Bus
                    if route_short_name.startswith(('N', 'n')):  # Night bus
                        stop_route_types.add('nightbus')
                    else:
                        stop_route_types.add('bus')
                elif route_type == 7:  # Funicular
                    stop_route_types.add('funicular')
        
        # Additional heuristics for tram/U-Bahn identification
        if not stop_route_types or (len(stop_route_types) == 1 and 'bus' in stop_route_types):
            # Check if this looks like a U-Bahn station (name ends with 'U' or contains 'U-Bahn' or has U followed by a number)
            if (name.endswith('U') or 'U-Bahn' in name or ' U ' in f" {name} " or 
                any(word.startswith('U') and len(word) <= 3 for word in name.split())):
                stop_route_types.add('metro')
            # Check if this looks like a tram stop (name contains common tram stop indicators)
            elif any(marker in name for marker in ['Gasse', 'Platz', 'Straße', 'gasse', 'platz', 'straße', 'Ring', 'Kai']):
                stop_route_types.add('tram')
        
        # If we still don't have any types, use location_type as fallback
        if not stop_route_types:
            if location_type == 1:  # Station
                # Check if it's likely a U-Bahn station based on name pattern
                if (name.endswith('U') or 'U-Bahn' in name or ' U ' in f" {name} " or 
                    any(word.startswith('U') and len(word) <= 3 for word in name.split())):
                    stop_route_types.add('metro')
                else:
                    stop_route_types.add('station')
            else:  # Default to bus if we can't determine the type
                stop_route_types.add('bus')
        
        # Special case for stops that are part of multiple route types
        # If we have both bus and another type, keep the more specific type
        if len(stop_route_types) > 1 and 'bus' in stop_route_types:
            # If we have a more specific type, remove the generic 'bus' type
            if any(t in stop_route_types for t in ['tram', 'metro', 'funicular']):
                stop_route_types.discard('bus')
        
        if name not in all_stations:
            all_stations[name] = {
                'lat': float(stop['lat']),
                'lon': float(stop['lon']),
                'types': stop_route_types,
                'stop_id': stop_id
            }
        else:
            # Update types if this stop serves additional route types
            all_stations[name]['types'].update(stop_route_types)
    
    if all_stations:
        output_file = output_dir / 'stations.md'
        print(f"  • Generating stations.md with {len(all_stations)} stations...")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("# Vienna Public Transport Stations\n\n")
            f.write("*Generated from official Wiener Linien GTFS data*  "
                  f"*Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n")
            
            # Add statistics
            type_counts = {}
            for station in all_stations.values():
                for t in station['types']:
                    type_counts[t] = type_counts.get(t, 0) + 1
            
            f.write("## Overview\n\n")
            f.write("This file contains all public transport stations and stops in Vienna.\n\n")
            f.write("### Transport Types\n\n")
            for t, count in sorted(type_counts.items()):
                f.write(f"- **{t.capitalize()}**: {count} stations\n")
            f.write("\n")
            
            f.write("## Station List\n\n")
            
            # Sort stations by name for consistency (case-insensitive)
            sorted_stations = sorted(
                all_stations.items(),
                key=lambda x: (x[0].lower(), x[0])
            )
            
            # Group stations by first letter for easier navigation
            from itertools import groupby
            
            # First, create a list of (letter, stations) tuples
            letter_groups = []
            for letter, group in groupby(sorted_stations, key=lambda x: x[0][0].upper() if x[0] else '#'):
                stations = list(group)
                if stations:
                    letter_groups.append((letter, stations))
            
            # Add table of contents
            f.write("### Table of Contents\n\n")
            for letter, _ in letter_groups:
                f.write(f"[{letter}](#letter-{letter.lower()}) | ")
            f.write("\n\n")
            
            # Write stations by letter
            for letter, stations in letter_groups:
                f.write(f"### <a id=\"letter-{letter.lower()}\"></a>{letter}\n\n")
                
                for i, (name, station) in enumerate(stations, 1):
                    # Skip stations without coordinates
                    if 'lat' not in station or 'lon' not in station:
                        continue
                        
                    f.write(f"{i}. **{name}**  \n")
                    f.write(f"   - Coordinates: {station['lat']:.6f}, {station['lon']:.6f}  \n")
                    
                    # Format types with proper names
                    type_names = []
                    for t in sorted(station['types']):
                        if t == 'tram':
                            type_names.append("Tram")
                        elif t == 'metro':
                            type_names.append("U-Bahn")
                        elif t == 'bus':
                            type_names.append("Bus")
                        elif t == 'nightbus':
                            type_names.append("Night Bus")
                        elif t == 'funicular':
                            type_names.append("Funicular")
                        elif t == 'station':
                            type_names.append("Station")
                        else:
                            type_names.append(t.capitalize())
                    
                    if type_names:
                        f.write(f"   - Serves: {', '.join(sorted(type_names))}  \n")
                    
                    # Add stop ID if available
                    if 'stop_id' in station:
                        f.write(f"   - Stop ID: {station['stop_id']}  \n")
                    
                    f.write("\n")
    
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
    parser = argparse.ArgumentParser(description='Download and process Wiener Linien GTFS data')
    parser.add_argument('--force-download', action='store_true', help='Force download of GTFS data even if it exists')
    parser.add_argument('--force-extract', action='store_true', help='Force extraction of GTFS data even if it exists')
    parser.add_argument('--full', action='store_true', help='Process the full dataset (may take a long time)')
    parser.add_argument('--max-entries', type=int, default=100000, 
                       help='Maximum number of stop time entries to process (for testing)')
    parser.add_argument('--max-stops', type=int, default=10000,
                       help='Maximum number of stops to process (for testing)')
    parser.add_argument('--debug', action='store_true',
                       help='Enable debug output')
    return parser.parse_args()

def main():
    """Main function to download and process GTFS data with error handling and timeouts."""
    args = parse_arguments()
    
    # Handle --list-cities
    if args.list_cities:
        cities = list_cities()
        print("\nAvailable pre-configured cities:")
        print("=" * 70)
        for city_id, config in cities.items():
            print(f"\n{city_id.upper()}")
            print(f"  Name: {config.name}")
            print(f"  URL: {config.gtfs_url}")
            print(f"  Timezone: {config.timezone}")
            print(f"  Description: {config.description}")
        print("\nUsage: python download_wienerlinien_data.py --city <city_id>")
        return 0
    
    # Determine GTFS URL and city config
    city_config: Optional[CityConfig] = None
    gtfs_url: str
    city_name: str = "unknown"
    
    if args.gtfs_url:
        # Direct URL provided
        gtfs_url = args.gtfs_url
        city_name = "custom"
        print(f"Using custom GTFS URL: {gtfs_url}")
    elif args.city:
        # City name provided
        city_config = get_city_config(args.city)
        if not city_config:
            print(f"Error: City '{args.city}' not found.")
            print("Use --list-cities to see available cities.")
            return 1
        gtfs_url = city_config.gtfs_url
        city_name = city_config.name.lower()
        print(f"Using city configuration: {city_config.name}")
        print(f"  Timezone: {city_config.timezone}")
        print(f"  URL: {gtfs_url}")
    else:
        # Default to Vienna for backward compatibility
        city_config = get_city_config(DEFAULT_CITY)
        gtfs_url = DEFAULT_GTFS_URL
        city_name = DEFAULT_CITY
        print(f"Using default city: {city_config.name if city_config else 'Vienna'}")
    
    # Get GTFS file path
    gtfs_zip = get_gtfs_path(city_name, args.gtfs_url)
    
    print("=" * 50)
    print("GTFS Data Processor")
    print("=" * 50)
    print(f"City: {city_config.name if city_config else 'Custom'}")
    print(f"GTFS URL: {gtfs_url}")
    print(f"Data directory: {DATA_DIR}")
    print(f"GTFS directory: {GTFS_DIR}")
    print(f"GTFS file: {gtfs_zip}")
    print("-" * 50)
    start_time = time.time()
    
    try:
        # Ensure directories exist
        print("\n[1/5] Setting up directories...")
        os.makedirs(DATA_DIR, exist_ok=True)
        os.makedirs(GTFS_DIR, exist_ok=True)
        print(f"  • Data directory: {DATA_DIR}")
        print(f"  • GTFS directory: {GTFS_DIR}")
        
        # Download GTFS data if needed
        print("\n[2/5] Checking GTFS data...")
        
        if not is_gtfs_fresh(gtfs_zip) or args.force_download:
            if gtfs_zip.exists():
                if args.force_download:
                    print("  • Forcing download of GTFS data...")
                else:
                    print(f"  • GTFS data is older than {GTFS_MAX_AGE_DAYS} days, downloading fresh copy...")
            else:
                print("  • GTFS data not found, downloading...")
                
            success, message = download_file(gtfs_url, gtfs_zip, force=args.force_download)
            if not success:
                raise ScriptError(f"Failed to download GTFS data: {message}")
        else:
            print(f"  • Using existing GTFS data (less than {GTFS_MAX_AGE_DAYS} days old)")
        
        # Extract GTFS data
        print("\n[3/5] Extracting GTFS data...")
        
        success, message = extract_gtfs(gtfs_zip, GTFS_EXTRACT_DIR, force=args.force_extract)
        if not success:
            raise ScriptError(f"Failed to extract GTFS data: {message}")
            
        # Verify required files exist
        required_files = ['routes.txt', 'trips.txt', 'stops.txt', 'stop_times.txt']
        missing_files = [f for f in required_files if not (GTFS_EXTRACT_DIR / f).exists()]
        if missing_files:
            raise ScriptError(f"Missing required GTFS files: {', '.join(missing_files)}")
        
        # Load and process GTFS data with timeout
        print("\n[4/5] Processing GTFS data...")
        gtfs_data = process_with_timeout(load_gtfs_data, GTFS_EXTRACT_DIR, timeout=PROCESSING_TIMEOUT)
        
        if not gtfs_data:
            raise ScriptError("No GTFS data loaded - check the GTFS files for errors")
        
        # Process the data with timeouts
        try:
            print("  • Processing routes...")
            routes = process_with_timeout(process_routes, gtfs_data, timeout=PROCESSING_TIMEOUT)
            
            # Process stops with a limit for testing
            print("  • Processing stops...")
            max_stops = 10000  # Start with a smaller subset for testing
            stops = process_with_timeout(process_stops, gtfs_data, max_stops, timeout=PROCESSING_TIMEOUT)
            
            print("  • Processing stop times...")
            # Process a limited number of entries for testing
            max_entries = 100000  # Start with a reasonable number for testing
            process_with_timeout(
                process_stop_times, 
                gtfs_data, routes, {}, stops, max_entries, 
                timeout=PROCESSING_TIMEOUT
            )
            
            print("\nInitial test processing completed successfully!")
            print("To process the full dataset, run with --full")
            
        except Exception as e:
            print(f"\nError during processing: {str(e)}")
            print("Trying to continue with partial data...")
            if 'routes' not in locals():
                routes = {}
            if 'stops' not in locals():
                stops = {}
        
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
