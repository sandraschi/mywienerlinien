/**
 * Geolocation and distance calculation utilities
 */

import { logger } from './logger.js';

// Earth's radius in meters (mean radius)
const EARTH_RADIUS = 6371000;

/**
 * Convert degrees to radians
 * @private
 */
function toRad(degrees) {
    return degrees * (Math.PI / 180);
}

/**
 * Calculate the distance between two coordinates using the Haversine formula
 * @param {Object} coord1 - First coordinate {lat, lng}
 * @param {Object} coord2 - Second coordinate {lat, lng}
 * @param {number} [precision=0] - Number of decimal places to round to
 * @returns {number} Distance in meters
 */
export function getDistance(coord1, coord2, precision = 0) {
    try {
        if (!coord1 || !coord2 || 
            coord1.lat === undefined || coord1.lng === undefined ||
            coord2.lat === undefined || coord2.lng === undefined) {
            throw new Error('Invalid coordinates');
        }
        
        const lat1 = parseFloat(coord1.lat);
        const lon1 = parseFloat(coord1.lng);
        const lat2 = parseFloat(coord2.lat);
        const lon2 = parseFloat(coord2.lng);
        
        const dLat = toRad(lat2 - lat1);
        const dLon = toRad(lon2 - lon1);
        
        const a = 
            Math.sin(dLat / 2) * Math.sin(dLat / 2) +
            Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) * 
            Math.sin(dLon / 2) * Math.sin(dLon / 2);
            
        const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
        const distance = EARTH_RADIUS * c;
        
        return precision ? parseFloat(distance.toFixed(precision)) : Math.round(distance);
    } catch (error) {
        logger.error('Error calculating distance:', error);
        return 0;
    }
}

/**
 * Calculate the bearing between two coordinates
 * @param {Object} coord1 - First coordinate {lat, lng}
 * @param {Object} coord2 - Second coordinate {lat, lng}
 * @returns {number} Bearing in degrees (0-360°)
 */
export function getBearing(coord1, coord2) {
    try {
        const lat1 = toRad(coord1.lat);
        const lon1 = toRad(coord1.lng);
        const lat2 = toRad(coord2.lat);
        const lon2 = toRad(coord2.lng);
        
        const y = Math.sin(lon2 - lon1) * Math.cos(lat2);
        const x = Math.cos(lat1) * Math.sin(lat2) - 
                 Math.sin(lat1) * Math.cos(lat2) * Math.cos(lon2 - lon1);
        
        let bearing = Math.atan2(y, x);
        bearing = (bearing * 180) / Math.PI;
        return (bearing + 360) % 360;
    } catch (error) {
        logger.error('Error calculating bearing:', error);
        return 0;
    }
}

/**
 * Calculate a destination point given a starting point, distance, and bearing
 * @param {Object} start - Starting coordinate {lat, lng}
 * @param {number} distance - Distance in meters
 * @param {number} bearing - Bearing in degrees (0-360°)
 * @returns {Object} Destination coordinate {lat, lng}
 */
export function getDestinationPoint(start, distance, bearing) {
    try {
        const lat1 = toRad(start.lat);
        const lon1 = toRad(start.lng);
        const brng = toRad(bearing);
        const dR = distance / EARTH_RADIUS;
        
        const lat2 = Math.asin(
            Math.sin(lat1) * Math.cos(dR) + 
            Math.cos(lat1) * Math.sin(dR) * Math.cos(brng)
        );
        
        const lon2 = lon1 + Math.atan2(
            Math.sin(brng) * Math.sin(dR) * Math.cos(lat1),
            Math.cos(dR) - Math.sin(lat1) * Math.sin(lat2)
        );
        
        return {
            lat: (lat2 * 180) / Math.PI,
            lng: (((lon2 * 180) / Math.PI + 540) % 360) - 180
        };
    } catch (error) {
        logger.error('Error calculating destination point:', error);
        return { ...start };
    }
}

/**
 * Calculate the midpoint between two coordinates
 * @param {Object} coord1 - First coordinate {lat, lng}
 * @param {Object} coord2 - Second coordinate {lat, lng}
 * @returns {Object} Midpoint coordinate {lat, lng}
 */
export function getMidpoint(coord1, coord2) {
    try {
        const lat1 = toRad(coord1.lat);
        const lon1 = toRad(coord1.lng);
        const lat2 = toRad(coord2.lat);
        const lon2 = toRad(coord2.lng);
        
        const Bx = Math.cos(lat2) * Math.cos(lon2 - lon1);
        const By = Math.cos(lat2) * Math.sin(lon2 - lon1);
        
        const lat3 = Math.atan2(
            Math.sin(lat1) + Math.sin(lat2),
            Math.sqrt((Math.cos(lat1) + Bx) * (Math.cos(lat1) + Bx) + By * By)
        );
        
        const lon3 = lon1 + Math.atan2(By, Math.cos(lat1) + Bx);
        
        return {
            lat: (lat3 * 180) / Math.PI,
            lng: (((lon3 * 180) / Math.PI + 540) % 360) - 180
        };
    } catch (error) {
        logger.error('Error calculating midpoint:', error);
        return {
            lat: (coord1.lat + coord2.lat) / 2,
            lng: (coord1.lng + coord2.lng) / 2
        };
    }
}

/**
 * Check if a point is inside a polygon
 * @param {Object} point - The point to check {lat, lng}
 * @param {Array} polygon - Array of coordinates that form the polygon
 * @returns {boolean} True if the point is inside the polygon
 */
export function isPointInPolygon(point, polygon) {
    try {
        if (!point || !polygon || !Array.isArray(polygon) || polygon.length < 3) {
            return false;
        }
        
        const x = parseFloat(point.lat);
        const y = parseFloat(point.lng);
        
        let inside = false;
        for (let i = 0, j = polygon.length - 1; i < polygon.length; j = i++) {
            const xi = parseFloat(polygon[i].lat);
            const yi = parseFloat(polygon[i].lng);
            const xj = parseFloat(polygon[j].lat);
            const yj = parseFloat(polygon[j].lng);
            
            const intersect = ((yi > y) !== (yj > y)) &&
                (x < (xj - xi) * (y - yi) / (yj - yi) + xi);
                
            if (intersect) inside = !inside;
        }
        
        return inside;
    } catch (error) {
        logger.error('Error checking point in polygon:', error);
        return false;
    }
}

/**
 * Format a distance in a human-readable way
 * @param {number} distance - Distance in meters
 * @param {boolean} [useImperial=false] - Whether to use imperial units (feet/miles)
 * @returns {string} Formatted distance string
 */
export function formatDistance(distance, useImperial = false) {
    try {
        if (useImperial) {
            // Convert to feet and miles
            const feet = distance * 3.28084;
            
            if (feet < 1000) {
                return `${Math.round(feet)} ft`;
            } else {
                const miles = feet / 5280;
                return `${miles.toFixed(1)} mi`;
            }
        } else {
            // Use metric (meters and kilometers)
            if (distance < 1000) {
                return `${Math.round(distance)} m`;
            } else {
                const km = distance / 1000;
                return `${km.toFixed(1)} km`;
            }
        }
    } catch (error) {
        logger.error('Error formatting distance:', error);
        return '0 m';
    }
}

/**
 * Calculate the area of a polygon in square meters
 * @param {Array} polygon - Array of coordinates that form the polygon
 * @returns {number} Area in square meters
 */
export function getPolygonArea(polygon) {
    try {
        if (!polygon || !Array.isArray(polygon) || polygon.length < 3) {
            return 0;
        }
        
        // Close the polygon if not already closed
        const coords = [...polygon];
        if (coords[0] !== coords[coords.length - 1]) {
            coords.push(coords[0]);
        }
        
        let area = 0;
        
        // Convert all coordinates to radians
        const points = coords.map(coord => ({
            lat: toRad(coord.lat),
            lng: toRad(coord.lng)
        }));
        
        // Calculate using the shoelace formula on a sphere
        for (let i = 0; i < points.length - 1; i++) {
            const p1 = points[i];
            const p2 = points[i + 1];
            
            area += (p2.lng - p1.lng) * 
                   (2 + Math.sin(p1.lat) + Math.sin(p2.lat));
        }
        
        area = Math.abs(area) * EARTH_RADIUS * EARTH_RADIUS / 2;
        return area;
    } catch (error) {
        logger.error('Error calculating polygon area:', error);
        return 0;
    }
}

/**
 * Get the center (centroid) of a polygon
 * @param {Array} polygon - Array of coordinates that form the polygon
 * @returns {Object} Centroid coordinate {lat, lng}
 */
export function getPolygonCenter(polygon) {
    try {
        if (!polygon || !Array.isArray(polygon) || polygon.length === 0) {
            return null;
        }
        
        // Calculate simple average for small areas
        if (polygon.length === 1) {
            return { ...polygon[0] };
        }
        
        // For larger areas, use spherical coordinates
        let x = 0, y = 0, z = 0;
        
        for (const point of polygon) {
            const lat = toRad(point.lat);
            const lng = toRad(point.lng);
            
            x += Math.cos(lat) * Math.cos(lng);
            y += Math.cos(lat) * Math.sin(lng);
            z += Math.sin(lat);
        }
        
        const total = polygon.length;
        x /= total;
        y /= total;
        z /= total;
        
        const centerLng = Math.atan2(y, x);
        const centerLat = Math.atan2(z, Math.sqrt(x * x + y * y));
        
        return {
            lat: (centerLat * 180) / Math.PI,
            lng: (centerLng * 180) / Math.PI
        };
    } catch (error) {
        logger.error('Error calculating polygon center:', error);
        
        // Fallback to simple average
        if (polygon && polygon.length > 0) {
            const sum = polygon.reduce((acc, point) => ({
                lat: acc.lat + parseFloat(point.lat),
                lng: acc.lng + parseFloat(point.lng)
            }), { lat: 0, lng: 0 });
            
            return {
                lat: sum.lat / polygon.length,
                lng: sum.lng / polygon.length
            };
        }
        
        return { lat: 0, lng: 0 };
    }
}

/**
 * Get the bounds that contain all the given coordinates
 * @param {Array} coordinates - Array of coordinates
 * @returns {Object} Bounds object with ne (north-east) and sw (south-west) points
 */
export function getBounds(coordinates) {
    try {
        if (!coordinates || !Array.isArray(coordinates) || coordinates.length === 0) {
            return null;
        }
        
        let minLat = 90, maxLat = -90;
        let minLng = 180, maxLng = -180;
        
        for (const coord of coordinates) {
            const lat = parseFloat(coord.lat);
            const lng = parseFloat(coord.lng);
            
            if (!isNaN(lat) && !isNaN(lng)) {
                minLat = Math.min(minLat, lat);
                maxLat = Math.max(maxLat, lat);
                minLng = Math.min(minLng, lng);
                maxLng = Math.max(maxLng, lng);
            }
        }
        
        // If no valid coordinates were found
        if (minLat === 90 || maxLat === -90 || minLng === 180 || maxLng === -180) {
            return null;
        }
        
        return {
            ne: { lat: maxLat, lng: maxLng },
            sw: { lat: minLat, lng: minLng },
            getCenter() {
                return {
                    lat: (maxLat + minLat) / 2,
                    lng: (maxLng + minLng) / 2
                };
            }
        };
    } catch (error) {
        logger.error('Error calculating bounds:', error);
        return null;
    }
}

/**
 * Get the current geolocation
 * @param {Object} [options] - Geolocation options
 * @param {boolean} [options.highAccuracy=false] - Whether to request high accuracy
 * @param {number} [options.timeout=10000] - Timeout in milliseconds
 * @param {number} [options.maximumAge=0] - Maximum age of a cached position
 * @returns {Promise<Object>} Promise that resolves with position or rejects with error
 */
export function getCurrentPosition(options = {}) {
    return new Promise((resolve, reject) => {
        if (!navigator.geolocation) {
            reject(new Error('Geolocation is not supported by this browser'));
            return;
        }
        
        const {
            highAccuracy = false,
            timeout = 10000,
            maximumAge = 0
        } = options;
        
        const geoOptions = {
            enableHighAccuracy: highAccuracy,
            timeout,
            maximumAge
        };
        
        navigator.geolocation.getCurrentPosition(
            (position) => {
                resolve({
                    lat: position.coords.latitude,
                    lng: position.coords.longitude,
                    accuracy: position.coords.accuracy,
                    altitude: position.coords.altitude,
                    altitudeAccuracy: position.coords.altitudeAccuracy,
                    heading: position.coords.heading,
                    speed: position.coords.speed,
                    timestamp: position.timestamp
                });
            },
            (error) => {
                let errorMessage = 'Unknown error occurred';
                
                switch (error.code) {
                    case error.PERMISSION_DENIED:
                        errorMessage = 'User denied the request for geolocation';
                        break;
                    case error.POSITION_UNAVAILABLE:
                        errorMessage = 'Location information is unavailable';
                        break;
                    case error.TIMEOUT:
                        errorMessage = 'The request to get user location timed out';
                        break;
                }
                
                reject(new Error(errorMessage));
            },
            geoOptions
        );
    });
}

/**
 * Watch the user's position
 * @param {Function} callback - Callback function that receives position updates
 * @param {Function} [errorCallback] - Callback function for errors
 * @param {Object} [options] - Watch position options
 * @returns {number} Watch ID that can be used to stop watching
 */
export function watchPosition(callback, errorCallback, options = {}) {
    if (!navigator.geolocation) {
        if (errorCallback) {
            errorCallback(new Error('Geolocation is not supported by this browser'));
        }
        return -1;
    }
    
    const {
        highAccuracy = false,
        timeout = 10000,
        maximumAge = 0
    } = options;
    
    const geoOptions = {
        enableHighAccuracy: highAccuracy,
        timeout,
        maximumAge
    };
    
    return navigator.geolocation.watchPosition(
        (position) => {
            callback({
                lat: position.coords.latitude,
                lng: position.coords.longitude,
                accuracy: position.coords.accuracy,
                altitude: position.coords.altitude,
                altitudeAccuracy: position.coords.altitudeAccuracy,
                heading: position.coords.heading,
                speed: position.coords.speed,
                timestamp: position.timestamp
            });
        },
        (error) => {
            if (errorCallback) {
                let errorMessage = 'Unknown error occurred';
                
                switch (error.code) {
                    case error.PERMISSION_DENIED:
                        errorMessage = 'User denied the request for geolocation';
                        break;
                    case error.POSITION_UNAVAILABLE:
                        errorMessage = 'Location information is unavailable';
                        break;
                    case error.TIMEOUT:
                        errorMessage = 'The request to get user location timed out';
                        break;
                }
                
                errorCallback(new Error(errorMessage));
            }
        },
        geoOptions
    );
}

/**
 * Stop watching the user's position
 * @param {number} watchId - The watch ID returned by watchPosition
 */
export function clearWatch(watchId) {
    if (navigator.geolocation) {
        navigator.geolocation.clearWatch(watchId);
    }
}

// Export a default object with all functions for convenience
export default {
    getDistance,
    getBearing,
    getDestinationPoint,
    getMidpoint,
    isPointInPolygon,
    formatDistance,
    getPolygonArea,
    getPolygonCenter,
    getBounds,
    getCurrentPosition,
    watchPosition,
    clearWatch,
    
    // Constants
    EARTH_RADIUS
};
