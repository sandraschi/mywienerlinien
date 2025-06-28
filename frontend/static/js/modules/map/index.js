/**
 * Map module - Initializes and manages the Leaflet map
 */

import L from 'leaflet';
import { CONFIG } from '../../config.js';
import { logger } from '../utils/logger.js';
import { setupMapLayers } from './layers.js';
import { setupMapEvents } from './events.js';

let mapInstance = null;

/**
 * Initialize the map
 * @param {string} containerId - ID of the map container element
 * @param {Object} options - Map configuration options
 * @returns {Promise<L.Map>} Initialized map instance
 */
export async function initMap(containerId, options = {}) {
    try {
        if (mapInstance) {
            logger.warn('Map already initialized');
            return mapInstance;
        }

        logger.info('Initializing map...');
        
        // Merge default options with provided options
        const mapOptions = {
            zoom: options.defaultZoom || CONFIG.MAP.DEFAULT_ZOOM,
            center: options.defaultCenter || CONFIG.MAP.DEFAULT_CENTER,
            maxZoom: options.maxZoom || CONFIG.MAP.MAX_ZOOM,
            minZoom: options.minZoom || CONFIG.MAP.MIN_ZOOM,
            zoomControl: false, // We'll add this manually
            ...options
        };

        // Create map instance
        mapInstance = L.map(containerId, mapOptions);
        
        // Set up base layers and overlays
        setupMapLayers(mapInstance);
        
        // Set up map events
        setupMapEvents(mapInstance);
        
        // Add zoom control with custom position
        L.control.zoom({
            position: 'topright'
        }).addTo(mapInstance);
        
        logger.info('Map initialized successfully');
        return mapInstance;
        
    } catch (error) {
        logger.error('Failed to initialize map:', error);
        throw error;
    }
}

/**
 * Get the current map instance
 * @returns {L.Map} The map instance
 */
export function getMap() {
    if (!mapInstance) {
        throw new Error('Map not initialized. Call initMap() first.');
    }
    return mapInstance;
}

/**
 * Clean up map resources
 */
export function cleanupMap() {
    if (mapInstance) {
        mapInstance.remove();
        mapInstance = null;
        logger.info('Map cleaned up');
    }
}

// Re-export commonly used functions
export * from './layers.js';
export * from './markers.js';
export * from './utils.js';
