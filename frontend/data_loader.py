"""
Data Loader Module for Wiener Linien Live Map

This module provides functions to load and parse structured data files
containing information about lines, stations, routes, and disruptions.
"""

import os
import json
import re
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

@dataclass
class Station:
    """Represents a transport station/stop."""
    name: str
    rbl: str
    type: str
    zone: str
    lat: Optional[float] = None
    lng: Optional[float] = None

@dataclass
class Line:
    """Represents a transport line."""
    name: str
    type: str
    color: str
    length: str
    stations: int
    description: str
    frequency: str
    operating_hours: str

@dataclass
class Route:
    """Represents a transport route."""
    line: str
    type: str
    color: str
    length: str
    stations: int
    description: str
    coordinates: List[List[float]]
    stops: List[Dict[str, Any]]

@dataclass
class Disruption:
    """Represents a service disruption."""
    id: str
    line: str
    type: str
    severity: str
    description: str
    affected_stations: List[str]
    start_time: datetime
    end_time: Optional[datetime]
    status: str

class DataLoader:
    """Main data loader class for parsing structured data files."""
    
    def __init__(self, data_dir: str = "data"):
        """Initialize the data loader with the data directory path."""
        self.data_dir = data_dir
        self._lines_cache = None
        self._stations_cache = None
        self._routes_cache = None
        self._disruptions_cache = None
        self._last_loaded = {}
    
    def _get_file_path(self, filename: str) -> str:
        """Get the full path to a data file."""
        return os.path.join(self.data_dir, filename)
    
    def _read_file(self, filename: str) -> str:
        """Read a file and return its contents."""
        file_path = self._get_file_path(filename)
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            logger.error(f"Data file not found: {file_path}")
            return ""
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
            return ""
    
    def _parse_markdown_sections(self, content: str) -> List[Dict[str, Any]]:
        """Parse markdown content into structured sections."""
        sections = []
        current_section = {}
        current_lines = []
        
        for line in content.split('\n'):
            line = line.strip()
            
            # Check for section headers (## or ###)
            if line.startswith('## '):
                # Save previous section
                if current_section:
                    current_section['content'] = '\n'.join(current_lines)
                    sections.append(current_section)
                
                # Start new section
                current_section = {
                    'title': line[3:],
                    'level': 2,
                    'content': ''
                }
                current_lines = []
                
            elif line.startswith('### '):
                # Save previous section
                if current_section:
                    current_section['content'] = '\n'.join(current_lines)
                    sections.append(current_section)
                
                # Start new section
                current_section = {
                    'title': line[4:],
                    'level': 3,
                    'content': ''
                }
                current_lines = []
                
            else:
                current_lines.append(line)
        
        # Save last section
        if current_section:
            current_section['content'] = '\n'.join(current_lines)
            sections.append(current_section)
        
        return sections
    
    def _parse_line_data(self, content: str) -> List[Line]:
        """Parse line data from markdown content."""
        lines = []
        sections = self._parse_markdown_sections(content)
        
        for section in sections:
            if section['level'] == 3:  # Individual line sections
                line_data = self._extract_line_info(section)
                if line_data:
                    lines.append(line_data)
        
        return lines
    
    def _extract_line_info(self, section: Dict[str, Any]) -> Optional[Line]:
        """Extract line information from a section."""
        try:
            # Parse line name and type from title
            title_parts = section['title'].split(' - ')
            if len(title_parts) < 2:
                return None
            
            line_name = title_parts[0].strip()
            line_type = self._determine_line_type(line_name)
            
            # Extract properties from content
            content = section['content']
            properties = {}
            
            for line in content.split('\n'):
                if '**' in line:
                    key, value = self._parse_property_line(line)
                    if key and value:
                        properties[key] = value
            
            # Debug logging
            if line_name in ['U1', 'D', '7A', 'N25']:  # Log a few sample lines
                logger.debug(f"Line {line_name} properties: {properties}")
            
            return Line(
                name=line_name,
                type=line_type,
                color=properties.get('Color', '#000000'),
                length=properties.get('Length', '0 km'),
                stations=int(properties.get('Stations', '0')),
                description=properties.get('Description', ''),
                frequency=properties.get('Frequency', ''),
                operating_hours=properties.get('Operating Hours', '')
            )
            
        except Exception as e:
            logger.error(f"Error parsing line info: {e}")
            return None
    
    def _determine_line_type(self, line_name: str) -> str:
        """Determine the type of transport line based on its name."""
        if line_name.startswith('U'):
            return 'Metro'
        elif line_name.startswith('N'):
            return 'NightBus'
        elif line_name.isdigit() or line_name in ['D', 'O', '1', '2', '5', '6', '9', '10', '11', '18', '25', '26', '30', '31', '33', '37', '38', '40', '41', '42', '43', '44', '46', '49', '52', '60', '62', '67', '71']:
            return 'Tram'
        elif line_name.endswith('A'):
            return 'Bus'
        else:
            return 'Unknown'
    
    def _parse_property_line(self, line: str) -> tuple[Optional[str], Optional[str]]:
        """Parse a property line in the format '- **Key**: Value'."""
        match = re.match(r'-\s*\*\*([^*]+)\*\*:\s*(.+)', line)
        if match:
            return match.group(1).strip(), match.group(2).strip()
        return None, None
    
    def _parse_station_data(self, content: str) -> List[Station]:
        """Parse station data from markdown content."""
        stations = []
        sections = self._parse_markdown_sections(content)
        
        for section in sections:
            if section['level'] == 3:  # Individual station sections
                station_data = self._extract_station_info(section)
                if station_data:
                    stations.extend(station_data)
        
        return stations
    
    def _extract_station_info(self, section: Dict[str, Any]) -> List[Station]:
        """Extract station information from a section."""
        stations = []
        content = section['content']
        
        # Parse numbered station list
        for line in content.split('\n'):
            if line.strip() and re.match(r'^\d+\.', line):
                station = self._parse_station_line(line)
                if station:
                    stations.append(station)
        
        return stations
    
    def _parse_station_line(self, line: str) -> Optional[Station]:
        """Parse a station line in the format '1. **Name** - RBL: XXXX, Type: X, Zone: X'."""
        try:
            # Extract station name
            name_match = re.search(r'\*\*([^*]+)\*\*', line)
            if not name_match:
                return None
            
            name = name_match.group(1).strip()
            
            # Extract RBL
            rbl_match = re.search(r'RBL:\s*(\d+)', line)
            rbl = rbl_match.group(1) if rbl_match else ''
            
            # Extract type
            type_match = re.search(r'Type:\s*(\w+)', line)
            station_type = type_match.group(1) if type_match else 'Unknown'
            
            # Extract zone
            zone_match = re.search(r'Zone:\s*(\d+)', line)
            zone = zone_match.group(1) if zone_match else '100'
            
            return Station(
                name=name,
                rbl=rbl,
                type=station_type,
                zone=zone
            )
            
        except Exception as e:
            logger.error(f"Error parsing station line: {e}")
            return None
    
    def _parse_route_data(self, content: str) -> List[Route]:
        """Parse route data from markdown content."""
        routes = []
        sections = self._parse_markdown_sections(content)
        
        for section in sections:
            if section['level'] == 3:  # Individual route sections
                route_data = self._extract_route_info(section)
                if route_data:
                    routes.append(route_data)
        
        return routes
    
    def _extract_route_info(self, section: Dict[str, Any]) -> Optional[Route]:
        """Extract route information from a section."""
        try:
            # Parse route name and type from title
            title_parts = section['title'].split(' - ')
            if len(title_parts) < 2:
                return None
            
            route_name = title_parts[0].strip()
            route_type = self._determine_line_type(route_name)
            
            # Extract properties from content
            content = section['content']
            properties = {}
            coordinates = []
            stops = []
            
            in_coordinates = False
            in_stops = False
            
            for line in content.split('\n'):
                line = line.strip()
                
                if '**Coordinates**:' in line:
                    in_coordinates = True
                    in_stops = False
                    continue
                elif '**Stops**:' in line:
                    in_coordinates = False
                    in_stops = True
                    continue
                elif line.startswith('- **') and not in_coordinates and not in_stops:
                    key, value = self._parse_property_line(line)
                    if key and value:
                        properties[key] = value
                elif in_coordinates and line.startswith('['):
                    coords = self._parse_coordinate_line(line)
                    if coords:
                        coordinates.append(coords)
                elif in_stops and line.startswith('{'):
                    stop = self._parse_stop_line(line)
                    if stop:
                        stops.append(stop)
            
            return Route(
                line=route_name,
                type=route_type,
                color=properties.get('Color', '#000000'),
                length=properties.get('Length', '0 km'),
                stations=int(properties.get('Stations', '0')),
                description=properties.get('Description', ''),
                coordinates=coordinates,
                stops=stops
            )
            
        except Exception as e:
            logger.error(f"Error parsing route info: {e}")
            return None
    
    def _parse_coordinate_line(self, line: str) -> Optional[List[float]]:
        """Parse a coordinate line in the format '[lat, lng]'."""
        try:
            # Remove comments and extract coordinates
            line = re.sub(r'//.*$', '', line).strip()
            if line.startswith('[') and line.endswith(']'):
                coords_str = line[1:-1]
                coords = [float(x.strip()) for x in coords_str.split(',')]
                if len(coords) == 2:
                    return coords
        except Exception as e:
            logger.error(f"Error parsing coordinate line: {e}")
        return None
    
    def _parse_stop_line(self, line: str) -> Optional[Dict[str, Any]]:
        """Parse a stop line in JSON format."""
        try:
            # Remove trailing comma if present
            line = line.rstrip(',')
            return json.loads(line)
        except Exception as e:
            logger.error(f"Error parsing stop line: {e}")
        return None
    
    def load_lines(self, force_reload: bool = False) -> List[Line]:
        """Load all transport lines from the data file."""
        if not force_reload and self._lines_cache is not None:
            return self._lines_cache
        
        content = self._read_file('lines.md')
        if content:
            self._lines_cache = self._parse_line_data(content)
            self._last_loaded['lines'] = datetime.now()
            logger.info(f"Loaded {len(self._lines_cache)} lines")
        else:
            self._lines_cache = []
        
        return self._lines_cache
    
    def load_stations(self, force_reload: bool = False) -> List[Station]:
        """Load station data from markdown file."""
        if not force_reload and self._stations_cache is not None:
            return self._stations_cache
        
        try:
            content = self._read_file('stations.md')
            stations = self._parse_station_data(content)
            
            # Extract coordinates from routes file to populate station coordinates
            self._populate_station_coordinates(stations)
            
            self._stations_cache = stations
            logger.info(f"Loaded {len(stations)} stations")
            return stations
            
        except Exception as e:
            logger.error(f"Error loading stations: {e}")
            return []
    
    def _populate_station_coordinates(self, stations: List[Station]):
        """Populate station coordinates from routes data."""
        try:
            # Load routes to get coordinate data
            routes_content = self._read_file('routes.md')
            routes_sections = self._parse_markdown_sections(routes_content)
            
            # Create a mapping of station names to coordinates
            station_coords = {}
            
            for section in routes_sections:
                if section['level'] == 3:  # Individual route sections
                    content = section['content']
                    
                    # Extract stops data
                    for line in content.split('\n'):
                        if line.strip().startswith('{"name":'):
                            # Parse stop data
                            try:
                                # Simple JSON parsing for stop data
                                line = line.strip().rstrip(',')
                                if line.endswith(']'):
                                    continue
                                
                                # Extract name, lat, lng, rbl from the line
                                name_match = re.search(r'"name":\s*"([^"]+)"', line)
                                lat_match = re.search(r'"lat":\s*([\d.]+)', line)
                                lng_match = re.search(r'"lng":\s*([\d.]+)', line)
                                rbl_match = re.search(r'"rbl":\s*(\d+)', line)
                                
                                if name_match and lat_match and lng_match:
                                    name = name_match.group(1)
                                    lat = float(lat_match.group(1))
                                    lng = float(lng_match.group(1))
                                    rbl = rbl_match.group(1) if rbl_match else ''
                                    
                                    station_coords[name] = {
                                        'lat': lat,
                                        'lng': lng,
                                        'rbl': rbl
                                    }
                            except Exception as e:
                                logger.debug(f"Error parsing stop line: {e}")
                                continue
            
            # Update stations with coordinates
            for station in stations:
                if station.name in station_coords:
                    coords = station_coords[station.name]
                    station.lat = coords['lat']
                    station.lng = coords['lng']
                    # Update RBL if not set
                    if not station.rbl and coords['rbl']:
                        station.rbl = coords['rbl']
                else:
                    # Set approximate coordinates based on station type and name
                    station.lat, station.lng = self._get_approximate_coordinates(station)
            
            logger.info(f"Populated coordinates for {len(stations)} stations")
            
        except Exception as e:
            logger.error(f"Error populating station coordinates: {e}")
    
    def _get_approximate_coordinates(self, station: Station) -> tuple[float, float]:
        """Get approximate coordinates for stations without exact data."""
        # Vienna center coordinates
        vienna_center = (48.2082, 16.3738)
        
        # Add some variation based on station name to avoid overlapping
        import hashlib
        name_hash = hashlib.md5(station.name.encode()).hexdigest()
        
        # Use hash to generate small offsets
        lat_offset = (int(name_hash[:8], 16) % 1000 - 500) / 10000.0
        lng_offset = (int(name_hash[8:16], 16) % 1000 - 500) / 10000.0
        
        return (vienna_center[0] + lat_offset, vienna_center[1] + lng_offset)
    
    def load_routes(self, force_reload: bool = False) -> List[Route]:
        """Load all routes from the data file."""
        if not force_reload and self._routes_cache is not None:
            return self._routes_cache
        
        content = self._read_file('routes.md')
        if content:
            self._routes_cache = self._parse_route_data(content)
            self._last_loaded['routes'] = datetime.now()
            logger.info(f"Loaded {len(self._routes_cache)} routes")
        else:
            self._routes_cache = []
        
        return self._routes_cache
    
    def get_line_by_name(self, line_name: str) -> Optional[Line]:
        """Get a specific line by name."""
        lines = self.load_lines()
        for line in lines:
            if line.name == line_name:
                return line
        return None
    
    def get_station_by_rbl(self, rbl: str) -> Optional[Station]:
        """Get a specific station by RBL number."""
        stations = self.load_stations()
        for station in stations:
            if station.rbl == rbl:
                return station
        return None
    
    def get_route_by_line(self, line_name: str) -> Optional[Route]:
        """Get a specific route by line name."""
        routes = self.load_routes()
        for route in routes:
            if route.line == line_name:
                return route
        return None
    
    def get_lines_by_type(self, line_type: str) -> List[Line]:
        """Get all lines of a specific type."""
        lines = self.load_lines()
        return [line for line in lines if line.type.lower() == line_type.lower()]
    
    def get_stations_by_type(self, station_type: str) -> List[Station]:
        """Get all stations of a specific type."""
        stations = self.load_stations()
        return [station for station in stations if station.type.lower() == station_type.lower()]
    
    def clear_cache(self):
        """Clear all cached data."""
        self._lines_cache = None
        self._stations_cache = None
        self._routes_cache = None
        self._disruptions_cache = None
        self._last_loaded = {}
        logger.info("Data cache cleared")
    
    def get_cache_status(self) -> Dict[str, Any]:
        """Get the status of cached data."""
        return {
            'lines_loaded': self._lines_cache is not None,
            'stations_loaded': self._stations_cache is not None,
            'routes_loaded': self._routes_cache is not None,
            'disruptions_loaded': self._disruptions_cache is not None,
            'last_loaded': self._last_loaded
        }

# Global data loader instance
data_loader = DataLoader() 