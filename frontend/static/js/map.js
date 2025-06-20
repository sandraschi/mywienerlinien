/**
 * Wiener Linien Live Map - Frontend JavaScript
 * 
 * This file handles the interactive map functionality, real-time updates,
 * and WebSocket connections for live vehicle tracking and disruption alerts.
 */

// Global variables
let map;
let vehicleMarkers = new Map();
let routePolylines = new Map();
let stopMarkers = new Map();
let disruptionAlerts = new Map();
let socket;
let currentFilters = {
    vehicleType: 'all',
    line: null,
    station: null
};

// WebSocket connection
function initializeWebSocket() {
    // Connect to WebSocket server
    socket = io();
    
    // Connection events
    socket.on('connect', function() {
        console.log('Connected to WebSocket server');
        updateConnectionStatus('Connected', 'success');
        
        // Request initial data
        socket.emit('request_updates', { type: 'all' });
    });
    
    socket.on('disconnect', function() {
        console.log('Disconnected from WebSocket server');
        updateConnectionStatus('Disconnected', 'error');
    });
    
    // Real-time updates
    socket.on('vehicle_updates', function(data) {
        console.log('Received vehicle updates:', data.vehicles.length);
        updateVehicleMarkers(data.vehicles);
    });
    
    socket.on('disruption_alert', function(alert) {
        console.log('Received disruption alert:', alert);
        handleDisruptionAlert(alert);
    });
    
    socket.on('disruption_alerts', function(data) {
        console.log('Received disruption alerts:', data.alerts.length);
        updateDisruptionAlerts(data.alerts);
    });
    
    socket.on('system_status', function(status) {
        console.log('Received system status:', status);
        updateSystemStatus(status);
    });
}

// Initialize the map
function initializeMap() {
    // Create map centered on Vienna
    map = L.map('map').setView([48.2082, 16.3738], 13);
    
    // Add OpenStreetMap tiles
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors'
    }).addTo(map);
    
    // Initialize WebSocket connection
    initializeWebSocket();
    
    // Load initial data
    loadInitialData();
    
    // Set up periodic refresh
    setInterval(refreshVehicleData, 60000); // Refresh every 60 seconds
}

// Load initial data
async function loadInitialData() {
    try {
        // Load lines, stations, and routes
        await Promise.all([
            loadLines(),
            loadStations(),
            loadRoutes()
        ]);
        
        // Load initial vehicle data
        await loadVehicleData();
        
        console.log('Initial data loaded successfully');
    } catch (error) {
        console.error('Error loading initial data:', error);
        showError('Failed to load initial data');
    }
}

// Load transport lines
async function loadLines() {
    try {
        const response = await fetch('/api/lines');
        const data = await response.json();
        
        if (data.lines) {
            populateLineDropdown(data.lines);
        }
    } catch (error) {
        console.error('Error loading lines:', error);
    }
}

// Load stations
async function loadStations() {
    try {
        const response = await fetch('/api/stations');
        const data = await response.json();
        
        if (data.stations) {
            populateStationDropdown(data.stations);
        }
    } catch (error) {
        console.error('Error loading stations:', error);
    }
}

// Load routes
async function loadRoutes() {
    try {
        const response = await fetch('/api/routes');
        const data = await response.json();
        
        if (data.routes) {
            displayRoutes(data.routes);
        }
    } catch (error) {
        console.error('Error loading routes:', error);
    }
}

// Load vehicle data
async function loadVehicleData() {
    try {
        const params = new URLSearchParams();
        if (currentFilters.vehicleType !== 'all') {
            params.append('type', currentFilters.vehicleType);
        }
        if (currentFilters.line) {
            params.append('line', currentFilters.line);
        }
        if (currentFilters.station) {
            params.append('station', currentFilters.station);
        }
        
        const response = await fetch(`/api/vehicles?${params}`);
        const data = await response.json();
        
        if (data.vehicles) {
            updateVehicleMarkers(data.vehicles);
        }
    } catch (error) {
        console.error('Error loading vehicle data:', error);
        showError('Failed to load vehicle data');
    }
}

// Refresh vehicle data
function refreshVehicleData() {
    loadVehicleData();
}

// Update vehicle markers on the map
function updateVehicleMarkers(vehicles) {
    // Clear existing markers
    vehicleMarkers.forEach(marker => map.removeLayer(marker));
    vehicleMarkers.clear();
    
    // Add new markers
    vehicles.forEach(vehicle => {
        const marker = createVehicleMarker(vehicle);
        vehicleMarkers.set(vehicle.id, marker);
        marker.addTo(map);
    });
    
    updateVehicleCount(vehicles.length);
}

// Create a vehicle marker
function createVehicleMarker(vehicle) {
    const icon = getVehicleIcon(vehicle.type, vehicle.line);
    const marker = L.marker([vehicle.lat, vehicle.lng], { icon: icon });
    
    // Create popup content
    const popupContent = `
        <div class="vehicle-popup">
            <h4>${vehicle.line}</h4>
            <p><strong>Type:</strong> ${vehicle.type}</p>
            <p><strong>Direction:</strong> ${vehicle.direction}</p>
            <p><strong>Next Station:</strong> ${vehicle.next_station}</p>
            <p><strong>Delay:</strong> ${vehicle.delay} min</p>
            <p><strong>Updated:</strong> ${new Date(vehicle.timestamp).toLocaleTimeString()}</p>
        </div>
    `;
    
    marker.bindPopup(popupContent);
    
    return marker;
}

// Get vehicle icon based on type and line
function getVehicleIcon(type, line) {
    const iconSize = [20, 20];
    const iconAnchor = [10, 10];
    
    let iconUrl;
    let color;
    
    switch (type) {
        case 'metro':
            color = '#FF0000';
            break;
        case 'tram':
            color = '#FF6600';
            break;
        case 'bus':
            color = '#0066CC';
            break;
        case 'night_bus':
            color = '#333333';
            break;
        default:
            color = '#999999';
    }
    
    // Create custom icon with line number
    return L.divIcon({
        className: 'vehicle-marker',
        html: `<div style="background-color: ${color}; color: white; border-radius: 50%; width: 20px; height: 20px; display: flex; align-items: center; justify-content: center; font-size: 10px; font-weight: bold;">${line}</div>`,
        iconSize: iconSize,
        iconAnchor: iconAnchor
    });
}

// Display routes on the map
function displayRoutes(routes) {
    // Clear existing routes
    routePolylines.forEach(polyline => map.removeLayer(polyline));
    routePolylines.clear();
    
    routes.forEach(route => {
        if (route.coordinates && route.coordinates.length > 0) {
            const polyline = L.polyline(route.coordinates, {
                color: route.color,
                weight: 4,
                opacity: 0.7
            }).addTo(map);
            
            routePolylines.set(route.name, polyline);
            
            // Add stops if available
            if (route.stops) {
                route.stops.forEach(stop => {
                    const stopMarker = L.circleMarker([stop.lat, stop.lng], {
                        radius: 6,
                        fillColor: route.color,
                        color: '#fff',
                        weight: 2,
                        opacity: 1,
                        fillOpacity: 0.8
                    }).addTo(map);
                    
                    stopMarker.bindPopup(`
                        <div class="stop-popup">
                            <h4>${stop.name}</h4>
                            <p><strong>Line:</strong> ${route.name}</p>
                            <p><strong>RBL:</strong> ${stop.rbl}</p>
                        </div>
                    `);
                    
                    stopMarkers.set(`${route.name}-${stop.rbl}`, stopMarker);
                });
            }
        }
    });
}

// Handle disruption alerts
function handleDisruptionAlert(alert) {
    // Store the alert
    disruptionAlerts.set(alert.id, alert);
    
    // Show notification
    showDisruptionNotification(alert);
    
    // Update disruption display
    updateDisruptionDisplay();
}

// Update disruption alerts
function updateDisruptionAlerts(alerts) {
    disruptionAlerts.clear();
    alerts.forEach(alert => {
        disruptionAlerts.set(alert.id, alert);
    });
    updateDisruptionDisplay();
}

// Show disruption notification
function showDisruptionNotification(alert) {
    const notification = document.createElement('div');
    notification.className = `disruption-notification ${alert.severity}`;
    notification.innerHTML = `
        <div class="notification-header">
            <h4>${alert.title}</h4>
            <button onclick="this.parentElement.parentElement.remove()">×</button>
        </div>
        <div class="notification-content">
            <p><strong>Line:</strong> ${alert.line}</p>
            <p><strong>Type:</strong> ${alert.type}</p>
            <p>${alert.description}</p>
        </div>
    `;
    
    document.body.appendChild(notification);
    
    // Auto-remove after 10 seconds
    setTimeout(() => {
        if (notification.parentElement) {
            notification.remove();
        }
    }, 10000);
}

// Update disruption display
function updateDisruptionDisplay() {
    const container = document.getElementById('disruption-container');
    if (!container) return;
    
    container.innerHTML = '';
    
    if (disruptionAlerts.size === 0) {
        container.innerHTML = '<p>No active disruptions</p>';
        return;
    }
    
    disruptionAlerts.forEach(alert => {
        const alertElement = document.createElement('div');
        alertElement.className = `disruption-item ${alert.severity}`;
        alertElement.innerHTML = `
            <h4>${alert.title}</h4>
            <p><strong>Line:</strong> ${alert.line}</p>
            <p><strong>Type:</strong> ${alert.type}</p>
            <p>${alert.description}</p>
            <small>Started: ${new Date(alert.start_time).toLocaleString()}</small>
        `;
        container.appendChild(alertElement);
    });
}

// Update system status
function updateSystemStatus(status) {
    const statusElement = document.getElementById('system-status');
    if (statusElement) {
        statusElement.innerHTML = `
            <div class="status-item">
                <span class="label">Connected Clients:</span>
                <span class="value">${status.websocket_clients}</span>
            </div>
            <div class="status-item">
                <span class="label">Active Disruptions:</span>
                <span class="value">${status.active_disruptions}</span>
            </div>
            <div class="status-item">
                <span class="label">Tracked Vehicles:</span>
                <span class="value">${status.vehicle_count}</span>
            </div>
            <div class="status-item">
                <span class="label">Last Updated:</span>
                <span class="value">${new Date(status.timestamp).toLocaleTimeString()}</span>
            </div>
        `;
    }
}

// Update connection status
function updateConnectionStatus(status, type) {
    const statusElement = document.getElementById('connection-status');
    if (statusElement) {
        statusElement.textContent = status;
        statusElement.className = `connection-status ${type}`;
    }
}

// Update vehicle count
function updateVehicleCount(count) {
    const countElement = document.getElementById('vehicle-count');
    if (countElement) {
        countElement.textContent = count;
    }
}

// Populate line dropdown
function populateLineDropdown(lines) {
    const select = document.getElementById('line-select');
    if (!select) return;
    
    select.innerHTML = '<option value="">All Lines</option>';
    
    lines.forEach(line => {
        const option = document.createElement('option');
        option.value = line.name;
        option.textContent = `${line.name} - ${line.description}`;
        select.appendChild(option);
    });
}

// Populate station dropdown
function populateStationDropdown(stations) {
    const select = document.getElementById('station-select');
    if (!select) return;
    
    select.innerHTML = '<option value="">All Stations</option>';
    
    stations.forEach(station => {
        const option = document.createElement('option');
        option.value = station.rbl;
        option.textContent = `${station.name} (${station.type})`;
        select.appendChild(option);
    });
}

// Filter change handlers
function onVehicleTypeChange() {
    const select = document.getElementById('vehicle-type-select');
    currentFilters.vehicleType = select.value;
    loadVehicleData();
}

function onLineChange() {
    const select = document.getElementById('line-select');
    currentFilters.line = select.value || null;
    loadVehicleData();
}

function onStationChange() {
    const select = document.getElementById('station-select');
    currentFilters.station = select.value || null;
    loadVehicleData();
}

// Toggle route display
function toggleRoutes() {
    const button = document.getElementById('toggle-routes');
    const isVisible = button.textContent.includes('Hide');
    
    routePolylines.forEach(polyline => {
        if (isVisible) {
            map.removeLayer(polyline);
        } else {
            polyline.addTo(map);
        }
    });
    
    button.textContent = isVisible ? 'Show Routes' : 'Hide Routes';
}

// Toggle stop markers
function toggleStops() {
    const button = document.getElementById('toggle-stops');
    const isVisible = button.textContent.includes('Hide');
    
    stopMarkers.forEach(marker => {
        if (isVisible) {
            map.removeLayer(marker);
        } else {
            marker.addTo(map);
        }
    });
    
    button.textContent = isVisible ? 'Show Stops' : 'Hide Stops';
}

// Show error message
function showError(message) {
    const errorDiv = document.getElementById('error-message');
    if (errorDiv) {
        errorDiv.textContent = message;
        errorDiv.style.display = 'block';
        
        setTimeout(() => {
            errorDiv.style.display = 'none';
        }, 5000);
    }
}

// Show success message
function showSuccess(message) {
    const successDiv = document.getElementById('success-message');
    if (successDiv) {
        successDiv.textContent = message;
        successDiv.style.display = 'block';
        
        setTimeout(() => {
            successDiv.style.display = 'none';
        }, 3000);
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeMap();
    
    // Set up event listeners
    const vehicleTypeSelect = document.getElementById('vehicle-type-select');
    const lineSelect = document.getElementById('line-select');
    const stationSelect = document.getElementById('station-select');
    
    if (vehicleTypeSelect) {
        vehicleTypeSelect.addEventListener('change', onVehicleTypeChange);
    }
    if (lineSelect) {
        lineSelect.addEventListener('change', onLineChange);
    }
    if (stationSelect) {
        stationSelect.addEventListener('change', onStationChange);
    }
    
    console.log('Wiener Linien Live Map initialized');
});
