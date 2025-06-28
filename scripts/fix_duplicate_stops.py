"""
Fix duplicate stops in GTFS data processing.

This script processes the GTFS data to combine duplicate stops (like Schottenring)
that appear multiple times with different RBL numbers.
"""

import os
import sys
import csv
from collections import defaultdict
from pathlib import Path

# Configuration
GTFS_DIR = Path(__file__).parent / "gtfs_data"
DATA_DIR = Path(__file__).parent.parent / "frontend" / "data"

def load_gtfs_file(filename: str) -> list[dict]:
    """Load a GTFS file as a list of dictionaries."""
    filepath = GTFS_DIR / "extracted" / filename
    if not filepath.exists():
        print(f"Warning: File not found: {filepath}")
        return []
    
    with open(filepath, 'r', encoding='utf-8-sig') as f:
        return list(csv.DictReader(f))

def process_stops() -> dict:
    """Process stops and combine duplicates by name."""
    stops_data = load_gtfs_file('stops.txt')
    
    # Group stops by name (case-insensitive)
    stops_by_name = defaultdict(list)
    for stop in stops_data:
        name = stop['stop_name'].strip()
        stops_by_name[name.lower()].append(stop)
    
    # Process each group of stops with the same name
    processed_stops = {}
    for name, stops in stops_by_name.items():
        if len(stops) == 1:
            # Single stop, no duplicates
            stop = stops[0]
            processed_stops[stop['stop_id']] = {
                'stop_id': stop['stop_id'],
                'stop_name': stop['stop_name'],
                'stop_lat': stop['stop_lat'],
                'stop_lon': stop['stop_lon'],
                'rbls': [stop.get('stop_code', '')],
                'zone_id': stop.get('zone_id', '')
            }
        else:
            # Multiple stops with same name - combine them
            primary = stops[0]
            rbls = list({s.get('stop_code', '') for s in stops if s.get('stop_code')})
            
            processed_stops[primary['stop_id']] = {
                'stop_id': primary['stop_id'],
                'stop_name': primary['stop_name'],
                'stop_lat': primary['stop_lat'],
                'stop_lon': primary['stop_lon'],
                'rbls': rbls,
                'zone_id': primary.get('zone_id', '')
            }
    
    return processed_stops

def process_stop_times(stops: dict) -> dict:
    """Process stop times and update with combined stop information."""
    stop_times = load_gtfs_file('stop_times.txt')
    trips = {t['trip_id']: t for t in load_gtfs_file('trips.txt')}
    
    # Group stop times by trip
    trip_stops = defaultdict(list)
    for st in stop_times:
        trip_id = st['trip_id']
        stop_id = st['stop_id']
        if stop_id in stops:
            stop_info = stops[stop_id].copy()
            stop_info.update({
                'stop_sequence': int(st['stop_sequence']),
                'arrival_time': st['arrival_time'],
                'departure_time': st['departure_time']
            })
            trip_stops[trip_id].append(stop_info)
    
    # Sort stops in each trip by sequence
    for trip_id in trip_stops:
        trip_stops[trip_id].sort(key=lambda x: x['stop_sequence'])
    
    return trip_stops

def generate_route_stops(trip_stops: dict, stops: dict) -> dict:
    """Generate unique stop sequences for each route."""
    route_stops = defaultdict(set)
    
    for trip_id, stop_list in trip_stops.items():
        # Create a unique key for this stop sequence
        sequence_key = tuple((s['stop_name'], s['stop_lat'], s['stop_lon']) for s in stop_list)
        route_stops[sequence_key].update(
            rbl for s in stop_list for rbl in s.get('rbls', [])
        )
    
    # Convert to list of stops with combined RBLs
    result = []
    for sequence_key, rbls in route_stops.items():
        stop_sequence = []
        for i, (name, lat, lon) in enumerate(sequence_key, 1):
            stop_sequence.append({
                'stop_sequence': i,
                'stop_name': name,
                'stop_lat': lat,
                'stop_lon': lon,
                'rbls': sorted(rbls)  # All RBLs for this station
            })
        result.append(stop_sequence)
    
    return result

def update_route_files(route_stops: dict, output_dir: Path):
    """Update route markdown files with deduplicated stops."""
    routes_data = load_gtfs_file('routes.txt')
    
    for route in routes_data:
        route_id = route['route_id']
        route_type = route['route_type']
        
        # Determine output file based on route type
        if route_type == '1':  # Metro
            filename = 'tuberoutes.md'
        elif route_type == '0':  # Tram
            filename = 'tramroutes.md'
        elif route_type == '3':  # Bus
            filename = 'busroutes.md'
        else:
            continue
        
        output_file = output_dir / filename
        
        # Read existing content
        with open(output_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find and update the route section
        route_header = f"## {route['route_short_name']} - {route['route_long_name']}"
        if route_header in content:
            # Generate new stops section
            stops_section = [
                f"{i+1}. **{stop['stop_name']}** - "
                f"RBL: {', '.join(stop['rbls'])}, "
                f"Coordinates: {stop['stop_lat']}, {stop['stop_lon']}"
                for i, stop in enumerate(route_stops[route_id])
            ]
            
            # Replace the stops section
            import re
            new_content = re.sub(
                r'(### Stops\n)(?:\d+\.\s+\*\*.*?\*\* - .*?\n)+',
                f'### Stops\n' + '\n'.join(stops_section) + '\n',
                content,
                flags=re.DOTALL
            )
            
            # Write updated content
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(new_content)

def main():
    """Main function to process and fix duplicate stops."""
    print("Processing stops to fix duplicates...")
    
    # Process stops and combine duplicates
    stops = process_stops()
    print(f"Processed {len(stops)} unique stops")
    
    # Process stop times with combined stops
    trip_stops = process_stop_times(stops)
    print(f"Processed {len(trip_stops)} trips")
    
    # Generate route stops with combined RBLs
    route_stops = generate_route_stops(trip_stops, stops)
    print(f"Generated {len(route_stops)} unique stop sequences")
    
    # Update route files
    update_route_files(route_stops, DATA_DIR)
    print("Updated route files with deduplicated stops")

if __name__ == "__main__":
    main()
