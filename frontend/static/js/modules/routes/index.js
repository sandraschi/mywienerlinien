/**
 * Routes module - Manages route visualization and interaction
 */

import { logger } from '../utils/logger.js';
import { initRouteUI } from './ui.js';
import { loadRoutesData } from './data.js';
import { setupRouteVisualization } from './visualization.js';

// Store routes data
let routes = [];
let routeLayers = new Map();
const activeRoutes = new Set();

/**
 * Initialize the routes module
 * @param {L.Map} map - The Leaflet map instance
 * @returns {Promise<void>}
 */
export async function initRoutes(map) {
    try {
        logger.info('Initializing routes module...');
        
        // Load routes data
        routes = await loadRoutesData();
        
        // Set up route visualization
        setupRouteVisualization(map, routes, routeLayers, activeRoutes);
        
        // Initialize route UI components
        initRouteUI(routes, (routeId, isVisible) => {
            updateRouteVisibility(map, routeId, isVisible, routes, routeLayers, activeRoutes);
        });
        
        logger.info('Routes module initialized');
        
    } catch (error) {
        logger.error('Failed to initialize routes module:', error);
        throw error;
    }
}

/**
 * Update route visibility on the map
 * @param {L.Map} map - The Leaflet map instance
 * @param {string} routeId - ID of the route to update
 * @param {boolean} isVisible - Whether the route should be visible
 * @param {Array} allRoutes - All available routes
 * @param {Map} layers - Map of route layers
 * @param {Set} activeSet - Set of active route IDs
 */
function updateRouteVisibility(map, routeId, isVisible, allRoutes, layers, activeSet) {
    logger.debug(`Updating route visibility: ${routeId} = ${isVisible}`);
    
    // Find all routes with this ID (there might be multiple for different directions)
    const matchingRoutes = allRoutes.filter(r => r.id === routeId);
    
    if (matchingRoutes.length === 0) {
        logger.warn(`No routes found with ID: ${routeId}`);
        return;
    }
    
    logger.debug(`Found ${matchingRoutes.length} route(s) with ID ${routeId}`);
    
    matchingRoutes.forEach(route => {
        if (isVisible) {
            // Add the route to the map if it's not already there
            if (!route.polyline) {
                addRouteToMap(map, route, layers);
            } else {
                // Show existing route
                showRoute(map, route, layers);
            }
            activeSet.add(routeId);
        } else {
            // Hide the route
            hideRoute(map, route, layers);
            activeSet.delete(routeId);
        }
    });
    
    // Save active routes to storage
    saveActiveRoutes(activeSet);
}

/**
 * Add a route to the map
 * @private
 */
function addRouteToMap(map, route, layers) {
    // Implementation moved to visualization.js
}

/**
 * Show a route on the map
 * @private
 */
function showRoute(map, route, layers) {
    // Implementation moved to visualization.js
}

/**
 * Hide a route from the map
 * @private
 */
function hideRoute(map, route, layers) {
    // Implementation moved to visualization.js
}

/**
 * Save active routes to storage
 * @private
 */
function saveActiveRoutes(activeSet) {
    // Implementation moved to data.js
}

// Export public API
export {
    routes,
    routeLayers,
    activeRoutes,
    updateRouteVisibility
};
