/**
 * Map utility functions
 */

import L from 'leaflet';
import { CONFIG } from '../../config.js';
import { logger } from '../utils/logger.js';

/**
 * Format coordinates for display
 * @param {L.LatLng} latlng - Coordinates to format
 * @param {number} [precision=6] - Decimal places
 * @returns {string} Formatted coordinates
 */
export function formatCoordinates(latlng, precision = 6) {
    if (!latlng) return 'N/A';
    const lat = typeof latlng.lat === 'function' ? latlng.lat() : latlng.lat;
    const lng = typeof latlng.lng === 'function' ? latlng.lng() : latlng.lng;
    return `${lat.toFixed(precision)}, ${lng.toFixed(precision)}`;
}

/**
 * Calculate the distance between two points in meters
 * @param {L.LatLng} point1 - First point
 * @param {L.LatLng} point2 - Second point
 * @returns {number} Distance in meters
 */
export function calculateDistance(point1, point2) {
    try {
        if (!point1 || !point2) return 0;
        return map.distanceTo(point1, point2);
    } catch (error) {
        logger.error('Failed to calculate distance:', error);
        return 0;
    }
}

/**
 * Fit the map to show all coordinates
 * @param {Array<L.LatLng>} coordinates - Array of coordinates
 * @param {Object} [options] - Fit bounds options
 * @param {number} [options.padding=50] - Padding in pixels
 * @param {number} [options.maxZoom=15] - Maximum zoom level
 */
export function fitToCoordinates(coordinates, options = {}) {
    try {
        if (!coordinates?.length) return;
        
        const bounds = L.latLngBounds(coordinates);
        const padding = options.padding || 50;
        const maxZoom = options.maxZoom || 15;
        
        map.fitBounds(bounds, {
            padding: [padding, padding],
            maxZoom
        });
        
    } catch (error) {
        logger.error('Failed to fit map to coordinates:', error);
    }
}

/**
 * Create a polyline with default styling
 * @param {Array<L.LatLng>} coordinates - Array of coordinates
 * @param {Object} [options] - Polyline options
 * @returns {L.Polyline} Created polyline
 */
export function createPolyline(coordinates, options = {}) {
    try {
        return L.polyline(coordinates, {
            color: options.color || '#3388ff',
            weight: options.weight || 5,
            opacity: options.opacity || 0.8,
            lineJoin: 'round',
            className: options.className || '',
            ...options
        });
    } catch (error) {
        logger.error('Failed to create polyline:', error);
        throw error;
    }
}

/**
 * Create a popup with consistent styling
 * @param {string} content - Popup content
 * @param {Object} [options] - Popup options
 * @returns {L.Popup} Created popup
 */
export function createPopup(content, options = {}) {
    try {
        return L.popup({
            maxWidth: 300,
            minWidth: 200,
            className: 'custom-popup',
            closeButton: true,
            autoClose: false,
            closeOnClick: false,
            ...options
        }).setContent(content);
    } catch (error) {
        logger.error('Failed to create popup:', error);
        throw error;
    }
}

/**
 * Create a tooltip with consistent styling
 * @param {string} content - Tooltip content
 * @param {Object} [options] - Tooltip options
 * @returns {L.Tooltip} Created tooltip
 */
export function createTooltip(content, options = {}) {
    try {
        return L.tooltip({
            direction: 'top',
            opacity: 0.9,
            className: 'custom-tooltip',
            ...options
        }).setContent(content);
    } catch (error) {
        logger.error('Failed to create tooltip:', error);
        throw error;
    }
}

/**
 * Check if a point is within the current map view
 * @param {L.LatLng} point - Point to check
 * @returns {boolean} True if the point is in the current view
 */
export function isInViewport(point) {
    try {
        const map = getMap();
        const bounds = map.getBounds();
        return bounds.contains(point);
    } catch (error) {
        logger.error('Failed to check if point is in viewport:', error);
        return false;
    }
}

/**
 * Add a loading indicator to the map
 * @param {string} [message='Loading...'] - Loading message
 */
export function showLoading(message = 'Loading...') {
    try {
        const map = getMap();
        
        // Remove existing loading control if any
        hideLoading();
        
        // Create loading control
        const loadingControl = L.control({ position: 'topleft' });
        
        loadingControl.onAdd = function() {
            const div = L.DomUtil.create('div', 'loading-control');
            div.innerHTML = `
                <div class="loading-spinner"></div>
                <div class="loading-text">${message}</div>
            `;
            return div;
        };
        
        // Add to map and store reference
        loadingControl.addTo(map);
        map._loadingControl = loadingControl;
        
    } catch (error) {
        logger.error('Failed to show loading indicator:', error);
    }
}

/**
 * Remove the loading indicator from the map
 */
export function hideLoading() {
    try {
        const map = getMap();
        if (map._loadingControl) {
            map.removeControl(map._loadingControl);
            delete map._loadingControl;
        }
    } catch (error) {
        logger.error('Failed to hide loading indicator:', error);
    }
}

// Helper function to get map instance
function getMap() {
    if (typeof map === 'undefined') {
        throw new Error('Map not initialized');
    }
    return map;
}
