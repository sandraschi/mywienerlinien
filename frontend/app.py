"""
Wiener Linien Live Map - Main Application

A Flask-based web application for real-time visualization of Vienna's public transport system.
Features include live vehicle tracking, route display, and disruption alerts.
"""

import os
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from functools import wraps

# Configure root logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join(os.path.dirname(__file__), 'logs', 'app.log'))
    ]
)

# Create logger instance
logger = logging.getLogger(__name__)

# Import database module
from database import db, init_db

from flask import Flask, render_template, jsonify, request, Response, send_from_directory
from flask_caching import Cache
from flask_socketio import SocketIO, emit
import requests

# Import our custom modules
from data_loader import data_loader
from websocket_manager import init_websocket_manager, get_websocket_manager
from disruption_alerts import disruption_monitor

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'wiener-linien-secret-key-2024')
app.config['CACHE_TYPE'] = 'SimpleCache'
app.config['CACHE_DEFAULT_TIMEOUT'] = 15
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'postgresql://wienerlinien:wienerlinien@db:5432/wienerlinien')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
db.init_app(app)

# Configure logging
try:
    # Ensure logs directory exists
    logs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
    try:
        os.makedirs(logs_dir, exist_ok=True)
        
        # In production mode, log to a file
        log_file = os.path.join(logs_dir, 'app.log')
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('Wiener Linien Live Map startup')
    except Exception as e:
        print(f"Warning: Could not set up file logging: {e}")
        print(f"Logs will be written to console only.")
        # Fall back to basic console logging if file logging fails
        logging.basicConfig(level=logging.INFO)
        logger = logging.getLogger('wiener_linien')
        logger.warning("File logging not available - using console logging only")
        
except Exception as e:
    print(f"Error setting up logging: {e}")
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger('wiener_linien')
    logger.error("Failed to set up logging configuration")

# Debug: Log Flask app initialization
logger.info("Flask app initialized")
logger.info(f"App root path: {app.root_path}")
logger.info(f"App static folder: {app.static_folder}")
logger.info(f"App template folder: {app.template_folder}")

# Initialize cache
cache = Cache(app)

# Initialize SocketIO for WebSocket support
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Initialize WebSocket manager
websocket_manager = init_websocket_manager(socketio)

# Start disruption monitoring
disruption_monitor.start_monitoring()

# API configuration
API_BASE_URL = "https://www.wienerlinien.at/ogd_realtime"
API_TIMEOUT = 10

# Rate limiting - increased to avoid 403 errors
last_api_call = {}
RATE_LIMIT_SECONDS = 30  # Increased from 15 to 30 seconds

# API headers to avoid 403 errors
API_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1'
}

def rate_limit(func):
    """Decorator to enforce rate limiting."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        func_name = func.__name__
        current_time = time.time()
        
        if func_name in last_api_call:
            time_since_last = current_time - last_api_call[func_name]
            if time_since_last < RATE_LIMIT_SECONDS:
                sleep_time = RATE_LIMIT_SECONDS - time_since_last
                logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f} seconds")
                time.sleep(sleep_time)
        
        last_api_call[func_name] = time.time()
        return func(*args, **kwargs)
    return wrapper

@rate_limit
def fetch_vehicle_data(rbl_number: str) -> Optional[Dict[str, Any]]:
    """Fetch vehicle data from Wiener Linien API."""
    try:
        url = f"{API_BASE_URL}/monitor"
        params = {'rbl': rbl_number}
        
        response = requests.get(url, params=params, timeout=API_TIMEOUT, headers=API_HEADERS)
        response.raise_for_status()
        
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed for RBL {rbl_number}: {e}")
        return None
    except Exception as e:
        logger.error(f"Error processing API response for RBL {rbl_number}: {e}")
        return None

@rate_limit
def fetch_traffic_info() -> Optional[Dict[str, Any]]:
    """Fetch traffic information from Wiener Linien API."""
    try:
        url = f"{API_BASE_URL}/trafficInfo"
        response = requests.get(url, timeout=API_TIMEOUT, headers=API_HEADERS)
        response.raise_for_status()
        
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching traffic info: {e}")
        return None
    except Exception as e:
        logger.error(f"Error processing traffic info: {e}")
        return None

@rate_limit
def fetch_news() -> Optional[Dict[str, Any]]:
    """Fetch news and announcements from Wiener Linien API."""
    try:
        url = f"{API_BASE_URL}/news"
        response = requests.get(url, timeout=API_TIMEOUT, headers=API_HEADERS)
        response.raise_for_status()
        
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching news: {e}")
        return None
    except Exception as e:
        logger.error(f"Error processing news: {e}")
        return None

def _calculate_delay(departure_time):
    """Calculate delay in minutes from departure time information."""
    try:
        planned_time = departure_time.get('timePlanned')
        real_time = departure_time.get('timeReal')
        
        if planned_time and real_time:
            # Parse ISO format times
            planned = datetime.fromisoformat(planned_time.replace('Z', '+00:00'))
            real = datetime.fromisoformat(real_time.replace('Z', '+00:00'))
            
            # Calculate delay in minutes
            delay_seconds = (real - planned).total_seconds()
            return int(delay_seconds / 60)
        else:
            return 0
    except Exception:
        return 0

@app.route('/')
def index():
    """Main page route."""
    return render_template('index.html')

@app.route('/api/vehicles')
def get_vehicles():
    """API endpoint for vehicle positions."""
    try:
        vehicle_type = request.args.get('type', 'all')
        line = request.args.get('line')
        station = request.args.get('station')
        
        logger.info(f"Fetching vehicles: type={vehicle_type}, line={line}, station={station}")
        
        vehicles = []
        successful_requests = 0
        failed_requests = 0
        
        # Get stations to query
        stations_to_query = []
        if station:
            # Query specific station
            stations_to_query = [station]
        else:
            # Query major stations
            all_stations = data_loader.load_stations()
            major_stations = [s.rbl for s in all_stations if s.rbl and len(s.rbl) == 4]
            stations_to_query = major_stations[:5]  # Limit to 5 stations
        
        # Fetch real vehicle data
        for rbl in stations_to_query:
            try:
                data = fetch_vehicle_data(rbl)
                if data and 'data' in data and 'monitors' in data['data']:
                    for monitor in data['data']['monitors']:
                        if 'lines' in monitor:
                            for line_data in monitor['lines']:
                                # Get line information
                                line_name = line_data.get('name', '')
                                line_type = line_data.get('type', 'unknown')
                                
                                # Process departures to get vehicle positions
                                departures = line_data.get('departures', {}).get('departure', [])
                                if not isinstance(departures, list):
                                    departures = [departures] if departures else []
                                
                                for departure in departures:
                                    if 'vehicle' in departure:
                                        vehicle_info = departure['vehicle']
                                        departure_time = departure.get('departureTime', {})
                                        
                                        # Create vehicle entry
                                        vehicle_entry = {
                                            'id': f"{line_name}_{rbl}_{len(vehicles)}",
                                            'type': line_type.replace('pt', '').lower(),  # Convert ptTram to tram
                                            'line': line_name,
                                            'lat': monitor.get('locationStop', {}).get('geometry', {}).get('coordinates', [0, 0])[1],
                                            'lng': monitor.get('locationStop', {}).get('geometry', {}).get('coordinates', [0, 0])[0],
                                            'direction': vehicle_info.get('towards', ''),
                                            'next_station': monitor.get('locationStop', {}).get('properties', {}).get('title', ''),
                                            'delay': _calculate_delay(departure_time),
                                            'timestamp': datetime.now().isoformat(),
                                            'countdown': departure_time.get('countdown', 0),
                                            'platform': vehicle_info.get('platform', ''),
                                            'barrier_free': vehicle_info.get('barrierFree', False)
                                        }
                                        vehicles.append(vehicle_entry)
                    successful_requests += 1
                else:
                    failed_requests += 1
            except Exception as e:
                logger.error(f"Error fetching data for RBL {rbl}: {e}")
                failed_requests += 1
        
        # Filter vehicles based on parameters
        if vehicle_type and vehicle_type != 'all':
            vehicles = [v for v in vehicles if v['type'] == vehicle_type]
        
        if line:
            vehicles = [v for v in vehicles if v['line'] == line]
        
        logger.info(f"Returning {len(vehicles)} vehicles (successful requests: {successful_requests}, failed: {failed_requests})")
        
        # If no vehicles found, return empty array instead of error
        if not vehicles:
            logger.warning("No vehicles found matching the criteria")
        
        return jsonify({
            'vehicles': vehicles,
            'timestamp': datetime.now().isoformat(),
            'successful_requests': successful_requests,
            'failed_requests': failed_requests
        })
        
    except Exception as e:
        logger.error(f"Error in get_vehicles: {e}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/lines')
def get_lines():
    """API endpoint for transport lines."""
    try:
        lines = data_loader.load_lines()
        line_data = []
        
        for line in lines:
            line_data.append({
                'name': line.name,
                'type': line.type,
                'color': line.color,
                'description': line.description,
                'frequency': line.frequency,
                'operating_hours': line.operating_hours
            })
        
        logger.info(f"Returning {len(line_data)} lines")
        return jsonify({'lines': line_data})
        
    except Exception as e:
        logger.error(f"Error in get_lines: {e}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/stations')
def get_stations():
    """API endpoint for stations."""
    try:
        stations = db.get_stations()
        station_data = []
        
        for station in stations:
            station_data.append({
                'name': station.name,
                'rbl': station.rbl,
                'type': station.type,
                'zone': station.zone,
                'lat': station.lat,
                'lng': station.lng
            })
        
        logger.info(f"Returning {len(station_data)} stations")
        return jsonify({'stations': station_data})
        
    except Exception as e:
        logger.error(f"Error in get_stations: {e}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/routes', methods=['GET'])
@cache.cached(timeout=300)  # Cache for 5 minutes
def get_routes():
    """
    API endpoint for routes.
    Returns a list of all available routes with their details.
    """
    try:
        # Get routes from database
        routes = db.get_routes()
        
        # Format response
        response = {
            'status': 'success',
            'data': routes,
            'count': len(routes),
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error in get_routes: {str(e)}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': 'Failed to fetch routes',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 500

@app.route('/api/disruptions')
def get_disruptions():
    """API endpoint for service disruptions."""
    try:
        line_filter = request.args.get('line')
        severity_filter = request.args.get('severity')
        
        if line_filter:
            disruptions = disruption_monitor.get_disruptions_by_line(line_filter)
        elif severity_filter:
            from disruption_alerts import DisruptionSeverity
            severity = DisruptionSeverity(severity_filter)
            disruptions = disruption_monitor.get_disruptions_by_severity(severity)
        else:
            disruptions = disruption_monitor.get_active_disruptions()
        
        disruption_data = []
        for disruption in disruptions:
            disruption_data.append({
                'id': disruption.id,
                'line': disruption.line,
                'type': disruption.type.value,
                'severity': disruption.severity.value,
                'status': disruption.status.value,
                'title': disruption.title,
                'description': disruption.description,
                'affected_stations': disruption.affected_stations,
                'affected_lines': disruption.affected_lines,
                'start_time': disruption.start_time.isoformat(),
                'end_time': disruption.end_time.isoformat() if disruption.end_time else None,
                'created_at': disruption.created_at.isoformat(),
                'updated_at': disruption.updated_at.isoformat()
            })
        
        logger.info(f"Returning {len(disruption_data)} disruptions")
        return jsonify({'disruptions': disruption_data})
        
    except Exception as e:
        logger.error(f"Error in get_disruptions: {e}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/disruptions/summary')
def get_disruption_summary():
    """API endpoint for disruption summary."""
    try:
        summary = disruption_monitor.get_disruption_summary()
        return jsonify(summary)
        
    except Exception as e:
        logger.error(f"Error in get_disruption_summary: {e}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/status')
def get_system_status():
    """API endpoint for system status."""
    try:
        ws_manager = get_websocket_manager()
        active_disruptions = disruption_monitor.get_active_disruptions()
        status = {
            'websocket_clients': ws_manager.get_connected_clients_count() if ws_manager else 0,
            'active_disruptions': len(active_disruptions),
            'vehicle_count': ws_manager.get_vehicle_count() if ws_manager else 0,
            'data_cache_status': db.get_cache_status(),
            'last_api_check': disruption_monitor.last_check.isoformat() if disruption_monitor.last_check else None,
            'timestamp': datetime.now().isoformat()
        }
        return jsonify(status)
        
    except Exception as e:
        logger.error(f"Error in get_system_status: {e}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500

# WebSocket event handlers
@socketio.on('connect')
def handle_connect(auth=None):
    """Handle client connection."""
    logger.info(f"Client connected: {request.sid}")
    
    # Get system status properly
    try:
        status_response = get_system_status()
        # Extract JSON from Flask response
        if hasattr(status_response, 'get_json'):
            system_status = status_response.get_json()
        elif hasattr(status_response, 'json'):
            system_status = status_response.json
        elif isinstance(status_response, dict):
            system_status = status_response
        else:
            # Fallback to basic status
            system_status = {
                'websocket_clients': 0,
                'active_disruptions': 0,
                'vehicle_count': 0,
                'timestamp': datetime.now().isoformat()
            }
    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        system_status = {
            'websocket_clients': 0,
            'active_disruptions': 0,
            'vehicle_count': 0,
            'timestamp': datetime.now().isoformat()
        }
    
    emit('connected', {
        'client_id': request.sid,
        'timestamp': datetime.now().isoformat(),
        'system_status': system_status
    })

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection."""
    logger.info(f"Client disconnected: {request.sid}")

@socketio.on('join_room')
def handle_join_room(data):
    """Handle room joining."""
    if isinstance(data, dict):
        room = data.get('room')
        if room:
            join_room(room)
            logger.info(f"Client {request.sid} joined room: {room}")

@socketio.on('leave_room')
def handle_leave_room(data):
    """Handle room leaving."""
    if isinstance(data, dict):
        room = data.get('room')
        if room:
            leave_room(room)
            logger.info(f"Client {request.sid} left room: {room}")

@socketio.on('request_updates')
def handle_request_updates(data):
    """Handle update requests."""
    if not isinstance(data, dict):
        logger.warning(f"Received non-dict data in request_updates: {type(data)}")
        data = {}
    
    update_type = data.get('type', 'all')
    client_id = request.sid
    
    if update_type in ['vehicles', 'all']:
        # Send current vehicle data
        vehicles = get_dummy_vehicles()
        emit('vehicle_updates', {
            'vehicles': vehicles,
            'timestamp': datetime.now().isoformat()
        })
    
    if update_type in ['disruptions', 'all']:
        # Send current disruption data
        disruptions = disruption_monitor.get_active_disruptions()
        disruption_data = []
        for disruption in disruptions:
            disruption_data.append({
                'id': disruption.id,
                'line': disruption.line,
                'type': disruption.type.value,
                'severity': disruption.severity.value,
                'title': disruption.title,
                'description': disruption.description,
                'start_time': disruption.start_time.isoformat(),
                'created_at': disruption.created_at.isoformat()
            })
        emit('disruption_alerts', {
            'alerts': disruption_data,
            'timestamp': datetime.now().isoformat()
        })
    
    if update_type in ['status', 'all']:
        # Send system status
        try:
            status_response = get_system_status()
            # Extract JSON from Flask response
            if hasattr(status_response, 'get_json'):
                status = status_response.get_json()
            elif hasattr(status_response, 'json'):
                status = status_response.json
            elif isinstance(status_response, dict):
                status = status_response
            else:
                # Fallback to basic status
                status = {
                    'websocket_clients': 0,
                    'active_disruptions': 0,
                    'vehicle_count': 0,
                    'timestamp': datetime.now().isoformat()
                }
            emit('system_status', status)
        except Exception as e:
            logger.error(f"Error getting system status: {e}")
            emit('system_status', {
                'websocket_clients': 0,
                'active_disruptions': 0,
                'vehicle_count': 0,
                'timestamp': datetime.now().isoformat()
            })

# Disruption alert callback
def on_disruption_alert(disruption, event_type):
    """Handle disruption alerts."""
    try:
        alert_data = {
            'id': disruption.id,
            'line': disruption.line,
            'type': disruption.type.value,
            'severity': disruption.severity.value,
            'title': disruption.title,
            'description': disruption.description,
            'start_time': disruption.start_time.isoformat(),
            'created_at': disruption.created_at.isoformat(),
            'event_type': event_type
        }
        
        # Broadcast to all connected clients
        socketio.emit('disruption_alert', alert_data)
        logger.info(f"Broadcasted disruption alert: {disruption.id} ({event_type})")
        
    except Exception as e:
        logger.error(f"Error handling disruption alert: {e}")

# Register disruption alert callback
disruption_monitor.subscribe(on_disruption_alert)

# Add a route to serve markdown files from the data directory
@app.route('/data/<path:filename>')
def serve_markdown(filename):
    """Serve markdown files from the data directory."""
    data_dir = '/app/data'  # This is where the data is mounted in the container
    logger.info(f"Attempting to serve file: {filename} from directory: {data_dir}")
    
    # Debug: Log the current working directory and list of files in the data directory
    cwd = os.getcwd()
    logger.info(f"Current working directory: {cwd}")
    
    try:
        files = os.listdir('.')
        logger.info(f"Files in current directory: {files}")
    except Exception as e:
        logger.error(f"Error listing current directory: {e}")
    
    try:
        files = os.listdir('/app')
        logger.info(f"Files in /app directory: {files}")
    except Exception as e:
        logger.error(f"Error listing /app directory: {e}")
        
    # Try to find the data directory
    possible_data_dirs = [
        '/app/data',
        '/data',
        os.path.join(app.root_path, 'data'),
        os.path.join(os.path.dirname(__file__), 'data')
    ]
    
    for dir_path in possible_data_dirs:
        if os.path.exists(dir_path):
            data_dir = dir_path
            logger.info(f"Found data directory at: {data_dir}")
            try:
                files = os.listdir(data_dir)
                logger.info(f"Files in data directory: {files}")
            except Exception as e:
                logger.error(f"Error listing data directory: {e}")
            break
    else:
        logger.error("Could not find data directory in any of the expected locations")
    
    # List all files in the data directory for debugging
    try:
        files = os.listdir(data_dir)
        logger.info(f"Files in data directory: {files}")
    except Exception as e:
        logger.error(f"Error listing data directory: {e}")
    
    # Check if file exists
    filepath = os.path.join(data_dir, filename)
    if not os.path.exists(filepath):
        logger.error(f"File not found: {filepath}")
        return f"File not found: {filename}", 404
    
    # Check if file is a markdown file
    if not filename.lower().endswith('.md'):
        logger.error(f"Invalid file type: {filename}")
        return "Only markdown files are allowed", 400
    
    logger.info(f"Serving file: {filepath}")
    return send_from_directory(data_dir, filename, mimetype='text/markdown')

# Add a route to list all registered routes for debugging
@app.route('/routes')
def list_routes():
    """List all registered routes for debugging."""
    output = []
    for rule in app.url_map.iter_rules():
        methods = ','.join(rule.methods)
        output.append(f"{rule.endpoint}: {rule.rule} [{methods}]")
    return '<br>'.join(sorted(output))

def initialize_app():
    """Initialize the application."""
    logger.info("Starting Wiener Linien Live Map application")
    
    # Ensure logs directory exists
    os.makedirs('logs', exist_ok=True)
    
    # Pre-load data
    data_loader.load_lines()
    data_loader.load_stations()
    data_loader.load_routes()

# Test route to verify route registration
@app.route('/test')
def test_route():
    """Test route to verify route registration."""
    return "Test route is working!"

# Application factory function to create and configure the Flask app
def create_app():
    """Application factory function to create and configure the Flask app."""
    # Create the Flask app
    app = Flask(__name__)
    
    # Configure the app
    app.config['SECRET_KEY'] = 'wiener-linien-secret-key-2024'
    app.config['CACHE_TYPE'] = 'SimpleCache'
    app.config['CACHE_DEFAULT_TIMEOUT'] = 15
    
    # Initialize extensions
    cache = Cache(app)
    
    # Register routes
    @app.route('/')
    def index_route():
        return render_template('index.html')
    
    @app.route('/api/vehicles')
    def get_vehicles_route():
        return get_vehicles()
    
    @app.route('/api/lines')
    def get_lines_route():
        return get_lines()
    
    @app.route('/api/stations')
    def get_stations_route():
        return get_stations()
    
    @app.route('/api/routes')
    def get_routes_route():
        return get_routes()
    
    @app.route('/api/disruptions')
    def get_disruptions_route():
        return get_disruptions()
    
    @app.route('/api/disruptions/summary')
    def get_disruption_summary_route():
        return get_disruption_summary()
    
    @app.route('/api/status')
    def get_system_status_route():
        return get_system_status()
    
    @app.route('/data/<path:filename>')
    def serve_markdown_route(filename):
        return serve_markdown(filename)
    
    @app.route('/routes')
    def list_routes_route():
        return list_routes()
    
    @app.route('/test')
    def test_route_route():
        return test_route()
    
    # Debug endpoint to list all registered routes
    @app.route('/debug/routes')
    def debug_routes():
        """Debug endpoint to list all registered routes."""
        routes = []
        for rule in app.url_map.iter_rules():
            routes.append({
                'endpoint': rule.endpoint,
                'methods': sorted(rule.methods),
                'rule': str(rule)
            })
        return jsonify({
            'status': 'success',
            'routes': routes
        })
    
    # Initialize the app
    initialize_app()
    
    # Initialize SocketIO with the app
    logger.info("Initializing SocketIO with the app")
    socketio.init_app(app)
    
    # Log all registered routes
    logger.info("=== Registered Routes ===")
    for rule in app.url_map.iter_rules():
        logger.info(f"{rule.endpoint}: {rule.rule} -> {rule.methods}")
    logger.info("======================================")
    
    return app

# Create the app
app = create_app()

if __name__ == '__main__':
    # Start the SocketIO server
    socketio.run(
        app,
        host='0.0.0.0',
        port=5000,
        debug=True,
        allow_unsafe_werkzeug=True
    )
