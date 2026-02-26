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
let reconnectAttempts = 0;
const MAX_RECONNECT_ATTEMPTS = 3;

/**
 * Load vehicle departure data from the API
 * NOTE: Wiener Linien API only provides stop-based departure information,
 * not real-time GPS positions of vehicles in transit.
 * @returns {Promise<Array>} Array of departure events (not actual vehicles)
 */
export async function loadVehiclesData() {
    try {
        logger.debug('Loading vehicles data...');
        
        // Invalidate cache if data is older than 30 seconds
        const now = Date.now();
        const cacheAge = lastUpdateTime ? now - lastUpdateTime : Infinity;
        
        if (vehiclesCache && cacheAge < 30000) {
            logger.debug(`Returning cached vehicles data (age: ${Math.round(cacheAge/1000)}s)`);
            return vehiclesCache;
        }
        
        logger.info('Fetching fresh vehicles data from API...');
        
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
        
        // Log raw API response for debugging
        logger.debug('Raw API response:', { 
            vehicleCount: vehicles.length,
            firstVehicle: vehicles.length > 0 ? vehicles[0] : 'No vehicles',
            responseTimestamp: new Date().toISOString()
        });

        // Group vehicles by coordinates to handle stacking
        const coordGroups = new Map();

        // Process and normalize vehicle data
        vehicles = vehicles.map(vehicle => {
            // Debug coordinate processing for first few vehicles
            const hasExistingCoords = vehicle.coordinates && Array.isArray(vehicle.coordinates);
            const fallbackCoords = [vehicle.lat, vehicle.lng].filter(Boolean);
            let finalCoords = hasExistingCoords ? vehicle.coordinates : fallbackCoords;

            if (!vehicle.id || vehicle.id.includes('transit') || vehicle.id.includes('68A_2629_0')) { // Debug transit vehicles
                logger.debug(`Processing vehicle ${vehicle.id}:`, {
                    lat: vehicle.lat,
                    lng: vehicle.lng,
                    hasExistingCoords,
                    fallbackCoords,
                    finalCoords,
                    inTransit: vehicle.in_transit
                });
            }

            // Apply stacking offset for departure events at stops
            if (finalCoords && finalCoords.length === 2) {
                const coordKey = `${finalCoords[0]},${finalCoords[1]}`;
                const groupIndex = coordGroups.get(coordKey) || 0;
                coordGroups.set(coordKey, groupIndex + 1);

                // Add small offset based on group index (spread vehicles slightly)
                if (groupIndex > 0) {
                    const offset = 0.0001 * groupIndex; // ~10 meters offset
                    finalCoords = [
                        finalCoords[0] + (Math.random() - 0.5) * offset,
                        finalCoords[1] + (Math.random() - 0.5) * offset
                    ];
                }
            }

            return {
                ...vehicle,
                // Ensure coordinates are in the correct format [lat, lng] for Leaflet
                coordinates: finalCoords && finalCoords.length === 2 ? finalCoords : null,
                // Normalize vehicle type
                type: normalizeVehicleType(vehicle.type),
                // Ensure required fields
                id: vehicle.id || generateVehicleId(vehicle),
                routeId: vehicle.routeId || null,
                lastUpdated: vehicle.lastUpdated || new Date().toISOString()
            };
        });
        
        // Debug: log coordinate processing
        logger.debug(`Processing ${vehicles.length} vehicles before coordinate filtering`);
        vehicles.forEach((v, i) => {
            if (i < 3) { // Log first 3 vehicles
                logger.debug(`Vehicle ${i}: id=${v.id}, lat=${v.lat}, lng=${v.lng}, hasCoordinates=${!!v.coordinates}`);
            }
        });

        // Filter out vehicles without valid coordinates
        const beforeFilter = vehicles.length;
        vehicles = vehicles.filter(vehicle =>
            vehicle.coordinates &&
            vehicle.coordinates.length === 2 &&
            !isNaN(vehicle.coordinates[0]) &&
            !isNaN(vehicle.coordinates[1])
        );

        logger.info(`Filtered ${beforeFilter} vehicles down to ${vehicles.length} with valid coordinates`);

        // Update cache
        vehiclesCache = vehicles;
        lastUpdateTime = now;

        logger.info(`Loaded ${vehicles.length} vehicles with coordinate offsets applied`);
        return vehicles;
        
    } catch (error) {
        logger.error('Failed to load vehicles data:', {
            error: error.toString(),
            stack: error.stack,
            timestamp: new Date().toISOString()
        });
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
            reconnectAttempts++;

            if (reconnectAttempts >= MAX_RECONNECT_ATTEMPTS) {
                logger.warn(`Max reconnect attempts (${MAX_RECONNECT_ATTEMPTS}) reached. Falling back to REST API polling.`);
                eventSource.close();
                eventSource = null;
                return;
            }

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
