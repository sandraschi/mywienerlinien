/**
 * City Switcher Component
 * Phase 4: Multi-city support for Austrian and international transit
 */

class CitySwitcher {
    constructor() {
        this.cities = [];
        this.currentCity = 'vienna';
        this.init();
    }

    async init() {
        await this.loadCities();
        this.renderCitySwitcher();
        this.setupEventListeners();
    }

    async loadCities() {
        try {
            const response = await fetch('/api/cities');
            const data = await response.json();
            
            this.cities = data.cities || [];
            this.currentCity = data.current_city || 'vienna';
            
            console.log('[CitySwitcher] Loaded', this.cities.length, 'cities');
            
        } catch (error) {
            console.error('[CitySwitcher] Error loading cities:', error);
        }
    }

    renderCitySwitcher() {
        const container = document.getElementById('city-switcher');
        if (!container) return;

        // Group cities by country
        const grouped = this.groupByCountry(this.cities);

        let html = `
            <div class="city-switcher-header">
                <i class="fas fa-globe"></i>
                <span>Cities</span>
            </div>
            <div class="city-list">
        `;

        Object.keys(grouped).forEach(country => {
            html += `<div class="city-group">`;
            html += `<div class="city-group-header">${country}</div>`;
            
            grouped[country].forEach(city => {
                const isActive = city.code === this.currentCity;
                const statusIcon = city.data_loaded ? '✓' : '○';
                const statusClass = city.data_loaded ? 'city-loaded' : 'city-not-loaded';
                
                html += `
                    <div class="city-item ${isActive ? 'city-active' : ''} ${statusClass}" 
                         data-city-code="${city.code}"
                         onclick="citySwitcher.switchCity('${city.code}')">
                        <div class="city-info">
                            <span class="city-name">${city.name}</span>
                            ${!city.data_loaded ? '<span class="city-badge">Data pending</span>' : ''}
                        </div>
                        <span class="city-status">${statusIcon}</span>
                    </div>
                `;
            });
            
            html += `</div>`;
        });

        html += `</div>`;
        container.innerHTML = html;
    }

    groupByCountry(cities) {
        const grouped = {};
        
        cities.forEach(city => {
            const country = city.country || 'Other';
            if (!grouped[country]) {
                grouped[country] = [];
            }
            grouped[country].push(city);
        });

        return grouped;
    }

    async switchCity(cityCode) {
        if (cityCode === this.currentCity) {
            console.log('[CitySwitcher] Already on', cityCode);
            return;
        }

        try {
            console.log('[CitySwitcher] Switching to', cityCode);
            
            const response = await fetch(`/api/cities/${cityCode}/switch`, {
                method: 'POST'
            });

            if (!response.ok) {
                throw new Error(`Switch failed: ${response.status}`);
            }

            const data = await response.json();
            
            if (data.success) {
                this.currentCity = cityCode;
                
                // Show success message
                this.showMessage(`Switched to ${data.city.name}!`, 'success');
                
                // Update UI
                this.renderCitySwitcher();
                
                // Reload map with new city center
                if (data.city.map_center && window.map) {
                    window.map.setView(
                        [data.city.map_center.lat, data.city.map_center.lng],
                        data.city.map_zoom || 13
                    );
                }
                
                // Reload data for new city
                if (typeof loadVehicleData === 'function') {
                    setTimeout(() => loadVehicleData(), 1000);
                }
                
            } else {
                throw new Error(data.message || 'Switch failed');
            }
            
        } catch (error) {
            console.error('[CitySwitcher] Switch error:', error);
            this.showMessage(`Failed to switch city: ${error.message}`, 'error');
        }
    }

    setupEventListeners() {
        // Listen for city changes from other sources
        window.addEventListener('city-changed', (e) => {
            this.currentCity = e.detail.city;
            this.renderCitySwitcher();
        });
    }

    showMessage(text, type = 'info') {
        // Create temporary message
        const message = document.createElement('div');
        message.className = `city-message city-message-${type}`;
        message.textContent = text;
        document.body.appendChild(message);
        
        setTimeout(() => message.classList.add('show'), 10);
        setTimeout(() => {
            message.classList.remove('show');
            setTimeout(() => message.remove(), 300);
        }, 3000);
    }
}

// Initialize city switcher
const citySwitcher = new CitySwitcher();
window.citySwitcher = citySwitcher;

console.log('[CitySwitcher] Initialized');

