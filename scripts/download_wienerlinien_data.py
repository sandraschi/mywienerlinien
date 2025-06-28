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
from datetime import datetime
from pathlib import Path

# Configuration
GTFS_URL = "https://www.wienerlinien.at/ogd_realtime/doku/ogd/gtfs/gtfs.zip"
DATA_DIR = Path(__file__).parent.parent / "frontend" / "data"
GTFS_DIR = Path(__file__).parent / "gtfs_data"

# Ensure directories exist
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(GTFS_DIR, exist_ok=True)

def download_file(url: str, output_path: Path) -> bool:
    """Download a file from a URL to the specified path."""
    import urllib.request
    try:
        print(f"Downloading {url}...")
        urllib.request.urlretrieve(url, output_path)
        print(f"Downloaded to {output_path}")
        return True
    except Exception as e:
        print(f"Error downloading {url}: {e}")
        return False

def extract_gtfs(gtfs_zip: Path, output_dir: Path) -> bool:
    """Extract GTFS zip file to the specified directory."""
    try:
        print(f"Extracting {gtfs_zip} to {output_dir}...")
        with zipfile.ZipFile(gtfs_zip, 'r') as zip_ref:
            zip_ref.extractall(output_dir)
        print("Extraction complete")
        return True
    except Exception as e:
        print(f"Error extracting {gtfs_zip}: {e}")
        return False

def load_gtfs_data(gtfs_dir: Path) -> dict:
    """Load GTFS data from the extracted directory."""
    data = {}
    required_files = [
        'routes.txt', 'trips.txt', 'stops.txt', 'stop_times.txt',
        'calendar.txt', 'calendar_dates.txt'
    ]
    
    for file in required_files:
        file_path = gtfs_dir / file
        if not file_path.exists():
            print(f"Warning: Missing GTFS file: {file}")
            continue
            
        print(f"Loading {file}...")
        with open(file_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            data[file] = list(reader)
    
    return data

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
    """Process stops from GTFS data."""
    stops = {}
    for stop in gtfs_data.get('stops.txt', []):
        stop_id = stop['stop_id']
        stops[stop_id] = {
            'stop_id': stop_id,
            'stop_name': stop['stop_name'],
            'stop_lat': float(stop['stop_lat']),
            'stop_lon': float(stop['stop_lon']),
            'zone_id': stop.get('zone_id', ''),
            'location_type': int(stop.get('location_type', 0)),
            'parent_station': stop.get('parent_station', '')
        }
    return stops

def process_stop_times(gtfs_data: dict, routes: dict, trips: dict, stops: dict):
    """Process stop times to build route sequences."""
    # First, index trips by route
    route_trips = {}
    for trip in gtfs_data.get('trips.txt', []):
        route_id = trip['route_id']
        if route_id not in route_trips:
            route_trips[route_id] = []
        route_trips[route_id].append(trip['trip_id'])
    
    # Then process stop times for each trip
    for stop_time in gtfs_data.get('stop_times.txt', []):
        trip_id = stop_time['trip_id']
        stop_id = stop_time['stop_id']
        
        # Find which route this stop belongs to
        for route_id, trip_list in route_trips.items():
            if trip_id in trip_list and route_id in routes and stop_id in stops:
                if stop_id not in [s['stop_id'] for s in routes[route_id]['stops']]:
                    routes[route_id]['stops'].append({
                        'stop_id': stop_id,
                        'stop_name': stops[stop_id]['stop_name'],
                        'stop_sequence': int(stop_time['stop_sequence']),
                        'lat': stops[stop_id]['stop_lat'],
                        'lon': stops[stop_id]['stop_lon']
                    })
    
    # Sort stops by sequence
    for route in routes.values():
        route['stops'].sort(key=lambda x: x['stop_sequence'])

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
        
        # Generate station file if we have stations
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

def main():
    """Main function to download and process GTFS data."""
    print("Starting script execution...")
    
    # Ensure directories exist
    print(f"Ensuring directories exist: {DATA_DIR}, {GTFS_DIR}")
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(GTFS_DIR, exist_ok=True)
    
    # Download GTFS data
    gtfs_zip = GTFS_DIR / "wienerlinien-gtfs.zip"
    print(f"GTFS zip path: {gtfs_zip}")
    
    if not gtfs_zip.exists():
        print("GTFS zip not found, attempting to download...")
        if not download_file(GTFS_URL, gtfs_zip):
            print("Failed to download GTFS data")
            return 1
    else:
        print("GTFS zip already exists, using cached version")
    
    # Extract GTFS data
    gtfs_extracted = GTFS_DIR / "extracted"
    if not gtfs_extracted.exists() or not any(gtfs_extracted.iterdir()):
        if not extract_gtfs(gtfs_zip, gtfs_extracted):
            print("Failed to extract GTFS data")
            return 1
    
    # Load and process GTFS data
    print("Processing GTFS data...")
    gtfs_data = load_gtfs_data(gtfs_extracted)
    
    if not gtfs_data:
        print("No GTFS data loaded")
        return 1
    
    # Process the data
    routes = process_routes(gtfs_data)
    stops = process_stops(gtfs_data)
    process_stop_times(gtfs_data, routes, {}, stops)
    
    # Generate markdown files
    print("Generating markdown files...")
    generate_markdown_files(routes, stops, DATA_DIR)
    
    print("\nDone! Generated files in:")
    for pattern in ["*routes.md", "*stations.md"]:
        for file in DATA_DIR.glob(pattern):
            print(f"- {file}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
