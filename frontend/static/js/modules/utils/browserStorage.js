/**
 * Browser storage utilities with fallbacks
 */

import { logger } from './logger.js';

// Storage types
const STORAGE_TYPES = {
    LOCAL: 'localStorage',
    SESSION: 'sessionStorage',
    MEMORY: 'memoryStorage'
};

// In-memory storage fallback
const memoryStorage = (() => {
    let store = {};
    
    return {
        getItem(key) {
            return store[key] || null;
        },
        setItem(key, value) {
            store[key] = String(value);
        },
        removeItem(key) {
            delete store[key];
        },
        clear() {
            store = {};
        },
        key(index) {
            return Object.keys(store)[index] || null;
        },
        get length() {
            return Object.keys(store).length;
        }
    };
})();

/**
 * Check if a storage type is available
 * @param {string} type - The storage type to check
 * @returns {boolean} True if the storage type is available
 */
function isStorageAvailable(type) {
    if (typeof window === 'undefined') {
        return false;
    }
    
    try {
        const storage = window[type];
        const testKey = '__storage_test__';
        
        storage.setItem(testKey, testKey);
        storage.removeItem(testKey);
        return true;
    } catch (e) {
        return false;
    }
}

/**
 * Get the best available storage type
 * @returns {string} The best available storage type
 */
function getBestStorageType() {
    if (isStorageAvailable(STORAGE_TYPES.LOCAL)) {
        return STORAGE_TYPES.LOCAL;
    } else if (isStorageAvailable(STORAGE_TYPES.SESSION)) {
        return STORAGE_TYPES.SESSION;
    } else {
        return STORAGE_TYPES.MEMORY;
    }
}

/**
 * Create a storage instance
 * @param {string} [type] - The storage type to use (defaults to best available)
 * @returns {Object} The storage instance
 */
function createStorage(type) {
    const storageType = type || getBestStorageType();
    
    switch (storageType) {
        case STORAGE_TYPES.LOCAL:
            return window.localStorage;
        case STORAGE_TYPES.SESSION:
            return window.sessionStorage;
        case STORAGE_TYPES.MEMORY:
        default:
            return memoryStorage;
    }
}

/**
 * Storage class with JSON serialization and expiration support
 */
class Storage {
    /**
     * Create a new storage instance
     * @param {Object} [options] - Storage options
     * @param {string} [options.prefix='app_'] - Key prefix
     * @param {string} [options.storageType] - Storage type to use
     */
    constructor(options = {}) {
        const {
            prefix = 'app_',
            storageType
        } = options;
        
        this.prefix = prefix;
        this.storage = createStorage(storageType);
        this.type = this.storage === memoryStorage ? STORAGE_TYPES.MEMORY : 
                   this.storage === window.sessionStorage ? STORAGE_TYPES.SESSION : 
                   STORAGE_TYPES.LOCAL;
    }
    
    /**
     * Get the full key with prefix
     * @private
     */
    _getKey(key) {
        return `${this.prefix}${key}`;
    }
    
    /**
     * Set a value in storage
     * @param {string} key - The key to set
     * @param {*} value - The value to store
     * @param {Object} [options] - Storage options
     * @param {number} [options.ttl] - Time to live in milliseconds
     * @returns {boolean} True if the operation succeeded
     */
    set(key, value, options = {}) {
        try {
            const data = {
                value,
                timestamp: Date.now(),
                ttl: options.ttl
            };
            
            this.storage.setItem(
                this._getKey(key),
                JSON.stringify(data)
            );
            
            return true;
        } catch (error) {
            logger.error(`Failed to set storage key '${key}':`, error);
            return false;
        }
    }
    
    /**
     * Get a value from storage
     * @param {string} key - The key to get
     * @param {*} [defaultValue=null] - The default value to return if the key doesn't exist
     * @returns {*} The stored value or the default value
     */
    get(key, defaultValue = null) {
        try {
            const item = this.storage.getItem(this._getKey(key));
            
            if (item === null) {
                return defaultValue;
            }
            
            const data = JSON.parse(item);
            
            // Check if the item has expired
            if (data.ttl && (Date.now() - data.timestamp > data.ttl)) {
                this.remove(key);
                return defaultValue;
            }
            
            return data.value !== undefined ? data.value : defaultValue;
        } catch (error) {
            logger.error(`Failed to get storage key '${key}':`, error);
            return defaultValue;
        }
    }
    
    /**
     * Remove a value from storage
     * @param {string} key - The key to remove
     * @returns {boolean} True if the operation succeeded
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
            if (this.storage === memoryStorage || this.prefix === '') {
                this.storage.clear();
            } else {
                // Only remove keys with the current prefix
                const keysToRemove = [];
                
                for (let i = 0; i < this.storage.length; i++) {
                    const key = this.storage.key(i);
                    if (key.startsWith(this.prefix)) {
                        keysToRemove.push(key);
                    }
                }
                
                keysToRemove.forEach(key => this.storage.removeItem(key));
            }
            
            return true;
        } catch (error) {
            logger.error('Failed to clear storage:', error);
            return false;
        }
    }
    
    /**
     * Get all keys with the current prefix
     * @returns {string[]} Array of keys
     */
    keys() {
        try {
            const keys = [];
            
            for (let i = 0; i < this.storage.length; i++) {
                const key = this.storage.key(i);
                if (key.startsWith(this.prefix)) {
                    keys.push(key.substring(this.prefix.length));
                }
            }
            
            return keys;
        } catch (error) {
            logger.error('Failed to get storage keys:', error);
            return [];
        }
    }
    
    /**
     * Check if a key exists in storage
     * @param {string} key - The key to check
     * @returns {boolean} True if the key exists and is not expired
     */
    has(key) {
        try {
            const item = this.storage.getItem(this._getKey(key));
            
            if (item === null) {
                return false;
            }
            
            const data = JSON.parse(item);
            
            // Check if the item has expired
            if (data.ttl && (Date.now() - data.timestamp > data.ttl)) {
                this.remove(key);
                return false;
            }
            
            return true;
        } catch (error) {
            logger.error(`Failed to check storage key '${key}':`, error);
            return false;
        }
    }
    
    /**
     * Get the number of items with the current prefix
     * @returns {number} The number of items
     */
    size() {
        return this.keys().length;
    }
    
    /**
     * Get all key-value pairs as an object
     * @returns {Object} An object with all key-value pairs
     */
    getAll() {
        const result = {};
        
        for (const key of this.keys()) {
            result[key] = this.get(key);
        }
        
        return result;
    }
    
    /**
     * Set multiple key-value pairs at once
     * @param {Object} items - An object with key-value pairs to set
     * @param {Object} [options] - Storage options
     * @returns {boolean} True if all operations succeeded
     */
    setAll(items, options = {}) {
        if (!items || typeof items !== 'object') {
            return false;
        }
        
        let allSucceeded = true;
        
        for (const [key, value] of Object.entries(items)) {
            const success = this.set(key, value, options);
            allSucceeded = allSucceeded && success;
        }
        
        return allSucceeded;
    }
    
    /**
     * Get multiple values at once
     * @param {string[]} keys - Array of keys to get
     * @returns {Object} An object with the requested key-value pairs
     */
    getMultiple(keys) {
        if (!Array.isArray(keys)) {
            return {};
        }
        
        const result = {};
        
        for (const key of keys) {
            result[key] = this.get(key);
        }
        
        return result;
    }
    
    /**
     * Remove multiple keys at once
     * @param {string[]} keys - Array of keys to remove
     * @returns {boolean} True if all operations succeeded
     */
    removeMultiple(keys) {
        if (!Array.isArray(keys)) {
            return false;
        }
        
        let allSucceeded = true;
        
        for (const key of keys) {
            const success = this.remove(key);
            allSucceeded = allSucceeded && success;
        }
        
        return allSucceeded;
    }
    
    /**
     * Add a change listener
     * @param {Function} callback - The callback function to call when storage changes
     * @returns {Function} A function to remove the event listener
     */
    onChange(callback) {
        if (typeof window === 'undefined' || this.type === STORAGE_TYPES.MEMORY) {
            // Memory storage doesn't support events
            return () => {};
        }
        
        const listener = (event) => {
            if (event.storageArea === this.storage) {
                const key = event.key;
                
                if (key && key.startsWith(this.prefix)) {
                    const shortKey = key.substring(this.prefix.length);
                    const newValue = event.newValue ? JSON.parse(event.newValue).value : null;
                    const oldValue = event.oldValue ? JSON.parse(event.oldValue).value : null;
                    
                    callback({
                        key: shortKey,
                        newValue,
                        oldValue,
                        storage: this,
                        originalEvent: event
                    });
                }
            }
        };
        
        window.addEventListener('storage', listener);
        
        // Return a function to remove the event listener
        return () => {
            window.removeEventListener('storage', listener);
        };
    }
}

// Export the Storage class and a default instance
export { Storage, STORAGE_TYPES };

// Create a default instance
export const storage = new Storage({
    prefix: 'wienerlinien_',
    storageType: STORAGE_TYPES.LOCAL
});

// Export a default object with all functions for convenience
export default {
    Storage,
    storage,
    STORAGE_TYPES,
    createStorage,
    isStorageAvailable,
    getBestStorageType
};
