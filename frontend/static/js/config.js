/**
 * Application configuration
 */

export const CONFIG = {
    // Map settings
    MAP: {
        DEFAULT_ZOOM: 12,
        DEFAULT_CENTER: [48.2082, 16.3738], // Vienna coordinates
        MAX_ZOOM: 18,
        MIN_ZOOM: 10,
        TILE_LAYER: 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
        TILE_ATTRIBUTION: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    },
    
    // API endpoints
    API: {
        BASE_URL: '/api',
        ENDPOINTS: {
            ROUTES: '/routes',
            VEHICLES: '/vehicles',
            STATIONS: '/stations',
            DISRUPTIONS: '/disruptions'
        }
    },
    
    // Route settings
    ROUTES: {
        LINE_WEIGHT: 5,
        LINE_OPACITY: 0.8,
        HIGHLIGHT_WEIGHT: 7,
        HIGHLIGHT_OPACITY: 0.9,
        DEFAULT_COLORS: {
            metro: '#c70f3e',
            tram: '#f39200',
            bus: '#0067b1',
            nightbus: '#1a1a1a',
            default: '#666666'
        }
    },
    
    // Marker settings
    MARKERS: {
        STOP: {
            RADIUS: 4,
            TERMINUS_RADIUS: 6,
            OPACITY: 1,
            FILL_OPACITY: 0.8,
            WEIGHT: 1,
            HOVER_WEIGHT: 2
        },
        VEHICLE: {
            ICON_SIZE: [24, 24],
            ICON_ANCHOR: [12, 12],
            POPUP_OFFSET: [0, -12]
        }
    },
    
    // UI settings
    UI: {
        TOAST_DURATION: 5000, // ms
        REFRESH_INTERVAL: 30000, // ms
        DEBOUNCE_DELAY: 300 // ms
    }
};

// Feature toggles
export const FEATURES = {
    ENABLE_OFFLINE_MODE: false,
    ENABLE_ANIMATIONS: true,
    ENABLE_LOGGING: true
};
