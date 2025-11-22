"""
GTFS Processor using gtfs-kit

This script processes GTFS data using the gtfs-kit library to generate
accurate route and station information for the Wiener Linien app.
"""

import sys
from pathlib import Path
from datetime import datetime
import logging
import gtfs_kit as gk
import pandas as pd

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Define route types for Vienna public transport
ROUTE_TYPES = {
    0: {'name': 'tram', 'title': 'Tram (Straßenbahn)', 'filename': 'tramroutes.md', 'station_file': 'tramstations.md'},
    1: {'name': 'metro', 'title': 'U-Bahn (Metro)', 'filename': 'tuberoutes.md', 'station_file': 'tubestations.md'},
    3: {'name': 'bus', 'title': 'Bus', 'filename': 'busroutes.md', 'station_file': 'busstations.md'},
    7: {'name': 'funicular', 'title': 'Funicular', 'filename': 'funicularroutes.md', 'station_file': 'funicularstations.md'}
}

class GTFSProcessor:
    """Process GTFS data using gtfs-kit and generate markdown files."""
    
    def __init__(self, data_dir: str, gtfs_path: str):
        """Initialize the processor with directories and paths."""
        self.data_dir = Path(data_dir)
        self.gtfs_path = Path(gtfs_path)
        self.feed = None
        
        # Ensure directories exist
        self.data_dir.mkdir(parents=True, exist_ok=True)
    
    def load_feed(self):
        """Load the GTFS feed from the specified path."""
        logger.info(f"Loading GTFS feed from {self.gtfs_path}")
        self.feed = gk.read_feed(self.gtfs_path, dist_units='km')
        logger.info(f"Loaded feed with {len(self.feed.routes)} routes and {len(self.feed.stops)} stops")
    
    def process_routes(self):
        """Process routes and generate markdown files."""
        if self.feed is None:
            self.load_feed()
        
        # Get current timestamp for the "last updated" note
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Process each route type
        for route_type, type_info in ROUTE_TYPES.items():
            routes = self.feed.routes[self.feed.routes['route_type'] == route_type]
            
            if routes.empty:
                logger.warning(f"No routes found for type: {type_info['name']}")
                continue
                
            logger.info(f"Processing {len(routes)} {type_info['name']} routes...")
            
            # Generate markdown content
            md_content = [
                f"# Vienna {type_info['title']} Routes",
                f"\n*Generated from official Wiener Linien GTFS data*  *Last updated: {timestamp}*\n",
                f"Vienna {type_info['name']} routes operated by Wiener Linien.\n",
                "## Route Index\n"
            ]
            
            # Add route index
            for _, route in routes.iterrows():
                route_name = route['route_short_name']
                route_long_name = route['route_long_name']
                route_id = route['route_id']
                
                # Create a sanitized ID for the route
                route_slug = f"{route_id}-{route_name}-{route_long_name}".lower()
                route_slug = "".join(c if c.isalnum() or c in ' -' else ' ' for c in route_slug)
                route_slug = "-".join(route_slug.split())
                
                md_content.append(f"- [{route_name} - {route_long_name}](#{route_slug})")
            
            md_content.append("\n## Route Details\n")
            
            # Add route details
            for _, route in routes.iterrows():
                route_name = route['route_short_name']
                route_long_name = route['route_long_name']
                route_id = route['route_id']
                route_slug = f"{route_id}-{route_name}-{route_long_name}".lower()
                route_slug = "".join(c if c.isalnum() or c in ' -' else ' ' for c in route_slug)
                route_slug = "-".join(route_slug.split())
                
                logger.info(f"Processing route {route_name} ({route_id})")
                
                # Get trips for this route
                trips = self.feed.trips[self.feed.trips['route_id'] == route_id]
                
                if trips.empty:
                    logger.warning(f"No trips found for route {route_name}")
                    continue
                
                # Get stop times for these trips
                stop_times = self.feed.stop_times[self.feed.stop_times['trip_id'].isin(trips['trip_id'])]
                
                if stop_times.empty:
                    logger.warning(f"No stop times found for route {route_name}")
                    continue
                
                # Get all stops for this route, preserving order
                stops = []
                seen_stops = set()
                
                # Group by trip_id and process each trip's stop sequence
                for trip_id, trip_stops in stop_times.groupby('trip_id'):
                    # Sort by stop_sequence
                    trip_stops = trip_stops.sort_values('stop_sequence')
                    
                    # Add stops to our list if not already present
                    for _, stop_time in trip_stops.iterrows():
                        stop_id = stop_time['stop_id']
                        if stop_id not in seen_stops:
                            # Get stop details
                            stop = self.feed.stops.loc[stop_id]
                            stops.append({
                                'stop_id': stop_id,
                                'stop_name': stop['stop_name'],
                                'stop_sequence': stop_time['stop_sequence'],
                                'lat': stop['stop_lat'],
                                'lon': stop['stop_lon']
                            })
                            seen_stops.add(stop_id)
                
                # Sort stops by sequence number
                stops.sort(key=lambda x: x['stop_sequence'])
                
                md_content.extend([
                    f"## <a id=\"{route_slug}\"></a>{route_name} - {route_long_name}\n",
                    f"- **Line**: {route_name}  ",
                    f"- **Type**: {type_info['title']}  ",
                    f"- **Total Stops**: {len(stops)}\n",
                    "### Stops\n"
                ])
                
                # Add stops in order
                for i, stop in enumerate(stops, 1):
                    md_content.append(f"{i}. **{stop['stop_name']}** (ID: {stop['stop_id']})  ")
                    md_content.append(f"   - Coordinates: {stop['lat']:.6f}, {stop['lon']:.6f}\n")
                
                md_content.append("\n")  # Add extra newline between routes
            
            # Write to file
            output_file = self.data_dir / type_info['filename']
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write("\n".join(md_content))
            
            logger.info(f"Wrote {len(routes)} {type_info['name']} routes to {output_file}")
    
    def process_stations(self):
        """Process stations and generate markdown files."""
        if self.feed is None:
            self.load_feed()
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Group stops by type
        stops_by_type = {}
        
        # Get all stops with their parent stations
        stops = self.feed.stops.copy()
        stops = stops[stops['location_type'] == 0]  # Only physical stops, not stations
        
        # Add route types to stops
        stop_routes = self.feed.stop_times.merge(
            self.feed.trips[['trip_id', 'route_id']], 
            on='trip_id'
        ).merge(
            self.feed.routes[['route_id', 'route_type']], 
            on='route_id'
        )
        
        stop_route_types = stop_routes.groupby('stop_id')['route_type'].unique()
        stops['route_types'] = stops['stop_id'].map(stop_route_types)
        
        # Categorize stops by their primary route type
        for stop_id, stop in stops.iterrows():
            if pd.isna(stop['route_types']).all():
                route_types = [3]  # Default to bus if no route type
            else:
                route_types = [rt for rt in stop['route_types'] if not pd.isna(rt)]
            
            # Use the most specific route type (prefer tram/metro over bus)
            if 0 in route_types:  # Tram
                route_type = 0
            elif 1 in route_types:  # Metro
                route_type = 1
            elif 7 in route_types:  # Funicular
                route_type = 7
            else:  # Default to bus
                route_type = 3
            
            if route_type not in stops_by_type:
                stops_by_type[route_type] = []
            
            stops_by_type[route_type].append(stop)
        
        # Generate markdown for each stop type
        for route_type, type_stops in stops_by_type.items():
            if route_type not in ROUTE_TYPES:
                logger.warning(f"Skipping unknown route type: {route_type}")
                continue
                
            type_info = ROUTE_TYPES[route_type]
            logger.info(f"Processing {len(type_stops)} {type_info['name']} stops...")
            
            # Sort stops by name
            type_stops_sorted = sorted(type_stops, key=lambda x: x['stop_name'])
            
            # Generate markdown
            md_content = [
                f"# Vienna {type_info['title']} Stations",
                f"\n*Generated from official Wiener Linien GTFS data*  *Last updated: {timestamp}*\n",
                f"List of all {type_info['name']} stations in Vienna.\n",
                "## Stations\n"
            ]
            
            for stop in type_stops_sorted:
                md_content.append(f"- **{stop['stop_name']}** (ID: {stop.name})  ")
                md_content.append(f"  - Location: {stop['stop_lat']:.6f}, {stop['stop_lon']:.6f}  ")
                
                # Add wheelchair accessibility info if available
                if 'wheelchair_boarding' in stop and not pd.isna(stop['wheelchair_boarding']):
                    accessibility = {
                        '0': 'No information',
                        '1': 'Partially accessible',
                        '2': 'Accessible'
                    }.get(str(int(stop['wheelchair_boarding'])), 'Unknown')
                    md_content.append(f"  - Wheelchair: {accessibility}  ")
                
                md_content.append("\n")
            
            # Write to file
            output_file = self.data_dir / type_info['station_file']
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write("\n".join(md_content))
            
            logger.info(f"Wrote {len(type_stops)} {type_info['name']} stations to {output_file}")

def main():
    """Main function to process GTFS data."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Process GTFS data for Wiener Linien')
    parser.add_argument('--gtfs', type=str, default='gtfs_data/gtfs.zip',
                        help='Path to GTFS zip file')
    parser.add_argument('--output', type=str, default='../frontend/data',
                        help='Output directory for markdown files')
    
    args = parser.parse_args()
    
    try:
        processor = GTFSProcessor(args.output, args.gtfs)
        processor.load_feed()
        processor.process_routes()
        processor.process_stations()
        logger.info("GTFS processing completed successfully")
    except Exception as e:
        logger.error(f"Error processing GTFS data: {e}", exc_info=True)
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
