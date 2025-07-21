/**
 * Routes data management
 */

import { CONFIG } from '../../config.js';
import { ROUTE_TYPES } from '../../constants.js';
import { logger } from '../utils/logger.js';
import loadRoutesFromMarkdown from './markdownLoader.js';

// Cache for route data
let routesCache = null;

/**
 * Load routes data from markdown files or cache
 * @returns {Promise<Array>} Array of route objects
 */
export async function loadRoutesData() {
    try {
        // Return cached data if available
        if (routesCache) {
            logger.debug('Returning cached routes data');
            return routesCache;
        }
        
        logger.info('Loading routes data from markdown...');
        
        // Load routes from markdown files
        let routes = await loadRoutesFromMarkdown();
        
        // Process and normalize route data
        routes = routes.map(route => {
            const normalizedRoute = {
                ...route,
                // Ensure type is lowercase and valid
                type: normalizeRouteType(route.type || ''),
                // Ensure color has a default based on type
                color: route.color || getDefaultColor(route.type || ''),
                // Ensure coordinates is an array
                coordinates: route.coordinates || [],
                // Ensure stops is an array
                stops: route.stops || []
            };
            
            logger.debug(`Processed route: ${route.id} (${route.name}), type: ${normalizedRoute.type}, stops: ${normalizedRoute.stops.length}`);
            return normalizedRoute;
        });
        
        // Cache the processed routes
        routesCache = routes;
        
        logger.info(`Loaded ${routes.length} routes from markdown`);
        return routes;
        
    } catch (error) {
        logger.error('Failed to load routes data from markdown:', error);
        throw error;
    }
}

/**
 * Get a route by ID
 * @param {string} routeId - The route ID to find
 * @returns {Object|undefined} The found route or undefined
 */
export function getRouteById(routeId) {
    if (!routesCache) return undefined;
    return routesCache.find(route => route.id === routeId);
}

/**
 * Get routes by type
 * @param {string} type - Route type to filter by
 * @returns {Array} Filtered array of routes
 */
export function getRoutesByType(type) {
    if (!routesCache) return [];
    const normalizedType = normalizeRouteType(type);
    return routesCache.filter(route => route.type === normalizedType);
}

/**
 * Save active routes to storage
 * @param {Set} activeRoutes - Set of active route IDs
 */
export function saveActiveRoutes(activeRoutes) {
    try {
        const activeRoutesArray = Array.from(activeRoutes);
        localStorage.setItem('activeRoutes', JSON.stringify(activeRoutesArray));
        logger.debug('Saved active routes to storage');
    } catch (error) {
        logger.error('Failed to save active routes:', error);
    }
}

/**
 * Load active routes from storage
 * @returns {Set} Set of active route IDs
 */
export function loadActiveRoutes() {
    try {
        const saved = localStorage.getItem('activeRoutes');
        if (saved) {
            const activeRoutes = new Set(JSON.parse(saved));
            logger.debug('Loaded active routes from storage');
            return activeRoutes;
        }
    } catch (error) {
        logger.error('Failed to load active routes:', error);
    }
    return new Set();
}

/**
 * Normalize route type to ensure consistency
 * @private
 */
function normalizeRouteType(type) {
    if (!type) return 'other';
    
    const lowerType = type.toLowerCase();
    
    // Map common variations to standard types
    const typeMap = {
        'u': ROUTE_TYPES.METRO,
        'u-bahn': ROUTE_TYPES.METRO,
        'metro': ROUTE_TYPES.METRO,
        'tram': ROUTE_TYPES.TRAM,
        'bus': ROUTE_TYPES.BUS,
        'nightbus': ROUTE_TYPES.NIGHTBUS,
        'n': ROUTE_TYPES.NIGHTBUS,
        'night': ROUTE_TYPES.NIGHTBUS
    };
    
    return typeMap[lowerType] || lowerType;
}

/**
 * Get default color for a route type
 * @private
 */
function getDefaultColor(type) {
    const normalizedType = normalizeRouteType(type);
    return CONFIG.ROUTES.DEFAULT_COLORS[normalizedType] || CONFIG.ROUTES.DEFAULT_COLORS.default;
}
