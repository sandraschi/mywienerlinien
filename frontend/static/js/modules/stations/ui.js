/**
 * Stations UI components and interaction
 */

import { CONFIG } from '../../config.js';
import { ICONS } from '../../constants.js';
import { logger } from '../utils/logger.js';

// DOM elements
let stationSearchInput = null;
let stationListContainer = null;

/**
 * Initialize the stations UI
 * @param {Array} stations - Array of station objects
 * @param {Function} onToggle - Callback for when a station is toggled
 */
export function initStationUI(stations, onToggle) {
    try {
        logger.info('Initializing stations UI...');
        
        // Create or get the search container
        const searchContainer = document.getElementById('station-search-container') || createStationSearchContainer();
        
        // Get or create the search input
        stationSearchInput = document.getElementById('station-search');
        if (!stationSearchInput) {
            stationSearchInput = document.createElement('input');
            stationSearchInput.id = 'station-search';
            stationSearchInput.type = 'text';
            stationSearchInput.placeholder = 'Search stations...';
            stationSearchInput.className = 'station-search-input';
            searchContainer.appendChild(stationSearchInput);
        }
        
        // Create or get the station list container
        stationListContainer = document.getElementById('station-list') || createStationListContainer();
        
        // Set up search functionality
        setupStationSearch(stations, onToggle);
        
        // Initial population of station list
        updateStationList(stations, onToggle);
        
        logger.info('Stations UI initialized');
        
    } catch (error) {
        logger.error('Failed to initialize stations UI:', error);
        throw error;
    }
}

/**
 * Create the station search container
 * @private
 */
function createStationSearchContainer() {
    const container = document.createElement('div');
    container.id = 'station-search-container';
    container.className = 'station-search-container';
    
    // Add to the sidebar if it exists, otherwise add to body
    const sidebar = document.querySelector('.sidebar') || document.body;
    sidebar.insertBefore(container, sidebar.firstChild);
    
    return container;
}

/**
 * Create the station list container
 * @private
 */
function createStationListContainer() {
    const container = document.createElement('div');
    container.id = 'station-list';
    container.className = 'station-list';
    
    // Add to the sidebar if it exists, otherwise add after search container
    const sidebar = document.querySelector('.sidebar') || document.body;
    const searchContainer = document.getElementById('station-search-container');
    
    if (searchContainer && searchContainer.parentNode === sidebar) {
        sidebar.insertBefore(container, searchContainer.nextSibling);
    } else {
        sidebar.appendChild(container);
    }
    
    return container;
}

/**
 * Set up station search functionality
 * @private
 */
function setupStationSearch(stations, onToggle) {
    if (!stationSearchInput) return;
    
    let searchTimeout = null;
    
    stationSearchInput.addEventListener('input', (e) => {
        clearTimeout(searchTimeout);
        
        searchTimeout = setTimeout(() => {
            const query = e.target.value.trim().toLowerCase();
            
            if (query.length === 0) {
                updateStationList(stations, onToggle);
                return;
            }
            
            const filteredStations = stations.filter(station => 
                station.name.toLowerCase().includes(query) ||
                String(station.id).toLowerCase().includes(query) ||
                (station.lines && station.lines.some(line => 
                    line.toLowerCase().includes(query)
                ))
            );
            
            updateStationList(filteredStations, onToggle);
        }, 300);
    });
}

/**
 * Update the station list in the UI
 * @private
 */
function updateStationList(stations, onToggle) {
    if (!stationListContainer) return;
    
    // Clear existing content
    stationListContainer.innerHTML = '';
    
    if (stations.length === 0) {
        const noResults = document.createElement('div');
        noResults.className = 'no-results';
        noResults.textContent = 'No stations found';
        stationListContainer.appendChild(noResults);
        return;
    }
    
    // Create a list of stations
    const list = document.createElement('ul');
    list.className = 'station-list-items';
    
    stations.forEach(station => {
        const item = createStationListItem(station, onToggle);
        list.appendChild(item);
    });
    
    stationListContainer.appendChild(list);
}

/**
 * Create a list item for a station
 * @private
 */
function createStationListItem(station, onToggle) {
    const item = document.createElement('li');
    item.className = 'station-list-item';
    item.dataset.stationId = station.id;
    
    // Create checkbox
    const checkbox = document.createElement('input');
    checkbox.type = 'checkbox';
    checkbox.id = `station-${station.id}`;
    checkbox.className = 'station-checkbox';
    checkbox.checked = false;
    
    // Toggle station visibility when checkbox changes
    checkbox.addEventListener('change', (e) => {
        onToggle(station.id, e.target.checked);
    });
    
    // Create label
    const label = document.createElement('label');
    label.htmlFor = `station-${station.id}`;
    label.className = 'station-label';
    
    // Add station icon
    const icon = document.createElement('i');
    icon.className = `fas ${ICONS.STATION || 'fa-map-marker-alt'}`;
    
    // Add station name
    const name = document.createElement('span');
    name.className = 'station-name';
    name.textContent = station.name;
    
    // Add station lines if available
    let linesInfo = '';
    if (station.lines && station.lines.length > 0) {
        linesInfo = document.createElement('div');
        linesInfo.className = 'station-lines';
        
        station.lines.forEach(line => {
            const lineBadge = document.createElement('span');
            lineBadge.className = 'line-badge';
            lineBadge.textContent = line;
            linesInfo.appendChild(lineBadge);
        });
    }
    
    // Assemble the label
    label.appendChild(icon);
    label.appendChild(name);
    
    // Assemble the list item
    item.appendChild(checkbox);
    item.appendChild(label);
    if (linesInfo) {
        item.appendChild(linesInfo);
    }
    
    return item;
}

/**
 * Update the visual state of a station in the list
 * @param {string} stationId - ID of the station
 * @param {boolean} isActive - Whether the station is active
 */
export function updateStationItemState(stationId, isActive) {
    const item = document.querySelector(`.station-list-item[data-station-id="${stationId}"]`);
    if (item) {
        const checkbox = item.querySelector('.station-checkbox');
        if (checkbox) {
            checkbox.checked = isActive;
        }
        item.classList.toggle('active', isActive);
    }
}

/**
 * Show a station in the list (scroll to it and highlight)
 * @param {string} stationId - ID of the station to show
 */
export function highlightStationInList(stationId) {
    const item = document.querySelector(`.station-list-item[data-station-id="${stationId}"]`);
    if (item) {
        // Scroll to the item
        item.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        
        // Add highlight class
        item.classList.add('highlighted');
        
        // Remove highlight after delay
        setTimeout(() => {
            item.classList.remove('highlighted');
        }, 2000);
    }
}
