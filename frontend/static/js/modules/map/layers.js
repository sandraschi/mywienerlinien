/**
 * Map layers management
 */

import L from 'leaflet';
import { CONFIG } from '../../config.js';
import { logger } from '../utils/logger.js';

// Layer groups
const layerGroups = {
    baseLayers: {},
    overlays: {}
};

/**
 * Set up base layers and overlay layers for the map
 * @param {L.Map} map - The Leaflet map instance
 */
export function setupMapLayers(map) {
    try {
        logger.debug('Setting up map layers');
        
        // Create base layers
        const osmLayer = L.tileLayer(CONFIG.MAP.TILE_LAYER, {
            attribution: CONFIG.MAP.TILE_ATTRIBUTION,
            maxZoom: CONFIG.MAP.MAX_ZOOM
        });
        
        // Add base layers to the map and layer groups
        layerGroups.baseLayers['OpenStreetMap'] = osmLayer;
        
        // Create overlay layer groups
        layerGroups.overlays['Routes'] = L.layerGroup().addTo(map);
        layerGroups.overlays['Stations'] = L.layerGroup().addTo(map);
        layerGroups.overlays['Vehicles'] = L.layerGroup().addTo(map);
        
        // Add base layer to map
        osmLayer.addTo(map);
        
        // Add layer control
        L.control.layers(
            layerGroups.baseLayers,
            layerGroups.overlays,
            { position: 'topright', collapsed: true }
        ).addTo(map);
        
        logger.debug('Map layers set up successfully');
        
    } catch (error) {
        logger.error('Failed to set up map layers:', error);
        throw error;
    }
}

/**
 * Get a layer group by name
 * @param {string} groupName - Name of the layer group
 * @param {string} [type='overlays'] - Type of layer group ('baseLayers' or 'overlays')
 * @returns {L.LayerGroup|undefined} The requested layer group
 */
export function getLayerGroup(groupName, type = 'overlays') {
    const group = layerGroups[type]?.[groupName];
    if (!group) {
        logger.warn(`Layer group '${groupName}' not found in ${type}`);
    }
    return group;
}

/**
 * Add a layer to a layer group
 * @param {string} groupName - Name of the target layer group
 * @param {L.Layer} layer - The layer to add
 * @param {string} [type='overlays'] - Type of layer group
 */
export function addToLayerGroup(groupName, layer, type = 'overlays') {
    try {
        const group = getLayerGroup(groupName, type);
        if (group) {
            group.addLayer(layer);
            logger.debug(`Added layer to group '${groupName}'`);
        }
    } catch (error) {
        logger.error(`Failed to add layer to group '${groupName}':`, error);
    }
}

/**
 * Remove a layer from a layer group
 * @param {string} groupName - Name of the target layer group
 * @param {L.Layer} layer - The layer to remove
 * @param {string} [type='overlays'] - Type of layer group
 */
export function removeFromLayerGroup(groupName, layer, type = 'overlays') {
    try {
        const group = getLayerGroup(groupName, type);
        if (group) {
            group.removeLayer(layer);
            logger.debug(`Removed layer from group '${groupName}'`);
        }
    } catch (error) {
        logger.error(`Failed to remove layer from group '${groupName}':`, error);
    }
}

/**
 * Clear all layers from a layer group
 * @param {string} groupName - Name of the target layer group
 * @param {string} [type='overlays'] - Type of layer group
 */
export function clearLayerGroup(groupName, type = 'overlays') {
    try {
        const group = getLayerGroup(groupName, type);
        if (group) {
            group.clearLayers();
            logger.debug(`Cleared all layers from group '${groupName}'`);
        }
    } catch (error) {
        logger.error(`Failed to clear layer group '${groupName}':`, error);
    }
}
