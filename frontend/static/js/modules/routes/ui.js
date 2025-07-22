/**
 * Routes UI components and interaction
 */

import { CONFIG } from '../../config.js';
import { ROUTE_TYPES } from '../../constants.js';
import { logger } from '../utils/logger.js';

// DOM elements
let routeToggleContainer = null;
let activeRoutes = new Set();

// Define route types in the order they should appear
const routeTypeOrder = [
    ROUTE_TYPES.SUBWAY, 
    ROUTE_TYPES.TRAM, 
    ROUTE_TYPES.BUS, 
    ROUTE_TYPES.TRAIN,
    ROUTE_TYPES.FERRY,
    ROUTE_TYPES.CABLECAR,
    ROUTE_TYPES.GONDOLA,
    ROUTE_TYPES.FUNICULAR
];

// Human-readable names for route types
const routeTypeNames = {
    [ROUTE_TYPES.SUBWAY]: 'U-Bahn',
    [ROUTE_TYPES.TRAM]: 'Tram',
    [ROUTE_TYPES.BUS]: 'Bus',
    [ROUTE_TYPES.TRAIN]: 'S-Bahn',
    [ROUTE_TYPES.FERRY]: 'Fähre',
    [ROUTE_TYPES.CABLECAR]: 'Seilbahn',
    [ROUTE_TYPES.GONDOLA]: 'Gondel',
    [ROUTE_TYPES.FUNICULAR]: 'Standseilbahn',
    [ROUTE_TYPES.NIGHTBUS]: 'Nightline'
};

// Icons for different route types (using Font Awesome classes)
const ROUTE_ICONS = {
    [ROUTE_TYPES.SUBWAY]: 'fa-subway',
    [ROUTE_TYPES.TRAM]: 'fa-train-tram',
    [ROUTE_TYPES.BUS]: 'fa-bus',
    [ROUTE_TYPES.TRAIN]: 'fa-train',
    [ROUTE_TYPES.FERRY]: 'fa-ferry',
    [ROUTE_TYPES.CABLECAR]: 'fa-mountain',
    [ROUTE_TYPES.GONDOLA]: 'fa-mountain-sun',
    [ROUTE_TYPES.FUNICULAR]: 'fa-mountain',
    [ROUTE_TYPES.NIGHTBUS]: 'fa-moon',
    default: 'fa-route'
};

// Colors for different route types (Vienna public transport colors)
const ROUTE_COLORS = {
    [ROUTE_TYPES.SUBWAY]: '#c70f3e', // U-Bahn red
    [ROUTE_TYPES.TRAM]: '#f39200',    // Tram yellow
    [ROUTE_TYPES.BUS]: '#0067b1',     // Bus blue
    [ROUTE_TYPES.TRAIN]: '#8c4799',   // S-Bahn purple
    [ROUTE_TYPES.FERRY]: '#0098a1',   // Ferry teal
    [ROUTE_TYPES.CABLECAR]: '#e30074', // Cable car pink
    [ROUTE_TYPES.GONDOLA]: '#e30074',  // Gondola pink
    [ROUTE_TYPES.FUNICULAR]: '#e30074',// Funicular pink
    [ROUTE_TYPES.NIGHTBUS]: '#1a1a1a', // Night bus black
    default: '#666666'
};

// Grid layout configuration
const GRID_CONFIG = {
    maxColumns: 8,       // Maximum number of buttons per row
    buttonSize: '40px',  // Fixed size for each button
    gap: '4px',          // Gap between buttons
    fontSize: '14px',    // Font size for button text
    iconSize: '14px'     // Font size for icons
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
    const section = document.createElement('div');
    section.className = 'route-type-section';
    section.style.marginBottom = '16px';
    
    // Create header with icon and title
    const header = document.createElement('div');
    header.className = 'route-type-header';
    header.style.display = 'flex';
    header.style.alignItems = 'center';
    header.style.marginBottom = '8px';
    header.style.paddingBottom = '4px';
    header.style.borderBottom = `2px solid ${ROUTE_COLORS[type] || ROUTE_COLORS.default}`;
    
    // Add icon
    const icon = document.createElement('i');
    icon.className = `fas ${ROUTE_ICONS[type] || ROUTE_ICONS.default} me-2`;
    icon.style.color = ROUTE_COLORS[type] || ROUTE_COLORS.default;
    icon.style.width = '20px';
    icon.style.textAlign = 'center';
    header.appendChild(icon);
    
    // Add type name
    const nameSpan = document.createElement('span');
    nameSpan.textContent = routeTypeNames[type] || type;
    nameSpan.style.flexGrow = '1';
    nameSpan.style.fontWeight = 'bold';
    nameSpan.style.fontSize = '0.9em';
    nameSpan.style.textTransform = 'uppercase';
    nameSpan.style.letterSpacing = '0.5px';
    header.appendChild(nameSpan);
    
    // Add toggle all button
    const toggleAllBtn = document.createElement('button');
    toggleAllBtn.className = 'btn btn-sm btn-outline-secondary';
    toggleAllBtn.innerHTML = '<i class="fas fa-exchange-alt"></i>';
    toggleAllBtn.title = `Toggle all ${routeTypeNames[type] || type} routes`;
    toggleAllBtn.style.padding = '2px 6px';
    toggleAllBtn.style.fontSize = '0.8em';
    toggleAllBtn.style.marginLeft = '8px';
    
    toggleAllBtn.addEventListener('click', (e) => {
        e.preventDefault();
        e.stopPropagation();
        const allActive = routes.every(route => activeRoutes.has(route.id));
        routes.forEach(route => onToggle(route.id, !allActive));
    });
    
    header.appendChild(toggleAllBtn);
    section.appendChild(header);
    
    // Create container for route toggles with grid layout
    const togglesContainer = document.createElement('div');
    togglesContainer.className = 'route-toggles-grid';
    
    // Apply grid styles
    Object.assign(togglesContainer.style, {
        display: 'grid',
        gridTemplateColumns: `repeat(auto-fill, minmax(${GRID_CONFIG.buttonSize}, 1fr))`,
        gap: GRID_CONFIG.gap,
        marginBottom: '12px',
        width: '100%'
    });
    
    // Add route toggles
    routes.forEach(route => {
        const toggle = createRouteToggle(route, onToggle);
        togglesContainer.appendChild(toggle);
    });
    
    section.appendChild(togglesContainer);
    routeToggleContainer.appendChild(section);
}
}

/**
 * Create a route toggle button
 * @private
 */
function createRouteToggle(route, onToggle) {
    const button = document.createElement('button');
    button.className = 'route-toggle';
    button.dataset.routeId = route.id;
    button.title = route.description || route.longName || route.name;
    
    // Set button style based on route color
    const bgColor = route.color || ROUTE_COLORS[route.type] || ROUTE_COLORS.default;
    const textColor = route.textColor || getContrastColor(bgColor);
    
    // Apply button styles
    Object.assign(button.style, {
        backgroundColor: bgColor,
        color: textColor,
        border: `1px solid ${darkenColor(bgColor, 20)}`,
        width: GRID_CONFIG.buttonSize,
        height: GRID_CONFIG.buttonSize,
        borderRadius: '4px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        cursor: 'pointer',
        padding: 0,
        margin: 0,
        fontSize: GRID_CONFIG.fontSize,
        fontWeight: 'bold',
        transition: 'all 0.2s ease',
        position: 'relative',
        overflow: 'hidden'
    });
    
    // Add hover effect
    button.addEventListener('mouseenter', () => {
        button.style.transform = 'scale(1.05)';
        button.style.boxShadow = '0 2px 8px rgba(0,0,0,0.2)';
    });
    
    button.addEventListener('mouseleave', () => {
        button.style.transform = '';
        button.style.boxShadow = '';
    });
    
    // Add active state
    button.addEventListener('mousedown', () => {
        button.style.transform = 'scale(0.95)';
    });
    
    button.addEventListener('mouseup', () => {
        button.style.transform = 'scale(1.05)';
    });
    
    // Add focus styles
    button.addEventListener('focus', () => {
        button.style.outline = 'none';
        button.style.boxShadow = `0 0 0 3px ${lightenColor(bgColor, 40)}`;
    });
    
    button.addEventListener('blur', () => {
        button.style.boxShadow = '';
    });
    
    // Add route name
    button.textContent = route.name;
    
    // Add click handler
    button.addEventListener('click', (e) => {
        e.preventDefault();
        e.stopPropagation();
        onToggle(route.id, !activeRoutes.has(route.id));
    });
    
    // Add keyboard support
    button.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            onToggle(route.id, !activeRoutes.has(route.id));
        }
    });
    
    return button;
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
    try {
        const toggle = document.querySelector(`.route-toggle[data-route-id="${routeId}"]`);
        if (toggle) {
            if (isActive) {
                activeRoutes.add(routeId);
                toggle.classList.add('active');
                toggle.style.opacity = '1';
                toggle.style.transform = 'scale(1.05)';
                toggle.style.boxShadow = '0 2px 8px rgba(0,0,0,0.2)';
                toggle.style.zIndex = '10';
            } else {
                activeRoutes.delete(routeId);
                toggle.classList.remove('active');
                toggle.style.opacity = '0.7';
                toggle.style.transform = 'scale(1)';
                toggle.style.boxShadow = 'none';
                toggle.style.zIndex = '1';
            }
        }
    } catch (error) {
        logger.error(`Failed to update route toggle state for ${routeId}:`, error);
    }
}

/**
 * Lighten or darken a color
 * @private
 */
function adjustColor(color, amount) {
    return '#' + color.replace(/^#/, '').replace(/../g, color => 
        ('0' + Math.min(255, Math.max(0, parseInt(color, 16) + amount)).toString(16)).substr(-2)
    );
}

/**
 * Lighten a color
 * @private
 */
function lightenColor(color, amount) {
    return adjustColor(color, amount);
}

/**
 * Darken a color
 * @private
 */
function darkenColor(color, amount) {
    return adjustColor(color, -amount);
}

/**
 * Get contrast color (black or white) for a given background color
 * @private
 */
function getContrastColor(hexColor) {
    // Convert hex to RGB
    const r = parseInt(hexColor.substr(1, 2), 16);
    const g = parseInt(hexColor.substr(3, 2), 16);
    const b = parseInt(hexColor.substr(5, 2), 16);
    
    // Calculate luminance (perceived brightness)
    const luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255;
    
    // Return black for light colors, white for dark colors
    return luminance > 0.5 ? '#000000' : '#ffffff';
}

/**
 * Update the "Show All" button text based on active routes
 * @private
 */
function updateToggleAllBtnText() {
    const toggleAllBtn = document.querySelector('.toggle-all-routes');
    if (toggleAllBtn) {
        const allToggles = document.querySelectorAll('.route-toggle');
        const activeCount = document.querySelectorAll('.route-toggle.active').length;
        
        if (activeCount === 0) {
            toggleAllBtn.textContent = 'Show All';
        } else if (activeCount === allToggles.length) {
            toggleAllBtn.textContent = 'Hide All';
        } else {
            toggleAllBtn.textContent = 'Toggle All';
        }
    }
}
