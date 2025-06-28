/**
 * Routes UI components and interaction
 */

import { CONFIG } from '../../config.js';
import { ROUTE_TYPES, ICONS } from '../../constants.js';
import { logger } from '../utils/logger.js';

// DOM elements
let routeToggleContainer = null;

/**
 * Initialize the routes UI
 * @param {Array} routes - Array of route objects
 * @param {Function} onToggle - Callback for when a route is toggled
 */
export function initRouteUI(routes, onToggle) {
    try {
        logger.info('Initializing routes UI...');
        
        // Get or create the toggle container
        routeToggleContainer = document.getElementById('route-toggle-container');
        if (!routeToggleContainer) {
            routeToggleContainer = document.createElement('div');
            routeToggleContainer.id = 'route-toggle-container';
            routeToggleContainer.className = 'route-toggle-container';
            document.body.appendChild(routeToggleContainer);
        }
        
        // Clear existing content
        routeToggleContainer.innerHTML = '';
        
        // Group routes by type
        const routesByType = groupRoutesByType(routes);
        
        // Create toggle controls for each route type
        Object.entries(routesByType).forEach(([type, typeRoutes]) => {
            createRouteTypeSection(type, typeRoutes, onToggle);
        });
        
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
        const type = route.type || 'other';
        if (!groups[type]) {
            groups[type] = [];
        }
        groups[type].push(route);
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
        section.className = `route-type-section ${type}`;
        
        // Create section header
        const header = document.createElement('div');
        header.className = 'route-type-header';
        
        // Add icon
        const icon = document.createElement('i');
        icon.className = `fas ${ICONS[type] || ICONS.default}`;
        header.appendChild(icon);
        
        // Add type name
        const typeName = document.createElement('span');
        typeName.className = 'route-type-name';
        typeName.textContent = type.charAt(0).toUpperCase() + type.slice(1);
        header.appendChild(typeName);
        
        // Add toggle all button
        const toggleAllBtn = document.createElement('button');
        toggleAllBtn.className = 'toggle-all-btn';
        toggleAllBtn.innerHTML = '<i class="fas fa-eye"></i>';
        toggleAllBtn.title = 'Toggle all routes of this type';
        toggleAllBtn.onclick = () => toggleAllRoutes(type, routes, onToggle);
        header.appendChild(toggleAllBtn);
        
        section.appendChild(header);
        
        // Create route list
        const routeList = document.createElement('div');
        routeList.className = 'route-list';
        
        // Sort routes by name/number
        const sortedRoutes = [...routes].sort((a, b) => {
            return (a.name || '').localeCompare(b.name || '');
        });
        
        // Add route toggles
        sortedRoutes.forEach(route => {
            const toggle = createRouteToggle(route, onToggle);
            routeList.appendChild(toggle);
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
    const toggle = document.createElement('div');
    toggle.className = 'route-toggle';
    toggle.dataset.routeId = route.id;
    
    // Create checkbox
    const checkbox = document.createElement('input');
    checkbox.type = 'checkbox';
    checkbox.id = `route-${route.id}`;
    checkbox.checked = false;
    checkbox.onchange = (e) => onToggle(route.id, e.target.checked);
    
    // Create label
    const label = document.createElement('label');
    label.htmlFor = `route-${route.id}`;
    label.style.borderColor = route.color || CONFIG.ROUTES.DEFAULT_COLORS[route.type] || '#ccc';
    
    // Add route name/number
    const routeName = document.createElement('span');
    routeName.className = 'route-name';
    routeName.textContent = route.name || `Route ${route.id}`;
    
    // Add route description if available
    if (route.description) {
        const routeDesc = document.createElement('span');
        routeDesc.className = 'route-desc';
        routeDesc.textContent = route.description;
        label.appendChild(routeDesc);
    }
    
    label.prepend(routeName);
    
    toggle.appendChild(checkbox);
    toggle.appendChild(label);
    
    return toggle;
}

/**
 * Toggle all routes of a specific type
 * @private
 */
function toggleAllRoutes(type, routes, onToggle) {
    try {
        // Check if any route of this type is visible
        const anyVisible = routes.some(route => {
            const toggle = document.getElementById(`route-${route.id}`);
            return toggle?.checked;
        });
        
        // Toggle all routes of this type
        routes.forEach(route => {
            const toggle = document.getElementById(`route-${route.id}`);
            if (toggle) {
                const shouldBeVisible = !anyVisible;
                toggle.checked = shouldBeVisible;
                onToggle(route.id, shouldBeVisible);
            }
        });
        
    } catch (error) {
        logger.error(`Failed to toggle all ${type} routes:`, error);
    }
}

/**
 * Update the visual state of a route toggle
 * @param {string} routeId - ID of the route
 * @param {boolean} isActive - Whether the route is active
 */
export function updateRouteToggleState(routeId, isActive) {
    try {
        const toggle = document.getElementById(`route-${routeId}`);
        if (toggle) {
            toggle.checked = isActive;
            const label = toggle.nextElementSibling;
            if (label) {
                label.classList.toggle('active', isActive);
            }
        }
    } catch (error) {
        logger.error(`Failed to update toggle state for route ${routeId}:`, error);
    }
}
