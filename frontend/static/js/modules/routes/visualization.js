/**
 * Route visualization and map interaction
 */

import L from 'leaflet';
import { CONFIG } from '../../config.js';
import { ROUTE_TYPES } from '../../constants.js';
import { logger } from '../utils/logger.js';
import { createPolyline, createMarker, createPopup } from '../map/utils.js';

// Store references to route polylines and markers
const routePolylines = new Map();
const routeLabels = new Map();
const stopMarkers = new Map();

/**
 * Set up route visualization on the map
 * @param {L.Map} map - The Leaflet map instance
 * @param {Array} routes - Array of route objects
 * @param {Map} routeLayers - Map to store route layers
 * @param {Set} activeRoutes - Set of active route IDs
 */
export function setupRouteVisualization(map, routes, routeLayers, activeRoutes) {
    try {
        logger.info('Setting up route visualization...');
        
        // Clear any existing layers
        clearAllRoutes(map);
        
        // Create layer groups for each route type
        const layerGroups = {
            [ROUTE_TYPES.METRO]: L.layerGroup(),
            [ROUTE_TYPES.TRAM]: L.layerGroup(),
            [ROUTE_TYPES.BUS]: L.layerGroup(),
            [ROUTE_TYPES.NIGHTBUS]: L.layerGroup()
        };
        
        // Add layer groups to the map
        Object.values(layerGroups).forEach(group => group.addTo(map));
        
        // Process each route
        routes.forEach(route => {
            try {
                // Create a layer group for this route
                const routeGroup = L.layerGroup();
                
                // Store the route group
                routeLayers.set(route.id, routeGroup);
                
                // Add to the appropriate layer group
                const typeGroup = layerGroups[route.type] || layerGroups[ROUTE_TYPES.BUS];
                typeGroup.addLayer(routeGroup);
                
                // If this route should be active by default, show it
                if (activeRoutes.has(route.id)) {
                    showRoute(map, route, routeLayers);
                }
                
            } catch (error) {
                logger.error(`Failed to process route ${route.id}:`, error);
            }
        });
        
        logger.info('Route visualization set up');
        
    } catch (error) {
        logger.error('Failed to set up route visualization:', error);
        throw error;
    }
}

/**
 * Add a route to the map
 * @param {L.Map} map - The Leaflet map instance
 * @param {Object} route - Route object to add
 * @param {Map} routeLayers - Map of route layers
 */
export function addRouteToMap(map, route, routeLayers) {
    try {
        logger.debug(`Adding route to map: ${route.id}`);
        
        const routeGroup = routeLayers.get(route.id) || L.layerGroup();
        
        // Create and add the route polyline
        const polyline = createRoutePolyline(route);
        routeGroup.addLayer(polyline);
        
        // Add stop markers if available
        if (route.stops && route.stops.length > 0) {
            const markers = createStopMarkers(route);
            markers.forEach(marker => routeGroup.addLayer(marker));
            
            // Store stop markers for later reference
            stopMarkers.set(route.id, markers);
        }
        
        // Add route label at midpoint
        if (route.coordinates && route.coordinates.length > 1) {
            const label = createRouteLabel(route);
            if (label) {
                routeGroup.addLayer(label);
                routeLabels.set(route.id, label);
            }
        }
        
        // Store the polyline for later reference
        routePolylines.set(route.id, polyline);
        
        // Add the route group to the map if not already added
        if (!map.hasLayer(routeGroup)) {
            routeGroup.addTo(map);
        }
        
        // Fit the map to show the new route
        if (route.coordinates && route.coordinates.length > 0) {
            map.fitBounds(L.latLngBounds(route.coordinates), {
                padding: [50, 50],
                maxZoom: 15
            });
        }
        
        logger.debug(`Route ${route.id} added to map`);
        
    } catch (error) {
        logger.error(`Failed to add route ${route.id} to map:`, error);
        throw error;
    }
}

/**
 * Show a route on the map
 * @param {L.Map} map - The Leaflet map instance
 * @param {Object} route - Route object to show
 * @param {Map} routeLayers - Map of route layers
 */
export function showRoute(map, route, routeLayers) {
    try {
        const routeGroup = routeLayers.get(route.id);
        if (routeGroup) {
            // If the route doesn't have a polyline yet, add it
            if (!routePolylines.has(route.id)) {
                addRouteToMap(map, route, routeLayers);
            } else {
                // Otherwise, just show the existing route group
                map.addLayer(routeGroup);
            }
            logger.debug(`Route ${route.id} shown`);
        }
    } catch (error) {
        logger.error(`Failed to show route ${route.id}:`, error);
    }
}

/**
 * Hide a route from the map
 * @param {L.Map} map - The Leaflet map instance
 * @param {Object} route - Route object to hide
 * @param {Map} routeLayers - Map of route layers
 */
export function hideRoute(map, route, routeLayers) {
    try {
        const routeGroup = routeLayers.get(route.id);
        if (routeGroup) {
            map.removeLayer(routeGroup);
            logger.debug(`Route ${route.id} hidden`);
        }
    } catch (error) {
        logger.error(`Failed to hide route ${route.id}:`, error);
    }
}

/**
 * Clear all routes from the map
 * @param {L.Map} map - The Leaflet map instance
 */
export function clearAllRoutes(map) {
    try {
        // Remove all polylines
        routePolylines.forEach((polyline, id) => {
            if (map.hasLayer(polyline)) {
                map.removeLayer(polyline);
            }
        });
        
        // Remove all labels
        routeLabels.forEach((label, id) => {
            if (map.hasLayer(label)) {
                map.removeLayer(label);
            }
        });
        
        // Remove all stop markers
        stopMarkers.forEach((markers, routeId) => {
            markers.forEach(marker => {
                if (map.hasLayer(marker)) {
                    map.removeLayer(marker);
                }
            });
        });
        
        // Clear all collections
        routePolylines.clear();
        routeLabels.clear();
        stopMarkers.clear();
        
        logger.debug('All routes cleared from map');
        
    } catch (error) {
        logger.error('Failed to clear routes:', error);
        throw error;
    }
}

/**
 * Create a polyline for a route
 * @private
 */
function createRoutePolyline(route) {
    return createPolyline(route.coordinates, {
        color: route.color,
        weight: CONFIG.ROUTES.LINE_WEIGHT,
        opacity: CONFIG.ROUTES.LINE_OPACITY,
        className: `route-line ${route.type}`
    });
}

/**
 * Create stop markers for a route
 * @private
 */
function createStopMarkers(route) {
    return route.stops
        .filter(stop => stop.coordinates)
        .map((stop, index, array) => {
            const isTerminus = index === 0 || index === array.length - 1;
            return createMarker(stop.coordinates, {
                radius: isTerminus ? 6 : 4,
                fillColor: route.color,
                color: '#fff',
                weight: 1,
                opacity: 1,
                fillOpacity: 0.8,
                className: `stop-marker ${route.type} ${isTerminus ? 'terminus' : ''}`
            });
        });
}

/**
 * Create a label for a route
 * @private
 */
function createRouteLabel(route) {
    try {
        if (!route.coordinates || route.coordinates.length === 0) {
            return null;
        }
        
        // Calculate midpoint of the route
        const midIndex = Math.floor(route.coordinates.length / 2);
        const midPoint = route.coordinates[midIndex];
        
        // Create route label
        return L.marker(midPoint, {
            icon: L.divIcon({
                className: 'route-label',
                html: `<div style="background: ${route.color}">${route.name}</div>`,
                iconSize: null,
                iconAnchor: [0, 0]
            }),
            interactive: false
        });
        
    } catch (error) {
        logger.error(`Failed to create label for route ${route.id}:`, error);
        return null;
    }
}
