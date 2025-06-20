/**
 * Wiener Linien Live Map - Map and Vehicle Tracking
 * Part of the Annoyinator Barnacle Projects
 */

// Store vehicle markers by ID for updating positions
const vehicleMarkers = {};

// Store previous positions for smooth transitions
const previousPositions = {};

// Initialize map centered on Vienna
const map = L.map('map').setView([48.2082, 16.3738], 13);

// Add OpenStreetMap tiles
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '&copy; <a href="https://openstreetmap.org/copyright">OpenStreetMap contributors</a>'
}).addTo(map);

// Vehicle icons for different transport types
const vehicleIcons = {
    metro: L.icon({
        iconUrl: '/static/images/metro.png',
        iconSize: [24, 24],
        iconAnchor: [12, 12],
        popupAnchor: [0, -12],
        className: 'vehicle-marker metro'
    }),
    tram: L.icon({
        iconUrl: '/static/images/tram.png',
        iconSize: [24, 24],
        iconAnchor: [12, 12],
        popupAnchor: [0, -12],
        className: 'vehicle-marker tram'
    }),
    bus: L.icon({
        iconUrl: '/static/images/bus.png',
        iconSize: [24, 24],
        iconAnchor: [12, 12],
        popupAnchor: [0, -12],
        className: 'vehicle-marker bus'
    }),
    unknown: L.icon({
        iconUrl: '/static/images/unknown.png',
        iconSize: [24, 24],
        iconAnchor: [12, 12],
        popupAnchor: [0, -12],
        className: 'vehicle-marker'
    })
};

// Fallback to colored markers if custom icons aren't available
const fallbackIcons = {
    metro: L.icon({
        iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-blue.png',
        iconSize: [25, 41],
        iconAnchor: [12, 41],
        popupAnchor: [1, -34],
        className: 'vehicle-marker metro'
    }),
    tram: L.icon({
        iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-red.png',
        iconSize: [25, 41],
        iconAnchor: [12, 41],
        popupAnchor: [1, -34],
        className: 'vehicle-marker tram'
    }),
    bus: L.icon({
        iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-green.png',
        iconSize: [25, 41],
        iconAnchor: [12, 41],
        popupAnchor: [1, -34],
        className: 'vehicle-marker bus'
    }),
    unknown: L.icon({
        iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-grey.png',
        iconSize: [25, 41],
        iconAnchor: [12, 41],
        popupAnchor: [1, -34],
        className: 'vehicle-marker'
    })
};

// Get appropriate icon for vehicle type
function getVehicleIcon(type) {
    return vehicleIcons[type] || vehicleIcons.unknown;
}

// Format popup content for a vehicle
function formatVehiclePopup(vehicle) {
    return `
        <div class="vehicle-popup-header">Line ${vehicle.line}</div>
        <div class="vehicle-popup-info">
            <div>Type: ${vehicle.type}</div>
            <div>Speed: ${Math.round(vehicle.speed || 0)} km/h</div>
            <div>Direction: ${Math.round(vehicle.heading || 0)}°</div>
            <div>Last updated: ${new Date(vehicle.timestamp * 1000).toLocaleTimeString()}</div>
        </div>
    `;
}

// Update vehicle markers on the map
function updateVehicles(vehicles) {
    const currentIds = new Set();
    
    // Update or add markers for each vehicle
    vehicles.forEach(vehicle => {
        const id = vehicle.id;
        currentIds.add(id);
        
        // Store previous position for animation
        if (!previousPositions[id] && vehicle.lat && vehicle.lng) {
            previousPositions[id] = [vehicle.lat, vehicle.lng];
        }
        
        if (vehicleMarkers[id]) {
            // Update existing marker
            const marker = vehicleMarkers[id];
            
            // Only move if position changed
            if (marker.getLatLng().lat !== vehicle.lat || marker.getLatLng().lng !== vehicle.lng) {
                marker.setLatLng([vehicle.lat, vehicle.lng]);
                
                // Update rotation if available
                if (vehicle.heading !== undefined) {
                    marker.setRotationAngle(vehicle.heading);
                }
            }
            
            // Update popup content
            marker.setPopupContent(formatVehiclePopup(vehicle));
            
        } else {
            // Create new marker
            const icon = getVehicleIcon(vehicle.type);
            const marker = L.marker([vehicle.lat, vehicle.lng], {
                icon: icon,
                rotationAngle: vehicle.heading || 0
            }).addTo(map);
            
            // Add popup
            marker.bindPopup(formatVehiclePopup(vehicle));
            
            // Store marker
            vehicleMarkers[id] = marker;
        }
        
        // Update previous position
        previousPositions[id] = [vehicle.lat, vehicle.lng];
    });
    
    // Remove markers for vehicles no longer in the data
    Object.keys(vehicleMarkers).forEach(id => {
        if (!currentIds.has(id)) {
            map.removeLayer(vehicleMarkers[id]);
            delete vehicleMarkers[id];
            delete previousPositions[id];
        }
    });
    
    // Update last update time
    document.getElementById('last-update').textContent = 'Last update: ' + new Date().toLocaleTimeString();
}

// Fetch vehicles from API
function fetchVehicles(filters = { lines: ['5'], types: ['tram'] }) {
    // Show loading indicator
    document.querySelector('.loading-overlay').classList.add('active');
    
    // Build API URL with filters
    let url = '/api/vehicles';
    const params = new URLSearchParams();
    params.append('real', '1');
    
    if (filters.types && filters.types.length > 0 && !filters.types.includes('all')) {
        params.append('type', filters.types.join(','));
    }
    
    if (filters.lines && filters.lines.length > 0) {
        params.append('line', filters.lines.join(','));
    }
    
    if (params.toString()) {
        url += '?' + params.toString();
    }
    
    // Fetch vehicle data
    fetch(url)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.error) {
                console.error('API Error:', data.error);
                showError(data.error);
                return;
            }
            
            // Update vehicles on map
            updateVehicles(data.vehicles || []);
            
            // Show raw API data if present
            if (data.raw_api_data) {
                let debugPanel = document.getElementById('debug-panel');
                if (!debugPanel) {
                    debugPanel = document.createElement('pre');
                    debugPanel.id = 'debug-panel';
                    debugPanel.style.position = 'fixed';
                    debugPanel.style.bottom = '0';
                    debugPanel.style.left = '0';
                    debugPanel.style.maxHeight = '30vh';
                    debugPanel.style.overflow = 'auto';
                    debugPanel.style.background = 'rgba(0,0,0,0.8)';
                    debugPanel.style.color = '#fff';
                    debugPanel.style.zIndex = '10000';
                    debugPanel.style.fontSize = '12px';
                    debugPanel.style.width = '100vw';
                    document.body.appendChild(debugPanel);
                }
                debugPanel.textContent = JSON.stringify(data.raw_api_data, null, 2);
            } else {
                let debugPanel = document.getElementById('debug-panel');
                if (debugPanel) debugPanel.textContent = '';
            }
            
            // Hide any previous error
            hideError();
        })
        .catch(error => {
            console.error('Error fetching vehicles:', error);
            showError(`Failed to fetch vehicle data: ${error.message}`);
        })
        .finally(() => {
            // Hide loading indicator
            document.querySelector('.loading-overlay').classList.remove('active');
        });
}

// Show error message
function showError(message) {
    const errorElement = document.getElementById('error-message');
    errorElement.textContent = message;
    errorElement.style.display = 'block';
}

// Hide error message
function hideError() {
    const errorElement = document.getElementById('error-message');
    errorElement.style.display = 'none';
}

// Initialize the map and start fetching data
function initMap() {
    // Initial vehicle fetch
    fetchVehicles();
    
    // Set up periodic refresh
    setInterval(() => {
        const filters = {
            types: getActiveVehicleTypes(),
            lines: getActiveLines()
        };
        fetchVehicles(filters);
    }, 30000); // Refresh every 30 seconds
}

// Get currently selected vehicle types
function getActiveVehicleTypes() {
    return Array.from(
        document.querySelectorAll('.vehicle-type-filter:checked')
    ).map(checkbox => checkbox.value);
}

// Get currently selected lines
function getActiveLines() {
    return Array.from(
        document.querySelectorAll('.line-button.active')
    ).map(button => button.dataset.lineId);
}

// When DOM is loaded, initialize map
document.addEventListener('DOMContentLoaded', initMap);
