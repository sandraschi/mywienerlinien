"""
WebSocket Manager for Wiener Linien Live Map

This module provides WebSocket support for real-time updates,
disruption alerts, and live vehicle tracking.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, asdict
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask import request
import threading
import time
import random

logger = logging.getLogger(__name__)

@dataclass
class DisruptionAlert:
    """Represents a disruption alert."""
    id: str
    line: str
    type: str
    severity: str
    title: str
    description: str
    affected_stations: List[str]
    start_time: datetime
    end_time: Optional[datetime]
    status: str
    created_at: datetime

@dataclass
class VehicleUpdate:
    """Represents a vehicle position update."""
    vehicle_id: str
    line: str
    type: str
    lat: float
    lng: float
    direction: str
    next_station: str
    delay: int
    timestamp: datetime

class WebSocketManager:
    """Manages WebSocket connections and real-time updates."""
    
    def __init__(self, socketio: SocketIO):
        """Initialize the WebSocket manager."""
        self.socketio = socketio
        self.connected_clients = {}
        self.disruption_alerts = {}
        self.vehicle_updates = {}
        self.update_callbacks = []
        self.alert_callbacks = []
        self.running = False
        self.update_thread = None
        
        # Register event handlers
        self._register_handlers()
    
    def _register_handlers(self):
        """Register WebSocket event handlers."""
        
        @self.socketio.on('connect')
        def handle_connect(auth=None):
            """Handle client connection."""
            client_id = request.sid
            self.connected_clients[client_id] = {
                'connected_at': datetime.now(),
                'rooms': set(),
                'filters': {}
            }
            logger.info(f"Client connected: {client_id}")
            emit('connected', {'client_id': client_id, 'timestamp': datetime.now().isoformat()})
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            """Handle client disconnection."""
            client_id = request.sid
            if client_id in self.connected_clients:
                del self.connected_clients[client_id]
            logger.info(f"Client disconnected: {client_id}")
        
        @self.socketio.on('join_room')
        def handle_join_room(data):
            """Handle room joining."""
            client_id = request.sid
            if isinstance(data, dict):
                room = data.get('room')
                if room and client_id in self.connected_clients:
                    join_room(room)
                    self.connected_clients[client_id]['rooms'].add(room)
                    logger.info(f"Client {client_id} joined room: {room}")
        
        @self.socketio.on('leave_room')
        def handle_leave_room(data):
            """Handle room leaving."""
            client_id = request.sid
            if isinstance(data, dict):
                room = data.get('room')
                if room and client_id in self.connected_clients:
                    leave_room(room)
                    self.connected_clients[client_id]['rooms'].discard(room)
                    logger.info(f"Client {client_id} left room: {room}")
        
        @self.socketio.on('set_filters')
        def handle_set_filters(data):
            """Handle filter updates."""
            client_id = request.sid
            if client_id in self.connected_clients and isinstance(data, dict):
                self.connected_clients[client_id]['filters'] = data
                logger.info(f"Client {client_id} updated filters: {data}")
        
        @self.socketio.on('request_updates')
        def handle_request_updates(data):
            """Handle update requests."""
            client_id = request.sid
            if not isinstance(data, dict):
                data = {}
            update_type = data.get('type', 'all')
            
            if update_type == 'vehicles' or update_type == 'all':
                self._send_vehicle_updates(client_id)
            
            if update_type == 'disruptions' or update_type == 'all':
                self._send_disruption_alerts(client_id)
            
            if update_type == 'status' or update_type == 'all':
                self._send_system_status(client_id)
    
    def start(self):
        """Start the WebSocket manager."""
        if not self.running:
            self.running = True
            self.update_thread = threading.Thread(target=self._update_loop, daemon=True)
            self.update_thread.start()
            logger.info("WebSocket manager started")
    
    def stop(self):
        """Stop the WebSocket manager."""
        self.running = False
        if self.update_thread:
            self.update_thread.join(timeout=5)
        logger.info("WebSocket manager stopped")
    
    def _update_loop(self):
        """Main update loop for real-time data."""
        while self.running:
            try:
                # Update vehicle positions
                self._update_vehicle_positions()
                
                # Check for new disruptions
                self._check_disruptions()
                
                # Send periodic updates to all clients
                self._broadcast_updates()
                
                # Sleep for update interval
                time.sleep(30)  # 30-second update interval
                
            except Exception as e:
                logger.error(f"Error in update loop: {e}")
                time.sleep(5)
    
    def _update_vehicle_positions(self):
        """Update vehicle positions from API."""
        try:
            # This would integrate with the actual Wiener Linien API
            # For now, we'll simulate updates
            from app import fetch_vehicle_data, get_dummy_vehicles
            
            # Get vehicle data for major stations
            major_stations = ['3052', '3058', '3062', '3071', '3080']  # Sample RBL numbers
            
            for rbl in major_stations:
                try:
                    vehicles_data = fetch_vehicle_data(rbl)
                    if vehicles_data and isinstance(vehicles_data, dict):
                        # Handle the API response structure
                        if 'data' in vehicles_data and 'monitors' in vehicles_data['data']:
                            for monitor in vehicles_data['data']['monitors']:
                                if 'lines' in monitor:
                                    for line_data in monitor['lines']:
                                        for vehicle in line_data.get('departures', {}).get('departure', []):
                                            if 'vehicle' in vehicle:
                                                vehicle_info = vehicle['vehicle']
                                                vehicle_data = {
                                                    'id': vehicle_info.get('name', f'vehicle_{rbl}_{len(self.vehicle_updates)}'),
                                                    'line': line_data.get('name', ''),
                                                    'type': line_data.get('type', 'unknown'),
                                                    'lat': vehicle_info.get('location', {}).get('latitude', 0),
                                                    'lng': vehicle_info.get('location', {}).get('longitude', 0),
                                                    'direction': vehicle_info.get('direction', ''),
                                                    'next_station': vehicle.get('departure', {}).get('locationStop', {}).get('name', ''),
                                                    'delay': vehicle.get('departure', {}).get('departureTime', {}).get('timeReal', 0)
                                                }
                                                self._process_vehicle_update(vehicle_data)
                except Exception as e:
                    logger.error(f"Error fetching vehicle data for RBL {rbl}: {e}")
                    continue
                    
            # If no real vehicles found, add some dummy vehicles for demonstration
            if len(self.vehicle_updates) == 0:
                dummy_vehicles = get_dummy_vehicles()
                for vehicle in dummy_vehicles:
                    if isinstance(vehicle, dict):
                        self._process_vehicle_update(vehicle)
                        
        except Exception as e:
            logger.error(f"Error updating vehicle positions: {e}")
    
    def _process_vehicle_update(self, vehicle_data):
        """Process a vehicle update."""
        try:
            # Handle both string and dictionary inputs
            if isinstance(vehicle_data, str):
                logger.warning(f"Received string instead of dict for vehicle update: {vehicle_data}")
                return
            
            if not isinstance(vehicle_data, dict):
                logger.warning(f"Received non-dict type for vehicle update: {type(vehicle_data)}")
                return
            
            vehicle_id = vehicle_data.get('id', 'unknown')
            
            update = VehicleUpdate(
                vehicle_id=vehicle_id,
                line=vehicle_data.get('line', ''),
                type=vehicle_data.get('type', ''),
                lat=float(vehicle_data.get('lat', 0.0)),
                lng=float(vehicle_data.get('lng', 0.0)),
                direction=vehicle_data.get('direction', ''),
                next_station=vehicle_data.get('next_station', ''),
                delay=int(vehicle_data.get('delay', 0)),
                timestamp=datetime.now()
            )
            
            self.vehicle_updates[vehicle_id] = update
            
            # Notify callbacks
            for callback in self.update_callbacks:
                try:
                    callback('vehicle', update)
                except Exception as e:
                    logger.error(f"Error in vehicle update callback: {e}")
                    
        except Exception as e:
            logger.error(f"Error processing vehicle update: {e}")
    
    def _check_disruptions(self):
        """Check for new disruptions."""
        try:
            # This would integrate with the actual Wiener Linien API
            # For now, we'll simulate disruption checks with proper disruption data
            
            # Simulate some realistic disruptions
            possible_disruptions = [
                {
                    'id': f"disruption_{int(datetime.now().timestamp())}_{random.randint(1000, 9999)}",
                    'line': 'U4',
                    'type': 'delays',
                    'severity': 'medium',
                    'title': 'Delays on U4 Line',
                    'description': 'Due to signal problems, expect delays of 5-10 minutes on U4 line.',
                    'affected_stations': ['1012', '1013', '1014'],
                    'start_time': datetime.now().isoformat(),
                    'end_time': (datetime.now() + timedelta(hours=2)).isoformat(),
                    'status': 'active'
                },
                {
                    'id': f"disruption_{int(datetime.now().timestamp())}_{random.randint(1000, 9999)}",
                    'line': 'D',
                    'type': 'construction',
                    'severity': 'low',
                    'title': 'Construction Work on Tram Line D',
                    'description': 'Construction work between stations. Minor delays expected.',
                    'affected_stations': ['3052', '3058'],
                    'start_time': datetime.now().isoformat(),
                    'end_time': (datetime.now() + timedelta(hours=4)).isoformat(),
                    'status': 'active'
                }
            ]
            
            # Randomly create disruptions (30% chance every check)
            if random.random() < 0.3:
                disruption_data = random.choice(possible_disruptions)
                if isinstance(disruption_data, dict):
                    self._process_disruption_alert(disruption_data)
                    
        except Exception as e:
            logger.error(f"Error checking disruptions: {e}")
    
    def _process_disruption_alert(self, disruption_data):
        """Process a disruption alert."""
        try:
            # Handle both string and dictionary inputs
            if isinstance(disruption_data, str):
                logger.warning(f"Received string instead of dict for disruption alert: {disruption_data}")
                return
            
            if not isinstance(disruption_data, dict):
                logger.warning(f"Received non-dict type for disruption alert: {type(disruption_data)}")
                return
            
            disruption_id = disruption_data.get('id', str(datetime.now().timestamp()))
            
            # Check if this is a new disruption
            if disruption_id not in self.disruption_alerts:
                # Parse datetime strings properly
                start_time_str = disruption_data.get('start_time', datetime.now().isoformat())
                end_time_str = disruption_data.get('end_time')
                
                try:
                    start_time = datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
                except:
                    start_time = datetime.now()
                
                end_time = None
                if end_time_str:
                    try:
                        end_time = datetime.fromisoformat(end_time_str.replace('Z', '+00:00'))
                    except:
                        end_time = None
                
                alert = DisruptionAlert(
                    id=disruption_id,
                    line=disruption_data.get('line', ''),
                    type=disruption_data.get('type', ''),
                    severity=disruption_data.get('severity', 'medium'),
                    title=disruption_data.get('title', 'Service Disruption'),
                    description=disruption_data.get('description', ''),
                    affected_stations=disruption_data.get('affected_stations', []),
                    start_time=start_time,
                    end_time=end_time,
                    status=disruption_data.get('status', 'active'),
                    created_at=datetime.now()
                )
                
                self.disruption_alerts[disruption_id] = alert
                
                # Broadcast to all clients
                self._broadcast_disruption_alert(alert)
                
                # Notify callbacks
                for callback in self.alert_callbacks:
                    try:
                        callback(alert)
                    except Exception as e:
                        logger.error(f"Error in disruption alert callback: {e}")
                        
        except Exception as e:
            logger.error(f"Error processing disruption alert: {e}")
    
    def _broadcast_updates(self):
        """Broadcast updates to all connected clients."""
        try:
            # Send vehicle updates with proper datetime serialization
            vehicle_data = []
            for update in self.vehicle_updates.values():
                vehicle_dict = asdict(update)
                # Convert datetime objects to ISO format strings
                vehicle_dict['timestamp'] = vehicle_dict['timestamp'].isoformat()
                vehicle_data.append(vehicle_dict)
            
            self.socketio.emit('vehicle_updates', {
                'vehicles': vehicle_data,
                'timestamp': datetime.now().isoformat()
            })
            
            # Send system status
            status_data = {
                'connected_clients': len(self.connected_clients),
                'active_disruptions': len([d for d in self.disruption_alerts.values() if d.status == 'active']),
                'vehicle_count': len(self.vehicle_updates),
                'timestamp': datetime.now().isoformat()
            }
            self.socketio.emit('system_status', status_data)
            
        except Exception as e:
            logger.error(f"Error broadcasting updates: {e}")
    
    def _broadcast_disruption_alert(self, alert: DisruptionAlert):
        """Broadcast a disruption alert to all clients."""
        try:
            # Convert to dict and serialize datetime objects properly
            alert_data = {
                'id': alert.id,
                'line': alert.line,
                'type': alert.type,
                'severity': alert.severity,
                'title': alert.title,
                'description': alert.description,
                'affected_stations': alert.affected_stations,
                'start_time': alert.start_time.isoformat(),
                'end_time': alert.end_time.isoformat() if alert.end_time else None,
                'status': alert.status,
                'created_at': alert.created_at.isoformat()
            }
            
            self.socketio.emit('disruption_alert', alert_data)
            logger.info(f"Broadcasted disruption alert: {alert.title} on line {alert.line}")
            
        except Exception as e:
            logger.error(f"Error broadcasting disruption alert: {e}")
    
    def _send_vehicle_updates(self, client_id: str):
        """Send vehicle updates to a specific client."""
        try:
            vehicle_data = [asdict(update) for update in self.vehicle_updates.values()]
            self.socketio.emit('vehicle_updates', {
                'vehicles': vehicle_data,
                'timestamp': datetime.now().isoformat()
            }, room=client_id)
            
        except Exception as e:
            logger.error(f"Error sending vehicle updates to {client_id}: {e}")
    
    def _send_disruption_alerts(self, client_id: str):
        """Send disruption alerts to a specific client."""
        try:
            active_alerts = []
            for alert in self.disruption_alerts.values():
                if alert.status == 'active':
                    alert_data = {
                        'id': alert.id,
                        'line': alert.line,
                        'type': alert.type,
                        'severity': alert.severity,
                        'title': alert.title,
                        'description': alert.description,
                        'affected_stations': alert.affected_stations,
                        'start_time': alert.start_time.isoformat(),
                        'end_time': alert.end_time.isoformat() if alert.end_time else None,
                        'status': alert.status,
                        'created_at': alert.created_at.isoformat()
                    }
                    active_alerts.append(alert_data)
            
            self.socketio.emit('disruption_alerts', {
                'alerts': active_alerts,
                'timestamp': datetime.now().isoformat()
            }, room=client_id)
            
        except Exception as e:
            logger.error(f"Error sending disruption alerts to {client_id}: {e}")
    
    def _send_system_status(self, client_id: str):
        """Send system status to a specific client."""
        try:
            status_data = {
                'connected_clients': len(self.connected_clients),
                'active_disruptions': len([d for d in self.disruption_alerts.values() if d.status == 'active']),
                'vehicle_count': len(self.vehicle_updates),
                'timestamp': datetime.now().isoformat()
            }
            self.socketio.emit('system_status', status_data, room=client_id)
            
        except Exception as e:
            logger.error(f"Error sending system status to {client_id}: {e}")
    
    def add_update_callback(self, callback: Callable[[str, Any], None]):
        """Add a callback for vehicle updates."""
        self.update_callbacks.append(callback)
    
    def add_alert_callback(self, callback: Callable[[DisruptionAlert], None]):
        """Add a callback for disruption alerts."""
        self.alert_callbacks.append(callback)
    
    def get_connected_clients_count(self) -> int:
        """Get the number of connected clients."""
        return len(self.connected_clients)
    
    def get_active_disruptions_count(self) -> int:
        """Get the number of active disruptions."""
        return len([d for d in self.disruption_alerts.values() if d.status == 'active'])
    
    def get_vehicle_count(self) -> int:
        """Get the number of tracked vehicles."""
        return len(self.vehicle_updates)
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get the current system status."""
        return {
            'connected_clients': self.get_connected_clients_count(),
            'active_disruptions': self.get_active_disruptions_count(),
            'vehicle_count': self.get_vehicle_count(),
            'timestamp': datetime.now().isoformat()
        }

# Global WebSocket manager instance
websocket_manager = None

def init_websocket_manager(socketio: SocketIO):
    """Initialize the global WebSocket manager."""
    global websocket_manager
    websocket_manager = WebSocketManager(socketio)
    websocket_manager.start()
    return websocket_manager

def get_websocket_manager() -> Optional[WebSocketManager]:
    """Get the global WebSocket manager instance."""
    return websocket_manager 