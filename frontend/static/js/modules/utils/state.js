/**
 * State management utilities
 */

import { logger } from './logger.js';
import { storage } from './browserStorage.js';

// Default state
const DEFAULT_STATE = {
    // Map state
    map: {
        center: [48.2082, 16.3738], // Vienna coordinates
        zoom: 12,
        bearing: 0,
        pitch: 0,
        style: 'streets',
        showTraffic: false,
        showBikeLanes: false,
        showPointsOfInterest: true,
        showTransit: true,
        show3DBuildings: false,
        darkMode: false
    },
    
    // Route state
    route: {
        origin: null,
        destination: null,
        waypoints: [],
        isFetching: false,
        error: null,
        routes: [],
        selectedRoute: null,
        travelMode: 'transit',
        departureTime: null,
        arrivalTime: null,
        alternatives: true,
        optimize: 'quickest',
        wheelchairAccessible: false,
        bikeFriendly: false
    },
    
    // Station state
    station: {
        selected: null,
        nearby: [],
        favorites: [],
        recent: [],
        departures: {},
        isLoadingDepartures: false,
        departuresError: null
    },
    
    // Vehicle state
    vehicle: {
        selected: null,
        trackedVehicles: [],
        vehiclePositions: {},
        lastUpdated: null
    },
    
    // UI state
    ui: {
        isSidebarOpen: true,
        activePanel: 'search', // 'search', 'routes', 'stations', 'favorites', 'settings'
        isFullscreen: false,
        isLoading: false,
        loadingMessage: '',
        notifications: [],
        activeModals: [],
        lastRouteView: null,
        lastStationView: null,
        lastVehicleView: null,
        theme: 'system', // 'light', 'dark', 'system'
        language: 'en',
        units: 'metric',
        showTutorial: true,
        tutorialStep: 0
    },
    
    // User preferences
    preferences: {
        mapProvider: 'mapbox', // 'mapbox', 'maplibre', 'leaflet', etc.
        mapStyle: 'streets',
        routeOptions: {
            avoidStairs: false,
            avoidElevation: false,
            maxWalkingDistance: 1000, // meters
            maxTransfers: 5,
            accessibility: 'none', // 'none', 'partial', 'full'
            bikeType: 'city' // 'city', 'trekking', 'road', 'mtb'
        },
        notificationPreferences: {
            departureAlerts: true,
            serviceAlerts: true,
            delayNotifications: true,
            marketing: false,
            sound: true,
            vibration: true
        },
        privacy: {
            trackLocation: true,
            analytics: true,
            crashReporting: true,
            personalizedAds: false
        },
        dataUsage: {
            cacheMapTiles: true,
            cacheRoutes: true,
            cacheStations: true,
            cacheSize: 500, // MB
            offlineMaps: false,
            offlineArea: null // Bounding box for offline maps
        },
        display: {
            fontSize: 'medium', // 'small', 'medium', 'large', 'xlarge'
            contrast: 'normal', // 'normal', 'high'
            reduceMotion: false,
            reduceTransparency: false,
            highlightTimetables: true
        },
        accessibility: {
            screenReader: false,
            voiceControl: false,
            highContrastMode: false,
            textToSpeech: {
                enabled: false,
                rate: 1.0,
                pitch: 1.0,
                voice: null
            }
        },
        experimental: {
            useWebGL2: true,
            enableBetaFeatures: false,
            enableDeveloperMode: false
        }
    },
    
    // App metadata
    meta: {
        version: '1.0.0',
        firstLaunch: true,
        lastUpdateCheck: null,
        updateAvailable: false,
        changelog: [],
        stats: {
            sessions: 0,
            routesPlanned: 0,
            stationsViewed: 0,
            distanceTraveled: 0, // km
            carbonSaved: 0, // kg CO2
            favoriteStations: [],
            frequentDestinations: []
        }
    },
    
    // Network status
    network: {
        isOnline: true,
        isReachable: true,
        connectionType: 'unknown', // 'ethernet', 'wifi', 'cellular', 'unknown'
        effectiveConnectionType: '4g', // 'slow-2g', '2g', '3g', '4g'
        downlink: 0, // Mbps
        rtt: 0, // ms
        saveData: false
    },
    
    // Authentication state
    auth: {
        isAuthenticated: false,
        user: null,
        token: null,
        refreshToken: null,
        expiresAt: null,
        isLoggingIn: false,
        loginError: null,
        isRegistering: false,
        registrationError: null,
        isResettingPassword: false,
        resetPasswordError: null
    },
    
    // Error state
    error: {
        message: null,
        code: null,
        details: null,
        timestamp: null,
        isFatal: false
    }
};

// State class
class StateManager {
    constructor(initialState = {}) {
        this.state = { ...DEFAULT_STATE, ...initialState };
        this.listeners = new Map();
        this.history = [];
        this.future = [];
        this.maxHistory = 50;
        this.isDispatching = false;
        this.middlewares = [];
        
        // Load state from storage
        this.load();
        
        // Save state to storage on changes
        this.subscribe('*', () => {
            this.save();
        });
    }
    
    /**
     * Get the current state
     * @param {string} [path] - Path to a specific part of the state (e.g., 'map.zoom')
     * @returns {*} The current state or a part of it
     */
    getState(path) {
        if (!path || path === '*') {
            return this.state;
        }
        
        return path.split('.').reduce((obj, key) => {
            return obj && obj[key] !== undefined ? obj[key] : undefined;
        }, this.state);
    }
    
    /**
     * Set state
     * @param {Object|Function} update - The new state or a function that receives the current state and returns the new state
     * @param {string} [description] - Description of the state change (for debugging)
     */
    setState(update, description = 'State update') {
        if (this.isDispatching) {
            throw new Error('Cannot call setState while dispatching');
        }
        
        try {
            this.isDispatching = true;
            
            // Get the previous state
            const prevState = this.state;
            
            // Calculate the next state
            const nextState = typeof update === 'function' 
                ? update(prevState) 
                : { ...prevState, ...update };
            
            // Skip if no change
            if (this.isEqual(prevState, nextState)) {
                return;
            }
            
            // Add to history
            this.history = [
                { state: { ...prevState }, description, timestamp: Date.now() },
                ...this.history
            ].slice(0, this.maxHistory);
            
            // Clear future history
            this.future = [];
            
            // Update state
            this.state = nextState;
            
            // Notify listeners
            this.notifyListeners(prevState, nextState, description);
            
            logger.debug(`State updated: ${description}`, {
                prevState,
                nextState,
                description
            });
            
            return nextState;
        } catch (error) {
            logger.error('Error updating state:', error);
            throw error;
        } finally {
            this.isDispatching = false;
        }
    }
    
    /**
     * Subscribe to state changes
     * @param {string} path - Path to subscribe to (e.g., 'map.zoom' or '*' for all changes)
     * @param {Function} listener - Callback function
     * @returns {Function} Unsubscribe function
     */
    subscribe(path, listener) {
        if (typeof listener !== 'function') {
            throw new Error('Listener must be a function');
        }
        
        if (!this.listeners.has(path)) {
            this.listeners.set(path, new Set());
        }
        
        this.listeners.get(path).add(listener);
        
        // Return unsubscribe function
        return () => {
            if (this.listeners.has(path)) {
                this.listeners.get(path).delete(listener);
                
                // Clean up empty sets
                if (this.listeners.get(path).size === 0) {
                    this.listeners.delete(path);
                }
            }
        };
    }
    
    /**
     * Notify listeners of state changes
     * @private
     */
    notifyListeners(prevState, nextState, description) {
        // Get all paths that have changed
        const changedPaths = this.getChangedPaths(prevState, nextState);
        
        // Get all listeners that should be notified
        const listenersToNotify = new Set();
        
        // Add wildcard listeners
        if (this.listeners.has('*')) {
            this.listeners.get('*').forEach(listener => listenersToNotify.add(listener));
        }
        
        // Add specific path listeners
        for (const path of changedPaths) {
            if (this.listeners.has(path)) {
                this.listeners.get(path).forEach(listener => listenersToNotify.add(listener));
            }
        }
        
        // Call listeners
        listenersToNotify.forEach(listener => {
            try {
                listener(nextState, prevState, description);
            } catch (error) {
                logger.error('Error in state listener:', error);
            }
        });
    }
    
    /**
     * Get all paths that have changed between two states
     * @private
     */
    getChangedPaths(prevState, nextState, path = '') {
        const changedPaths = [];
        
        // Handle null/undefined states
        if (prevState === nextState) {
            return [];
        }
        
        if (prevState === null || nextState === null || 
            typeof prevState !== 'object' || typeof nextState !== 'object') {
            return [path || '*'];
        }
        
        // Get all unique keys from both states
        const allKeys = new Set([
            ...Object.keys(prevState),
            ...Object.keys(nextState)
        ]);
        
        // Check each key for changes
        for (const key of allKeys) {
            const currentPath = path ? `${path}.${key}` : key;
            
            if (!(key in prevState)) {
                // New key added
                changedPaths.push(currentPath);
            } else if (!(key in nextState)) {
                // Key removed
                changedPaths.push(currentPath);
            } else if (!this.isEqual(prevState[key], nextState[key])) {
                // Value changed
                if (typeof prevState[key] === 'object' && prevState[key] !== null &&
                    typeof nextState[key] === 'object' && nextState[key] !== null) {
                    // Recursively check nested objects
                    changedPaths.push(...this.getChangedPaths(prevState[key], nextState[key], currentPath));
                } else {
                    changedPaths.push(currentPath);
                }
            }
        }
        
        return changedPaths;
    }
    
    /**
     * Check if two values are equal
     * @private
     */
    isEqual(a, b) {
        // Handle primitive types and null/undefined
        if (a === b) return true;
        if (a == null || b == null) return a === b;
        
        // Handle dates
        if (a instanceof Date && b instanceof Date) {
            return a.getTime() === b.getTime();
        }
        
        // Handle arrays
        if (Array.isArray(a) && Array.isArray(b)) {
            if (a.length !== b.length) return false;
            
            for (let i = 0; i < a.length; i++) {
                if (!this.isEqual(a[i], b[i])) {
                    return false;
                }
            }
            
            return true;
        }
        
        // Handle objects
        if (typeof a === 'object' && typeof b === 'object') {
            const keysA = Object.keys(a);
            const keysB = Object.keys(b);
            
            if (keysA.length !== keysB.length) return false;
            
            for (const key of keysA) {
                if (!Object.prototype.hasOwnProperty.call(b, key) || 
                    !this.isEqual(a[key], b[key])) {
                    return false;
                }
            }
            
            return true;
        }
        
        return false;
    }
    
    /**
     * Undo the last state change
     * @returns {boolean} True if undo was successful
     */
    undo() {
        if (this.history.length === 0) {
            return false;
        }
        
        const previous = this.history[0];
        this.future = [{ state: { ...this.state }, description: 'Undo', timestamp: Date.now() }, ...this.future];
        this.state = { ...previous.state };
        this.history = this.history.slice(1);
        
        // Notify listeners
        this.notifyListeners(previous.state, this.state, `Undo: ${previous.description}`);
        
        return true;
    }
    
    /**
     * Redo the last undone state change
     * @returns {boolean} True if redo was successful
     */
    redo() {
        if (this.future.length === 0) {
            return false;
        }
        
        const next = this.future[0];
        this.history = [{ state: { ...this.state }, description: 'Redo', timestamp: Date.now() }, ...this.history];
        this.state = { ...next.state };
        this.future = this.future.slice(1);
        
        // Notify listeners
        this.notifyListeners(next.state, this.state, `Redo: ${next.description}`);
        
        return true;
    }
    
    /**
     * Reset state to default
     */
    reset() {
        const prevState = this.state;
        this.state = { ...DEFAULT_STATE };
        this.history = [];
        this.future = [];
        
        // Notify listeners
        this.notifyListeners(prevState, this.state, 'Reset state');
    }
    
    /**
     * Reset a specific part of the state
     * @param {string} path - Path to reset (e.g., 'map' or 'route.origin')
     */
    resetPath(path) {
        if (!path) {
            this.reset();
            return;
        }
        
        const parts = path.split('.');
        const key = parts.pop();
        const parentPath = parts.join('.');
        const parent = this.getState(parentPath);
        
        if (parent && key in parent) {
            const defaultValue = this.getDefaultValue(path);
            
            if (defaultValue !== undefined) {
                this.setState(state => {
                    const newState = { ...state };
                    let current = newState;
                    
                    for (const part of parts) {
                        if (!current[part]) {
                            current[part] = {};
                        }
                        current = current[part];
                    }
                    
                    current[key] = JSON.parse(JSON.stringify(defaultValue));
                    return newState;
                }, `Reset ${path} to default`);
            }
        }
    }
    
    /**
     * Get the default value for a path
     * @private
     */
    getDefaultValue(path) {
        const parts = path.split('.');
        let current = DEFAULT_STATE;
        
        for (const part of parts) {
            if (current && typeof current === 'object' && part in current) {
                current = current[part];
            } else {
                return undefined;
            }
        }
        
        return current !== undefined ? JSON.parse(JSON.stringify(current)) : undefined;
    }
    
    /**
     * Load state from storage
     */
    load() {
        try {
            const savedState = storage.get('app_state');
            
            if (savedState) {
                // Merge with default state to ensure all fields exist
                this.state = this.mergeDeep(
                    { ...DEFAULT_STATE },
                    savedState
                );
                
                logger.debug('State loaded from storage');
                return true;
            }
        } catch (error) {
            logger.error('Error loading state from storage:', error);
        }
        
        return false;
    }
    
    /**
     * Save state to storage
     */
    save() {
        try {
            // Only save non-sensitive data
            const stateToSave = {
                ...this.state,
                // Clear sensitive data
                auth: {
                    ...this.state.auth,
                    token: null,
                    refreshToken: null
                }
            };
            
            storage.set('app_state', stateToSave);
            return true;
        } catch (error) {
            logger.error('Error saving state to storage:', error);
            return false;
        }
    }
    
    /**
     * Deep merge two objects
     * @private
     */
    mergeDeep(target, source) {
        if (source === null || typeof source !== 'object') {
            return source;
        }
        
        if (Array.isArray(source)) {
            return [...source];
        }
        
        const output = { ...target };
        
        for (const key in source) {
            if (Object.prototype.hasOwnProperty.call(source, key)) {
                if (source[key] && typeof source[key] === 'object' && 
                    target[key] && typeof target[key] === 'object') {
                    output[key] = this.mergeDeep(target[key], source[key]);
                } else {
                    output[key] = source[key];
                }
            }
        }
        
        return output;
    }
    
    /**
     * Add a middleware
     * @param {Function} middleware - Middleware function
     */
    use(middleware) {
        if (typeof middleware !== 'function') {
            throw new Error('Middleware must be a function');
        }
        
        this.middlewares.push(middleware);
        return () => {
            this.middlewares = this.middlewares.filter(m => m !== middleware);
        };
    }
    
    /**
     * Dispatch an action
     * @param {string} type - Action type
     * @param {*} payload - Action payload
     * @returns {*} The result of the action
     */
    dispatch(type, payload) {
        if (this.isDispatching) {
            throw new Error('Cannot dispatch while another action is being processed');
        }
        
        const action = { type, payload };
        
        // Create a chain of middlewares
        const chain = this.middlewares.map(middleware => middleware(this));
        
        // Compose the chain with the final dispatch
        const dispatchWithMiddleware = chain.reduceRight(
            (next, middleware) => middleware(next),
            (action) => this.handleAction(action)
        );
        
        return dispatchWithMiddleware(action);
    }
    
    /**
     * Handle an action
     * @private
     */
    handleAction(action) {
        // This is where you would handle actions in a Redux-like way
        // For now, we'll just log the action
        logger.debug('Action dispatched:', action);
        
        // Example of handling actions
        switch (action.type) {
            case 'RESET_STATE':
                this.reset();
                break;
            case 'LOAD_STATE':
                this.load();
                break;
            case 'SAVE_STATE':
                this.save();
                break;
            // Add more action handlers as needed
        }
        
        return action;
    }
}

// Create a singleton instance
export const stateManager = new StateManager();

// Export a default object with the singleton instance and utility functions
export default {
    // Singleton instance
    stateManager,
    
    // Utility functions
    getState: (path) => stateManager.getState(path),
    setState: (update, description) => stateManager.setState(update, description),
    subscribe: (path, listener) => stateManager.subscribe(path, listener),
    undo: () => stateManager.undo(),
    redo: () => stateManager.redo(),
    reset: () => stateManager.reset(),
    resetPath: (path) => stateManager.resetPath(path),
    load: () => stateManager.load(),
    save: () => stateManager.save(),
    dispatch: (type, payload) => stateManager.dispatch(type, payload),
    use: (middleware) => stateManager.use(middleware)
};
