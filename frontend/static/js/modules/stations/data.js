/**
 * Stations data management
 */

import { CONFIG } from '../../config.js';
import { logger } from '../utils/logger.js';
import { fetchWithTimeout } from '../utils/api.js';

// Cache for station data
let stationsCache = null;

/**
 * Load stations data from the API or cache
 * @returns {Promise<Array>} Array of station objects
 */
export async function loadStationsData() {
    try {
        // Return cached data if available
        if (stationsCache) {
            logger.debug('Returning cached stations data');
            return stationsCache;
        }
        
        logger.info('Loading stations data...');
        
        // Fetch stations from the API
        const response = await fetchWithTimeout(`${CONFIG.API.BASE_URL}${CONFIG.API.ENDPOINTS.STATIONS}`);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        let stations = await response.json();
        
        // Process and normalize station data
        stations = stations.map(station => ({
            ...station,
            // Ensure coordinates are in the correct format
            coordinates: station.coordinates && Array.isArray(station.coordinates)
                ? station.coordinates
                : [station.lat, station.lng].filter(Boolean).length === 2
                    ? [station.lat, station.lng]
                    : null,
            // Add type if not present
            type: station.type || 'station',
            // Ensure name is a string
            name: String(station.name || `Station ${station.id}`)
        }));
        
        // Filter out stations without valid coordinates
        stations = stations.filter(station => 
            station.coordinates && 
            station.coordinates.length === 2 &&
            !isNaN(station.coordinates[0]) && 
            !isNaN(station.coordinates[1])
        );
        
        // Cache the processed stations
        stationsCache = stations;
        
        logger.info(`Loaded ${stations.length} stations`);
        return stations;
        
    } catch (error) {
        logger.error('Failed to load stations data:', error);
        throw error;
    }
}

/**
 * Get a station by ID
 * @param {string} stationId - The station ID to find
 * @returns {Object|undefined} The found station or undefined
 */
export function getStationById(stationId) {
    if (!stationsCache) return undefined;
    return stationsCache.find(station => station.id === stationId);
}

/**
 * Find stations by name or ID
 * @param {string} query - Search query
 * @returns {Array} Matching stations
 */
export function searchStations(query) {
    if (!stationsCache) return [];
    
    const lowerQuery = query.toLowerCase();
    return stationsCache.filter(station => 
        station.name.toLowerCase().includes(lowerQuery) ||
        String(station.id).toLowerCase().includes(lowerQuery)
    );
}

/**
 * Get stations by type
 * @param {string} type - Station type to filter by
 * @returns {Array} Filtered array of stations
 */
export function getStationsByType(type) {
    if (!stationsCache) return [];
    return stationsCache.filter(station => station.type === type);
}

/**
 * Get stations within a bounding box
 * @param {L.LatLngBounds} bounds - Bounding box to search within
 * @returns {Array} Stations within the bounds
 */
export function getStationsInBounds(bounds) {
    if (!stationsCache || !bounds) return [];
    return stationsCache.filter(station => 
        station.coordinates && 
        bounds.contains(L.latLng(station.coordinates))
    );
}

/**
 * Save active stations to storage
 * @param {Set} activeStations - Set of active station IDs
 */
export function saveActiveStations(activeStations) {
    try {
        const activeStationsArray = Array.from(activeStations);
        localStorage.setItem('activeStations', JSON.stringify(activeStationsArray));
        logger.debug('Saved active stations to storage');
    } catch (error) {
        logger.error('Failed to save active stations:', error);
    }
}

/**
 * Load active stations from storage
 * @returns {Set} Set of active station IDs
 */
export function loadActiveStations() {
    try {
        const saved = localStorage.getItem('activeStations');
        if (saved) {
            const activeStations = new Set(JSON.parse(saved));
            logger.debug('Loaded active stations from storage');
            return activeStations;
        }
    } catch (error) {
        logger.error('Failed to load active stations:', error);
    }
    return new Set();
}
