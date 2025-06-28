/**
 * Application constants
 */

export const ROUTE_TYPES = {
    METRO: 'metro',
    TRAM: 'tram',
    BUS: 'bus',
    NIGHTBUS: 'nightbus'
};

export const VEHICLE_TYPES = {
    METRO: 'ptMetro',
    TRAM: 'ptTram',
    BUS: 'ptBus',
    NIGHTBUS: 'ptNightBus'
};

export const STORAGE_KEYS = {
    ACTIVE_ROUTES: 'activeRoutes',
    MAP_POSITION: 'mapPosition',
    SELECTED_FILTERS: 'selectedFilters'
};

export const EVENT_TYPES = {
    ROUTES_LOADED: 'routes:loaded',
    VEHICLES_UPDATED: 'vehicles:updated',
    STATIONS_LOADED: 'stations:loaded',
    DISRUPTIONS_UPDATED: 'disruptions:updated',
    ROUTE_TOGGLED: 'route:toggled',
    MAP_VIEW_CHANGED: 'map:viewchanged'
};

export const ROUTE_COLORS = {
    [ROUTE_TYPES.METRO]: '#c70f3e',
    [ROUTE_TYPES.TRAM]: '#f39200',
    [ROUTE_TYPES.BUS]: '#0067b1',
    [ROUTE_TYPES.NIGHTBUS]: '#1a1a1a',
    DEFAULT: '#666666'
};

export const ICONS = {
    [ROUTE_TYPES.METRO]: 'fa-train-subway',
    [ROUTE_TYPES.TRAM]: 'fa-train-tram',
    [ROUTE_TYPES.BUS]: 'fa-bus',
    [ROUTE_TYPES.NIGHTBUS]: 'fa-moon',
    STATION: 'fa-map-marker-alt',
    VEHICLE: 'fa-circle',
    DISRUPTION: 'fa-exclamation-triangle'
};

export const DEFAULT_ZOOM_LEVELS = {
    [ROUTE_TYPES.METRO]: 12,
    [ROUTE_TYPES.TRAM]: 13,
    [ROUTE_TYPES.BUS]: 14,
    [ROUTE_TYPES.NIGHTBUS]: 12,
    DEFAULT: 12
};
