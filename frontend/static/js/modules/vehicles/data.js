/**
 * Vehicles data management
 */

import { CONFIG } from '../../config.js';
import { VEHICLE_TYPES } from '../../constants.js';
import { logger } from '../utils/logger.js';
import { fetchWithTimeout } from '../utils/api.js';

// Cache for vehicle data
let vehiclesCache = null;
let lastUpdateTime = null;
let eventSource = null;

/**
 * Load vehicles data from the API
 * @returns {Promise<Array>} Array of vehicle objects
 */
export async function loadVehiclesData() {
    try {
        logger.debug('Loading vehicles data...');
        
        // Invalidate cache if data is older than 30 seconds
        const now = Date.now();
        const cacheAge = lastUpdateTime ? now - lastUpdateTime : Infinity;
        
        if (vehiclesCache && cacheAge < 30000) {
            logger.debug('Returning cached vehicles data');
            return vehiclesCache;
        }
        
        // Fetch vehicles from the API
        const response = await fetchWithTimeout(
            `${CONFIG.API.BASE_URL}${CONFIG.API.ENDPOINTS.VEHICLES}`,
            {
                method: 'GET',
                headers: {
                    'Accept': 'application/json',
                    'Cache-Control': 'no-cache'
                }
            }
        );
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        let vehicles = await response.json();
        
        // Process and normalize vehicle data
        vehicles = vehicles.map(vehicle => ({
            ...vehicle,
            // Ensure coordinates are in the correct format
            coordinates: vehicle.coordinates && Array.isArray(vehicle.coordinates)
                ? vehicle.coordinates
                : [vehicle.lat, vehicle.lng].filter(Boolean).length === 2
                    ? [vehicle.lat, vehicle.lng]
                    : null,
            // Normalize vehicle type
            type: normalizeVehicleType(vehicle.type),
            // Ensure required fields
            id: vehicle.id || generateVehicleId(vehicle),
            routeId: vehicle.routeId || null,
            lastUpdated: vehicle.lastUpdated || new Date().toISOString()
        }));
        
        // Filter out vehicles without valid coordinates
        vehicles = vehicles.filter(vehicle => 
            vehicle.coordinates && 
            vehicle.coordinates.length === 2 &&
            !isNaN(vehicle.coordinates[0]) && 
            !isNaN(vehicle.coordinates[1])
        );
        
        // Update cache
        vehiclesCache = vehicles;
        lastUpdateTime = now;
        
        logger.debug(`Loaded ${vehicles.length} vehicles`);
        return vehicles;
        
    } catch (error) {
        logger.error('Failed to load vehicles data:', error);
        throw error;
    }
}

/**
 * Start receiving real-time vehicle updates via Server-Sent Events (SSE)
 * @param {Function} onUpdate - Callback for when vehicle data is updated
 * @returns {Function} Cleanup function to stop the updates
 */
export function startVehicleUpdates(onUpdate) {
    try {
        // Close any existing connection
        if (eventSource) {
            eventSource.close();
        }
        
        logger.info('Starting vehicle updates...');
        
        // Create a new EventSource connection
        const url = `${CONFIG.API.BASE_URL}${CONFIG.API.ENDPOINTS.VEHICLES}/updates`;
        eventSource = new EventSource(url);
        
        // Handle incoming messages
        eventSource.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                onUpdate(data);
            } catch (error) {
                logger.error('Failed to parse vehicle update:', error);
            }
        };
        
        // Handle errors
        eventSource.onerror = (error) => {
            logger.error('Vehicle updates error:', error);
            // Attempt to reconnect after a delay
            setTimeout(() => {
                if (eventSource) {
                    eventSource.close();
                    startVehicleUpdates(onUpdate);
                }
            }, 5000);
        };
        
        logger.debug('Vehicle updates started');
        
        // Return cleanup function
        return () => {
            if (eventSource) {
                eventSource.close();
                eventSource = null;
                logger.debug('Vehicle updates stopped');
            }
        };
        
    } catch (error) {
        logger.error('Failed to start vehicle updates:', error);
        throw error;
    }
}

/**
 * Get a vehicle by ID
 * @param {string} vehicleId - The vehicle ID to find
 * @returns {Object|undefined} The found vehicle or undefined
 */
export function getVehicleById(vehicleId) {
    if (!vehiclesCache) return undefined;
    return vehiclesCache.find(vehicle => vehicle.id === vehicleId);
}

/**
 * Get vehicles by route ID
 * @param {string} routeId - The route ID to filter by
 * @returns {Array} Filtered array of vehicles
 */
export function getVehiclesByRoute(routeId) {
    if (!vehiclesCache) return [];
    return vehiclesCache.filter(vehicle => vehicle.routeId === routeId);
}

/**
 * Get vehicles by type
 * @param {string} type - Vehicle type to filter by
 * @returns {Array} Filtered array of vehicles
 */
export function getVehiclesByType(type) {
    if (!vehiclesCache) return [];
    const normalizedType = normalizeVehicleType(type);
    return vehiclesCache.filter(vehicle => vehicle.type === normalizedType);
}

/**
 * Generate a unique ID for a vehicle
 * @private
 */
function generateVehicleId(vehicle) {
    // Use a combination of properties to generate a stable ID
    const parts = [
        vehicle.type,
        vehicle.routeId,
        vehicle.coordinates?.join(','),
        vehicle.lastUpdated
    ].filter(Boolean);
    
    return btoa(parts.join('|')).substring(0, 16);
}

/**
 * Normalize vehicle type
 * @private
 */
function normalizeVehicleType(type) {
    if (!type) return 'unknown';
    
    const lowerType = type.toLowerCase();
    
    // Map common variations to standard types
    const typeMap = {
        'u-bahn': VEHICLE_TYPES.METRO,
        'metro': VEHICLE_TYPES.METRO,
        'tram': VEHICLE_TYPES.TRAM,
        'bus': VEHICLE_TYPES.BUS,
        'nightbus': VEHICLE_TYPES.NIGHTBUS,
        'night': VEHICLE_TYPES.NIGHTBUS,
        'unknown': 'unknown'
    };
    
    return typeMap[lowerType] || lowerType;
}

/**
 * Get the default icon for a vehicle type
 * @param {string} type - Vehicle type
 * @returns {string} Icon class name
 */
export function getVehicleIcon(type) {
    const iconMap = {
        [VEHICLE_TYPES.METRO]: 'fa-train',
        [VEHICLE_TYPES.TRAM]: 'fa-train-tram',
        [VEHICLE_TYPES.BUS]: 'fa-bus',
        [VEHICLE_TYPES.NIGHTBUS]: 'fa-moon',
        'default': 'fa-car'
    };
    
    return iconMap[type] || iconMap.default;
}
