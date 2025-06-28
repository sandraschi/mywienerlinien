"""
GTFS Markdown Generator

This script processes GTFS data and generates markdown documentation for:
- Lines (grouped by transport type)
- Routes (with detailed stop sequences)
- Stops/Stations (with connections and facilities)

Features:
- Comprehensive error handling
- Detailed logging
- Configurable output
- Support for all GTFS transport types
"""

import os
import sys
import logging
import argparse
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any, Set
from sqlalchemy import inspect

import pygtfs
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, text, exc as sa_exc

# Configure logger
logger = logging.getLogger('gtfs_markdown_generator')

class GTFSMarkdownGenerator:
    """Generate markdown documentation from GTFS data."""
    
    def __init__(self, db_path: str, output_dir: str):
        """Initialize the GTFS markdown generator.
        
        Args:
            db_path: Path to the SQLite database with GTFS data
            output_dir: Directory to save generated markdown files
        """
        self.db_path = Path(db_path).resolve()
        self.output_dir = Path(output_dir).resolve()
        self.schedule = None
        self.session = None
        
        # Transport type mappings
        self.route_types = {
            '0': {'name': 'Tram', 'filename': 'tram_lines.md', 'icon': '🚊'},
            '1': {'name': 'Metro', 'filename': 'metro_lines.md', 'icon': '🚇'},
            '2': {'name': 'Rail', 'filename': 'rail_lines.md', 'icon': '🚆'},
            '3': {'name': 'Bus', 'filename': 'bus_lines.md', 'icon': '🚌'},
            '4': {'name': 'Ferry', 'filename': 'ferry_lines.md', 'icon': '⛴️'},
            '5': {'name': 'Cable Car', 'filename': 'cable_car_lines.md', 'icon': '🚡'},
            '6': {'name': 'Gondola', 'filename': 'gondola_lines.md', 'icon': '🚠'},
            '7': {'name': 'Funicular', 'filename': 'funicular_lines.md', 'icon': '🚞'},
        }
        
        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize database connection
        self._init_database()
    
    def _init_database(self) -> None:
        """Initialize database connection and verify schema."""
        try:
            db_url = f'sqlite:///{self.db_path}'
            logger.info(f"Connecting to database: {db_url}")
            
            # Verify database exists and is accessible
            if not self.db_path.exists():
                raise FileNotFoundError(f"Database file not found: {self.db_path}")
                
            # Initialize GTFS schedule with the database URL string
            self.schedule = pygtfs.Schedule(db_url)
            
            # Create a separate engine for our session
            engine = create_engine(
                db_url,
                pool_pre_ping=True,
                connect_args={"timeout": 30, "check_same_thread": False}
            )
            
            # Test connection
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            
            # Initialize session
            self.Session = sessionmaker(bind=engine)
            self.session = self.Session()
            
            logger.info("Successfully connected to GTFS database")
            
        except sa_exc.SQLAlchemyError as e:
            logger.error(f"Database connection error: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    def generate_all(self, stops_only: bool = False) -> None:
        """Generate markdown files.
        
        Args:
            stops_only: If True, only generate stop/station documents and skip route generation
        """
        try:
            logger.info("Starting markdown generation")
            
            if stops_only:
                logger.info("Skipping route generation (--stops-only flag set)")
                # We still need routes for stop documents, but we won't generate route files
                routes_by_type = self._get_routes_by_type()
                self._generate_stop_documents()
            else:
                # Generate files for each transport type
                routes_by_type = self._get_routes_by_type()
                
                # Generate line overview files
                self._generate_line_overviews(routes_by_type)
                
                # Generate route detail files
                self._generate_route_details(routes_by_type)
                
                # Generate stop/station files
                self._generate_stop_documents()
            
            logger.info("Markdown generation completed successfully")
            
        except Exception as e:
            logger.error(f"Error during markdown generation: {e}", exc_info=True)
            raise
    
    def _get_routes_by_type(self) -> Dict[str, List[Any]]:
        """Get all routes grouped by route type."""
        routes_by_type = {}
        try:
            logger.info("Querying database for routes...")
            all_routes = self.session.query(pygtfs.gtfs_entities.Route).all()
            logger.info(f"Found {len(all_routes)} total routes in the database")
            
            if not all_routes:
                logger.warning("No routes found in the database!")
                # Try to list all tables to debug
                try:
                    inspector = inspect(self.session.get_bind())
                    tables = inspector.get_table_names()
                    logger.info(f"Available tables in database: {tables}")
                except Exception as e:
                    logger.error(f"Could not list tables: {e}")
                return {}
            
            for route in all_routes:
                route_type = str(route.route_type)
                if route_type not in routes_by_type:
                    routes_by_type[route_type] = []
                routes_by_type[route_type].append(route)
                
            logger.info(f"Routes by type: { {k: len(v) for k, v in routes_by_type.items()} }")
            return routes_by_type
            
        except Exception as e:
            logger.error(f"Error getting routes by type: {e}", exc_info=True)
            return {}
    
    def _generate_line_overviews(self, routes_by_type: Dict[str, List[Any]]) -> None:
        """Generate markdown files with line overviews by transport type."""
        try:
            for route_type, routes in routes_by_type.items():
                type_info = self.route_types.get(route_type, {
                    'name': f'Type {route_type}',
                    'filename': f'type_{route_type}_lines.md',
                    'icon': '🚋'
                })
                
                output_file = self.output_dir / type_info['filename']
                icon = type_info.get('icon', '🚋')
                
                content = [
                    f"# {icon} {type_info['name']} Lines",
                    f"\n*Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n",
                    "## Overview\n"
                ]
                
                # Group routes by their short name (line number)
                lines = {}
                for route in routes:
                    if route.route_short_name not in lines:
                        lines[route.route_short_name] = []
                    lines[route.route_short_name].append(route)
                
                # Add each line with its variants
                for line_num, line_routes in sorted(lines.items()):
                    if not line_num:
                        continue
                        
                    # Get a representative route for basic info
                    route = line_routes[0]
                    content.append(f"### {icon} Line {line_num}: {route.route_long_name}")
                    
                    # Add variants (different directions/termini)
                    if len(line_routes) > 1:
                        content.append("#### Variants:")
                        for variant in line_routes:
                            content.append(f"- {variant.trips[0].trip_headsign if variant.trips else 'Unknown'}")
                    
                    # Add basic info
                    content.extend([
                        "\n**Details:**",
                        f"- **Type**: {type_info['name']}",
                        f"- **Agency**: {getattr(route.agency, 'agency_name', 'Unknown')}",
                        f"- **Color**: `#{route.route_color}`" if hasattr(route, 'route_color') and route.route_color else "",
                        ""
                    ])
                
                # Write to file
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(filter(None, content)))
                
                logger.info(f"Generated line overview: {output_file}")
                
        except Exception as e:
            logger.error(f"Error generating line overviews: {e}", exc_info=True)
            raise
    
    def _generate_route_details(self, routes_by_type: Dict[str, List[Any]]) -> None:
        """Generate detailed markdown files for each route."""
        try:
            routes_dir = self.output_dir / 'routes'
            routes_dir.mkdir(exist_ok=True)
            
            for route_type, routes in routes_by_type.items():
                type_info = self.route_types.get(route_type, {'name': f'Type {route_type}'})
                
                for route in routes:
                    if not route.route_short_name:
                        continue
                        
                    try:
                        # Get all trips for this route
                        trips = self.session.query(pygtfs.gtfs_entities.Trip).filter_by(
                            route_id=route.route_id
                        ).all()
                        
                        if not trips:
                            logger.warning(f"No trips found for route {route.route_short_name}")
                            continue
                        
                        # Get stop sequence from first trip
                        stop_times = self.session.query(pygtfs.gtfs_entities.StopTime).filter_by(
                            trip_id=trips[0].trip_id
                        ).order_by(
                            pygtfs.gtfs_entities.StopTime.stop_sequence
                        ).all()
                        
                        # Generate content
                        content = [
                            f"# {type_info.get('icon', '🚋')} Line {route.route_short_name}: {route.route_long_name}",
                            f"\n*Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n",
                            f"**Type:** {type_info['name']}",
                            f"**Agency:** {getattr(route.agency, 'agency_name', 'Unknown')}",
                            f"**Description:** {getattr(route, 'route_desc', '')}",
                            f"**URL:** {getattr(route, 'route_url', '')}",
                            f"**Color:** `#{route.route_color}`" if hasattr(route, 'route_color') and route.route_color else "",
                            "\n## Stops\n"
                        ]
                        
                        # Add stop sequence
                        for i, stop_time in enumerate(stop_times, 1):
                            stop = stop_time.stop
                            content.append(f"{i}. **{stop.stop_name}**")
                            if hasattr(stop, 'platform_code') and stop.platform_code:
                                content[-1] += f" (Platform {stop.platform_code})"
                            content[-1] += f" - `{stop.stop_id}`"
                            
                            # Add transfer info
                            transfers = self.session.query(pygtfs.gtfs_entities.Transfer).filter_by(
                                from_stop_id=stop.stop_id
                            ).all()
                            
                            if transfers:
                                transfer_lines = []
                                for t in transfers:
                                    to_stop = self.session.query(pygtfs.gtfs_entities.Stop).get(t.to_stop_id)
                                    if to_stop:
                                        transfer_lines.append(f"  - Transfer to {to_stop.stop_name} (Walk: {t.min_transfer_time}s)")
                                
                                if transfer_lines:
                                    content.extend(transfer_lines)
                        
                        # Write to file
                        safe_name = ''.join(c if c.isalnum() else '_' for c in route.route_short_name)
                        output_file = routes_dir / f"{safe_name}_{route.route_id}.md"
                        
                        with open(output_file, 'w', encoding='utf-8') as f:
                            f.write('\n'.join(filter(None, content)))
                        
                        logger.debug(f"Generated route details: {output_file}")
                        
                    except Exception as e:
                        logger.error(f"Error processing route {route.route_short_name}: {e}", exc_info=True)
                        continue
            
            logger.info(f"Generated route details in {routes_dir}")
            
        except Exception as e:
            logger.error(f"Error generating route details: {e}", exc_info=True)
            raise
    
    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize a string to be used as a valid Windows filename.
        
        Args:
            filename: The input filename to sanitize
            
        Returns:
            A sanitized filename with invalid characters replaced
        """
        # Replace invalid Windows filename characters with underscores
        invalid_chars = '<>:"/\\|?*\0\t\n\r'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
            
        # Remove leading/trailing spaces and dots
        filename = filename.strip(' .')
        
        # Ensure filename is not empty
        if not filename:
            filename = 'unnamed_stop'
            
        # Truncate if too long (Windows max path is 260, leave room for path and extension)
        max_length = 100
        if len(filename) > max_length:
            filename = filename[:max_length].rstrip('_') + '_truncated'
            
        return filename
    
    def _generate_stop_documents(self) -> None:
        """Generate markdown files for each stop/station."""
        try:
            stops_dir = self.output_dir / 'stops'
            stops_dir.mkdir(exist_ok=True)
            
            logger.info("Generating stop/station documents...")
            
            # Get all stops that are parent stations or have no parent (platforms)
            stops = self.session.query(pygtfs.gtfs_entities.Stop).filter(
                (pygtfs.gtfs_entities.Stop.location_type == 1) |  # Parent stations
                (pygtfs.gtfs_entities.Stop.parent_station == None)  # No parent
            ).all()
            
            logger.info(f"Found {len(stops)} stops/stations to process")
            
            for stop in stops:
                try:
                    # Get all child stops (platforms)
                    child_stops = self.session.query(pygtfs.gtfs_entities.Stop).filter_by(
                        parent_station=stop.stop_id
                    ).all()
                    
                    # Get all routes serving this stop
                    routes = set()
                    for child in [stop] + child_stops:
                        stop_times = self.session.query(pygtfs.gtfs_entities.StopTime).filter_by(
                            stop_id=child.stop_id
                        ).all()
                        
                        for st in stop_times:
                            try:
                                # Get feed_id from stop_time or use default
                                feed_id = getattr(st, 'feed_id', None) or getattr(self, 'feed_id', None)
                                
                                if feed_id is not None:
                                    # Use composite key (feed_id, trip_id)
                                    trip = self.session.query(pygtfs.gtfs_entities.Trip).get((feed_id, st.trip_id))
                                else:
                                    # Fallback to just trip_id (may not work for all GTFS feeds)
                                    trip = self.session.query(pygtfs.gtfs_entities.Trip).filter_by(
                                        trip_id=st.trip_id
                                    ).first()
                                
                                if trip and hasattr(trip, 'route') and trip.route:
                                    routes.add((
                                        trip.route.route_short_name, 
                                        trip.route.route_type, 
                                        trip.route.route_long_name
                                    ))
                            except Exception as e:
                                logger.warning(f"Error processing trip {st.trip_id} for stop {child.stop_id}: {e}")
                                continue
                    
                    # Generate content
                    content = [
                        f"# 🚉 {stop.stop_name}",
                        f"\n*Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n",
                        f"**Stop ID:** `{stop.stop_id}`",
                        f"**Location:** {stop.stop_lat:.6f}, {stop.stop_lon:.6f}",
                        f"**Wheelchair Accessible:** {getattr(stop, 'wheelchair_boarding', 'Unknown')}",
                        f"**Zone ID:** {getattr(stop, 'zone_id', 'N/A')}",
                        "\n## Connections\n"
                    ]
                    
                    # Add routes
                    if routes:
                        content.append("### Lines Serving This Station:")
                        for route_num, route_type, route_name in sorted(routes):
                            if route_num:
                                type_info = self.route_types.get(str(route_type), {'name': f'Type {route_type}', 'icon': '🚋'})
                                content.append(f"- {type_info.get('icon', '🚋')} **{route_num}**: {route_name} ({type_info['name']})")
                    
                    # Add child stops (platforms)
                    if child_stops:
                        content.append("\n## Platforms\n")
                        for child in sorted(child_stops, key=lambda x: x.platform_code or ''):
                            content.append(f"### Platform {getattr(child, 'platform_code', '?')}")
                            content.append(f"- **ID:** `{child.stop_id}`")
                            if child.stop_desc:
                                content.append(f"- **Description:** {child.stop_desc}")
                            content.append("")
                    
                    # Write to file with sanitized filename
                    safe_name = self._sanitize_filename(stop.stop_name)
                    output_file = stops_dir / f"{safe_name}_{stop.stop_id}.md"
                    
                    with open(output_file, 'w', encoding='utf-8') as f:
                        f.write('\n'.join(filter(None, content)))
                    
                    logger.debug(f"Generated stop details: {output_file}")
                    
                except Exception as e:
                    logger.error(f"Error processing stop {stop.stop_name}: {e}", exc_info=True)
                    continue
            
            logger.info(f"Generated stop details in {stops_dir}")
            
        except Exception as e:
            logger.error(f"Error generating stop documents: {e}", exc_info=True)
            raise

def setup_logging(log_level: str = 'INFO') -> None:
    """Set up logging configuration with standardized log location."""
    # Create logs directory if it doesn't exist
    logs_dir = Path(r'D:\Dev\repos\mywienerlinien\.windsurf\logs')
    logs_dir.mkdir(parents=True, exist_ok=True)
    
    # Set up log file path with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = logs_dir / f'gtfs_markdown_generator_{timestamp}.log'
    
    # Configure logging
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    formatter = logging.Formatter(log_format)
    
    # Clear any existing handlers
    logging.getLogger().handlers.clear()
    
    # Create handlers
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setFormatter(formatter)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    
    logger.info(f"Logging initialized. Log file: {log_file}")

def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Generate markdown documentation from GTFS data.')
    parser.add_argument(
        '--db', 
        type=str, 
        default='gtfs.sqlite',
        help='Path to SQLite database with GTFS data (default: gtfs.sqlite)'
    )
    parser.add_argument(
        '--output', 
        type=str, 
        default='output',
        help='Output directory for markdown files (default: output/)'
    )
    parser.add_argument(
        '--log-level', 
        type=str, 
        default='INFO',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        help='Logging level (default: INFO)'
    )
    parser.add_argument(
        '--stops-only',
        action='store_true',
        help='Only generate stop/station documents, skip route generation'
    )
    return parser.parse_args()

def main() -> None:
    """Main entry point."""
    try:
        args = parse_args()
        setup_logging(args.log_level)
        
        logger.info("Starting GTFS Markdown Generator")
        logger.info(f"Database: {args.db}")
        logger.info(f"Output directory: {args.output}")
        logger.info(f"Stops only mode: {args.stops_only}")
        
        generator = GTFSMarkdownGenerator(args.db, args.output)
        generator.generate_all(stops_only=args.stops_only)
        
        logger.info("GTFS Markdown Generator completed successfully")
        return 0
        
    except Exception as e:
        logger.critical(f"Fatal error: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
