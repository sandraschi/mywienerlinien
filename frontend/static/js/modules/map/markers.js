/**
 * Map markers and related utilities
 */

import L from 'leaflet';
import { CONFIG } from '../../config.js';
import { ROUTE_TYPES } from '../../constants.js';
import { logger } from '../utils/logger.js';

// Cache for markers to avoid duplicates
const markerCache = new Map();

/**
 * Create a marker with custom icon
 * @param {L.LatLng} latlng - Marker position
 * @param {Object} options - Marker options
 * @param {string} [options.type='default'] - Type of marker
 * @param {string} [options.color] - Marker color
 * @param {string} [options.icon] - Custom icon class
 * @param {string} [options.html] - Custom HTML content
 * @param {string} [options.title] - Marker title
 * @param {boolean} [options.draggable=false] - Whether the marker is draggable
 * @returns {L.Marker} Created marker
 */
export function createMarker(latlng, options = {}) {
    try {
        const {
            type = 'default',
            color = CONFIG.MARKERS.STOP.COLOR,
            icon = null,
            html = null,
            title = '',
            draggable = false
        } = options;

        // Create a unique cache key
        const cacheKey = `${type}-${latlng.lat.toFixed(6)}-${latlng.lng.toFixed(6)}`;
        
        // Return cached marker if available
        if (markerCache.has(cacheKey) && !options.forceNew) {
            return markerCache.get(cacheKey);
        }

        let marker;
        
        // Create different marker types
        switch (type) {
            case 'circle':
                marker = L.circleMarker(latlng, {
                    radius: 8,
                    fillColor: color,
                    color: '#fff',
                    weight: 2,
                    opacity: 1,
                    fillOpacity: 0.8,
                    ...options
                });
                break;
                
            case 'icon':
                marker = L.marker(latlng, {
                    icon: L.divIcon({
                        className: 'custom-marker',
                        html: html || `<div class="marker-icon ${icon}" style="background: ${color}"></div>`,
                        iconSize: [24, 24],
                        iconAnchor: [12, 24],
                        popupAnchor: [0, -24]
                    }),
                    title,
                    draggable,
                    ...options
                });
                break;
                
            default:
                marker = L.marker(latlng, {
                    title,
                    draggable,
                    ...options
                });
        }
        
        // Cache the marker
        markerCache.set(cacheKey, marker);
        
        return marker;
        
    } catch (error) {
        logger.error('Failed to create marker:', error);
        throw error;
    }
}

/**
 * Create a route stop marker
 * @param {Object} stop - Stop data
 * @param {string} routeType - Type of route (metro, tram, bus, nightbus)
 * @param {boolean} [isTerminus=false] - Whether this is a terminus stop
 * @returns {L.CircleMarker} Created stop marker
 */
export function createStopMarker(stop, routeType, isTerminus = false) {
    try {
        if (!stop?.coordinates) {
            throw new Error('Stop coordinates are required');
        }

        const radius = isTerminus 
            ? CONFIG.MARKERS.STOP.TERMINUS_RADIUS 
            : CONFIG.MARKERS.STOP.RADIUS;
            
        const color = CONFIG.ROUTES.DEFAULT_COLORS[routeType] || CONFIG.ROUTES.DEFAULT_COLORS.default;
        
        const marker = L.circleMarker(stop.coordinates, {
            radius,
            fillColor: color,
            color: '#fff',
            weight: CONFIG.MARKERS.STOP.WEIGHT,
            opacity: CONFIG.MARKERS.STOP.OPACITY,
            fillOpacity: CONFIG.MARKERS.STOP.FILL_OPACITY,
            className: `stop-marker ${routeType} ${isTerminus ? 'terminus' : ''}`
        });
        
        // Add hover effects
        marker.on('mouseover', () => {
            marker.setStyle({
                weight: CONFIG.MARKERS.STOP.HOVER_WEIGHT,
                opacity: 1,
                fillOpacity: 1
            });
        });
        
        marker.on('mouseout', () => {
            marker.setStyle({
                weight: CONFIG.MARKERS.STOP.WEIGHT,
                opacity: CONFIG.MARKERS.STOP.OPACITY,
                fillOpacity: CONFIG.MARKERS.STOP.FILL_OPACITY
            });
        });
        
        return marker;
        
    } catch (error) {
        logger.error('Failed to create stop marker:', error);
        throw error;
    }
}

/**
 * Create a vehicle marker
 * @param {Object} vehicle - Vehicle data
 * @param {string} routeType - Type of route
 * @returns {L.Marker} Created vehicle marker
 */
export function createVehicleMarker(vehicle, routeType) {
    try {
        if (!vehicle?.coordinates) {
            throw new Error('Vehicle coordinates are required');
        }
        
        const color = CONFIG.ROUTES.DEFAULT_COLORS[routeType] || CONFIG.ROUTES.DEFAULT_COLORS.default;
        
        // Create a custom vehicle icon
        const icon = L.divIcon({
            className: 'vehicle-marker',
            html: `
                <div class="vehicle-icon" style="background: ${color}">
                    <span class="vehicle-badge">${vehicle.routeNumber || ''}</span>
                </div>
            `,
            iconSize: CONFIG.MARKERS.VEHICLE.ICON_SIZE,
            iconAnchor: CONFIG.MARKERS.VEHICLE.ICON_ANCHOR,
            popupAnchor: CONFIG.MARKERS.VEHICLE.POPUP_OFFSET
        });
        
        // Create the marker with rotation if bearing is available
        const marker = L.marker(vehicle.coordinates, {
            icon,
            rotationAngle: vehicle.bearing || 0,
            rotationOrigin: 'center',
            zIndexOffset: 1000 // Ensure vehicles appear above other markers
        });
        
        return marker;
        
    } catch (error) {
        logger.error('Failed to create vehicle marker:', error);
        throw error;
    }
}

/**
 * Clear all markers from the cache
 */
export function clearMarkerCache() {
    markerCache.clear();
    logger.debug('Marker cache cleared');
}
