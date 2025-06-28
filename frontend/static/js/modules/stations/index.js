/**
 * Stations module - Manages station visualization and interaction
 */

import { logger } from '../utils/logger.js';
import { loadStationsData } from './data.js';
import { setupStationVisualization } from './visualization.js';
import { initStationUI } from './ui.js';

// Store stations data
let stations = [];
let stationLayers = new Map();
const activeStations = new Set();

/**
 * Initialize the stations module
 * @param {L.Map} map - The Leaflet map instance
 * @returns {Promise<void>}
 */
export async function initStations(map) {
    try {
        logger.info('Initializing stations module...');
        
        // Load stations data
        stations = await loadStationsData();
        
        // Set up station visualization
        setupStationVisualization(map, stations, stationLayers, activeStations);
        
        // Initialize station UI components
        initStationUI(stations, (stationId, isVisible) => {
            updateStationVisibility(map, stationId, isVisible, stations, stationLayers, activeStations);
        });
        
        logger.info('Stations module initialized');
        
    } catch (error) {
        logger.error('Failed to initialize stations module:', error);
        throw error;
    }
}

/**
 * Update station visibility on the map
 * @param {L.Map} map - The Leaflet map instance
 * @param {string} stationId - ID of the station to update
 * @param {boolean} isVisible - Whether the station should be visible
 * @param {Array} allStations - All available stations
 * @param {Map} layers - Map of station layers
 * @param {Set} activeSet - Set of active station IDs
 */
function updateStationVisibility(map, stationId, isVisible, allStations, layers, activeSet) {
    logger.debug(`Updating station visibility: ${stationId} = ${isVisible}`);
    
    const station = allStations.find(s => s.id === stationId);
    if (!station) {
        logger.warn(`Station not found: ${stationId}`);
        return;
    }
    
    if (isVisible) {
        // Show the station
        if (!layers.has(stationId)) {
            addStationToMap(map, station, layers);
        } else {
            showStation(map, station, layers);
        }
        activeSet.add(stationId);
    } else {
        // Hide the station
        hideStation(map, station, layers);
        activeSet.delete(stationId);
    }
    
    // Save active stations to storage
    saveActiveStations(activeSet);
}

/**
 * Add a station to the map
 * @private
 */
function addStationToMap(map, station, layers) {
    // Implementation moved to visualization.js
}

/**
 * Show a station on the map
 * @private
 */
function showStation(map, station, layers) {
    // Implementation moved to visualization.js
}

/**
 * Hide a station from the map
 * @private
 */
function hideStation(map, station, layers) {
    // Implementation moved to visualization.js
}

/**
 * Save active stations to storage
 * @private
 */
function saveActiveStations(activeSet) {
    // Implementation moved to data.js
}

// Export public API
export {
    stations,
    stationLayers,
    activeStations,
    updateStationVisibility
};
