/**
 * Main routes module
 */

import { logger } from '../utils/logger.js';
import { loadRoutes } from './data.js';
import { initRouteUI, updateRouteToggleState } from './ui.js';
import { setupRouteVisualization, showRoute, hideRoute, highlightRoute } from './visualization.js';

// Store references to route data and map
let routes = [];
let map = null;
let routeLayers = new Map();
let activeRoutes = new Set();

// Store the current route data
let routeData = {
    routes: [],
    stops: [],
    loading: false,
    error: null
};

/**
 * Initialize the routes module
 * @param {L.Map} leafletMap - The Leaflet map instance
 */
export async function initRoutes(leafletMap) {
    try {
        logger.info('Initializing routes module...');
        
        // Store the map reference
        map = leafletMap;
        
        // Set loading state
        routeData.loading = true;
        routeData.error = null;
        
        try {
            // Load route data
            const { routes: loadedRoutes, stops } = await loadRoutes();
            routes = loadedRoutes;
            
            // Update route data
            routeData = {
                routes: loadedRoutes,
                stops: stops || [],
                loading: false,
                error: null
            };
            
            logger.info(`Loaded ${routes.length} routes and ${routeData.stops.length} stops`);
            
            // Initialize the route visualization
            setupRouteVisualization(map, routes, routeLayers, activeRoutes);
            
            // Initialize the route UI
            initRouteUI(routes, handleRouteToggle);
            
            // Show a default set of routes (e.g., all metro lines)
            showDefaultRoutes();
            
        } catch (error) {
            logger.error('Failed to load route data:', error);
            routeData.error = error.message || 'Failed to load route data';
            routeData.loading = false;
            throw error;
        }
        
        logger.info('Routes module initialized');
        
    } catch (error) {
        logger.error('Failed to initialize routes module:', error);
        routeData.error = error.message || 'Failed to initialize routes module';
        routeData.loading = false;
        throw error;
    }
}

/**
 * Show all routes by default
 */
function showDefaultRoutes() {
    // Show all routes by default
    routes.forEach(route => {
        if (!activeRoutes.has(route.id)) {
            handleRouteToggle(route.id, true);
        }
    });
}

/**
 * Handle route toggle events
 * @private
 */
function handleRouteToggle(routeId, isActive) {
    try {
        logger.debug(`Route ${routeId} toggled: ${isActive ? 'on' : 'off'}`);
        
        // Find the route data
        const route = routes.find(r => r.id === routeId);
        if (!route) {
            logger.warn(`Route ${routeId} not found`);
            return;
        }
        
        // Update the active routes set
        if (isActive) {
            activeRoutes.add(routeId);
            showRoute(map, routeId, routeLayers, route);
        } else {
            activeRoutes.delete(routeId);
            hideRoute(map, routeId, routeLayers);
        }
        
        // Update the UI to reflect the new state
        updateRouteToggleState(routeId, isActive);
        
    } catch (error) {
        logger.error(`Failed to toggle route ${routeId}:`, error);
    }
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
