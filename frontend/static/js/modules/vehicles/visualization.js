/**
 * Vehicle visualization and map interaction
 */

import L from 'leaflet';
import { CONFIG } from '../../config.js';
import { logger } from '../utils/logger.js';
import { getVehicleIcon } from './data.js';

// Store references to vehicle markers and popups
const vehicleMarkers = new Map();
const vehiclePopups = new Map();
const vehicleTrails = new Map();

// Store vehicle positions for trail drawing
const vehiclePositionHistory = new Map();

/**
 * Set up vehicle visualization on the map
 * @param {L.Map} map - The Leaflet map instance
 * @param {Map} vehicleLayers - Map to store vehicle layers
 */
export function setupVehicleVisualization(map, vehicleLayers) {
    try {
        logger.info('Setting up vehicle visualization...');
        
        // Create layer groups for different vehicle types
        const vehicleLayersGroup = L.layerGroup();
        const trailLayersGroup = L.layerGroup();
        
        // Add layer groups to the map
        vehicleLayersGroup.addTo(map);
        trailLayersGroup.addTo(map);
        
        // Store layer references
        vehicleLayers.set('vehicles', vehicleLayersGroup);
        vehicleLayers.set('trails', trailLayersGroup);
        
        logger.info('Vehicle visualization set up');
        
    } catch (error) {
        logger.error('Failed to set up vehicle visualization:', error);
        throw error;
    }
}

/**
 * Update vehicle markers on the map
 * @param {L.Map} map - The Leaflet map instance
 * @param {Array} vehicles - Array of vehicle objects
 * @param {Map} vehicleLayers - Map of vehicle layers
 * @param {Set} activeVehicles - Set of active vehicle IDs
 */
export function updateVehicleMarkers(map, vehicles, vehicleLayers, activeVehicles) {
    try {
        logger.debug(`Updating ${vehicles.length} vehicle markers`);
        
        const vehicleLayersGroup = vehicleLayers.get('vehicles');
        const trailLayersGroup = vehicleLayers.get('trails');
        
        if (!vehicleLayersGroup || !trailLayersGroup) {
            throw new Error('Vehicle layers not initialized');
        }
        
        // Track which vehicles we've processed
        const processedVehicles = new Set();
        
        // Update or add vehicle markers
        vehicles.forEach(vehicle => {
            try {
                processedVehicles.add(vehicle.id);
                
                // Update position history for trails
                updatePositionHistory(vehicle);
                
                // Get or create the vehicle marker
                let marker = vehicleMarkers.get(vehicle.id);
                
                if (marker) {
                    // Update existing marker position
                    marker.setLatLng(vehicle.coordinates);
                    
                    // Update popup content if open
                    const popup = vehiclePopups.get(vehicle.id);
                    if (popup && popup.isOpen()) {
                        popup.setContent(createPopupContent(vehicle));
                    }
                } else {
                    // Create new marker
                    marker = createVehicleMarker(vehicle);
                    vehicleMarkers.set(vehicle.id, marker);
                    
                    // Add to the map if this vehicle is active
                    if (activeVehicles.has(vehicle.id)) {
                        marker.addTo(vehicleLayersGroup);
                    }
                }
                
                // Update or create the trail
                updateVehicleTrail(vehicle, trailLayersGroup, activeVehicles);
                
            } catch (error) {
                logger.error(`Failed to update vehicle ${vehicle.id}:`, error);
            }
        });
        
        // Remove markers for vehicles that are no longer active
        const currentVehicles = new Set(vehicleMarkers.keys());
        currentVehicles.forEach(vehicleId => {
            if (!processedVehicles.has(vehicleId)) {
                removeVehicle(vehicleId, vehicleLayersGroup, trailLayersGroup);
            }
        });
        
        logger.debug('Vehicle markers updated');
        
    } catch (error) {
        logger.error('Failed to update vehicle markers:', error);
        throw error;
    }
}

/**
 * Update the position history for a vehicle
 * @private
 */
function updatePositionHistory(vehicle) {
    if (!vehiclePositionHistory.has(vehicle.id)) {
        vehiclePositionHistory.set(vehicle.id, []);
    }
    
    const history = vehiclePositionHistory.get(vehicle.id);
    const now = Date.now();
    
    // Add current position to history
    history.push({
        position: vehicle.coordinates,
        timestamp: now,
        bearing: vehicle.bearing || 0
    });
    
    // Keep only positions from the last 5 minutes
    const fiveMinutesAgo = now - 5 * 60 * 1000;
    while (history.length > 0 && history[0].timestamp < fiveMinutesAgo) {
        history.shift();
    }
}

/**
 * Create a vehicle marker
 * @private
 */
function createVehicleMarker(vehicle) {
    const icon = L.divIcon({
        className: `vehicle-marker vehicle-${vehicle.type}`,
        html: `<div class="marker-inner">
                 <i class="fas ${getVehicleIcon(vehicle.type)}"></i>
                 <span class="vehicle-label">${vehicle.label || ''}</span>
               </div>`,
        iconSize: [24, 24],
        iconAnchor: [12, 12],
        popupAnchor: [0, -12]
    });
    
    const marker = L.marker(vehicle.coordinates, {
        icon: icon,
        rotationAngle: vehicle.bearing || 0,
        rotationOrigin: 'center',
        zIndexOffset: 200
    });
    
    // Create and bind popup
    const popup = L.popup({
        className: 'vehicle-popup',
        maxWidth: 300,
        minWidth: 200,
        autoPan: false
    }).setContent(createPopupContent(vehicle));
    
    marker.bindPopup(popup);
    vehiclePopups.set(vehicle.id, popup);
    
    // Add hover effect
    marker.on('mouseover', function() {
        this.openPopup();
        // Highlight trail if it exists
        const trail = vehicleTrails.get(vehicle.id);
        if (trail) {
            trail.setStyle({
                weight: 4,
                opacity: 1
            });
        }
    });
    
    marker.on('mouseout', function() {
        // Reset trail style
        const trail = vehicleTrails.get(vehicle.id);
        if (trail) {
            trail.setStyle({
                weight: 2,
                opacity: 0.7
            });
        }
    });
    
    return marker;
}

/**
 * Create popup content for a vehicle
 * @private
 */
function createPopupContent(vehicle) {
    const content = document.createElement('div');
    content.className = 'vehicle-popup-content';
    
    // Add vehicle header
    const header = document.createElement('div');
    header.className = 'vehicle-header';
    
    const icon = document.createElement('i');
    icon.className = `fas ${getVehicleIcon(vehicle.type)}`;
    
    const title = document.createElement('h3');
    title.textContent = vehicle.label || `Vehicle ${vehicle.id}`;
    
    header.appendChild(icon);
    header.appendChild(title);
    content.appendChild(header);
    
    // Add vehicle details
    const details = document.createElement('div');
    details.className = 'vehicle-details';
    
    if (vehicle.routeId) {
        const route = document.createElement('div');
        route.className = 'vehicle-route';
        route.innerHTML = `<strong>Route:</strong> ${vehicle.routeId}`;
        details.appendChild(route);
    }
    
    if (vehicle.destination) {
        const dest = document.createElement('div');
        dest.className = 'vehicle-destination';
        dest.innerHTML = `<strong>To:</strong> ${vehicle.destination}`;
        details.appendChild(dest);
    }
    
    if (vehicle.speed) {
        const speed = document.createElement('div');
        speed.className = 'vehicle-speed';
        speed.innerHTML = `<strong>Speed:</strong> ${vehicle.speed} km/h`;
        details.appendChild(speed);
    }
    
    if (vehicle.lastUpdated) {
        const updated = document.createElement('div');
        updated.className = 'vehicle-updated';
        updated.innerHTML = `<strong>Updated:</strong> ${formatTime(vehicle.lastUpdated)}`;
        details.appendChild(updated);
    }
    
    content.appendChild(details);
    
    return content;
}

/**
 * Update or create a vehicle trail
 * @private
 */
function updateVehicleTrail(vehicle, trailLayersGroup, activeVehicles) {
    const history = vehiclePositionHistory.get(vehicle.id) || [];
    
    // Skip if not enough history points
    if (history.length < 2) return;
    
    // Get or create the trail
    let trail = vehicleTrails.get(vehicle.id);
    const positions = history.map(h => h.position);
    
    if (trail) {
        // Update existing trail
        trail.setLatLngs(positions);
    } else {
        // Create new trail
        trail = L.polyline(positions, {
            color: vehicle.color || '#0078ff',
            weight: 2,
            opacity: 0.7,
            lineCap: 'round',
            lineJoin: 'round'
        });
        
        // Add to the map if this vehicle is active
        if (activeVehicles.has(vehicle.id)) {
            trail.addTo(trailLayersGroup);
        }
        
        vehicleTrails.set(vehicle.id, trail);
    }
    
    // Update trail style based on vehicle type
    trail.setStyle({
        color: vehicle.color || '#0078ff',
        weight: activeVehicles.has(vehicle.id) ? 2 : 0.5,
        opacity: activeVehicles.has(vehicle.id) ? 0.7 : 0.3
    });
}

/**
 * Remove a vehicle and its trail from the map
 * @private
 */
function removeVehicle(vehicleId, vehicleLayersGroup, trailLayersGroup) {
    // Remove marker
    const marker = vehicleMarkers.get(vehicleId);
    if (marker) {
        vehicleLayersGroup.removeLayer(marker);
        vehicleMarkers.delete(vehicleId);
    }
    
    // Remove popup
    const popup = vehiclePopups.get(vehicleId);
    if (popup && popup.isOpen()) {
        popup.remove();
    }
    vehiclePopups.delete(vehicleId);
    
    // Remove trail
    const trail = vehicleTrails.get(vehicleId);
    if (trail) {
        trailLayersGroup.removeLayer(trail);
        vehicleTrails.delete(vehicleId);
    }
    
    // Clear position history
    vehiclePositionHistory.delete(vehicleId);
}

/**
 * Format a timestamp as a readable time
 * @private
 */
function formatTime(timestamp) {
    try {
        const date = new Date(timestamp);
        return date.toLocaleTimeString();
    } catch (error) {
        return 'Unknown';
    }
}

/**
 * Toggle vehicle trail visibility
 * @param {string} vehicleId - ID of the vehicle
 * @param {boolean} visible - Whether to show the trail
 * @param {L.LayerGroup} trailLayersGroup - The trail layer group
 */
export function toggleVehicleTrail(vehicleId, visible, trailLayersGroup) {
    const trail = vehicleTrails.get(vehicleId);
    if (trail) {
        if (visible) {
            trail.addTo(trailLayersGroup);
            trail.setStyle({ opacity: 0.7 });
        } else {
            trail.setStyle({ opacity: 0 });
        }
    }
}
