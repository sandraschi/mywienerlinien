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
from typing import Dict, List, Optional, Any
from functools import wraps

from flask import Flask, render_template, jsonify, request, Response
from flask_caching import Cache
from flask_socketio import SocketIO, emit
import requests

# Import our custom modules
from data_loader import data_loader
from websocket_manager import init_websocket_manager, get_websocket_manager
from disruption_alerts import disruption_monitor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('wiener_linien')

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'wiener-linien-secret-key-2024'
app.config['CACHE_TYPE'] = 'SimpleCache'
app.config['CACHE_DEFAULT_TIMEOUT'] = 15

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

# Rate limiting
last_api_call = {}
RATE_LIMIT_SECONDS = 15

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
        
        response = requests.get(url, params=params, timeout=API_TIMEOUT)
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
        response = requests.get(url, timeout=API_TIMEOUT)
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
        response = requests.get(url, timeout=API_TIMEOUT)
        response.raise_for_status()
        
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching news: {e}")
        return None
    except Exception as e:
        logger.error(f"Error processing news: {e}")
        return None

def get_dummy_vehicles(vehicle_type: Optional[str] = None, line: Optional[str] = None) -> List[Dict[str, Any]]:
    """Generate dummy vehicle data for demonstration."""
    dummy_vehicles = [
        {
            'id': 'tram_d_001',
            'type': 'tram',
            'line': 'D',
            'lat': 48.2027,
            'lng': 16.3680,
            'direction': 'Nußdorf',
            'next_station': 'Karlsplatz',
            'delay': 0,
            'timestamp': datetime.now().isoformat()
        },
        {
            'id': 'tram_5_001',
            'type': 'tram',
            'line': '5',
            'lat': 48.2140,
            'lng': 16.3720,
            'direction': 'Westbahnhof',
            'next_station': 'Schottentor',
            'delay': 2,
            'timestamp': datetime.now().isoformat()
        },
        {
            'id': 'bus_1a_001',
            'type': 'bus',
            'line': '1A',
            'lat': 48.2089,
            'lng': 16.3717,
            'direction': 'Kaisermühlen',
            'next_station': 'Stephansplatz',
            'delay': 0,
            'timestamp': datetime.now().isoformat()
        },
        {
            'id': 'metro_u1_001',
            'type': 'metro',
            'line': 'U1',
            'lat': 48.2459,
            'lng': 16.4269,
            'direction': 'Reumannplatz',
            'next_station': 'Stephansplatz',
            'delay': 1,
            'timestamp': datetime.now().isoformat()
        },
        {
            'id': 'metro_u2_001',
            'type': 'metro',
            'line': 'U2',
            'lat': 48.2090,
            'lng': 16.4620,
            'direction': 'Karlsplatz',
            'next_station': 'Schottentor',
            'delay': 0,
            'timestamp': datetime.now().isoformat()
        },
        {
            'id': 'metro_u3_001',
            'type': 'metro',
            'line': 'U3',
            'lat': 48.2100,
            'lng': 16.2660,
            'direction': 'Simmering',
            'next_station': 'Stephansplatz',
            'delay': 3,
            'timestamp': datetime.now().isoformat()
        },
        {
            'id': 'metro_u4_001',
            'type': 'metro',
            'line': 'U4',
            'lat': 48.1890,
            'lng': 16.2220,
            'direction': 'Heiligenstadt',
            'next_station': 'Karlsplatz',
            'delay': 0,
            'timestamp': datetime.now().isoformat()
        },
        {
            'id': 'metro_u6_001',
            'type': 'metro',
            'line': 'U6',
            'lat': 48.1500,
            'lng': 16.2660,
            'direction': 'Floridsdorf',
            'next_station': 'Westbahnhof',
            'delay': 2,
            'timestamp': datetime.now().isoformat()
        },
        {
            'id': 'night_bus_n25_001',
            'type': 'night_bus',
            'line': 'N25',
            'lat': 48.2089,
            'lng': 16.3717,
            'direction': 'Floridsdorf',
            'next_station': 'Ring',
            'delay': 0,
            'timestamp': datetime.now().isoformat()
        }
    ]
    
    # Filter by vehicle type if specified
    if vehicle_type and vehicle_type != 'all':
        dummy_vehicles = [v for v in dummy_vehicles if v['type'] == vehicle_type]
    
    # Filter by line if specified
    if line:
        dummy_vehicles = [v for v in dummy_vehicles if v['line'] == line]
    
    return dummy_vehicles

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
                                for vehicle in line_data.get('departures', {}).get('departure', []):
                                    if 'vehicle' in vehicle:
                                        vehicle_info = vehicle['vehicle']
                                        vehicles.append({
                                            'id': vehicle_info.get('name', f'vehicle_{len(vehicles)}'),
                                            'type': line_data.get('type', 'unknown'),
                                            'line': line_data.get('name', ''),
                                            'lat': vehicle_info.get('location', {}).get('latitude', 0),
                                            'lng': vehicle_info.get('location', {}).get('longitude', 0),
                                            'direction': vehicle_info.get('direction', ''),
                                            'next_station': vehicle.get('departure', {}).get('locationStop', {}).get('name', ''),
                                            'delay': vehicle.get('departure', {}).get('departureTime', {}).get('timeReal', 0),
                                            'timestamp': datetime.now().isoformat()
                                        })
                    successful_requests += 1
                else:
                    failed_requests += 1
            except Exception as e:
                logger.error(f"Error fetching data for RBL {rbl}: {e}")
                failed_requests += 1
        
        # If no real vehicles found, add dummy vehicles
        if not vehicles:
            logger.info("No real vehicles found, adding dummy vehicles")
            vehicles = get_dummy_vehicles(vehicle_type, line)
        
        # Filter vehicles based on parameters
        if vehicle_type and vehicle_type != 'all':
            vehicles = [v for v in vehicles if v['type'] == vehicle_type]
        
        if line:
            vehicles = [v for v in vehicles if v['line'] == line]
        
        logger.info(f"Returning {len(vehicles)} vehicles (successful requests: {successful_requests}, failed: {failed_requests})")
        
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
        stations = data_loader.load_stations()
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

@app.route('/api/routes')
def get_routes():
    """API endpoint for routes."""
    try:
        line_filter = request.args.get('line')
        routes = data_loader.load_routes()
        
        if line_filter:
            routes = [r for r in routes if r.line == line_filter]
            logger.info(f"Returning route for line {line_filter}")
        else:
            logger.info(f"Returning {len(routes)} routes")
        
        route_data = []
        for route in routes:
            route_data.append({
                'name': route.line,
                'type': route.type,
                'color': route.color,
                'description': route.description,
                'coordinates': route.coordinates,
                'stops': route.stops
            })
        
        return jsonify({'routes': route_data})
        
    except Exception as e:
        logger.error(f"Error in get_routes: {e}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500

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
        status = {
            'websocket_clients': ws_manager.get_connected_clients_count() if ws_manager else 0,
            'active_disruptions': disruption_monitor.get_active_disruptions_count(),
            'vehicle_count': ws_manager.get_vehicle_count() if ws_manager else 0,
            'data_cache_status': data_loader.get_cache_status(),
            'last_api_check': disruption_monitor.last_check.isoformat() if disruption_monitor.last_check else None,
            'timestamp': datetime.now().isoformat()
        }
        return jsonify(status)
        
    except Exception as e:
        logger.error(f"Error in get_system_status: {e}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500

# WebSocket event handlers
@socketio.on('connect')
def handle_connect():
    """Handle client connection."""
    logger.info(f"Client connected: {request.sid}")
    
    # Get system status properly
    try:
        status_response = get_system_status()
        if hasattr(status_response, 'json'):
            system_status = status_response.json
        else:
            system_status = status_response
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
    room = data.get('room')
    if room:
        join_room(room)
        logger.info(f"Client {request.sid} joined room: {room}")

@socketio.on('leave_room')
def handle_leave_room(data):
    """Handle room leaving."""
    room = data.get('room')
    if room:
        leave_room(room)
        logger.info(f"Client {request.sid} left room: {room}")

@socketio.on('request_updates')
def handle_request_updates(data):
    """Handle update requests."""
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
            if hasattr(status_response, 'json'):
                status = status_response.json
            else:
                status = status_response
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

def initialize_app():
    """Initialize the application."""
    logger.info("Starting Wiener Linien Live Map application")
    
    # Ensure logs directory exists
    os.makedirs('logs', exist_ok=True)
    
    # Pre-load data
    data_loader.load_lines()
    data_loader.load_stations()
    data_loader.load_routes()

# Initialize the app immediately
initialize_app()

if __name__ == '__main__':
    logger.info("Starting Wiener Linien Live Map application")
    socketio.run(app, host='0.0.0.0', port=3080, debug=True)
