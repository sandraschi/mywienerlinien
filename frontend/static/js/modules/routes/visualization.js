/**
 * Route visualization and map interaction
 */

import L from 'leaflet';
import { CONFIG } from '../../config.js';
import { ROUTE_TYPES } from '../../constants.js';
import { logger } from '../utils/logger.js';
import { createPolyline, createMarker, createPopup } from '../map/utils.js';

// Store references to route polylines and markers
const routeLayers = new Map();
const routeLabels = new Map();
const stopMarkers = new Map();

// Colors for different route types
const ROUTE_COLORS = {
    [ROUTE_TYPES.METRO]: '#c70f3e',
    [ROUTE_TYPES.TRAM]: '#f39200',
    [ROUTE_TYPES.BUS]: '#0067b1',
    [ROUTE_TYPES.NIGHTBUS]: '#1a1a1a',
    default: '#666666'
};

// Default route style
const DEFAULT_ROUTE_STYLE = {
    weight: 4,
    opacity: 0.8,
    color: '#666666',
    dashArray: '5, 5',
    lineCap: 'round',
    lineJoin: 'round'
};

// Active route style
const ACTIVE_ROUTE_STYLE = {
    weight: 6,
    opacity: 1.0,
    dashArray: '',
    lineCap: 'round',
    lineJoin: 'round',
    className: 'active-route'
};

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
        
        // Create a single layer group for all routes
        const routesLayerGroup = L.layerGroup();
        routesLayerGroup.addTo(map);
        
        // Process each route
        routes.forEach(route => {
            try {
                // Create a layer group for this route
                const routeGroup = L.layerGroup();
                
                // Store the route group
                routeLayers.set(route.id, routeGroup);
                
                // Add to the main routes layer group
                routesLayerGroup.addLayer(routeGroup);
                
                // If this route should be active by default, show it
                if (activeRoutes.has(route.id)) {
                    showRoute(map, route.id, routeLayers);
                }
                
            } catch (error) {
                logger.error(`Failed to process route ${route.id}:`, error);
            }
        });
        
        logger.info(`Route visualization set up with ${routes.length} routes`);
        
    } catch (error) {
        logger.error('Failed to set up route visualization:', error);
        throw error;
    }
}

/**
 * Add a route to the map
 * @param {L.Map} map - The Leaflet map instance
 * @param {string} routeId - ID of the route to add
 * @param {Map} routeLayers - Map of route layers
 * @param {Object} route - Route object containing coordinates and stops
 */
export function addRouteToMap(map, routeId, routeLayers, route = null) {
    try {
        logger.debug(`Adding route to map: ${routeId}`);
        
        // Get or create the route group
        let routeGroup = routeLayers.get(routeId);
        if (!routeGroup) {
            routeGroup = L.layerGroup();
            routeLayers.set(routeId, routeGroup);
        }
        
        // If we have route data, create the visualization
        if (route) {
            // Create and add the route polyline
            const polyline = createRoutePolyline(route);
            if (polyline) {
                routeGroup.addLayer(polyline);
            }
            
            // Add stop markers if available
            if (route.stops && route.stops.length > 0) {
                const markers = createStopMarkers(route);
                if (markers && markers.length > 0) {
                    markers.forEach(marker => routeGroup.addLayer(marker));
                    stopMarkers.set(routeId, markers);
                }
            }
            
            // Add route label at midpoint if we have coordinates
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
        }
        
        logger.debug(`Route ${routeId} added to map`);
        
    } catch (error) {
        logger.error(`Failed to add route ${routeId} to map:`, error);
        throw error;
    }
}

/**
 * Show a route on the map
 * @param {L.Map} map - The Leaflet map instance
 * @param {string} routeId - ID of the route to show
 * @param {Map} routeLayers - Map of route layers
 * @param {Object} route - Optional route data (if not already loaded)
 */
export function showRoute(map, routeId, routeLayers, route = null) {
    try {
        logger.debug(`Showing route: ${routeId}`);
        
        // Add the route if it's not already on the map
        if (!routeLayers.has(routeId) || !map.hasLayer(routeLayers.get(routeId))) {
            addRouteToMap(map, routeId, routeLayers, route);
        }
        
        // Ensure the route is visible
        const routeGroup = routeLayers.get(routeId);
        if (routeGroup && !map.hasLayer(routeGroup)) {
            routeGroup.addTo(map);
        }
        
        // Highlight the route
        highlightRoute(routeId, true);
        
        return routeGroup;
    } catch (error) {
        logger.error(`Failed to show route ${routeId}:`, error);
        throw error;
    }
}

/**
 * Hide a route from the map
 * @param {L.Map} map - The Leaflet map instance
 * @param {string} routeId - ID of the route to hide
 * @param {Map} routeLayers - Map of route layers
 */
export function hideRoute(map, routeId, routeLayers) {
    try {
        logger.debug(`Hiding route: ${routeId}`);
        
        // Remove the route from the map but keep it in the layers map
        const routeGroup = routeLayers.get(routeId);
        if (routeGroup && map.hasLayer(routeGroup)) {
            routeGroup.removeFrom(map);
        }
        
        // Remove highlight
        highlightRoute(routeId, false);
        
    } catch (error) {
        logger.error(`Failed to hide route ${routeId}:`, error);
        throw error;
    }
}

/**
 * Highlight a route on the map
 * @param {string} routeId - ID of the route to highlight
 * @param {boolean} highlight - Whether to highlight or unhighlight the route
 */
export function highlightRoute(routeId, highlight) {
    try {
        // Get all polylines for this route (there might be multiple segments)
        const routeGroup = routeLayers.get(routeId);
        if (!routeGroup) {
            return;
        }
        
        // Find all polylines in the route group
        routeGroup.eachLayer(layer => {
            if (layer instanceof L.Polyline) {
                if (highlight) {
                    layer.setStyle({
                        ...ACTIVE_ROUTE_STYLE,
                        color: layer.options.color || ROUTE_COLORS.default
                    });
                    layer.bringToFront();
                } else {
                    // Reset to default style
                    layer.setStyle({
                        ...DEFAULT_ROUTE_STYLE,
                        color: layer.options.color || ROUTE_COLORS.default
                    });
                }
            }
        });
        
    } catch (error) {
        logger.error(`Failed to ${highlight ? 'highlight' : 'unhighlight'} route ${routeId}:`, error);
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
    if (!route.coordinates || route.coordinates.length < 2) {
        logger.warn(`Route ${route.id} has insufficient coordinates`);
        return null;
    }
    
    try {
        // Convert coordinates to LatLng objects
        const latlngs = route.coordinates.map(coord => {
            // Ensure coordinates are in the correct format [lat, lng]
            if (Array.isArray(coord) && coord.length >= 2) {
                return L.latLng(coord[0], coord[1]);
            }
            return null;
        }).filter(Boolean); // Remove any null/invalid coordinates
        
        if (latlngs.length < 2) {
            logger.warn(`Route ${route.id} has no valid coordinates`);
            return null;
        }
        
        // Get the color based on route type
        const color = ROUTE_COLORS[route.type] || ROUTE_COLORS.default;
        
        // Create polyline with appropriate style
        return L.polyline(latlngs, {
            ...DEFAULT_ROUTE_STYLE,
            color: color
        });
        
    } catch (error) {
        logger.error(`Failed to create polyline for route ${route.id}:`, error);
        return null;
    }
}

/**
 * Create stop markers for a route
 * @private
 */
function createStopMarkers(route) {
    if (!route.stops || route.stops.length === 0) {
        return [];
    }
    
    try {
        return route.stops.map(stop => {
            // Skip if coordinates are invalid
            if (typeof stop.lat !== 'number' || typeof stop.lng !== 'number') {
                return null;
            }
            
            const marker = L.circleMarker(
                [stop.lat, stop.lng],
                {
                    radius: 4,
                    fillColor: '#ffffff',
                    color: ROUTE_COLORS[route.type] || ROUTE_COLORS.default,
                    weight: 1.5,
                    opacity: 0.8,
                    fillOpacity: 1.0
                }
            );
            
            // Add popup with stop information
            if (stop.name) {
                marker.bindPopup(`
                    <div class="stop-popup">
                        <h4>${stop.name}</h4>
                        <div class="route-badge" style="background-color: ${ROUTE_COLORS[route.type] || ROUTE_COLORS.default}">
                            ${route.id}
                        </div>
                    </div>
                `);
            }
            
            return marker;
        }).filter(Boolean); // Remove any null markers
        
    } catch (error) {
        logger.error(`Failed to create stop markers for route ${route.id}:`, error);
        return [];
    }
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

