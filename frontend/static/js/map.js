/**
 * Wiener Linien Live Map - Frontend JavaScript
 * 
 * This file handles the interactive map functionality, real-time updates,
 * and WebSocket connections for live vehicle tracking and disruption alerts.
 */

// Global variables
let map;
let vehicleMarkers = new Map();
let routePolylines = new Map(); // Map<lineName, L.Polyline[]>
let lineStopMarkers = new Map(); // Map<lineName, L.Layer[]>
let disruptionAlerts = new Map();
let socket;
let selectedStopHighlight = null; // Highlight circle for selected stop
let currentCity = 'vienna'; // Default city
let cityConfig = null; // Current city configuration

// Line selection state
let lineData = [];
let lineRouteCache = new Map(); // Map<lineName, RouteData>
let selectedLines = new Set();
let activeLineType = 'all';
let routesVisible = true;
let stopsVisible = false;
let lineControlsInitialized = false;

const LINE_TYPE_INFO = {
    all: { label: 'All', icon: 'fa-solid fa-layer-group', color: '#3f51b5' },
    metro: { label: 'Metro', icon: 'fa-solid fa-train-subway', color: '#EE1C24' },
    tram: { label: 'Tram', icon: 'fa-solid fa-train-tram', color: '#FF6F00' },
    bus: { label: 'Bus', icon: 'fa-solid fa-bus', color: '#0066CC' },
    nightbus: { label: 'Night Bus', icon: 'fa-solid fa-moon', color: '#000066' },
    unknown: { label: 'Other', icon: 'fa-solid fa-question', color: '#757575' }
};

let currentFilters = {
    vehicleType: 'all'
};

function updateSocketFilters() {
    if (!socket || !socket.connected) {
        return;
    }

    const payload = {
        vehicle_type: currentFilters.vehicleType,
        lines: getSelectedLinesArray(),
    };

    socket.emit('update_filters', payload);
}

// WebSocket connection
function initializeWebSocket() {
    // Connect to WebSocket server
    socket = io({
        path: '/ws/socket.io'
    });
    
    // Connection events
    socket.on('connect', function() {
        console.log('Connected to WebSocket server');
        updateConnectionStatus('Connected', 'success');
        
        // Request initial data
        socket.emit('request_updates', { type: 'all' });
        updateSocketFilters();
    });
    
    socket.on('disconnect', function() {
        console.log('Disconnected from WebSocket server');
        updateConnectionStatus('Disconnected', 'error');
    });
    
    // Real-time updates
    socket.on('vehicle_updates', function(data) {
        console.log('Received vehicle updates:', data.vehicles.length);
        updateVehicleMarkers(data.vehicles);
    });
    
    socket.on('disruption_alert', function(alert) {
        console.log('Received disruption alert:', alert);
        handleDisruptionAlert(alert);
    });
    
    socket.on('disruption_alerts', function(data) {
        console.log('Received disruption alerts:', data.alerts.length);
        updateDisruptionAlerts(data.alerts);
    });
    
    socket.on('system_status', function(status) {
        console.log('Received system status:', status);
        updateSystemStatus(status);
    });
}

// Get city from URL parameter or localStorage
function getCityFromURL() {
    const params = new URLSearchParams(window.location.search);
    const cityParam = params.get('city');
    if (cityParam) {
        localStorage.setItem('selectedCity', cityParam);
        return cityParam;
    }
    // Fallback to localStorage
    return localStorage.getItem('selectedCity') || 'vienna';
}

// Load city configuration
async function loadCityConfig(cityKey) {
    try {
        const response = await fetch(`/api/cities/${encodeURIComponent(cityKey)}`);
        if (!response.ok) {
            console.warn(`City ${cityKey} not found, falling back to vienna`);
            return await loadCityConfig('vienna');
        }
        const data = await response.json();
        return data;
    } catch (error) {
        console.error('Error loading city config:', error);
        // Return default Vienna config
        return {
            key: 'vienna',
            name: 'Vienna',
            map_center: { lat: 48.2082, lng: 16.3738 },
            map_zoom: 13
        };
    }
}

// Initialize the map
async function initializeMap() {
    // Get city from URL or localStorage
    currentCity = getCityFromURL();
    
    // Load city configuration
    cityConfig = await loadCityConfig(currentCity);
    
    // Update page title
    document.title = `${cityConfig.name} Live Map`;
    const headerTitle = document.querySelector('.header h1');
    if (headerTitle) {
        headerTitle.textContent = `${cityConfig.name} Live Map`;
    }
    
    // Update city selector if it exists
    const citySelector = document.getElementById('city-selector');
    if (citySelector) {
        citySelector.value = currentCity;
    }
    
    // Get map center from city config or use defaults
    const mapCenter = cityConfig.map_center || { lat: 48.2082, lng: 16.3738 };
    const mapZoom = cityConfig.map_zoom || 13;
    
    // Create map centered on selected city
    map = L.map('map').setView([mapCenter.lat, mapCenter.lng], mapZoom);
    
    // Add OpenStreetMap tiles
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors'
    }).addTo(map);
    
    // Initialize WebSocket connection
    initializeWebSocket();
    
    // Load initial data
    loadInitialData();
    
    // Set up periodic refresh
    setInterval(refreshVehicleData, 60000); // Refresh every 60 seconds

    initializeArrivalsPanel();
    initializeFavoritesPanel();
    initializeTrafficAlerts();
}

// Switch to a different city
async function switchCity(cityKey) {
    // Update URL without reload
    const url = new URL(window.location.href);
    url.searchParams.set('city', cityKey);
    window.history.pushState({ city: cityKey }, '', url);
    
    // Update current city
    currentCity = cityKey;
    localStorage.setItem('selectedCity', cityKey);
    
    // Reload city config
    cityConfig = await loadCityConfig(cityKey);
    
    // Update page title
    document.title = `${cityConfig.name} Live Map`;
    const headerTitle = document.querySelector('.header h1');
    if (headerTitle) {
        headerTitle.textContent = `${cityConfig.name} Live Map`;
    }
    
    // Update city selector
    const citySelector = document.getElementById('city-selector');
    if (citySelector) {
        citySelector.value = cityKey;
    }
    
    // Update map center
    if (cityConfig.map_center && map) {
        const mapCenter = cityConfig.map_center;
        const mapZoom = cityConfig.map_zoom || 13;
        map.setView([mapCenter.lat, mapCenter.lng], mapZoom);
    }
    
    // Clear existing data
    vehicleMarkers.forEach((marker) => {
        if (map.hasLayer(marker)) {
            map.removeLayer(marker);
        }
    });
    vehicleMarkers.clear();
    
    routePolylines.forEach((polylines) => {
        polylines.forEach((polyline) => {
            if (map.hasLayer(polyline)) {
                map.removeLayer(polyline);
            }
        });
    });
    routePolylines.clear();
    
    lineStopMarkers.forEach((markers) => {
        markers.forEach((marker) => {
            if (map.hasLayer(marker)) {
                map.removeLayer(marker);
            }
        });
    });
    lineStopMarkers.clear();
    
    selectedLines.clear();
    lineRouteCache.clear();
    
    // Reload data for new city
    await loadInitialData();
}

// Load initial data
async function loadInitialData() {
    try {
        showLoading();
        await loadLines();
        await loadVehicleData();
        console.log('Initial data loaded successfully');
        hideLoading();
    } catch (error) {
        console.error('Error loading initial data:', error);
        showError('Failed to load initial data');
        hideLoading();
    }
}

// Load transport lines
async function loadLines() {
    try {
        const response = await fetch('/api/lines');
        if (!response.ok) {
            throw new Error(`Failed to fetch lines: ${response.status}`);
        }

        const data = await response.json();
        lineData = (data.lines || []).map((line) => ({
            ...line,
            normalizedType: normalizeLineType(line.type),
            color: line.color || getLineTypeColor(normalizeLineType(line.type))
        }));

        renderLineSelectionControls();
    } catch (error) {
        console.error('Error loading lines:', error);
        showError('Unable to load lines');
    }
}

function normalizeLineType(type) {
    if (!type) {
        return 'unknown';
    }

    const value = type.toString().trim().toLowerCase();
    if (value.startsWith('u')) {
        return 'metro';
    }
    if (value.includes('night')) {
        return 'nightbus';
    }
    if (value.includes('tram')) {
        return 'tram';
    }
    if (value.includes('bus')) {
        return 'bus';
    }
    return value || 'unknown';
}

function getLineTypeColor(type) {
    const info = LINE_TYPE_INFO[type] || LINE_TYPE_INFO.unknown;
    return info.color;
}

function getLineTypeLabel(type) {
    const info = LINE_TYPE_INFO[type];
    return info ? info.label : type.charAt(0).toUpperCase() + type.slice(1);
}

function renderLineSelectionControls() {
    renderLineTypeTabs();
    renderLineMatrix();
    updateSelectedLinesSummary();
    updateRoutesToggleButton();
    updateStopsToggleButton();

    if (!lineControlsInitialized) {
        const searchInput = document.getElementById('line-search');
        if (searchInput) {
            searchInput.addEventListener('input', onLineSearchInput);
        }

        const clearButton = document.getElementById('clear-selected-lines');
        if (clearButton) {
            clearButton.addEventListener('click', clearSelectedLines);
        }

        lineControlsInitialized = true;
    }
}

function renderLineTypeTabs() {
    const container = document.getElementById('line-type-tabs');
    if (!container) {
        return;
    }

    container.innerHTML = '';

    const types = new Set(['all']);
    lineData.forEach((line) => types.add(line.normalizedType));

    types.forEach((type) => {
        const button = document.createElement('button');
        button.type = 'button';
        button.className = `line-type-tab${type === activeLineType ? ' active' : ''}`;
        const info = LINE_TYPE_INFO[type] || LINE_TYPE_INFO.unknown;
        const iconClass = info.icon || 'fa-solid fa-train';
        button.innerHTML = `<i class="${iconClass}"></i> ${getLineTypeLabel(type)}`;
        button.dataset.type = type;
        button.addEventListener('click', () => setActiveLineType(type));
        container.appendChild(button);
    });
}

function renderLineMatrix() {
    const container = document.getElementById('line-checkbox-matrix');
    if (!container) {
        return;
    }

    const searchTerm = (document.getElementById('line-search')?.value || '').trim().toLowerCase();

    const filteredLines = lineData.filter((line) => {
        const matchesType = activeLineType === 'all' || line.normalizedType === activeLineType;
        const matchesSearch = !searchTerm || line.name.toLowerCase().includes(searchTerm) ||
            (line.description || '').toLowerCase().includes(searchTerm);
        return matchesType && matchesSearch;
    });

    container.innerHTML = '';

    if (filteredLines.length === 0) {
        const emptyState = document.createElement('div');
        emptyState.className = 'loading-message';
        emptyState.textContent = 'No lines match your filter';
        container.appendChild(emptyState);
        return;
    }

    filteredLines
        .sort((a, b) => a.name.localeCompare(b.name))
        .forEach((line) => {
            container.appendChild(createLineCheckbox(line));
        });
}

function createLineCheckbox(line) {
    const label = document.createElement('label');
    label.className = 'line-checkbox';
    label.style.borderColor = line.color;

    const input = document.createElement('input');
    input.type = 'checkbox';
    input.value = line.name;
    input.checked = selectedLines.has(line.name);
    input.addEventListener('change', async (event) => {
        await handleLineToggle(line, event.target.checked);
    });

    const colorDot = document.createElement('span');
    colorDot.className = 'legend-color';
    colorDot.style.backgroundColor = line.color;
    colorDot.style.borderColor = line.color;

    const text = document.createElement('span');
    text.textContent = line.name;

    label.appendChild(input);
    label.appendChild(colorDot);
    label.appendChild(text);

    return label;
}

async function handleLineToggle(line, isChecked) {
    if (isChecked) {
        selectedLines.add(line.name);
    } else {
        selectedLines.delete(line.name);
    }

    updateSelectedLinesSummary();
    updateSocketFilters();
    await renderSelectedRoutes();
    await loadVehicleData();
}

function onLineSearchInput() {
    renderLineMatrix();
}

function setActiveLineType(type) {
    if (type === activeLineType) {
        return;
    }
    activeLineType = type;
    renderLineTypeTabs();
    renderLineMatrix();
}

function updateSelectedLinesSummary() {
    const list = document.getElementById('selected-lines-list');
    const countElement = document.getElementById('selected-lines-count');

    if (countElement) {
        countElement.textContent = selectedLines.size.toString();
    }

    if (!list) {
        return;
    }

    list.innerHTML = '';

    if (selectedLines.size === 0) {
        const emptyItem = document.createElement('li');
        emptyItem.className = 'empty';
        emptyItem.textContent = 'No lines selected';
        list.appendChild(emptyItem);
        return;
    }

    Array.from(selectedLines)
        .sort()
        .forEach((lineName) => {
            const lineItem = document.createElement('li');
            lineItem.className = 'line-chip';
            const lineInfo = lineData.find((line) => line.name === lineName);
            lineItem.style.backgroundColor = `${(lineInfo?.color || '#3f51b5')}22`;
            lineItem.style.color = lineInfo?.color || '#3f51b5';
            lineItem.innerHTML = `
                <span>${lineName}</span>
                <button type="button" aria-label="Remove ${lineName}">×</button>
            `;
            lineItem.querySelector('button').addEventListener('click', async () => {
                selectedLines.delete(lineName);
                renderLineMatrix();
                updateSelectedLinesSummary();
                await renderSelectedRoutes();
                await loadVehicleData();
            });
            list.appendChild(lineItem);
        });
}

async function clearSelectedLines() {
    if (selectedLines.size === 0) {
        return;
    }
    selectedLines.clear();
    renderLineMatrix();
    updateSelectedLinesSummary();
    updateSocketFilters();
    await renderSelectedRoutes();
    await loadVehicleData();
}

function getSelectedLinesArray() {
    return Array.from(selectedLines);
}

async function renderSelectedRoutes() {
    const selected = getSelectedLinesArray();

    // Remove routes that are no longer selected
    routePolylines.forEach((polylines, lineName) => {
        if (!selectedLines.has(lineName)) {
            polylines.forEach((polyline) => {
                if (map.hasLayer(polyline)) {
                    map.removeLayer(polyline);
                }
            });
            routePolylines.delete(lineName);
        }
    });

    lineStopMarkers.forEach((markers, lineName) => {
        if (!selectedLines.has(lineName)) {
            markers.forEach((marker) => {
                if (map.hasLayer(marker)) {
                    map.removeLayer(marker);
                }
            });
            lineStopMarkers.delete(lineName);
        }
    });

    if (selected.length === 0) {
        updateRoutesToggleButton();
        updateStopsToggleButton();
        return;
    }

    const fetchPromises = selected.map(async (lineName) => {
        if (!lineRouteCache.has(lineName)) {
            try {
                const routeData = await fetchLineRoute(lineName);
                lineRouteCache.set(lineName, routeData);
            } catch (error) {
                console.error(`Failed to fetch route for ${lineName}:`, error);
            }
        }
    });

    await Promise.all(fetchPromises);

    const aggregateBounds = L.latLngBounds([]);

    selected.forEach((lineName) => {
        const route = lineRouteCache.get(lineName);
        if (!route) {
            return;
        }
        drawRoute(route);

        const routeBounds = getRouteBounds(route);
        if (routeBounds) {
            aggregateBounds.extend(routeBounds);
        }
    });

    if (aggregateBounds.isValid()) {
        map.fitBounds(aggregateBounds.pad(0.1));
    }

    updateRoutesToggleButton();
    updateStopsToggleButton();
}

async function fetchLineRoute(lineName) {
    const response = await fetch(`/api/lines/${encodeURIComponent(lineName)}/route`);
    if (!response.ok) {
        throw new Error(`Failed to load route for ${lineName}`);
    }

    const payload = await response.json();
    return payload.route || payload;
}

function drawRoute(routeData) {
    const lineName = routeData.line || routeData.name || routeData.route_short_name;
    if (!lineName) {
        return;
    }

    const color = routeData.color || getLineTypeColor(normalizeLineType(routeData.type));
    const existingPolylines = routePolylines.get(lineName);
    if (existingPolylines) {
        existingPolylines.forEach((polyline) => {
            if (map.hasLayer(polyline)) {
                map.removeLayer(polyline);
            }
        });
    }
    const polylines = [];
    const segments = Array.isArray(routeData.segments) && routeData.segments.length > 0
        ? routeData.segments
        : [{ coordinates: routeData.coordinates }];

    segments.forEach((segment) => {
        if (!Array.isArray(segment.coordinates) || segment.coordinates.length === 0) {
            return;
        }

        const latLngs = segment.coordinates.map(([lat, lng]) => [lat, lng]);
        const polyline = L.polyline(latLngs, {
            color,
            weight: 4,
            opacity: 0.8
        });

        if (routesVisible && !map.hasLayer(polyline)) {
            polyline.addTo(map);
        }

        polylines.push(polyline);
    });

    if (polylines.length > 0) {
        routePolylines.set(lineName, polylines);
    }

    if (Array.isArray(routeData.stops) && routeData.stops.length > 0) {
        const existingMarkers = lineStopMarkers.get(lineName);
        if (existingMarkers) {
            existingMarkers.forEach((marker) => {
                if (map.hasLayer(marker)) {
                    map.removeLayer(marker);
                }
            });
        }

        const markers = routeData.stops.map((stop) => {
            const marker = L.circleMarker([stop.lat, stop.lng], {
                radius: 6,
                fillColor: color,
                color: '#fff',
                weight: 2,
                opacity: 1,
                fillOpacity: 0.9
            });

            const popup = `
                <div class="stop-popup">
                    <h4>${stop.name || 'Unknown stop'}</h4>
                    <p><strong>Line:</strong> ${lineName}</p>
                    ${stop.rbl ? `<p><strong>RBL:</strong> ${stop.rbl}</p>` : ''}
                    ${typeof stop.sequence === 'number' ? `<p><strong>Sequence:</strong> ${stop.sequence}</p>` : ''}
                </div>
            `;
            marker.bindPopup(popup);

            marker.on('click', () => {
                if (stop.rbl) {
                    highlightStopOnMap(stop, marker);
                    fetchArrivalsForStop(stop);
                }
            });

            if (stopsVisible && !map.hasLayer(marker)) {
                marker.addTo(map);
            }

            return marker;
        });

        lineStopMarkers.set(lineName, markers);
    } else {
        lineStopMarkers.delete(lineName);
    }
}

let currentArrivalsFilter = 'all';
let currentArrivalsData = [];
let currentSelectedStop = null; // Track currently selected stop for favorites
let arrivalsRefreshInterval = null; // Auto-refresh interval for arrivals
const ARRIVALS_REFRESH_MS = 30000; // Refresh arrivals every 30 seconds

function highlightStopOnMap(stop, marker) {
    // Remove existing highlight if any
    if (selectedStopHighlight) {
        map.removeLayer(selectedStopHighlight);
        selectedStopHighlight = null;
    }
    
    // Create pulsing circle highlight
    if (stop.lat && stop.lng) {
        selectedStopHighlight = L.circle([stop.lat, stop.lng], {
            radius: 100, // 100 meters
            color: '#007bff',
            fillColor: '#007bff',
            fillOpacity: 0.2,
            weight: 3,
            opacity: 0.8,
            className: 'stop-highlight'
        }).addTo(map);
        
        // Zoom to stop if needed (but don't zoom too close)
        const currentZoom = map.getZoom();
        if (currentZoom < 15) {
            map.setView([stop.lat, stop.lng], Math.max(currentZoom, 15));
        } else {
            map.setView([stop.lat, stop.lng], currentZoom);
        }
    }
}

async function fetchArrivalsForStop(stop, isAutoRefresh = false) {
    try {
        currentSelectedStop = stop; // Store for favorites
        
        // Start auto-refresh interval (only on initial fetch, not auto-refresh)
        if (!isAutoRefresh) {
            startArrivalsAutoRefresh(stop);
        }
        
        const listEl = document.getElementById('arrivals-list');
        const nameEl = document.getElementById('arrivals-stop-name');
        const metaEl = document.getElementById('arrivals-stop-meta');
        const filtersEl = document.getElementById('arrivals-filters');
        const loadingEl = document.getElementById('arrivals-loading');
        
        if (nameEl && !isAutoRefresh) {
            if (stop.rbl) {
                const isFavorite = checkIfStopIsFavorite(stop.rbl);
                nameEl.innerHTML = `${stop.name || 'Selected stop'} <button class="favorite-btn" data-rbl="${stop.rbl}" title="${isFavorite ? 'Remove from favorites' : 'Add to favorites'}">${isFavorite ? '★' : '☆'}</button>`;
                const favBtn = nameEl.querySelector('.favorite-btn');
                if (favBtn) {
                    favBtn.addEventListener('click', (e) => {
                        e.stopPropagation();
                        toggleStopFavorite(stop);
                    });
                }
            } else {
                nameEl.textContent = stop.name || 'Selected stop';
            }
        }
        if (metaEl && !isAutoRefresh) {
            metaEl.textContent = stop.rbl ? `RBL: ${stop.rbl}` : '';
        }
        
        // Highlight the stop on map (only on initial fetch)
        if (!isAutoRefresh && stop.lat && stop.lng) {
            highlightStopOnMap(stop, null);
        }
        if (filtersEl && !isAutoRefresh) {
            filtersEl.style.display = 'flex';
        }
        // Show loading only on initial fetch, not auto-refresh (to avoid flicker)
        if (loadingEl && !isAutoRefresh) {
            loadingEl.style.display = 'flex';
        }
        if (listEl && !isAutoRefresh) {
            listEl.innerHTML = '';
        }
        
        const url = `/api/arrivals?rbl=${encodeURIComponent(stop.rbl)}`;
        const resp = await fetch(url);
        if (!resp.ok) {
            throw new Error(`Arrivals failed: ${resp.status}`);
        }
        const data = await resp.json();
        currentArrivalsData = data.vehicles || [];
        
        if (loadingEl) {
            loadingEl.style.display = 'none';
        }
        renderArrivalsList(listEl, currentArrivalsData);
        
        // Update last refresh indicator
        if (metaEl && stop.rbl) {
            const now = new Date();
            metaEl.textContent = `RBL: ${stop.rbl} • Updated ${now.toLocaleTimeString()}`;
        }
    } catch (err) {
        console.error('Error fetching arrivals', err);
        const listEl = document.getElementById('arrivals-list');
        const loadingEl = document.getElementById('arrivals-loading');
        if (loadingEl) {
            loadingEl.style.display = 'none';
        }
        if (listEl && !isAutoRefresh) {
            listEl.innerHTML = '<li class="empty">Failed to load arrivals.</li>';
        }
    }
}

function startArrivalsAutoRefresh(stop) {
    // Clear any existing interval
    stopArrivalsAutoRefresh();
    
    // Start new interval
    arrivalsRefreshInterval = setInterval(() => {
        if (currentSelectedStop && currentSelectedStop.rbl === stop.rbl) {
            console.log('Auto-refreshing arrivals for', stop.name);
            fetchArrivalsForStop(stop, true);
        } else {
            // Stop refresh if stop changed
            stopArrivalsAutoRefresh();
        }
    }, ARRIVALS_REFRESH_MS);
    
    console.log(`Started arrivals auto-refresh (${ARRIVALS_REFRESH_MS / 1000}s interval)`);
}

function stopArrivalsAutoRefresh() {
    if (arrivalsRefreshInterval) {
        clearInterval(arrivalsRefreshInterval);
        arrivalsRefreshInterval = null;
        console.log('Stopped arrivals auto-refresh');
    }
}

function isNightRoute(line) {
    if (!line) return false;
    const lineUpper = line.toUpperCase();
    return lineUpper.includes('N') || lineUpper.startsWith('N') || 
           (lineUpper.match(/^\d+$/) && parseInt(lineUpper) >= 20 && parseInt(lineUpper) <= 99);
}

function filterArrivals(vehicles, filter) {
    if (filter === 'all') return vehicles;
    if (filter === 'day') {
        return vehicles.filter(v => !isNightRoute(v.line));
    }
    if (filter === 'night') {
        return vehicles.filter(v => isNightRoute(v.line));
    }
    return vehicles;
}

function getLineTypeClass(line) {
    if (!line) return '';
    const lineUpper = line.toUpperCase();
    if (lineUpper.startsWith('U')) return 'metro';
    if (lineUpper.match(/^[A-Z]$/) || lineUpper.match(/^\d{1,2}$/)) {
        const num = parseInt(lineUpper);
        if (num >= 20 && num <= 99) return 'nightbus';
        return 'tram';
    }
    if (isNightRoute(line)) return 'nightbus';
    if (lineUpper.match(/^\d{3,}$/)) return 'bus';
    return '';
}

function renderArrivalsList(listEl, vehicles) {
    if (!listEl) return;
    
    // Apply current filter
    const filtered = filterArrivals(vehicles, currentArrivalsFilter);
    
    listEl.innerHTML = '';
    if (!filtered.length) {
        const message = currentArrivalsFilter === 'all' 
            ? 'No upcoming departures.' 
            : `No ${currentArrivalsFilter} departures.`;
        listEl.innerHTML = `<li class="empty">${message}</li>`;
        return;
    }
    
    const sorted = filtered.slice().sort((a, b) => (a.countdown ?? 0) - (b.countdown ?? 0));
    sorted.slice(0, 20).forEach((v) => {
        const li = document.createElement('li');
        const countdown = Number.isFinite(v.countdown) ? v.countdown : null;
        const countdownText = countdown !== null ? `${countdown} min` : 'soon';
        const delay = v.delay ? `${v.delay} min` : '';
        const lineTypeClass = getLineTypeClass(v.line);
        const countdownClass = countdown !== null && countdown < 3 ? 'soon' : 
                              (v.delay && v.delay > 2 ? 'delayed' : '');
        
        li.innerHTML = `
            <div class="arrival-item">
                <span class="arrival-line ${lineTypeClass}">${v.line || ''}</span>
                <div class="arrival-info">
                    <div>
                        <span class="arrival-countdown ${countdownClass}">${countdownText}</span>
                        ${delay ? `<span class="arrival-delay">+${delay}</span>` : ''}
                    </div>
                    <div class="arrival-destination">${v.next_station || 'Unknown destination'}</div>
                </div>
            </div>
        `;
        listEl.appendChild(li);
    });
}

function setupArrivalsFilters() {
    const filterButtons = document.querySelectorAll('.arrivals-filter-btn');
    filterButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            // Update active state
            filterButtons.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            
            // Update filter
            currentArrivalsFilter = btn.dataset.filter || 'all';
            
            // Re-render with new filter
            const listEl = document.getElementById('arrivals-list');
            if (listEl && currentArrivalsData.length > 0) {
                renderArrivalsList(listEl, currentArrivalsData);
            }
        });
    });
}

function updateRoutesToggleButton() {
    const button = document.getElementById('toggle-routes');
    if (!button) {
        return;
    }
    const hasRoutes = routePolylines.size > 0;
    button.disabled = !hasRoutes;
    button.textContent = routesVisible ? 'Hide Routes' : 'Show Routes';
}

function updateStopsToggleButton() {
    const button = document.getElementById('toggle-stops');
    if (!button) {
        return;
    }
    const hasStops = lineStopMarkers.size > 0;
    button.disabled = !hasStops;
    button.textContent = stopsVisible ? 'Hide Stops' : 'Show Stops';
}

function getRouteBounds(routeData) {
    const bounds = L.latLngBounds([]);

    const segments = Array.isArray(routeData.segments) && routeData.segments.length > 0
        ? routeData.segments
        : [];

    segments.forEach((segment) => {
        if (!Array.isArray(segment.coordinates)) {
            return;
        }
        segment.coordinates.forEach(([lat, lng]) => {
            if (typeof lat === 'number' && typeof lng === 'number') {
                bounds.extend([lat, lng]);
            }
        });
    });

    if (Array.isArray(routeData.stops)) {
        routeData.stops.forEach((stop) => {
            if (typeof stop?.lat === 'number' && typeof stop?.lng === 'number') {
                bounds.extend([stop.lat, stop.lng]);
            }
        });
    }

    return bounds.isValid() ? bounds : null;
}

// Favorites management functions
function checkIfStopIsFavorite(rbl) {
    try {
        const favorites = JSON.parse(localStorage.getItem('favorites') || '{}');
        return !!(favorites.stops && favorites.stops[rbl]);
    } catch (e) {
        return false;
    }
}

function toggleStopFavorite(stop) {
    try {
        const favorites = JSON.parse(localStorage.getItem('favorites') || '{}');
        if (!favorites.stops) favorites.stops = {};
        
        if (favorites.stops[stop.rbl]) {
            delete favorites.stops[stop.rbl];
        } else {
            favorites.stops[stop.rbl] = {
                id: stop.rbl,
                name: stop.name,
                lat: stop.lat,
                lng: stop.lng,
                timestamp: Date.now()
            };
        }
        
        localStorage.setItem('favorites', JSON.stringify(favorites));
        renderFavoritesList();
        
        // Update favorite button in arrivals panel
        if (currentSelectedStop && currentSelectedStop.rbl === stop.rbl) {
            const nameEl = document.getElementById('arrivals-stop-name');
            if (nameEl) {
                const isFavorite = checkIfStopIsFavorite(stop.rbl);
                nameEl.innerHTML = `${stop.name || 'Selected stop'} <button class="favorite-btn" data-rbl="${stop.rbl}" title="${isFavorite ? 'Remove from favorites' : 'Add to favorites'}">${isFavorite ? '★' : '☆'}</button>`;
                const favBtn = nameEl.querySelector('.favorite-btn');
                if (favBtn) {
                    favBtn.addEventListener('click', (e) => {
                        e.stopPropagation();
                        toggleStopFavorite(stop);
                    });
                }
            }
        }
    } catch (e) {
        console.error('Failed to toggle favorite:', e);
    }
}

function renderFavoritesList() {
    const listEl = document.getElementById('favorites-list');
    if (!listEl) return;
    
    try {
        const favorites = JSON.parse(localStorage.getItem('favorites') || '{}');
        const stops = favorites.stops || {};
        const home = favorites.home || null;
        const work = favorites.work || null;
        
        listEl.innerHTML = '';
        
        if (Object.keys(stops).length === 0 && !home && !work) {
            listEl.innerHTML = '<li class="empty">No favorites yet. Click a stop and use the star icon to add.</li>';
            return;
        }
        
        // Add home/work if set
        if (home) {
            const li = document.createElement('li');
            li.className = 'favorite-item home';
            li.innerHTML = `
                <span class="favorite-icon">🏠</span>
                <span class="favorite-name">${home.name || 'Home'}</span>
                <button class="favorite-remove" data-rbl="${home.rbl}" title="Remove">×</button>
            `;
            li.querySelector('.favorite-remove').addEventListener('click', () => {
                if (confirm('Remove Home favorite?')) {
                    favorites.home = null;
                    localStorage.setItem('favorites', JSON.stringify(favorites));
                    renderFavoritesList();
                }
            });
            li.addEventListener('click', () => {
                fetchArrivalsForStop(home);
            });
            listEl.appendChild(li);
        }
        
        if (work) {
            const li = document.createElement('li');
            li.className = 'favorite-item work';
            li.innerHTML = `
                <span class="favorite-icon">💼</span>
                <span class="favorite-name">${work.name || 'Work'}</span>
                <button class="favorite-remove" data-rbl="${work.rbl}" title="Remove">×</button>
            `;
            li.querySelector('.favorite-remove').addEventListener('click', () => {
                if (confirm('Remove Work favorite?')) {
                    favorites.work = null;
                    localStorage.setItem('favorites', JSON.stringify(favorites));
                    renderFavoritesList();
                }
            });
            li.addEventListener('click', () => {
                fetchArrivalsForStop(work);
            });
            listEl.appendChild(li);
        }
        
        // Add regular favorites
        Object.values(stops).forEach(stop => {
            if (stop.rbl === (home?.rbl) || stop.rbl === (work?.rbl)) return; // Skip if already shown as home/work
            
            const li = document.createElement('li');
            li.className = 'favorite-item';
            li.innerHTML = `
                <span class="favorite-icon">★</span>
                <span class="favorite-name">${stop.name || `Stop ${stop.rbl}`}</span>
                <button class="favorite-remove" data-rbl="${stop.rbl}" title="Remove">×</button>
            `;
            li.querySelector('.favorite-remove').addEventListener('click', (e) => {
                e.stopPropagation();
                toggleStopFavorite(stop);
            });
            li.addEventListener('click', () => {
                fetchArrivalsForStop(stop);
            });
            listEl.appendChild(li);
        });
    } catch (e) {
        console.error('Failed to render favorites:', e);
        listEl.innerHTML = '<li class="empty">Error loading favorites.</li>';
    }
}

function initializeTrafficAlerts() {
    const alertsList = document.getElementById('traffic-alerts-list');
    const loadingEl = document.getElementById('traffic-alerts-loading');
    
    async function loadTrafficAlerts() {
        if (loadingEl) loadingEl.style.display = 'flex';
        if (alertsList) alertsList.innerHTML = '';
        
        try {
            const resp = await fetch('/api/traffic-info');
            if (!resp.ok) throw new Error(resp.status);
            const data = await resp.json();
            
            if (loadingEl) loadingEl.style.display = 'none';
            
            if (!alertsList) return;
            
            if (!data.alerts || data.alerts.length === 0) {
                alertsList.innerHTML = '<li class="empty">No service alerts at this time.</li>';
                return;
            }
            
            alertsList.innerHTML = '';
            data.alerts.forEach(alert => {
                const li = document.createElement('li');
                li.className = `traffic-alert-item severity-${alert.severity || 'low'}`;
                
                const linesHtml = alert.lines && alert.lines.length > 0
                    ? `<div class="traffic-alert-lines">${alert.lines.map(line => `<span class="traffic-alert-line">${line}</span>`).join('')}</div>`
                    : '';
                
                li.innerHTML = `
                    <div class="traffic-alert-title">${alert.title || 'Service Alert'}</div>
                    <div class="traffic-alert-description">${alert.description || ''}</div>
                    ${linesHtml}
                `;
                alertsList.appendChild(li);
            });
        } catch (err) {
            console.error('Failed to load traffic alerts:', err);
            if (loadingEl) loadingEl.style.display = 'none';
            if (alertsList) {
                alertsList.innerHTML = '<li class="empty">Unable to load service alerts.</li>';
            }
        }
    }
    
    // Load alerts on init and refresh every 5 minutes
    loadTrafficAlerts();
    setInterval(loadTrafficAlerts, 5 * 60 * 1000);
}

function initializeFavoritesPanel() {
    const homeBtn = document.getElementById('favorite-home');
    const workBtn = document.getElementById('favorite-work');
    
    if (homeBtn) {
        homeBtn.addEventListener('click', () => {
            if (currentSelectedStop && currentSelectedStop.rbl) {
                const favorites = JSON.parse(localStorage.getItem('favorites') || '{}');
                favorites.home = {
                    id: currentSelectedStop.rbl,
                    name: currentSelectedStop.name,
                    lat: currentSelectedStop.lat,
                    lng: currentSelectedStop.lng,
                    rbl: currentSelectedStop.rbl,
                    timestamp: Date.now()
                };
                localStorage.setItem('favorites', JSON.stringify(favorites));
                renderFavoritesList();
                alert('Home location set!');
            } else {
                alert('Please select a stop first by clicking on the map.');
            }
        });
    }
    
    if (workBtn) {
        workBtn.addEventListener('click', () => {
            if (currentSelectedStop && currentSelectedStop.rbl) {
                const favorites = JSON.parse(localStorage.getItem('favorites') || '{}');
                favorites.work = {
                    id: currentSelectedStop.rbl,
                    name: currentSelectedStop.name,
                    lat: currentSelectedStop.lat,
                    lng: currentSelectedStop.lng,
                    rbl: currentSelectedStop.rbl,
                    timestamp: Date.now()
                };
                localStorage.setItem('favorites', JSON.stringify(favorites));
                renderFavoritesList();
                alert('Work location set!');
            } else {
                alert('Please select a stop first by clicking on the map.');
            }
        });
    }
    
    renderFavoritesList();
}

function initializeArrivalsPanel() {
    const clearBtn = document.getElementById('arrivals-clear');
    if (clearBtn) {
        clearBtn.addEventListener('click', () => {
            const listEl = document.getElementById('arrivals-list');
            const nameEl = document.getElementById('arrivals-stop-name');
            const metaEl = document.getElementById('arrivals-stop-meta');
            const filtersEl = document.getElementById('arrivals-filters');
            if (listEl) {
                listEl.innerHTML = '<li class="empty">Click a stop marker or use "Near Me" to see arrivals.</li>';
            }
            if (nameEl) nameEl.textContent = 'No stop selected';
            if (metaEl) metaEl.textContent = '';
            if (filtersEl) filtersEl.style.display = 'none';
            currentArrivalsData = [];
            currentArrivalsFilter = 'all';
            currentSelectedStop = null;
            
            // Stop auto-refresh
            stopArrivalsAutoRefresh();
            
            // Remove stop highlight
            if (selectedStopHighlight) {
                map.removeLayer(selectedStopHighlight);
                selectedStopHighlight = null;
            }
            // Reset filter buttons
            document.querySelectorAll('.arrivals-filter-btn').forEach(btn => {
                btn.classList.remove('active');
                if (btn.dataset.filter === 'all') btn.classList.add('active');
            });
        });
    }
    
    // Setup filter buttons
    setupArrivalsFilters();
    const nearMeBtn = document.getElementById('near-me-button');
    if (nearMeBtn && navigator.geolocation) {
        nearMeBtn.addEventListener('click', () => {
            navigator.geolocation.getCurrentPosition(
                async (pos) => {
                    const { latitude, longitude } = pos.coords;
                    try {
                        const resp = await fetch(`/api/stops/nearby?lat=${latitude}&lon=${longitude}&limit=1`);
                        if (!resp.ok) throw new Error(resp.status);
                        const data = await resp.json();
                        const first = (data.stops || [])[0];
                        if (first && first.lat && first.lng) {
                            map.setView([first.lat, first.lng], 16);
                            await fetchArrivalsForStop(first);
                        }
                    } catch (err) {
                        console.error('Near me failed', err);
                    }
                },
                (err) => {
                    console.warn('Geolocation denied', err);
                }
            );
        });
    }
}

// Load vehicle data
async function loadVehicleData() {
    try {
        showLoading(); // Show loading during vehicle data refresh
        
        const params = new URLSearchParams();
        if (currentFilters.vehicleType !== 'all') {
            params.append('type', currentFilters.vehicleType);
        }
        const lines = getSelectedLinesArray();
        if (lines.length === 1) {
            params.append('line', lines[0]);
        } else if (lines.length > 1) {
            params.append('lines', lines.join(','));
        }
        
        const response = await fetch(`/api/vehicles?${params}`);
        const data = await response.json();
        
        if (data.vehicles) {
            updateVehicleMarkers(data.vehicles);
        }
        
        hideLoading(); // Hide loading when done
    } catch (error) {
        console.error('Error loading vehicle data:', error);
        showError('Failed to load vehicle data');
        hideLoading(); // Hide loading on error
    }
}

// Refresh vehicle data
function refreshVehicleData() {
    loadVehicleData();
}

// Update vehicle markers on the map
function updateVehicleMarkers(vehicles) {
    const seenIds = new Set();

    vehicles.forEach((vehicle) => {
        if (!vehicle.lat || !vehicle.lng) {
            return;
        }
        seenIds.add(vehicle.id);
        let marker = vehicleMarkers.get(vehicle.id);
        if (!marker) {
            marker = createVehicleMarker(vehicle);
            vehicleMarkers.set(vehicle.id, marker);
            marker.addTo(map);
        } else {
            marker.setLatLng([vehicle.lat, vehicle.lng]);
        }
        marker.setPopupContent(buildVehiclePopup(vehicle));
    });

    vehicleMarkers.forEach((marker, id) => {
        if (!seenIds.has(id)) {
            map.removeLayer(marker);
            vehicleMarkers.delete(id);
        }
    });

    updateVehicleCount(vehicleMarkers.size);
}

// Create a vehicle marker
function createVehicleMarker(vehicle) {
    const icon = getVehicleIcon(vehicle.type, vehicle.line);
    const marker = L.marker([vehicle.lat, vehicle.lng], { icon });
    marker.bindPopup(buildVehiclePopup(vehicle));
    return marker;
}

function buildVehiclePopup(vehicle) {
    return `
        <div class="vehicle-popup">
            <h4>${vehicle.line}</h4>
            <p><strong>Type:</strong> ${vehicle.type}</p>
            <p><strong>Direction:</strong> ${vehicle.direction}</p>
            <p><strong>Next Station:</strong> ${vehicle.next_station}</p>
            <p><strong>Delay:</strong> ${vehicle.delay} min</p>
            <p><strong>Updated:</strong> ${new Date(vehicle.timestamp).toLocaleTimeString()}</p>
        </div>
    `;
}

// Get vehicle icon based on type and line
function getVehicleIcon(type, line) {
    const iconSize = [32, 32];
    const iconAnchor = [16, 16];
    
    let iconUrl;
    let color;
    
    switch (type.toLowerCase()) {
        case 'metro':
            color = '#FF0000';
            break;
        case 'tram':
            color = '#FF6600';
            break;
        case 'bus':
            color = '#0066CC';
            break;
        case 'nightbus':
        case 'night_bus':
            color = '#000066';
            break;
        default:
            color = '#999999';
    }
    
    // Create custom icon with line number
    return L.divIcon({
        className: 'vehicle-marker',
        html: `<div style="background-color: ${color}; color: white; border-radius: 50%; width: 32px; height: 32px; display: flex; align-items: center; justify-content: center; font-size: 14px; font-weight: bold;">${line}</div>`,
        iconSize: iconSize,
        iconAnchor: iconAnchor
    });
}


// Handle disruption alerts
function handleDisruptionAlert(alert) {
    // Store the alert
    disruptionAlerts.set(alert.id, alert);
    
    // Show notification
    showDisruptionNotification(alert);
    
    // Update disruption display
    updateDisruptionDisplay();
}

// Update disruption alerts
function updateDisruptionAlerts(alerts) {
    disruptionAlerts.clear();
    alerts.forEach(alert => {
        disruptionAlerts.set(alert.id, alert);
    });
    updateDisruptionDisplay();
}

// Show disruption notification
function showDisruptionNotification(alert) {
    const notification = document.createElement('div');
    notification.className = `disruption-notification ${alert.severity}`;
    notification.innerHTML = `
        <div class="notification-header">
            <h4>${alert.title}</h4>
            <button onclick="this.parentElement.parentElement.remove()">×</button>
        </div>
        <div class="notification-content">
            <p><strong>Line:</strong> ${alert.line}</p>
            <p><strong>Type:</strong> ${alert.type}</p>
            <p>${alert.description}</p>
        </div>
    `;
    
    document.body.appendChild(notification);
    
    // Auto-remove after 10 seconds
    setTimeout(() => {
        if (notification.parentElement) {
            notification.remove();
        }
    }, 10000);
}

// Update disruption display
function updateDisruptionDisplay() {
    const container = document.getElementById('disruption-container');
    if (!container) return;
    
    container.innerHTML = '';
    
    if (disruptionAlerts.size === 0) {
        container.innerHTML = '<p>No active disruptions</p>';
        return;
    }
    
    disruptionAlerts.forEach(alert => {
        const alertElement = document.createElement('div');
        alertElement.className = `disruption-item ${alert.severity}`;
        alertElement.innerHTML = `
            <h4>${alert.title}</h4>
            <p><strong>Line:</strong> ${alert.line}</p>
            <p><strong>Type:</strong> ${alert.type}</p>
            <p>${alert.description}</p>
            <small>Started: ${new Date(alert.start_time).toLocaleString()}</small>
        `;
        container.appendChild(alertElement);
    });
}

// Update system status
function updateSystemStatus(status) {
    const statusElement = document.getElementById('system-status');
    if (statusElement) {
        const vehicleUpdatedAt = status.vehicle_updated_at || status.timestamp;
        statusElement.innerHTML = `
            <div class="status-item">
                <span class="label">Connected Clients:</span>
                <span class="value">${status.websocket_clients ?? 0}</span>
            </div>
            <div class="status-item">
                <span class="label">Active Disruptions:</span>
                <span class="value">${status.active_disruptions ?? 0}</span>
            </div>
            <div class="status-item">
                <span class="label">Tracked Vehicles:</span>
                <span class="value">${status.vehicle_count ?? 0}</span>
            </div>
            <div class="status-item">
                <span class="label">Last Updated:</span>
                <span class="value">${vehicleUpdatedAt ? new Date(vehicleUpdatedAt).toLocaleTimeString() : '—'}</span>
            </div>
        `;
    }
}

// Update connection status
function updateConnectionStatus(status, type) {
    const statusElement = document.getElementById('connection-status');
    if (statusElement) {
        statusElement.textContent = status;
        statusElement.className = `connection-status ${type}`;
    }
}

// Update vehicle count
function updateVehicleCount(count) {
    const countElement = document.getElementById('vehicle-count');
    if (countElement) {
        countElement.textContent = count;
    }
}

// Filter change handlers
function onVehicleTypeChange() {
    const select = document.getElementById('vehicle-type-select');
    currentFilters.vehicleType = select.value;
    updateSocketFilters();
    loadVehicleData();
}

// Toggle route display
function toggleRoutes() {
    routesVisible = !routesVisible;

    routePolylines.forEach((polylines) => {
        polylines.forEach((polyline) => {
            if (routesVisible) {
                polyline.addTo(map);
            } else {
                if (map.hasLayer(polyline)) {
                    map.removeLayer(polyline);
                }
            }
        });
    });

    updateRoutesToggleButton();
}

// Toggle stop markers
function toggleStops() {
    stopsVisible = !stopsVisible;

    lineStopMarkers.forEach((markers) => {
        markers.forEach((marker) => {
            if (stopsVisible) {
                marker.addTo(map);
            } else {
                if (map.hasLayer(marker)) {
                    map.removeLayer(marker);
                }
            }
        });
    });

    updateStopsToggleButton();
}

// Show loading overlay
function showLoading() {
    const loader = document.getElementById('map-loader');
    if (loader) {
        loader.classList.add('visible');
    }
}

// Hide loading overlay
function hideLoading() {
    const loader = document.getElementById('map-loader');
    if (loader) {
        loader.classList.remove('visible');
    }
}

// Show error message
function showError(message) {
    const errorDiv = document.getElementById('error-message');
    if (errorDiv) {
        errorDiv.textContent = message;
        errorDiv.style.display = 'block';
        
        setTimeout(() => {
            errorDiv.style.display = 'none';
        }, 5000);
    }
    hideLoading(); // Hide loading when there's an error
}

// Show success message
function showSuccess(message) {
    const successDiv = document.getElementById('success-message');
    if (successDiv) {
        successDiv.textContent = message;
        successDiv.style.display = 'block';
        
        setTimeout(() => {
            successDiv.style.display = 'none';
        }, 3000);
    }
}

// Initialize city selector dropdown
async function initializeCitySelector() {
    const citySelector = document.getElementById('city-selector');
    if (!citySelector) {
        return;
    }
    
    try {
        const response = await fetch('/api/cities');
        if (!response.ok) {
            console.error('Failed to load cities');
            return;
        }
        const data = await response.json();
        const cities = data.cities || [];
        
        // Clear existing options
        citySelector.innerHTML = '';
        
        // Add cities to dropdown
        cities.forEach(city => {
            const option = document.createElement('option');
            option.value = city.key;
            option.textContent = city.name;
            if (city.key === currentCity) {
                option.selected = true;
            }
            citySelector.appendChild(option);
        });
        
        // Add change event listener
        citySelector.addEventListener('change', async (e) => {
            const selectedCity = e.target.value;
            if (selectedCity !== currentCity) {
                await switchCity(selectedCity);
            }
        });
    } catch (error) {
        console.error('Error initializing city selector:', error);
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', async function() {
    // Hide loading overlay by default
    hideLoading();
    
    const buildTimestamp = document.getElementById('build-timestamp');
    if (buildTimestamp) {
        const now = new Date();
        buildTimestamp.textContent = now.toLocaleString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
            hour12: false
        });
    }

    // Initialize city selector first
    await initializeCitySelector();
    
    // Then initialize map (which will use the selected city)
    await initializeMap();
    
    // Set up event listeners
    const vehicleTypeSelect = document.getElementById('vehicle-type-select');
    
    if (vehicleTypeSelect) {
        vehicleTypeSelect.addEventListener('change', onVehicleTypeChange);
    }
    
    // Handle browser back/forward buttons
    window.addEventListener('popstate', async (e) => {
        if (e.state && e.state.city) {
            await switchCity(e.state.city);
        } else {
            const cityFromURL = getCityFromURL();
            if (cityFromURL !== currentCity) {
                await switchCity(cityFromURL);
            }
        }
    });
    
    console.log('Live Map initialized');
});
