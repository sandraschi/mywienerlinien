/**
 * Journey Planning UI Module
 * Phase 3B Enhancement: Route comparison with real-time delays
 */

class JourneyPlannerUI {
    constructor() {
        this.currentRoutes = [];
        this.selectedRouteIndex = 0;
        this.init();
    }

    /**
     * Initialize journey planner UI
     */
    init() {
        this.setupEventListeners();
        console.log('[Journey] Planner UI initialized');
    }

    /**
     * Setup event listeners for journey planning
     */
    setupEventListeners() {
        // Journey planning form
        const planBtn = document.getElementById('plan-journey-btn');
        if (planBtn) {
            planBtn.addEventListener('click', () => this.planJourney());
        }

        // Enter key in inputs
        ['from-station-input', 'to-station-input'].forEach(id => {
            const input = document.getElementById(id);
            if (input) {
                input.addEventListener('keypress', (e) => {
                    if (e.key === 'Enter') {
                        this.planJourney();
                    }
                });
            }
        });

        // Swap origin/destination button
        const swapBtn = document.getElementById('swap-stations-btn');
        if (swapBtn) {
            swapBtn.addEventListener('click', () => this.swapStations());
        }
    }

    /**
     * Plan journey between stations
     */
    async planJourney() {
        const fromInput = document.getElementById('from-station-input');
        const toInput = document.getElementById('to-station-input');
        const includeDelays = document.getElementById('include-delays-checkbox')?.checked !== false;

        if (!fromInput || !toInput) {
            console.error('[Journey] Input elements not found');
            return;
        }

        const from = fromInput.value.trim();
        const to = toInput.value.trim();

        if (!from || !to) {
            this.showError('Please enter both origin and destination stations');
            return;
        }

        if (from.toLowerCase() === to.toLowerCase()) {
            this.showError('Origin and destination must be different');
            return;
        }

        try {
            this.showLoading();

            const params = new URLSearchParams({
                from: from,
                to: to,
                alternatives: '3',
                include_delays: includeDelays ? 'true' : 'false'
            });

            const response = await fetch(`/api/journey/plan?${params}`);
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Journey planning failed');
            }

            const data = await response.json();
            this.currentRoutes = data.routes || [];
            
            if (this.currentRoutes.length === 0) {
                this.showError('No routes found between these stations');
                return;
            }

            this.displayRoutes(data);
            this.hideLoading();
            
        } catch (error) {
            console.error('[Journey] Planning error:', error);
            this.showError(error.message || 'Failed to plan journey');
            this.hideLoading();
        }
    }

    /**
     * Display route options
     */
    displayRoutes(data) {
        const container = document.getElementById('journey-results');
        if (!container) return;

        const routes = data.routes;

        let html = `
            <div class="journey-header">
                <h3>${data.origin.name} → ${data.destination.name}</h3>
                <p class="journey-meta">
                    ${routes.length} route option${routes.length !== 1 ? 's' : ''} found
                    ${data.delays_included ? ' • Real-time delays included' : ''}
                </p>
            </div>
            <div class="journey-routes">
        `;

        routes.forEach((route, index) => {
            html += this.renderRoute(route, index);
        });

        html += '</div>';
        container.innerHTML = html;
        container.style.display = 'block';

        // Setup route selection handlers
        this.setupRouteSelectionHandlers();
    }

    /**
     * Render a single route option
     */
    renderRoute(route, index) {
        const isFastest = index === 0;
        const hasWalking = route.segments.some(seg => seg.is_walking);
        
        let html = `
            <div class="journey-route ${isFastest ? 'route-recommended' : ''}" data-route-index="${index}">
                <div class="route-header" onclick="journeyPlannerUI.selectRoute(${index})">
                    <div class="route-summary">
                        ${isFastest ? '<span class="badge badge-recommended">Fastest</span>' : ''}
                        <span class="route-duration">
                            <i class="fas fa-clock"></i> ${route.total_duration_minutes} min
                        </span>
                        <span class="route-transfers">
                            <i class="fas fa-exchange-alt"></i> ${route.transfers} transfer${route.transfers !== 1 ? 's' : ''}
                        </span>
                        ${hasWalking ? '<span class="route-walking"><i class="fas fa-walking"></i> Walking</span>' : ''}
                        <span class="route-cost">${route.estimated_cost}</span>
                    </div>
                    <i class="fas fa-chevron-down route-toggle"></i>
                </div>
                <div class="route-details" id="route-details-${index}" style="display: ${index === 0 ? 'block' : 'none'};">
                    ${this.renderSegments(route.segments)}
                    <div class="route-footer">
                        <span>Departure: ${this.formatTime(route.departure_time)}</span>
                        <span>Arrival: ${this.formatTime(route.arrival_time)}</span>
                    </div>
                </div>
            </div>
        `;

        return html;
    }

    /**
     * Render journey segments
     */
    renderSegments(segments) {
        return segments.map((seg, idx) => {
            const isWalking = seg.is_walking;
            const vehicleIcon = this.getVehicleIcon(seg.vehicle_type);
            const lineColor = this.getLineColor(seg.line);

            return `
                <div class="journey-segment ${isWalking ? 'segment-walking' : ''}">
                    <div class="segment-line" style="background-color: ${lineColor}">
                        <i class="${vehicleIcon}"></i>
                        <span>${seg.line}</span>
                    </div>
                    <div class="segment-route">
                        <div class="segment-stop">
                            <i class="fas fa-circle stop-marker"></i>
                            <span>${seg.from_station}</span>
                            <span class="segment-time">${this.formatTime(seg.departure_time)}</span>
                        </div>
                        <div class="segment-connector">
                            <div class="connector-line"></div>
                            <span class="connector-duration">${seg.duration_minutes} min</span>
                        </div>
                        <div class="segment-stop">
                            <i class="fas fa-circle stop-marker"></i>
                            <span>${seg.to_station}</span>
                            <span class="segment-time">${this.formatTime(seg.arrival_time)}</span>
                        </div>
                    </div>
                </div>
                ${idx < segments.length - 1 ? '<div class="segment-transfer"><i class="fas fa-exchange-alt"></i> Transfer (5 min)</div>' : ''}
            `;
        }).join('');
    }

    /**
     * Select and expand a route
     */
    selectRoute(index) {
        this.selectedRouteIndex = index;

        // Toggle all route details
        document.querySelectorAll('.route-details').forEach((el, idx) => {
            el.style.display = idx === index ? 'block' : 'none';
        });

        // Update toggle icons
        document.querySelectorAll('.route-toggle').forEach((el, idx) => {
            el.classList.toggle('fa-chevron-down', idx !== index);
            el.classList.toggle('fa-chevron-up', idx === index);
        });
    }

    /**
     * Swap origin and destination
     */
    swapStations() {
        const fromInput = document.getElementById('from-station-input');
        const toInput = document.getElementById('to-station-input');

        if (fromInput && toInput) {
            const temp = fromInput.value;
            fromInput.value = toInput.value;
            toInput.value = temp;
        }
    }

    /**
     * Format datetime for display
     */
    formatTime(isoString) {
        const date = new Date(isoString);
        return date.toLocaleTimeString('de-AT', { hour: '2-digit', minute: '2-digit' });
    }

    /**
     * Get icon for vehicle type
     */
    getVehicleIcon(vehicleType) {
        const icons = {
            'metro': 'fas fa-subway',
            'tram': 'fas fa-train',
            'bus': 'fas fa-bus',
            'rail': 'fas fa-train',
            'walk': 'fas fa-walking'
        };
        return icons[vehicleType] || 'fas fa-bus';
    }

    /**
     * Get color for transit line
     */
    getLineColor(line) {
        // Vienna line colors
        const colors = {
            'U1': '#E30613',
            'U2': '#9669BC',
            'U3': '#F39100',
            'U4': '#00975F',
            'U6': '#964B00',
            'WALK': '#999999'
        };
        
        if (colors[line]) return colors[line];
        if (line.startsWith('U')) return '#E30613';
        if (line.match(/^\d+$/)) return '#DC0714';  // Tram
        if (line.match(/^\d+[AB]$/)) return '#0088CE';  // Bus
        return '#666666';
    }

    /**
     * Show loading state
     */
    showLoading() {
        const resultsContainer = document.getElementById('journey-results');
        if (resultsContainer) {
            resultsContainer.innerHTML = `
                <div class="journey-loading">
                    <div class="loading-spinner"></div>
                    <p>Planning your journey...</p>
                </div>
            `;
            resultsContainer.style.display = 'block';
        }
    }

    /**
     * Hide loading state
     */
    hideLoading() {
        // Loading is replaced by results
    }

    /**
     * Show error message
     */
    showError(message) {
        const resultsContainer = document.getElementById('journey-results');
        if (resultsContainer) {
            resultsContainer.innerHTML = `
                <div class="journey-error">
                    <i class="fas fa-exclamation-triangle"></i>
                    <p>${message}</p>
                </div>
            `;
            resultsContainer.style.display = 'block';
        }
    }
}

// Initialize journey planner UI
const journeyPlannerUI = new JourneyPlannerUI();
window.journeyPlannerUI = journeyPlannerUI;

console.log('[Journey] Planner UI loaded');

