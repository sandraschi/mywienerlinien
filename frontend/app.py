"""
Wiener Linien Public Transport Map Display
-----------------------------------------
A Flask application that displays real-time vehicle positions for Vienna's public transport
using the official Wiener Linien API.

Note: As of 2024, no API key is required for the Wiener Linien API.
"""

import os
import json
import time
import logging
import requests
from typing import Dict, List, Optional, Tuple
from flask import Flask, render_template, jsonify, request
from flask_caching import Cache
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Configure cache - store API responses for 60 seconds to respect rate limits
cache = Cache(app, config={
    'CACHE_TYPE': 'SimpleCache',
    'CACHE_DEFAULT_TIMEOUT': 60
})

# Base URL for Wiener Linien API
API_BASE_URL = 'https://www.wienerlinien.at/ogd_realtime'

# Vienna center coordinates
VIENNA_CENTER = (48.2082, 16.3738)

# Vehicle types and their icons
VEHICLE_TYPES = {
    'ptBusCity': 'bus',
    'ptBusNight': 'bus', 
    'ptTram': 'tram',
    'ptTramWLB': 'tram',
    'ptMetro': 'metro',
    'ptTrainS': 'train'
}

# Known RBL numbers for Vienna stops (major stops)
VIENNA_RBL_STOPS = [
    '4011',  # Staatsoper
    '4025',  # Hauptbahnhof Ost
    '4009',  # Schottentor
    '3047',  # Westbahnhof
    '3043',  # Praterstern
    '3052',  # Kaiserstraße/Westbahnstraße
    '1234',  # Flotowgasse
    '3047',  # Westbahnhof
    '3043',  # Praterstern
    '3052',  # Kaiserstraße/Westbahnstraße
    '4011',  # Staatsoper
    '4025',  # Hauptbahnhof Ost
    '4009',  # Schottentor
]

# Setup logging
def setup_logger():
    """Setup application logger following rulebook guidelines."""
    logger = logging.getLogger('wiener_linien')
    logger.setLevel(logging.INFO)
    
    # Prevent duplicate handlers
    if logger.handlers:
        return logger
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # File handler
    if not os.path.exists('logs'):
        os.makedirs('logs')
    file_handler = logging.FileHandler('logs/app.log')
    file_handler.setLevel(logging.INFO)
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
    
    return logger

logger = setup_logger()

@app.route('/')
def index():
    """Render the main map page."""
    try:
        return render_template('index.html')
    except Exception as e:
        logger.error("Error rendering index page: %s", str(e), exc_info=True)
        return "Error loading page", 500

def get_vehicle_type(wl_type: str) -> str:
    """Map Wiener Linien vehicle types to our simplified types."""
    return VEHICLE_TYPES.get(wl_type, 'unknown')

def validate_rbl_number(rbl: str) -> bool:
    """Validate RBL number format."""
    if not rbl or not rbl.isdigit():
        return False
    return True

def make_api_request(url: str, params: Dict = None, timeout: int = 10) -> Optional[requests.Response]:
    """Make a properly configured API request with error handling."""
    headers = {
        'User-Agent': 'WienerLinienMap/1.0 (https://github.com/your-repo)',
        'Accept': 'application/json'
    }
    
    try:
        logger.debug("Making API request to %s with params %s", url, params)
        response = requests.get(url, params=params, headers=headers, timeout=timeout)
        response.raise_for_status()
        return response
    except requests.exceptions.Timeout:
        logger.warning("API request timed out after %d seconds", timeout)
        return None
    except requests.exceptions.HTTPError as e:
        logger.error("HTTP error %d: %s", e.response.status_code, e.response.text)
        return None
    except requests.exceptions.ConnectionError:
        logger.error("Failed to connect to API server")
        return None
    except Exception as e:
        logger.error("Unexpected error in API request: %s", str(e), exc_info=True)
        return None

def parse_vehicle_data(monitor_data: Dict) -> List[Dict]:
    """Parse vehicle data from monitor response."""
    vehicles = []
    
    try:
        # Get stop coordinates
        stop_coords = monitor_data.get('locationStop', {}).get('geometry', {}).get('coordinates', [])
        if not stop_coords or len(stop_coords) < 2:
            logger.warning("Invalid stop coordinates in monitor data")
            return vehicles
        
        stop_lng, stop_lat = stop_coords[0], stop_coords[1]
        
        # Parse lines and departures
        lines = monitor_data.get('lines', [])
        for line in lines:
            line_name = line.get('name', 'Unknown')
            line_type = line.get('type', 'unknown')
            vehicle_type = get_vehicle_type(line_type)
            
            # Parse departures
            departures = line.get('departures', {}).get('departure', [])
            for departure in departures:
                try:
                    # Create vehicle object
                    vehicle = {
                        'id': f"{line_name}-{departure.get('departureTime', {}).get('countdown', 0)}",
                        'type': vehicle_type,
                        'line': line_name,
                        'lat': stop_lat,
                        'lng': stop_lng,
                        'heading': 0,  # Default heading
                        'speed': 0,    # Default speed
                        'timestamp': int(time.time()),
                        'towards': line.get('towards', 'Unknown'),
                        'countdown': departure.get('departureTime', {}).get('countdown', 0),
                        'platform': line.get('platform', 'Unknown')
                    }
                    vehicles.append(vehicle)
                except Exception as e:
                    logger.warning("Error parsing departure: %s", str(e))
                    continue
                    
    except Exception as e:
        logger.error("Error parsing vehicle data: %s", str(e), exc_info=True)
    
    return vehicles

def get_dummy_vehicles() -> List[Dict]:
    """Get dummy vehicles for demonstration purposes."""
    center_lat, center_lng = VIENNA_CENTER
    current_time = int(time.time())
    
    # Create realistic dummy vehicles around Vienna
    dummy_vehicles = [
        # U-Bahn vehicles
        {
            'id': 'dummy-u1-1',
            'type': 'metro',
            'line': 'U1',
            'lat': center_lat - 0.008,
            'lng': center_lng - 0.005,
            'heading': 45,
            'speed': 35,
            'timestamp': current_time,
            'towards': 'Leopoldau',
            'countdown': 2,
            'platform': '1'
        },
        {
            'id': 'dummy-u4-1',
            'type': 'metro',
            'line': 'U4',
            'lat': center_lat + 0.006,
            'lng': center_lng - 0.012,
            'heading': 180,
            'speed': 32,
            'timestamp': current_time,
            'towards': 'Heiligenstadt',
            'countdown': 5,
            'platform': '2'
        },
        {
            'id': 'dummy-u6-1',
            'type': 'metro',
            'line': 'U6',
            'lat': center_lat + 0.012,
            'lng': center_lng + 0.008,
            'heading': 90,
            'speed': 30,
            'timestamp': current_time,
            'towards': 'Siebenhirten',
            'countdown': 1,
            'platform': '1'
        },
        
        # Tram vehicles
        {
            'id': 'dummy-d-1',
            'type': 'tram',
            'line': 'D',
            'lat': center_lat + 0.004,
            'lng': center_lng + 0.007,
            'heading': 90,
            'speed': 18,
            'timestamp': current_time,
            'towards': 'Nußdorf',
            'countdown': 3,
            'platform': '1'
        },
        {
            'id': 'dummy-1-1',
            'type': 'tram',
            'line': '1',
            'lat': center_lat - 0.006,
            'lng': center_lng + 0.003,
            'heading': 270,
            'speed': 20,
            'timestamp': current_time,
            'towards': 'Prater',
            'countdown': 7,
            'platform': '2'
        },
        {
            'id': 'dummy-5-1',
            'type': 'tram',
            'line': '5',
            'lat': center_lat - 0.003,
            'lng': center_lng - 0.009,
            'heading': 135,
            'speed': 16,
            'timestamp': current_time,
            'towards': 'Westbahnhof',
            'countdown': 4,
            'platform': '1'
        },
        
        # Bus vehicles
        {
            'id': 'dummy-13a-1',
            'type': 'bus',
            'line': '13A',
            'lat': center_lat,
            'lng': center_lng + 0.01,
            'heading': 0,
            'speed': 22,
            'timestamp': current_time,
            'towards': 'Hütteldorf',
            'countdown': 6,
            'platform': 'A'
        },
        {
            'id': 'dummy-26a-1',
            'type': 'bus',
            'line': '26A',
            'lat': center_lat + 0.008,
            'lng': center_lng - 0.004,
            'heading': 315,
            'speed': 25,
            'timestamp': current_time,
            'towards': 'Kagran U',
            'countdown': 2,
            'platform': 'B'
        },
        {
            'id': 'dummy-35a-1',
            'type': 'bus',
            'line': '35A',
            'lat': center_lat - 0.005,
            'lng': center_lng - 0.008,
            'heading': 45,
            'speed': 19,
            'timestamp': current_time,
            'towards': 'Salmannsdorf',
            'countdown': 8,
            'platform': 'C'
        }
    ]
    
    return dummy_vehicles

@cache.cached(timeout=60)
@app.route('/api/vehicles')
def get_vehicles():
    """
    Fetch real-time vehicle positions from Wiener Linien API.
    
    This endpoint is cached for 60 seconds to comply with fair use policy.
    """
    try:
        # Get filter parameters
        vehicle_type = request.args.get('type')
        line_filter = request.args.get('line')
        station_filter = request.args.get('station')
        
        logger.info("Fetching vehicles: type=%s, line=%s, station=%s", vehicle_type, line_filter, station_filter)
        
        all_vehicles = []
        successful_requests = 0
        failed_requests = 0
        
        # Try to get real data first
        try:
            # Rotate through RBL stops to get comprehensive data
            for i, rbl in enumerate(VIENNA_RBL_STOPS[:3]):  # Limit to 3 stops to respect rate limits
                try:
                    # Make API request
                    url = f"{API_BASE_URL}/monitor"
                    params = {'rbl': rbl}
                    
                    response = make_api_request(url, params)
                    if not response:
                        failed_requests += 1
                        continue
                    
                    # Parse response
                    data = response.json()
                    if 'data' not in data or 'monitors' not in data['data']:
                        logger.warning("Invalid API response structure for RBL %s", rbl)
                        failed_requests += 1
                        continue
                    
                    # Parse vehicles from monitors
                    monitors = data['data']['monitors']
                    for monitor in monitors:
                        vehicles = parse_vehicle_data(monitor)
                        all_vehicles.extend(vehicles)
                    
                    successful_requests += 1
                    logger.debug("Successfully fetched data for RBL %s: %d vehicles", rbl, len(vehicles))
                    
                except Exception as e:
                    logger.error("Error processing RBL %s: %s", rbl, str(e))
                    failed_requests += 1
                    continue
        except Exception as e:
            logger.warning("Failed to fetch real data: %s", str(e))
        
        # If no real data, add dummy vehicles
        if not all_vehicles:
            logger.info("No real vehicles found, adding dummy vehicles")
            all_vehicles = get_dummy_vehicles()
        
        # Apply filters
        filtered_vehicles = all_vehicles
        
        if vehicle_type and vehicle_type != 'all':
            filtered_vehicles = [v for v in filtered_vehicles if v['type'] == vehicle_type]
        
        if line_filter:
            line_list = line_filter.split(',')
            filtered_vehicles = [v for v in filtered_vehicles if v['line'] in line_list]
        
        logger.info("Returning %d vehicles (successful requests: %d, failed: %d)", 
                   len(filtered_vehicles), successful_requests, failed_requests)
        
        return jsonify({
            'vehicles': filtered_vehicles,
            'total_vehicles': len(filtered_vehicles),
            'successful_requests': successful_requests,
            'failed_requests': failed_requests,
            'timestamp': int(time.time()),
            'has_dummy_data': len(all_vehicles) > 0 and successful_requests == 0
        })
        
    except Exception as e:
        logger.error("Unexpected error in get_vehicles: %s", str(e), exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/lines')
def get_lines():
    """Get all available lines with their types and colors."""
    try:
        # Define Vienna's major transport lines
        lines = [
            # U-Bahn (Metro) lines
            {'id': 'U1', 'name': 'U1', 'type': 'metro', 'color': '#FF0000', 'towards': 'Reumannplatz - Leopoldau'},
            {'id': 'U2', 'name': 'U2', 'type': 'metro', 'color': '#9B26B6', 'towards': 'Karlsplatz - Seestadt'},
            {'id': 'U3', 'name': 'U3', 'type': 'metro', 'color': '#FF8000', 'towards': 'Ottakring - Simmering'},
            {'id': 'U4', 'name': 'U4', 'type': 'metro', 'color': '#00FF00', 'towards': 'Hütteldorf - Heiligenstadt'},
            {'id': 'U6', 'name': 'U6', 'type': 'metro', 'color': '#8B4513', 'towards': 'Siebenhirten - Floridsdorf'},
            
            # Tram lines
            {'id': 'D', 'name': 'D', 'type': 'tram', 'color': '#FF0000', 'towards': 'Hauptbahnhof - Nußdorf'},
            {'id': '1', 'name': '1', 'type': 'tram', 'color': '#FF0000', 'towards': 'Stefan-Fadinger-Platz - Prater'},
            {'id': '2', 'name': '2', 'type': 'tram', 'color': '#FF0000', 'towards': 'Dornbach - Friedrich-Engels-Platz'},
            {'id': '5', 'name': '5', 'type': 'tram', 'color': '#FF0000', 'towards': 'Praterstern - Westbahnhof'},
            {'id': '6', 'name': '6', 'type': 'tram', 'color': '#FF0000', 'towards': 'Burggasse - Geiereckstraße'},
            {'id': '9', 'name': '9', 'type': 'tram', 'color': '#FF0000', 'towards': 'Gersthof - Westbahnhof'},
            {'id': '10', 'name': '10', 'type': 'tram', 'color': '#FF0000', 'towards': 'Dornbach - Hauptbahnhof'},
            {'id': '11', 'name': '11', 'type': 'tram', 'color': '#FF0000', 'towards': 'Kaiserebersdorf - Otto-Probst-Platz'},
            {'id': '18', 'name': '18', 'type': 'tram', 'color': '#FF0000', 'towards': 'Burggasse - Schlachthausgasse'},
            {'id': '25', 'name': '25', 'type': 'tram', 'color': '#FF0000', 'towards': 'Aspern - Floridsdorf'},
            {'id': '26', 'name': '26', 'type': 'tram', 'color': '#FF0000', 'towards': 'Hausfeldstraße - Strebersdorf'},
            {'id': '30', 'name': '30', 'type': 'tram', 'color': '#FF0000', 'towards': 'Floridsdorf - Stammersdorf'},
            {'id': '31', 'name': '31', 'type': 'tram', 'color': '#FF0000', 'towards': 'Schottenring - Stammersdorf'},
            {'id': '33', 'name': '33', 'type': 'tram', 'color': '#FF0000', 'towards': 'Josefstädter Straße - Friedrich-Engels-Platz'},
            {'id': '37', 'name': '37', 'type': 'tram', 'color': '#FF0000', 'towards': 'Hohe Warte - Schottentor'},
            {'id': '38', 'name': '38', 'type': 'tram', 'color': '#FF0000', 'towards': 'Grinzing - Schottentor'},
            {'id': '40', 'name': '40', 'type': 'tram', 'color': '#FF0000', 'towards': 'Gerichtsgasse - Schottentor'},
            {'id': '41', 'name': '41', 'type': 'tram', 'color': '#FF0000', 'towards': 'Pötzleinsdorf - Schottentor'},
            {'id': '42', 'name': '42', 'type': 'tram', 'color': '#FF0000', 'towards': 'Antonigasse - Schottentor'},
            {'id': '43', 'name': '43', 'type': 'tram', 'color': '#FF0000', 'towards': 'Neuwaldegg - Schottentor'},
            {'id': '44', 'name': '44', 'type': 'tram', 'color': '#FF0000', 'towards': 'Dornbach - Schottentor'},
            {'id': '46', 'name': '46', 'type': 'tram', 'color': '#FF0000', 'towards': 'Ring - Joachimsthalerplatz'},
            {'id': '49', 'name': '49', 'type': 'tram', 'color': '#FF0000', 'towards': 'Ring - Hütteldorf'},
            {'id': '52', 'name': '52', 'type': 'tram', 'color': '#FF0000', 'towards': 'Westbahnhof - Baumgarten'},
            {'id': '60', 'name': '60', 'type': 'tram', 'color': '#FF0000', 'towards': 'Raxstraße - Hietzing'},
            {'id': '62', 'name': '62', 'type': 'tram', 'color': '#FF0000', 'towards': 'Lainz - Meidling'},
            {'id': '67', 'name': '67', 'type': 'tram', 'color': '#FF0000', 'towards': 'Ottakring - Hütteldorf'},
            {'id': '71', 'name': '71', 'type': 'tram', 'color': '#FF0000', 'towards': 'Börsegasse - Kaiserebersdorf'},
            
            # Bus lines (major ones)
            {'id': '13A', 'name': '13A', 'type': 'bus', 'color': '#0000FF', 'towards': 'Alser Straße - Hütteldorf'},
            {'id': '14A', 'name': '14A', 'type': 'bus', 'color': '#0000FF', 'towards': 'Penzing - Hütteldorf'},
            {'id': '15A', 'name': '15A', 'type': 'bus', 'color': '#0000FF', 'towards': 'Ottakring - Hütteldorf'},
            {'id': '16A', 'name': '16A', 'type': 'bus', 'color': '#0000FF', 'towards': 'Ottakring - Hernals'},
            {'id': '17A', 'name': '17A', 'type': 'bus', 'color': '#0000FF', 'towards': 'Neulerchenfeld - Hernals'},
            {'id': '18A', 'name': '18A', 'type': 'bus', 'color': '#0000FF', 'towards': 'Burggasse - Hernals'},
            {'id': '19A', 'name': '19A', 'type': 'bus', 'color': '#0000FF', 'towards': 'Grinzing - Heiligenstadt'},
            {'id': '20A', 'name': '20A', 'type': 'bus', 'color': '#0000FF', 'towards': 'Heiligenstadt - Grinzing'},
            {'id': '21A', 'name': '21A', 'type': 'bus', 'color': '#0000FF', 'towards': 'Floridsdorf - Stammersdorf'},
            {'id': '22A', 'name': '22A', 'type': 'bus', 'color': '#0000FF', 'towards': 'Kagran - Aspern'},
            {'id': '23A', 'name': '23A', 'type': 'bus', 'color': '#0000FF', 'towards': 'Kagran - Essling'},
            {'id': '24A', 'name': '24A', 'type': 'bus', 'color': '#0000FF', 'towards': 'Kagran - Breitenlee'},
            {'id': '25A', 'name': '25A', 'type': 'bus', 'color': '#0000FF', 'towards': 'Kagran - Hirschstetten'},
            {'id': '26A', 'name': '26A', 'type': 'bus', 'color': '#0000FF', 'towards': 'Kagran - Aspern'},
            {'id': '27A', 'name': '27A', 'type': 'bus', 'color': '#0000FF', 'towards': 'Kagran - Essling'},
            {'id': '28A', 'name': '28A', 'type': 'bus', 'color': '#0000FF', 'towards': 'Kagran - Breitenlee'},
            {'id': '29A', 'name': '29A', 'type': 'bus', 'color': '#0000FF', 'towards': 'Kagran - Hirschstetten'},
            {'id': '30A', 'name': '30A', 'type': 'bus', 'color': '#0000FF', 'towards': 'Kagran - Aspern'},
            {'id': '31A', 'name': '31A', 'type': 'bus', 'color': '#0000FF', 'towards': 'Kagran - Essling'},
            {'id': '32A', 'name': '32A', 'type': 'bus', 'color': '#0000FF', 'towards': 'Kagran - Breitenlee'},
            {'id': '33A', 'name': '33A', 'type': 'bus', 'color': '#0000FF', 'towards': 'Kagran - Hirschstetten'},
            {'id': '34A', 'name': '34A', 'type': 'bus', 'color': '#0000FF', 'towards': 'Kagran - Aspern'},
            {'id': '35A', 'name': '35A', 'type': 'bus', 'color': '#0000FF', 'towards': 'Kagran - Essling'},
            {'id': '36A', 'name': '36A', 'type': 'bus', 'color': '#0000FF', 'towards': 'Kagran - Breitenlee'},
            {'id': '37A', 'name': '37A', 'type': 'bus', 'color': '#0000FF', 'towards': 'Kagran - Hirschstetten'},
            {'id': '38A', 'name': '38A', 'type': 'bus', 'color': '#0000FF', 'towards': 'Kagran - Aspern'},
            {'id': '39A', 'name': '39A', 'type': 'bus', 'color': '#0000FF', 'towards': 'Kagran - Essling'},
            {'id': '40A', 'name': '40A', 'type': 'bus', 'color': '#0000FF', 'towards': 'Kagran - Breitenlee'},
            {'id': '41A', 'name': '41A', 'type': 'bus', 'color': '#0000FF', 'towards': 'Kagran - Hirschstetten'},
            {'id': '42A', 'name': '42A', 'type': 'bus', 'color': '#0000FF', 'towards': 'Kagran - Aspern'},
            {'id': '43A', 'name': '43A', 'type': 'bus', 'color': '#0000FF', 'towards': 'Kagran - Essling'},
            {'id': '44A', 'name': '44A', 'type': 'bus', 'color': '#0000FF', 'towards': 'Kagran - Breitenlee'},
            {'id': '45A', 'name': '45A', 'type': 'bus', 'color': '#0000FF', 'towards': 'Kagran - Hirschstetten'},
            {'id': '46A', 'name': '46A', 'type': 'bus', 'color': '#0000FF', 'towards': 'Kagran - Aspern'},
            {'id': '47A', 'name': '47A', 'type': 'bus', 'color': '#0000FF', 'towards': 'Kagran - Essling'},
            {'id': '48A', 'name': '48A', 'type': 'bus', 'color': '#0000FF', 'towards': 'Kagran - Breitenlee'},
            {'id': '49A', 'name': '49A', 'type': 'bus', 'color': '#0000FF', 'towards': 'Kagran - Hirschstetten'},
            {'id': '50A', 'name': '50A', 'type': 'bus', 'color': '#0000FF', 'towards': 'Kagran - Aspern'},
        ]
        
        # Filter by type if specified
        vehicle_type = request.args.get('type')
        if vehicle_type and vehicle_type != 'all':
            lines = [line for line in lines if line['type'] == vehicle_type]
        
        logger.info("Returning %d lines", len(lines))
        return jsonify({'lines': lines})
        
    except Exception as e:
        logger.error("Error in get_lines: %s", str(e), exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/stops')
def get_stops():
    """Get all major stops in Vienna."""
    try:
        # Define major Vienna stops
        stops = [
            {'id': '4011', 'name': 'Staatsoper', 'lat': 48.2038, 'lng': 16.3697, 'type': 'metro'},
            {'id': '4025', 'name': 'Hauptbahnhof Ost', 'lat': 48.1858, 'lng': 16.3789, 'type': 'metro'},
            {'id': '4009', 'name': 'Schottentor', 'lat': 48.2167, 'lng': 16.3667, 'type': 'metro'},
            {'id': '3047', 'name': 'Westbahnhof', 'lat': 48.1967, 'lng': 16.3378, 'type': 'metro'},
            {'id': '3043', 'name': 'Praterstern', 'lat': 48.2189, 'lng': 16.3917, 'type': 'metro'},
            {'id': '3052', 'name': 'Kaiserstraße/Westbahnstraße', 'lat': 48.2017, 'lng': 16.3417, 'type': 'tram'},
            {'id': '1234', 'name': 'Flotowgasse', 'lat': 48.2406, 'lng': 16.3391, 'type': 'bus'},
            {'id': '4012', 'name': 'Stephansplatz', 'lat': 48.2085, 'lng': 16.3731, 'type': 'metro'},
            {'id': '4013', 'name': 'Karlsplatz', 'lat': 48.2008, 'lng': 16.3697, 'type': 'metro'},
            {'id': '4014', 'name': 'Museumsquartier', 'lat': 48.2038, 'lng': 16.3617, 'type': 'metro'},
            {'id': '4015', 'name': 'Volkstheater', 'lat': 48.2038, 'lng': 16.3617, 'type': 'metro'},
            {'id': '4016', 'name': 'Rathaus', 'lat': 48.2108, 'lng': 16.3567, 'type': 'metro'},
            {'id': '4017', 'name': 'Schottentor', 'lat': 48.2167, 'lng': 16.3667, 'type': 'metro'},
            {'id': '4018', 'name': 'Herrengasse', 'lat': 48.2108, 'lng': 16.3667, 'type': 'metro'},
            {'id': '4019', 'name': 'Stephansplatz', 'lat': 48.2085, 'lng': 16.3731, 'type': 'metro'},
            {'id': '4020', 'name': 'Schwedenplatz', 'lat': 48.2138, 'lng': 16.3789, 'type': 'metro'},
            {'id': '4021', 'name': 'Landstraße', 'lat': 48.2085, 'lng': 16.3831, 'type': 'metro'},
            {'id': '4022', 'name': 'Wien Mitte', 'lat': 48.2085, 'lng': 16.3831, 'type': 'metro'},
            {'id': '4023', 'name': 'Stadtpark', 'lat': 48.2008, 'lng': 16.3789, 'type': 'metro'},
            {'id': '4024', 'name': 'Kettenbrückengasse', 'lat': 48.2008, 'lng': 16.3617, 'type': 'metro'},
            {'id': '4025', 'name': 'Neubaugasse', 'lat': 48.2008, 'lng': 16.3567, 'type': 'metro'},
            {'id': '4026', 'name': 'Westbahnhof', 'lat': 48.1967, 'lng': 16.3378, 'type': 'metro'},
            {'id': '4027', 'name': 'Burggasse-Stadthalle', 'lat': 48.2008, 'lng': 16.3378, 'type': 'metro'},
            {'id': '4028', 'name': 'Thaliastraße', 'lat': 48.2108, 'lng': 16.3378, 'type': 'metro'},
            {'id': '4029', 'name': 'Alser Straße', 'lat': 48.2208, 'lng': 16.3378, 'type': 'metro'},
            {'id': '4030', 'name': 'Josefstädter Straße', 'lat': 48.2108, 'lng': 16.3567, 'type': 'metro'},
            {'id': '4031', 'name': 'Althanstraße', 'lat': 48.2208, 'lng': 16.3567, 'type': 'metro'},
            {'id': '4032', 'name': 'Heiligenstadt', 'lat': 48.2308, 'lng': 16.3567, 'type': 'metro'},
            {'id': '4033', 'name': 'Spittelau', 'lat': 48.2308, 'lng': 16.3667, 'type': 'metro'},
            {'id': '4034', 'name': 'Friedensbrücke', 'lat': 48.2308, 'lng': 16.3789, 'type': 'metro'},
            {'id': '4035', 'name': 'Rossauer Lände', 'lat': 48.2208, 'lng': 16.3789, 'type': 'metro'},
            {'id': '4036', 'name': 'Schottenring', 'lat': 48.2208, 'lng': 16.3789, 'type': 'metro'},
            {'id': '4037', 'name': 'Schottentor', 'lat': 48.2167, 'lng': 16.3667, 'type': 'metro'},
            {'id': '4038', 'name': 'Rathaus', 'lat': 48.2108, 'lng': 16.3567, 'type': 'metro'},
            {'id': '4039', 'name': 'Volkstheater', 'lat': 48.2038, 'lng': 16.3617, 'type': 'metro'},
            {'id': '4040', 'name': 'Museumsquartier', 'lat': 48.2038, 'lng': 16.3617, 'type': 'metro'},
        ]
        
        logger.info("Returning %d stops", len(stops))
        return jsonify({'stops': stops})
        
    except Exception as e:
        logger.error("Error in get_stops: %s", str(e), exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    logger.info("Starting Wiener Linien Live Map application")
    app.run(host='0.0.0.0', port=5000, debug=True)
