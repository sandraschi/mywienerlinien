/**
 * Storage utilities for localStorage and sessionStorage with type safety and expiration
 */

import { logger } from './logger.js';

// Storage keys
const STORAGE_KEYS = {
    ACTIVE_ROUTES: 'activeRoutes',
    ACTIVE_STATIONS: 'activeStations',
    ACTIVE_VEHICLES: 'activeVehicles',
    MAP_POSITION: 'mapPosition',
    SETTINGS: 'appSettings',
    RECENT_SEARCHES: 'recentSearches',
    FAVORITES: 'favorites'
};

// Default storage TTL in milliseconds (7 days)
const DEFAULT_TTL = 7 * 24 * 60 * 60 * 1000;

/**
 * Base storage class with common functionality
 */
class BaseStorage {
    /**
     * Create a new storage instance
     * @param {Storage} storage - The Storage implementation (localStorage or sessionStorage)
     * @param {string} prefix - Prefix for all storage keys
     */
    constructor(storage, prefix = '') {
        this.storage = storage;
        this.prefix = prefix ? `${prefix}:` : '';
    }
    
    /**
     * Get a namespaced storage key
     * @private
     */
    _getKey(key) {
        return `${this.prefix}${key}`;
    }
    
    /**
     * Set a value in storage
     * @param {string} key - The storage key
     * @param {*} value - The value to store (will be JSON stringified)
     * @param {Object} [options] - Storage options
     * @param {number} [options.ttl] - Time to live in milliseconds
     * @returns {boolean} True if the operation succeeded
     */
    set(key, value, { ttl } = {}) {
        try {
            const item = {
                value,
                _timestamp: Date.now(),
                _expires: ttl ? Date.now() + ttl : null
            };
            
            this.storage.setItem(this._getKey(key), JSON.stringify(item));
            return true;
        } catch (error) {
            logger.error(`Failed to set storage key '${key}':`, error);
            return false;
        }
    }
    
    /**
     * Get a value from storage
     * @param {string} key - The storage key
     * @param {*} [defaultValue] - Default value if the key doesn't exist or is expired
     * @returns {*} The stored value or defaultValue
     */
    get(key, defaultValue = null) {
        try {
            const itemStr = this.storage.getItem(this._getKey(key));
            
            if (!itemStr) {
                return defaultValue;
            }
            
            const item = JSON.parse(itemStr);
            
            // Check if the item has expired
            if (item._expires && Date.now() > item._expires) {
                this.remove(key);
                return defaultValue;
            }
            
            return item.value !== undefined ? item.value : defaultValue;
        } catch (error) {
            logger.error(`Failed to get storage key '${key}':`, error);
            return defaultValue;
        }
    }
    
    /**
     * Remove a value from storage
     * @param {string} key - The storage key to remove
     * @returns {boolean} True if the key was found and removed
     */
    remove(key) {
        try {
            this.storage.removeItem(this._getKey(key));
            return true;
        } catch (error) {
            logger.error(`Failed to remove storage key '${key}':`, error);
            return false;
        }
    }
    
    /**
     * Clear all keys with the current prefix
     * @returns {boolean} True if the operation succeeded
     */
    clear() {
        try {
            const prefix = this.prefix;
            const keysToRemove = [];
            
            // Find all keys with the current prefix
            for (let i = 0; i < this.storage.length; i++) {
                const key = this.storage.key(i);
                if (key.startsWith(prefix)) {
                    keysToRemove.push(key);
                }
            }
            
            // Remove the keys
            keysToRemove.forEach(key => this.storage.removeItem(key));
            
            return true;
        } catch (error) {
            logger.error('Failed to clear storage:', error);
            return false;
        }
    }
    
    /**
     * Get all keys with the current prefix
     * @returns {string[]} Array of storage keys
     */
    keys() {
        const keys = [];
        const prefix = this.prefix;
        
        for (let i = 0; i < this.storage.length; i++) {
            const key = this.storage.key(i);
            if (key.startsWith(prefix)) {
                keys.push(key.slice(prefix.length));
            }
        }
        
        return keys;
    }
    
    /**
     * Check if a key exists in storage
     * @param {string} key - The key to check
     * @returns {boolean} True if the key exists and is not expired
     */
    has(key) {
        const item = this.get(key);
        return item !== null && item !== undefined;
    }
    
    /**
     * Get the number of items with the current prefix
     * @returns {number} The number of items
     */
    size() {
        return this.keys().length;
    }
}

/**
 * Local storage wrapper with type safety and expiration
 */
class LocalStorage extends BaseStorage {
    constructor(prefix = '') {
        super(localStorage, prefix);
    }
    
    /**
     * Store data with a time-to-live (TTL)
     * @param {string} key - The storage key
     * @param {*} value - The value to store
     * @param {number} ttl - Time to live in milliseconds
     * @returns {boolean} True if the operation succeeded
     */
    setWithTTL(key, value, ttl = DEFAULT_TTL) {
        return this.set(key, value, { ttl });
    }
    
    /**
     * Get all stored data as an object
     * @returns {Object} An object with all stored key-value pairs
     */
    getAll() {
        const result = {};
        const keys = this.keys();
        
        keys.forEach(key => {
            result[key] = this.get(key);
        });
        
        return result;
    }
}

/**
 * Session storage wrapper with type safety
 */
class SessionStorage extends BaseStorage {
    constructor(prefix = '') {
        super(sessionStorage, prefix);
    }
}

// Create default storage instances
export const local = new LocalStorage('wienerlinien');
export const session = new SessionStorage('wienerlinien');

// Export storage keys
export { STORAGE_KEYS };

// Helper functions for common storage operations

export const storageHelpers = {
    /**
     * Get active routes from storage
     * @returns {string[]} Array of active route IDs
     */
    getActiveRoutes: () => {
        return local.get(STORAGE_KEYS.ACTIVE_ROUTES, []);
    },
    
    /**
     * Save active routes to storage
     * @param {string[]} routeIds - Array of active route IDs
     * @returns {boolean} True if the operation succeeded
     */
    saveActiveRoutes: (routeIds) => {
        return local.set(STORAGE_KEYS.ACTIVE_ROUTES, routeIds);
    },
    
    /**
     * Get active stations from storage
     * @returns {string[]} Array of active station IDs
     */
    getActiveStations: () => {
        return local.get(STORAGE_KEYS.ACTIVE_STATIONS, []);
    },
    
    /**
     * Save active stations to storage
     * @param {string[]} stationIds - Array of active station IDs
     * @returns {boolean} True if the operation succeeded
     */
    saveActiveStations: (stationIds) => {
        return local.set(STORAGE_KEYS.ACTIVE_STATIONS, stationIds);
    },
    
    /**
     * Get active vehicles from storage
     * @returns {string[]} Array of active vehicle IDs
     */
    getActiveVehicles: () => {
        return local.get(STORAGE_KEYS.ACTIVE_VEHICLES, []);
    },
    
    /**
     * Save active vehicles to storage
     * @param {string[]} vehicleIds - Array of active vehicle IDs
     * @returns {boolean} True if the operation succeeded
     */
    saveActiveVehicles: (vehicleIds) => {
        return local.set(STORAGE_KEYS.ACTIVE_VEHICLES, vehicleIds);
    },
    
    /**
     * Get map position from storage
     * @returns {Object|null} Map position object or null if not found
     */
    getMapPosition: () => {
        return local.get(STORAGE_KEYS.MAP_POSITION, null);
    },
    
    /**
     * Save map position to storage
     * @param {Object} position - Map position object
     * @returns {boolean} True if the operation succeeded
     */
    saveMapPosition: (position) => {
        return local.set(STORAGE_KEYS.MAP_POSITION, position);
    },
    
    /**
     * Get recent searches from storage
     * @param {number} [limit=10] - Maximum number of recent searches to return
     * @returns {Array} Array of recent searches
     */
    getRecentSearches: (limit = 10) => {
        const searches = local.get(STORAGE_KEYS.RECENT_SEARCHES, []);
        return searches.slice(0, limit);
    },
    
    /**
     * Add a search to recent searches
     * @param {string} query - The search query
     * @param {number} [maxItems=10] - Maximum number of items to keep
     * @returns {boolean} True if the operation succeeded
     */
    addRecentSearch: (query, maxItems = 10) => {
        if (!query || typeof query !== 'string') {
            return false;
        }
        
        try {
            const searches = local.get(STORAGE_KEYS.RECENT_SEARCHES, []);
            
            // Remove duplicate and add to the beginning
            const updatedSearches = [
                query.trim(),
                ...searches.filter(item => 
                    item.toLowerCase() !== query.trim().toLowerCase()
                )
            ].slice(0, maxItems);
            
            return local.set(STORAGE_KEYS.RECENT_SEARCHES, updatedSearches);
        } catch (error) {
            logger.error('Failed to add recent search:', error);
            return false;
        }
    },
    
    /**
     * Clear recent searches
     * @returns {boolean} True if the operation succeeded
     */
    clearRecentSearches: () => {
        return local.set(STORAGE_KEYS.RECENT_SEARCHES, []);
    },
    
    /**
     * Get favorites from storage
     * @returns {Object} Object with favorite items
     */
    getFavorites: () => {
        return local.get(STORAGE_KEYS.FAVORITES, {});
    },
    
    /**
     * Add an item to favorites
     * @param {string} type - The type of favorite (e.g., 'route', 'station')
     * @param {string} id - The ID of the item
     * @param {Object} data - Additional data to store with the favorite
     * @returns {boolean} True if the operation succeeded
     */
    addFavorite: (type, id, data = {}) => {
        try {
            const favorites = local.get(STORAGE_KEYS.FAVORITES, {});
            
            if (!favorites[type]) {
                favorites[type] = {};
            }
            
            favorites[type][id] = {
                ...data,
                id,
                type,
                timestamp: Date.now()
            };
            
            return local.set(STORAGE_KEYS.FAVORITES, favorites);
        } catch (error) {
            logger.error('Failed to add favorite:', error);
            return false;
        }
    },
    
    /**
     * Remove an item from favorites
     * @param {string} type - The type of favorite
     * @param {string} id - The ID of the item to remove
     * @returns {boolean} True if the operation succeeded
     */
    removeFavorite: (type, id) => {
        try {
            const favorites = local.get(STORAGE_KEYS.FAVORITES, {});
            
            if (favorites[type] && favorites[type][id]) {
                delete favorites[type][id];
                
                // Remove the type if it's empty
                if (Object.keys(favorites[type]).length === 0) {
                    delete favorites[type];
                }
                
                return local.set(STORAGE_KEYS.FAVORITES, favorites);
            }
            
            return true; // Already not in favorites
        } catch (error) {
            logger.error('Failed to remove favorite:', error);
            return false;
        }
    },
    
    /**
     * Check if an item is in favorites
     * @param {string} type - The type of favorite
     * @param {string} id - The ID of the item to check
     * @returns {boolean} True if the item is in favorites
     */
    isFavorite: (type, id) => {
        try {
            const favorites = local.get(STORAGE_KEYS.FAVORITES, {});
            return !!(favorites[type] && favorites[type][id]);
        } catch (error) {
            logger.error('Failed to check favorite:', error);
            return false;
        }
    },
    
    /**
     * Toggle an item in favorites
     * @param {string} type - The type of favorite
     * @param {string} id - The ID of the item to toggle
     * @param {Object} [data={}] - Additional data to store if adding to favorites
     * @returns {boolean} True if the item is now in favorites, false otherwise
     */
    toggleFavorite: (type, id, data = {}) => {
        if (storageHelpers.isFavorite(type, id)) {
            storageHelpers.removeFavorite(type, id);
            return false;
        } else {
            storageHelpers.addFavorite(type, id, data);
            return true;
        }
    }
};

// Export default storage instance for backward compatibility
export default local;
