"""
Extract station data from GTFS SQLite database and generate markdown files.
"""

import sqlite3
import logging
from pathlib import Path
from typing import Dict, List
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger('gtfs_stations')


def get_db_connection(db_path: Path):
    """Create a database connection to the SQLite database."""
    try:
        conn = sqlite3.connect(f'file:{db_path}?mode=ro', uri=True)
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        logger.error("Error connecting to database: %s", e)
        sys.exit(1)


def get_stations(conn) -> List[Dict]:
    """Retrieve all stations from the database."""
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM stops
            WHERE location_type = 1 OR parent_station IS NULL OR parent_station = ''
            ORDER BY stop_name
        """)
        stations = [dict(row) for row in cursor.fetchall()]
        logger.info("Found %d stations", len(stations))
        return stations
    except sqlite3.Error as e:
        logger.error("Error fetching stations: %s", e)
        return []


def get_routes_for_stop(conn, stop_id: str) -> List[Dict]:
    """Get all routes that serve a given stop."""
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT DISTINCT r.route_id, r.route_short_name,
                   r.route_long_name, r.route_type
            FROM routes r
            JOIN trips t ON r.route_id = t.route_id
            JOIN stop_times st ON t.trip_id = st.trip_id
            WHERE st.stop_id = ?
            ORDER BY r.route_short_name, r.route_long_name
        """, (stop_id,))
        return [dict(row) for row in cursor.fetchall()]
    except sqlite3.Error as e:
        logger.error("Error fetching routes for stop %s: %s", stop_id, e)
        return []


def generate_station_markdown(station: Dict, routes: List[Dict]) -> str:
    """Generate markdown content for a station."""
    lines = [f"# 🚉 {station['stop_name']}", ""]

    # Add basic info
    if station.get('stop_desc'):
        lines.append(f"*{station['stop_desc']}*")

    lines.append(f"\n**Stop ID:** {station['stop_id']}")

    if station.get('stop_code'):
        lines.append(f"\n**Code:** {station['stop_code']}")

    if station.get('zone_id'):
        lines.append(f"\n**Zone:** {station['zone_id']}")

    if 'stop_lat' in station and 'stop_lon' in station:
        lat, lon = station['stop_lat'], station['stop_lon']
        lines.append(f"\n**Location:** {lat}, {lon}")
        lines.append(f"\n[Open in Google Maps](https://www.google.com/maps?q={lat},{lon})")

    # Add routes
    if routes:
        lines.append("\n## 🚆 Served by Routes")
        route_types = {
            0: '🚊 Tram',
            1: '🚇 Metro',
            2: '🚆 Rail',
            3: '🚌 Bus',
            4: '⛴️ Ferry',
            5: '🚋 Tram',
            6: '🚠 Gondola',
            7: '🚞 Funicular'
        }

        routes_by_type = {}
        for route in routes:
            route_type = route.get('route_type', 3)  # Default to Bus
            if route_type not in routes_by_type:
                routes_by_type[route_type] = []
            routes_by_type[route_type].append(route)

        for route_type in sorted(routes_by_type.keys()):
            type_name = route_types.get(route_type, f'Type {route_type}')
            lines.append(f"\n### {type_name}")
            for route in sorted(routes_by_type[route_type],
                             key=lambda x: (x.get('route_short_name', ''),
                                         x.get('route_long_name', ''))):
                name = (route.get('route_short_name') or
                       route.get('route_long_name', 'Unnamed Route'))
                lines.append(f"- {name}")

    return '\n'.join(lines)


def main():
    """Main function to generate station markdown files."""
    # Paths
    base_dir = Path(__file__).parent.parent
    db_path = base_dir / 'gtfs_data' / 'gtfs.sqlite'
    output_dir = base_dir / 'docs' / 'gtfs' / 'stops'

    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    # Connect to database
    logger.info("Connecting to database: %s", db_path)
    conn = get_db_connection(db_path)

    try:
        # Get all stations
        stations = get_stations(conn)

        if not stations:
            logger.error("No stations found in the database")
            return

        # Process each station
        for i, station in enumerate(stations, 1):
            stop_id = station['stop_id']
            stop_name = station.get('stop_name', f'stop_{stop_id}')

            # Sanitize filename
            safe_name = "".join(
                c if c.isalnum() or c in ' _-' else '_' for c in stop_name
            )
            safe_name = safe_name[:100]  # Limit filename length
            output_file = output_dir / f"{safe_name}.md"

            # Get routes for this stop
            routes = get_routes_for_stop(conn, stop_id)

            # Generate markdown
            markdown = generate_station_markdown(station, routes)

            # Write to file
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(markdown)

            if i % 100 == 0 or i == len(stations):
                logger.info("Processed %d/%d stations", i, len(stations))

        logger.info(
            "Successfully generated %d station markdown files in %s",
            len(stations), output_dir
        )

    finally:
        conn.close()


if __name__ == "__main__":
    main()
