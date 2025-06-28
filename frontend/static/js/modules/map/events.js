/**
 * Map event handling
 */

import { CONFIG } from '../../config.js';
import { logger } from '../utils/logger.js';
import { STORAGE_KEYS } from '../../constants.js';
import { saveToStorage } from '../utils/storage.js';

/**
 * Set up map event listeners
 * @param {L.Map} map - The Leaflet map instance
 */
export function setupMapEvents(map) {
    try {
        logger.debug('Setting up map event listeners');
        
        // Save map position when view changes
        map.on('moveend', () => saveMapPosition(map));
        
        // Log map events for debugging
        if (process.env.NODE_ENV === 'development') {
            map.on('zoomend', () => {
                logger.debug(`Map zoomed to: ${map.getZoom()}`);
            });
            
            map.on('click', (e) => {
                logger.debug(`Map clicked at:`, e.latlng);
            });
        }
        
        // Handle errors
        map.on('error', (error) => {
            logger.error('Map error:', error);
        });
        
        logger.debug('Map event listeners set up successfully');
        
    } catch (error) {
        logger.error('Failed to set up map event listeners:', error);
        throw error;
    }
}

/**
 * Save the current map position to storage
 * @param {L.Map} map - The Leaflet map instance
 */
function saveMapPosition(map) {
    try {
        const position = {
            center: map.getCenter(),
            zoom: map.getZoom()
        };
        
        saveToStorage(STORAGE_KEYS.MAP_POSITION, position);
        logger.debug('Map position saved');
        
    } catch (error) {
        logger.error('Failed to save map position:', error);
    }
}

/**
 * Restore the map position from storage
 * @param {L.Map} map - The Leaflet map instance
 * @returns {boolean} True if position was restored, false otherwise
 */
export function restoreMapPosition(map) {
    try {
        const position = loadFromStorage(STORAGE_KEYS.MAP_POSITION);
        
        if (position?.center && position.zoom) {
            map.setView(
                [position.center.lat, position.center.lng],
                position.zoom
            );
            logger.debug('Map position restored');
            return true;
        }
        
        return false;
        
    } catch (error) {
        logger.error('Failed to restore map position:', error);
        return false;
    }
}

/**
 * Fit the map to show all features in a layer group
 * @param {L.LayerGroup} layerGroup - The layer group to fit bounds to
 * @param {Object} [options] - Fit bounds options
 * @param {number} [options.padding=50] - Padding in pixels
 * @param {number} [options.maxZoom=15] - Maximum zoom level
 */
export function fitMapToLayerGroup(layerGroup, options = {}) {
    try {
        const map = getMap();
        const bounds = layerGroup.getBounds();
        
        if (bounds.isValid()) {
            const padding = L.point(
                options.padding || 50,
                options.padding || 50
            );
            
            map.fitBounds(bounds, {
                padding: [padding.y, padding.x],
                maxZoom: options.maxZoom || 15
            });
            
            logger.debug('Map fitted to layer group');
        }
    } catch (error) {
        logger.error('Failed to fit map to layer group:', error);
    }
}
