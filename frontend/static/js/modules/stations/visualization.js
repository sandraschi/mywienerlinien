/**
 * Station visualization and map interaction
 */

import L from 'leaflet';
import { CONFIG } from '../../config.js';
import { logger } from '../utils/logger.js';
import { createMarker, createPopup } from '../map/utils.js';

// Store references to station markers and popups
const stationMarkers = new Map();
const stationPopups = new Map();

/**
 * Set up station visualization on the map
 * @param {L.Map} map - The Leaflet map instance
 * @param {Array} stations - Array of station objects
 * @param {Map} stationLayers - Map to store station layers
 * @param {Set} activeStations - Set of active station IDs
 */
export function setupStationVisualization(map, stations, stationLayers, activeStations) {
    try {
        logger.info('Setting up station visualization...');
        
        // Clear any existing layers
        clearAllStations(map);
        
        // Create a layer group for all stations
        const stationsLayer = L.layerGroup();
        
        // Add the layer group to the map
        stationsLayer.addTo(map);
        
        // Process each station
        stations.forEach(station => {
            try {
                // Create a marker for the station
                const marker = createStationMarker(station);
                
                // Create a popup for the station
                const popup = createStationPopup(station);
                marker.bindPopup(popup);
                
                // Add to the layer group
                stationsLayer.addLayer(marker);
                
                // Store references
                stationMarkers.set(station.id, marker);
                stationPopups.set(station.id, popup);
                
                // If this station should be active by default, show it
                if (activeStations.has(station.id)) {
                    marker.addTo(map);
                }
                
            } catch (error) {
                logger.error(`Failed to process station ${station.id}:`, error);
            }
        });
        
        // Store the layer group
        stationLayers.set('all', stationsLayer);
        
        logger.info('Station visualization set up');
        
    } catch (error) {
        logger.error('Failed to set up station visualization:', error);
        throw error;
    }
}

/**
 * Add a station to the map
 * @param {L.Map} map - The Leaflet map instance
 * @param {Object} station - Station object to add
 * @param {Map} stationLayers - Map of station layers
 */
export function addStationToMap(map, station, stationLayers) {
    try {
        logger.debug(`Adding station to map: ${station.id}`);
        
        // Create marker if it doesn't exist
        if (!stationMarkers.has(station.id)) {
            const marker = createStationMarker(station);
            const popup = createStationPopup(station);
            marker.bindPopup(popup);
            
            stationMarkers.set(station.id, marker);
            stationPopups.set(station.id, popup);
        }
        
        // Add to the map
        const marker = stationMarkers.get(station.id);
        marker.addTo(map);
        
        logger.debug(`Station ${station.id} added to map`);
        
    } catch (error) {
        logger.error(`Failed to add station ${station.id} to map:`, error);
        throw error;
    }
}

/**
 * Show a station on the map
 * @param {L.Map} map - The Leaflet map instance
 * @param {Object} station - Station object to show
 * @param {Map} stationLayers - Map of station layers
 */
export function showStation(map, station, stationLayers) {
    try {
        const marker = stationMarkers.get(station.id);
        if (marker) {
            map.addLayer(marker);
            logger.debug(`Station ${station.id} shown`);
        }
    } catch (error) {
        logger.error(`Failed to show station ${station.id}:`, error);
    }
}

/**
 * Hide a station from the map
 * @param {L.Map} map - The Leaflet map instance
 * @param {Object} station - Station object to hide
 * @param {Map} stationLayers - Map of station layers
 */
export function hideStation(map, station, stationLayers) {
    try {
        const marker = stationMarkers.get(station.id);
        if (marker) {
            map.removeLayer(marker);
            logger.debug(`Station ${station.id} hidden`);
        }
    } catch (error) {
        logger.error(`Failed to hide station ${station.id}:`, error);
    }
}

/**
 * Clear all stations from the map
 * @param {L.Map} map - The Leaflet map instance
 */
export function clearAllStations(map) {
    try {
        // Remove all station markers
        stationMarkers.forEach((marker, id) => {
            if (map.hasLayer(marker)) {
                map.removeLayer(marker);
            }
        });
        
        // Clear all popups
        stationPopups.forEach((popup, id) => {
            if (popup.isOpen()) {
                popup.remove();
            }
        });
        
        // Clear all collections
        stationMarkers.clear();
        stationPopups.clear();
        
        logger.debug('All stations cleared from map');
        
    } catch (error) {
        logger.error('Failed to clear stations:', error);
        throw error;
    }
}

/**
 * Create a marker for a station
 * @private
 */
function createStationMarker(station) {
    const marker = L.marker(station.coordinates, {
        title: station.name,
        icon: L.divIcon({
            className: 'station-marker',
            html: `<div class="marker-inner"><i class="fas fa-train"></i></div>`,
            iconSize: [24, 24],
            iconAnchor: [12, 24],
            popupAnchor: [0, -24]
        }),
        zIndexOffset: 100
    });
    
    // Add hover effect
    marker.on('mouseover', function() {
        this.openPopup();
    });
    
    return marker;
}

/**
 * Create a popup for a station
 * @private
 */
function createStationPopup(station) {
    // Create popup content
    const content = document.createElement('div');
    content.className = 'station-popup';
    
    // Add station name
    const name = document.createElement('h3');
    name.textContent = station.name;
    content.appendChild(name);
    
    // Add station ID if available
    if (station.id) {
        const id = document.createElement('div');
        id.className = 'station-id';
        id.textContent = `ID: ${station.id}`;
        content.appendChild(id);
    }
    
    // Add station type if available
    if (station.type) {
        const type = document.createElement('div');
        type.className = 'station-type';
        type.textContent = `Type: ${station.type}`;
        content.appendChild(type);
    }
    
    // Add additional station info if available
    if (station.lines && station.lines.length > 0) {
        const lines = document.createElement('div');
        lines.className = 'station-lines';
        lines.innerHTML = `<strong>Lines:</strong> ${station.lines.join(', ')}`;
        content.appendChild(lines);
    }
    
    // Add facilities if available
    if (station.facilities && Object.keys(station.facilities).length > 0) {
        const facilities = document.createElement('div');
        facilities.className = 'station-facilities';
        facilities.innerHTML = '<strong>Facilities:</strong>';
        
        const list = document.createElement('ul');
        
        Object.entries(station.facilities).forEach(([key, value]) => {
            if (value) {
                const item = document.createElement('li');
                item.textContent = key.replace(/([A-Z])/g, ' $1').trim();
                list.appendChild(item);
            }
        });
        
        facilities.appendChild(list);
        content.appendChild(facilities);
    }
    
    return content;
}
