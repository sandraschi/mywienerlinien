/**
 * Routes UI components and interaction
 */

import { CONFIG } from '../../config.js';
import { ROUTE_TYPES } from '../../constants.js';
import { logger } from '../utils/logger.js';

// DOM elements
let routeToggleContainer = null;
let activeRoutes = new Set();
const routeTypeOrder = [ROUTE_TYPES.METRO, ROUTE_TYPES.TRAM, ROUTE_TYPES.BUS, ROUTE_TYPES.NIGHTBUS];
const routeTypeNames = {
    [ROUTE_TYPES.METRO]: 'U-Bahn',
    [ROUTE_TYPES.TRAM]: 'Tram',
    [ROUTE_TYPES.BUS]: 'Bus',
    [ROUTE_TYPES.NIGHTBUS]: 'Night Bus'
};

// Icons for different route types
const ROUTE_ICONS = {
    [ROUTE_TYPES.METRO]: 'subway',
    [ROUTE_TYPES.TRAM]: 'train-tram',
    [ROUTE_TYPES.BUS]: 'bus',
    [ROUTE_TYPES.NIGHTBUS]: 'moon',
    default: 'route'
};

// Colors for different route types
const ROUTE_COLORS = {
    [ROUTE_TYPES.METRO]: '#c70f3e',
    [ROUTE_TYPES.TRAM]: '#f39200',
    [ROUTE_TYPES.BUS]: '#0067b1',
    [ROUTE_TYPES.NIGHTBUS]: '#1a1a1a',
    default: '#666666'
};

/**
 * Initialize the routes UI
 * @param {Array} routes - Array of route objects
 * @param {Function} onToggle - Callback for when a route is toggled
 */
export function initRouteUI(routes, onToggle) {
    try {
        logger.info('Initializing routes UI...');
        
        // Get the route toggles container
        routeToggleContainer = document.getElementById('route-toggles');
        if (!routeToggleContainer) {
            logger.error('Route toggles container not found');
            return;
        }
        
        // Clear loading message
        routeToggleContainer.innerHTML = '';
        
        // Group routes by type
        const routesByType = groupRoutesByType(routes);
        
        // Sort routes within each type
        Object.values(routesByType).forEach(routes => {
            routes.sort((a, b) => {
                // Extract numbers for proper numeric sorting (e.g., U1, U2, U11)
                const numA = a.id.match(/\d+/) ? parseInt(a.id.match(/(\d+)/)[0], 10) : 0;
                const numB = b.id.match(/\d+/) ? parseInt(b.id.match(/(\d+)/)[0], 10) : 0;
                
                // If both have numbers, sort numerically
                if (!isNaN(numA) && !isNaN(numB)) {
                    return numA - numB;
                }
                
                // Otherwise sort alphabetically
                return a.id.localeCompare(b.id);
            });
        });
        
        // Create toggle controls for each route type in the specified order
        routeTypeOrder.forEach(type => {
            if (routesByType[type] && routesByType[type].length > 0) {
                createRouteTypeSection(type, routesByType[type], onToggle);
            }
        });
        
        // Add event listener for the "Show All" button
        const toggleAllBtn = document.querySelector('.toggle-all-routes');
        if (toggleAllBtn) {
            toggleAllBtn.addEventListener('click', () => toggleAllRoutes(routes, onToggle));
        }
        
        logger.info('Routes UI initialized');
        
    } catch (error) {
        logger.error('Failed to initialize routes UI:', error);
        throw error;
    }
}

/**
 * Group routes by their type
 * @private
 */
function groupRoutesByType(routes) {
    return routes.reduce((groups, route) => {
        // Ensure we have a valid type, default to 'other'
        const type = routeTypeOrder.includes(route.type) ? route.type : 'other';
        if (!groups[type]) {
            groups[type] = [];
        }
        
        // Check for duplicates
        const exists = groups[type].some(r => r.id === route.id);
        if (!exists) {
            groups[type].push(route);
        }
        
        return groups;
    }, {});
}

/**
 * Create a section for a specific route type
 * @private
 */
function createRouteTypeSection(type, routes, onToggle) {
    try {
        // Create section container
        const section = document.createElement('div');
        section.className = `route-type-section`;
        
        // Create section header
        const header = document.createElement('h4');
        header.className = 'route-type-header';
        header.textContent = routeTypeNames[type] || type;
        section.appendChild(header);
        
        // Create route list container
        const routeList = document.createElement('div');
        routeList.className = 'route-list';
        
        // Add route toggles
        routes.forEach(route => {
            const routeToggle = createRouteToggle(route, onToggle);
            routeList.appendChild(routeToggle);
        });
        
        section.appendChild(routeList);
        routeToggleContainer.appendChild(section);
        
    } catch (error) {
        logger.error(`Failed to create route type section for ${type}:`, error);
    }
}

/**
 * Create a route toggle button
 * @private
 */
function createRouteToggle(route, onToggle) {
    const toggle = document.createElement('button');
    toggle.className = `route-toggle ${route.type}`;
    toggle.dataset.routeId = route.id;
    
    // Create route icon with the route ID
    const icon = document.createElement('span');
    icon.className = 'route-icon';
    icon.textContent = route.id;
    
    // Set the background color based on route type
    const routeColor = ROUTE_COLORS[route.type] || ROUTE_COLORS.default;
    icon.style.backgroundColor = routeColor;
    
    // Create route name (optional, can be removed if not needed)
    const name = document.createElement('span');
    name.className = 'route-name';
    name.textContent = route.name || '';
    
    // Add elements to toggle
    toggle.appendChild(icon);
    if (name.textContent) {
        toggle.appendChild(name);
    }
    
    // Add click handler
    toggle.addEventListener('click', (e) => {
        e.preventDefault();
        const isActive = toggle.classList.toggle('active');
        
        // Update active routes set
        if (isActive) {
            activeRoutes.add(route.id);
        } else {
            activeRoutes.delete(route.id);
        }
        
        // Call the provided callback
        onToggle(route.id, isActive);
    });
    
    return toggle;
}

/**
 * Toggle all routes
 * @private
 */
function toggleAllRoutes(routes, onToggle) {
    try {
        const allToggles = document.querySelectorAll('.route-toggle');
        const anyActive = activeRoutes.size > 0;
        
        // Clear active routes
        activeRoutes.clear();
        
        // Toggle all routes
        allToggles.forEach(toggle => {
            const routeId = toggle.dataset.routeId;
            const isActive = !anyActive;
            
            if (isActive) {
                toggle.classList.add('active');
                activeRoutes.add(routeId);
            } else {
                toggle.classList.remove('active');
            }
            
            // Call the provided callback for each route
            onToggle(routeId, isActive);
        });
        
        // Update the "Show All" button text
        const toggleAllBtn = document.querySelector('.toggle-all-routes');
        if (toggleAllBtn) {
            toggleAllBtn.textContent = anyActive ? '[Show All]' : '[Hide All]';
        }
        
    } catch (error) {
        logger.error('Failed to toggle all routes:', error);
    }
}

/**
 * Update the visual state of a route toggle
 * @param {string} routeId - ID of the route
 * @param {boolean} isActive - Whether the route is active
 */
export function updateRouteToggleState(routeId, isActive) {
    const toggle = document.querySelector(`.route-toggle[data-route-id="${routeId}"]`);
    if (toggle) {
        if (isActive) {
            toggle.classList.add('active');
            activeRoutes.add(routeId);
        } else {
            toggle.classList.remove('active');
            activeRoutes.delete(routeId);
        }
    }
    
    // Update the "Show All" button text based on active routes
    const toggleAllBtn = document.querySelector('.toggle-all-routes');
    if (toggleAllBtn) {
        const allToggles = document.querySelectorAll('.route-toggle');
        if (activeRoutes.size === allToggles.length) {
            toggleAllBtn.textContent = '[Hide All]';
        } else if (activeRoutes.size === 0) {
            toggleAllBtn.textContent = '[Show All]';
        } else {
            toggleAllBtn.textContent = `[${activeRoutes.size} active]`;
        }
    }
}
