/**
 * Vehicles module - Manages vehicle tracking and visualization
 */

import { logger } from '../utils/logger.js';
import { loadVehiclesData, startVehicleUpdates } from './data.js';
import { setupVehicleVisualization } from './visualization.js';
import { initVehicleUI } from './ui.js';

// Store vehicles data
let vehicles = [];
const vehicleLayers = new Map();
const activeVehicles = new Set();
let updateInterval = null;

/**
 * Initialize the vehicles module
 * @param {L.Map} map - The Leaflet map instance
 * @returns {Promise<void>}
 */
export async function initVehicles(map) {
    try {
        logger.info('Initializing vehicles module...');
        
        // Set up vehicle visualization
        setupVehicleVisualization(map, vehicleLayers);
        
        // Initialize vehicle UI components
        initVehicleUI({
            onToggle: (vehicleId, isVisible) => {
                updateVehicleVisibility(map, vehicleId, isVisible);
            },
            onRefresh: () => {
                refreshVehicles(map);
            },
            onAutoUpdateChange: (enabled) => {
                if (enabled) {
                    startAutoUpdates(map);
                } else {
                    stopAutoUpdates();
                }
            }
        });
        
        // Load initial vehicle data
        await refreshVehicles(map);
        
        // Start auto-updates
        startAutoUpdates(map);
        
        logger.info('Vehicles module initialized');
        
    } catch (error) {
        logger.error('Failed to initialize vehicles module:', error);
        throw error;
    }
}

/**
 * Update vehicle visibility on the map
 * @param {L.Map} map - The Leaflet map instance
 * @param {string} vehicleId - ID of the vehicle to update
 * @param {boolean} isVisible - Whether the vehicle should be visible
 */
function updateVehicleVisibility(map, vehicleId, isVisible) {
    logger.debug(`Updating vehicle visibility: ${vehicleId} = ${isVisible}`);
    
    try {
        if (isVisible) {
            // Show the vehicle
            const vehicle = vehicles.find(v => v.id === vehicleId);
            if (vehicle) {
                showVehicle(map, vehicle);
                activeVehicles.add(vehicleId);
            }
        } else {
            // Hide the vehicle
            hideVehicle(map, vehicleId);
            activeVehicles.delete(vehicleId);
        }
        
        // Save active vehicles to storage
        saveActiveVehicles(activeVehicles);
        
    } catch (error) {
        logger.error(`Failed to update vehicle ${vehicleId} visibility:`, error);
    }
}

/**
 * Show a vehicle on the map
 * @private
 */
function showVehicle(map, vehicle) {
    // Implementation moved to visualization.js
}

/**
 * Hide a vehicle from the map
 * @private
 */
function hideVehicle(map, vehicleId) {
    // Implementation moved to visualization.js
}

/**
 * Refresh vehicle data from the server
 * @param {L.Map} map - The Leaflet map instance
 */
async function refreshVehicles(map) {
    try {
        logger.debug('Refreshing vehicle data...');
        
        // Show loading indicator
        // (Implementation depends on your UI framework)
        
        // Load vehicle data
        vehicles = await loadVehiclesData();
        
        // Update vehicle markers
        updateVehicleMarkers(map);
        
        logger.info(`Refreshed ${vehicles.length} vehicles`);
        
    } catch (error) {
        logger.error('Failed to refresh vehicle data:', error);
        throw error;
    } finally {
        // Hide loading indicator
    }
}

/**
 * Update vehicle markers on the map
 * @private
 */
function updateVehicleMarkers(map) {
    // Implementation moved to visualization.js
}

/**
 * Start automatic vehicle updates
 * @private
 */
function startAutoUpdates(map) {
    stopAutoUpdates(); // Clear any existing interval
    
    updateInterval = setInterval(() => {
        refreshVehicles(map).catch(error => {
            logger.error('Auto-update failed:', error);
        });
    }, 30000); // Update every 30 seconds
    
    logger.debug('Started vehicle auto-updates');
}

/**
 * Stop automatic vehicle updates
 * @private
 */
function stopAutoUpdates() {
    if (updateInterval) {
        clearInterval(updateInterval);
        updateInterval = null;
        logger.debug('Stopped vehicle auto-updates');
    }
}

/**
 * Save active vehicles to storage
 * @private
 */
function saveActiveVehicles(activeSet) {
    try {
        const activeVehiclesArray = Array.from(activeSet);
        localStorage.setItem('activeVehicles', JSON.stringify(activeVehiclesArray));
        logger.debug('Saved active vehicles to storage');
    } catch (error) {
        logger.error('Failed to save active vehicles:', error);
    }
}

// Clean up on page unload
window.addEventListener('beforeunload', () => {
    stopAutoUpdates();
});

// Export public API
export {
    vehicles,
    vehicleLayers,
    activeVehicles,
    updateVehicleVisibility,
    refreshVehicles
};
