/**
 * Vehicles UI components and interaction
 */

import { CONFIG } from '../../config.js';
import { VEHICLE_TYPES, ICONS } from '../../constants.js';
import { logger } from '../utils/logger.js';

// DOM elements
let vehicleControls = null;
let vehicleListContainer = null;

/**
 * Initialize the vehicles UI
 * @param {Object} options - Configuration options
 * @param {Function} options.onToggle - Callback for when a vehicle is toggled
 * @param {Function} options.onRefresh - Callback for manual refresh
 * @param {Function} options.onAutoUpdateChange - Callback for auto-update toggle
 */
export function initVehicleUI({ onToggle, onRefresh, onAutoUpdateChange }) {
    try {
        logger.info('Initializing vehicles UI...');
        
        // Create or get the vehicles container
        const container = document.getElementById('vehicles-container') || createVehiclesContainer();
        
        // Create or get the controls
        vehicleControls = document.getElementById('vehicle-controls') || createVehicleControls(container);
        
        // Set up refresh button
        const refreshBtn = vehicleControls.querySelector('.refresh-btn');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => {
                logger.debug('Manual refresh requested');
                onRefresh();
            });
        }
        
        // Set up auto-update toggle
        const autoUpdateToggle = vehicleControls.querySelector('.auto-update-toggle');
        if (autoUpdateToggle) {
            autoUpdateToggle.checked = true; // Default to on
            
            autoUpdateToggle.addEventListener('change', (e) => {
                const isEnabled = e.target.checked;
                logger.debug(`Auto-update ${isEnabled ? 'enabled' : 'disabled'}`);
                onAutoUpdateChange(isEnabled);
            });
        }
        
        // Create or get the vehicle list container
        vehicleListContainer = document.getElementById('vehicle-list') || createVehicleListContainer(container);
        
        logger.info('Vehicles UI initialized');
        
    } catch (error) {
        logger.error('Failed to initialize vehicles UI:', error);
        throw error;
    }
}

/**
 * Create the vehicles container
 * @private
 */
function createVehiclesContainer() {
    const container = document.createElement('div');
    container.id = 'vehicles-container';
    container.className = 'vehicles-container';
    
    // Add to the sidebar if it exists, otherwise add to body
    const sidebar = document.querySelector('.sidebar') || document.body;
    sidebar.appendChild(container);
    
    return container;
}

/**
 * Create the vehicle controls
 * @private
 */
function createVehicleControls(container) {
    const controls = document.createElement('div');
    controls.id = 'vehicle-controls';
    controls.className = 'vehicle-controls';
    
    // Add title
    const title = document.createElement('h3');
    title.className = 'vehicle-controls-title';
    title.innerHTML = '<i class="fas fa-car-side"></i> Vehicles';
    controls.appendChild(title);
    
    // Add controls
    const controlsRow = document.createElement('div');
    controlsRow.className = 'controls-row';
    
    // Refresh button
    const refreshBtn = document.createElement('button');
    refreshBtn.className = 'btn btn-sm btn-outline-primary refresh-btn';
    refreshBtn.title = 'Refresh vehicle data';
    refreshBtn.innerHTML = '<i class="fas fa-sync-alt"></i>';
    
    // Auto-update toggle
    const toggleWrapper = document.createElement('label');
    toggleWrapper.className = 'toggle-switch';
    toggleWrapper.title = 'Toggle auto-update';
    
    const toggleInput = document.createElement('input');
    toggleInput.type = 'checkbox';
    toggleInput.className = 'auto-update-toggle';
    toggleInput.checked = true;
    
    const toggleSlider = document.createElement('span');
    toggleSlider.className = 'toggle-slider';
    
    toggleWrapper.appendChild(toggleInput);
    toggleWrapper.appendChild(toggleSlider);
    
    // Add to controls row
    controlsRow.appendChild(refreshBtn);
    controlsRow.appendChild(toggleWrapper);
    
    // Add to controls
    controls.appendChild(controlsRow);
    
    // Add to container
    container.appendChild(controls);
    
    return controls;
}

/**
 * Create the vehicle list container
 * @private
 */
function createVehicleListContainer(container) {
    const listContainer = document.createElement('div');
    listContainer.id = 'vehicle-list';
    listContainer.className = 'vehicle-list';
    
    // Add placeholder
    const placeholder = document.createElement('div');
    placeholder.className = 'no-vehicles';
    placeholder.textContent = 'No vehicles available';
    listContainer.appendChild(placeholder);
    
    // Add to container
    container.appendChild(listContainer);
    
    return listContainer;
}

/**
 * Update the vehicle list in the UI
 * @param {Array} vehicles - Array of vehicle objects
 * @param {Function} onToggle - Callback for when a vehicle is toggled
 */
export function updateVehicleList(vehicles, onToggle) {
    if (!vehicleListContainer) return;
    
    try {
        // Clear existing content
        vehicleListContainer.innerHTML = '';
        
        if (!vehicles || vehicles.length === 0) {
            const noVehicles = document.createElement('div');
            noVehicles.className = 'no-vehicles';
            noVehicles.textContent = 'No vehicles available';
            vehicleListContainer.appendChild(noVehicles);
            return;
        }
        
        // Group vehicles by type
        const vehiclesByType = groupVehiclesByType(vehicles);
        
        // Create a section for each vehicle type
        Object.entries(vehiclesByType).forEach(([type, typeVehicles]) => {
            createVehicleTypeSection(type, typeVehicles, onToggle);
        });
        
    } catch (error) {
        logger.error('Failed to update vehicle list:', error);
        
        // Show error message
        vehicleListContainer.innerHTML = `
            <div class="alert alert-danger">
                <i class="fas fa-exclamation-triangle"></i>
                Failed to load vehicle data
            </div>
        `;
    }
}

/**
 * Group vehicles by their type
 * @private
 */
function groupVehiclesByType(vehicles) {
    return vehicles.reduce((groups, vehicle) => {
        const type = vehicle.type || 'other';
        if (!groups[type]) {
            groups[type] = [];
        }
        groups[type].push(vehicle);
        return groups;
    }, {});
}

/**
 * Create a section for a specific vehicle type
 * @private
 */
function createVehicleTypeSection(type, vehicles, onToggle) {
    try {
        // Create section container
        const section = document.createElement('div');
        section.className = `vehicle-type-section ${type}`;
        
        // Create section header
        const header = document.createElement('div');
        header.className = 'vehicle-type-header';
        
        // Add icon
        const icon = document.createElement('i');
        icon.className = `fas ${ICONS[type] || ICONS.VEHICLE}`;
        header.appendChild(icon);
        
        // Add type name
        const typeName = document.createElement('span');
        typeName.className = 'vehicle-type-name';
        typeName.textContent = type.charAt(0).toUpperCase() + type.slice(1);
        header.appendChild(typeName);
        
        // Add count
        const count = document.createElement('span');
        count.className = 'vehicle-count';
        count.textContent = `(${vehicles.length})`;
        header.appendChild(count);
        
        // Add toggle all button
        const toggleAllBtn = document.createElement('button');
        toggleAllBtn.className = 'toggle-all-btn';
        toggleAllBtn.innerHTML = '<i class="fas fa-eye"></i>';
        toggleAllBtn.title = 'Toggle all vehicles of this type';
        toggleAllBtn.onclick = () => toggleAllVehicles(type, vehicles, onToggle);
        header.appendChild(toggleAllBtn);
        
        section.appendChild(header);
        
        // Create vehicle list
        const vehicleList = document.createElement('div');
        vehicleList.className = 'vehicle-list-items';
        
        // Sort vehicles by label or ID
        const sortedVehicles = [...vehicles].sort((a, b) => {
            const aLabel = a.label || a.id;
            const bLabel = b.label || b.id;
            return aLabel.localeCompare(bLabel);
        });
        
        // Add vehicles to the list
        sortedVehicles.forEach(vehicle => {
            const item = createVehicleListItem(vehicle, onToggle);
            vehicleList.appendChild(item);
        });
        
        section.appendChild(vehicleList);
        vehicleListContainer.appendChild(section);
        
    } catch (error) {
        logger.error(`Failed to create vehicle type section for ${type}:`, error);
    }
}

/**
 * Create a list item for a vehicle
 * @private
 */
function createVehicleListItem(vehicle, onToggle) {
    const item = document.createElement('div');
    item.className = 'vehicle-list-item';
    item.dataset.vehicleId = vehicle.id;
    
    // Create checkbox
    const checkbox = document.createElement('input');
    checkbox.type = 'checkbox';
    checkbox.id = `vehicle-${vehicle.id}`;
    checkbox.className = 'vehicle-checkbox';
    checkbox.checked = false;
    
    // Toggle vehicle visibility when checkbox changes
    checkbox.addEventListener('change', (e) => {
        onToggle(vehicle.id, e.target.checked);
    });
    
    // Create label
    const label = document.createElement('label');
    label.htmlFor = `vehicle-${vehicle.id}`;
    label.className = 'vehicle-label';
    
    // Add vehicle icon
    const icon = document.createElement('i');
    icon.className = `fas ${getVehicleIcon(vehicle.type)}`;
    
    // Add vehicle label or ID
    const name = document.createElement('span');
    name.className = 'vehicle-name';
    name.textContent = vehicle.label || `Vehicle ${vehicle.id}`;
    
    // Add route info if available
    let routeInfo = '';
    if (vehicle.routeId) {
        routeInfo = document.createElement('span');
        routeInfo.className = 'vehicle-route';
        routeInfo.textContent = vehicle.routeId;
    }
    
    // Assemble the label
    label.appendChild(icon);
    label.appendChild(name);
    if (routeInfo) {
        label.appendChild(routeInfo);
    }
    
    // Assemble the list item
    item.appendChild(checkbox);
    item.appendChild(label);
    
    return item;
}

/**
 * Toggle all vehicles of a specific type
 * @private
 */
function toggleAllVehicles(type, vehicles, onToggle) {
    try {
        // Check if any vehicle of this type is visible
        const anyVisible = vehicles.some(vehicle => {
            const checkbox = document.getElementById(`vehicle-${vehicle.id}`);
            return checkbox?.checked;
        });
        
        // Toggle all vehicles of this type
        vehicles.forEach(vehicle => {
            const checkbox = document.getElementById(`vehicle-${vehicle.id}`);
            if (checkbox) {
                const shouldBeVisible = !anyVisible;
                checkbox.checked = shouldBeVisible;
                onToggle(vehicle.id, shouldBeVisible);
            }
        });
        
    } catch (error) {
        logger.error(`Failed to toggle all ${type} vehicles:`, error);
    }
}

/**
 * Update the visual state of a vehicle in the list
 * @param {string} vehicleId - ID of the vehicle
 * @param {boolean} isActive - Whether the vehicle is active
 */
export function updateVehicleItemState(vehicleId, isActive) {
    const item = document.querySelector(`.vehicle-list-item[data-vehicle-id="${vehicleId}"]`);
    if (item) {
        const checkbox = item.querySelector('.vehicle-checkbox');
        if (checkbox) {
            checkbox.checked = isActive;
        }
        item.classList.toggle('active', isActive);
    }
}

/**
 * Get the icon for a vehicle type
 * @private
 */
function getVehicleIcon(type) {
    switch (type) {
        case VEHICLE_TYPES.METRO:
            return 'fa-train';
        case VEHICLE_TYPES.TRAM:
            return 'fa-train-tram';
        case VEHICLE_TYPES.BUS:
            return 'fa-bus';
        case VEHICLE_TYPES.NIGHTBUS:
            return 'fa-moon';
        default:
            return 'fa-car';
    }
}

/**
 * Show a loading indicator in the vehicle list
 * @param {boolean} isLoading - Whether to show the loading indicator
 */
export function setLoadingState(isLoading) {
    if (!vehicleListContainer) return;
    
    const loadingIndicator = vehicleListContainer.querySelector('.loading-indicator');
    
    if (isLoading) {
        if (!loadingIndicator) {
            const loader = document.createElement('div');
            loader.className = 'loading-indicator';
            loader.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Loading...';
            vehicleListContainer.appendChild(loader);
        }
    } else if (loadingIndicator) {
        loadingIndicator.remove();
    }
}

/**
 * Show an error message in the vehicle list
 * @param {string} message - The error message to display
 */
export function showError(message) {
    if (!vehicleListContainer) return;
    
    // Clear existing content
    vehicleListContainer.innerHTML = '';
    
    const errorDiv = document.createElement('div');
    errorDiv.className = 'alert alert-danger';
    errorDiv.innerHTML = `
        <i class="fas fa-exclamation-triangle"></i>
        ${message}
    `;
    
    vehicleListContainer.appendChild(errorDiv);
}
