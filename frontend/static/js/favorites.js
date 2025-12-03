/**
 * Favorites Management Module
 * Handles favorite stations with localStorage persistence
 * Phase 2 Enhancement: Client-side favorites with future server-side sync support
 */

class FavoritesManager {
    constructor() {
        this.storageKey = 'wl-favorites';
        this.favorites = this.loadFavorites();
        this.setupEventListeners();
    }

    /**
     * Load favorites from localStorage
     */
    loadFavorites() {
        try {
            const stored = localStorage.getItem(this.storageKey);
            return stored ? JSON.parse(stored) : [];
        } catch (error) {
            console.error('[Favorites] Error loading from localStorage:', error);
            return [];
        }
    }

    /**
     * Save favorites to localStorage
     */
    saveFavorites() {
        try {
            localStorage.setItem(this.storageKey, JSON.stringify(this.favorites));
            this.dispatchChangeEvent();
            return true;
        } catch (error) {
            console.error('[Favorites] Error saving to localStorage:', error);
            return false;
        }
    }

    /**
     * Add a station to favorites
     */
    add(station) {
        const exists = this.favorites.some(fav => fav.id === station.id);
        if (exists) {
            console.log('[Favorites] Station already in favorites:', station.id);
            return false;
        }

        const favorite = {
            id: station.id || station.stop_id,
            name: station.name || station.stop_name,
            lat: station.lat || station.latitude,
            lng: station.lng || station.longitude,
            rbl: station.rbl || station.stop_code,
            type: station.type || 'station',
            addedAt: new Date().toISOString()
        };

        this.favorites.push(favorite);
        this.saveFavorites();
        console.log('[Favorites] Added:', favorite.name);
        return true;
    }

    /**
     * Remove a station from favorites
     */
    remove(stationId) {
        const initialLength = this.favorites.length;
        this.favorites = this.favorites.filter(fav => fav.id !== stationId);
        
        if (this.favorites.length < initialLength) {
            this.saveFavorites();
            console.log('[Favorites] Removed:', stationId);
            return true;
        }
        
        return false;
    }

    /**
     * Check if a station is favorited
     */
    isFavorite(stationId) {
        return this.favorites.some(fav => fav.id === stationId);
    }

    /**
     * Get all favorites
     */
    getAll() {
        return [...this.favorites];
    }

    /**
     * Get favorite by ID
     */
    get(stationId) {
        return this.favorites.find(fav => fav.id === stationId);
    }

    /**
     * Clear all favorites
     */
    clear() {
        if (confirm('Remove all favorite stations?')) {
            this.favorites = [];
            this.saveFavorites();
            console.log('[Favorites] Cleared all');
            return true;
        }
        return false;
    }

    /**
     * Export favorites as JSON
     */
    export() {
        const dataStr = JSON.stringify(this.favorites, null, 2);
        const blob = new Blob([dataStr], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `wl-favorites-${new Date().toISOString().split('T')[0]}.json`;
        link.click();
        URL.revokeObjectURL(url);
    }

    /**
     * Import favorites from JSON file
     */
    async import(file) {
        try {
            const text = await file.text();
            const imported = JSON.parse(text);
            
            if (!Array.isArray(imported)) {
                throw new Error('Invalid favorites file format');
            }

            // Merge with existing favorites (avoid duplicates)
            imported.forEach(station => {
                if (!this.isFavorite(station.id)) {
                    this.favorites.push(station);
                }
            });

            this.saveFavorites();
            console.log('[Favorites] Imported:', imported.length, 'stations');
            return true;
        } catch (error) {
            console.error('[Favorites] Import error:', error);
            return false;
        }
    }

    /**
     * Dispatch custom event when favorites change
     */
    dispatchChangeEvent() {
        window.dispatchEvent(new CustomEvent('favorites-changed', {
            detail: { favorites: this.getAll() }
        }));
    }

    /**
     * Setup UI event listeners
     */
    setupEventListeners() {
        // Listen for changes from other tabs
        window.addEventListener('storage', (e) => {
            if (e.key === this.storageKey) {
                this.favorites = this.loadFavorites();
                this.dispatchChangeEvent();
            }
        });
    }

    /**
     * Render favorites panel
     */
    renderPanel() {
        const panel = document.getElementById('favorites-panel');
        if (!panel) return;

        const favorites = this.getAll();

        if (favorites.length === 0) {
            panel.innerHTML = `
                <div class="favorites-empty">
                    <i class="fas fa-star"></i>
                    <p>No favorite stations yet</p>
                    <p class="favorites-hint">Click the star icon on any station to add it to favorites</p>
                </div>
            `;
            return;
        }

        const html = favorites.map(fav => `
            <div class="favorite-item" data-station-id="${fav.id}">
                <div class="favorite-info" onclick="favoritesManager.zoomToStation('${fav.id}')">
                    <h4>${fav.name}</h4>
                    ${fav.rbl ? `<span class="favorite-rbl">RBL: ${fav.rbl}</span>` : ''}
                    <span class="favorite-type">${fav.type}</span>
                </div>
                <div class="favorite-actions">
                    <button class="btn-icon" onclick="favoritesManager.showDepartures('${fav.id}')" 
                            title="Show departures" aria-label="Show departures for ${fav.name}">
                        <i class="fas fa-clock"></i>
                    </button>
                    <button class="btn-icon btn-remove" onclick="favoritesManager.remove('${fav.id}')" 
                            title="Remove favorite" aria-label="Remove ${fav.name} from favorites">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </div>
        `).join('');

        panel.innerHTML = html;
    }

    /**
     * Zoom map to station
     */
    zoomToStation(stationId) {
        const favorite = this.get(stationId);
        if (favorite && window.map) {
            window.map.setView([favorite.lat, favorite.lng], 16);
            console.log('[Favorites] Zoomed to:', favorite.name);
        }
    }

    /**
     * Show departures for station
     */
    async showDepartures(stationId) {
        const favorite = this.get(stationId);
        if (favorite && typeof fetchArrivalsForStop === 'function') {
            await fetchArrivalsForStop(favorite);
        }
    }

    /**
     * Toggle favorite status for a station
     */
    toggle(station) {
        const stationId = station.id || station.stop_id;
        
        if (this.isFavorite(stationId)) {
            return this.remove(stationId);
        } else {
            return this.add(station);
        }
    }

    /**
     * Update UI for a station's favorite status
     */
    updateStationUI(stationId) {
        const isFav = this.isFavorite(stationId);
        const buttons = document.querySelectorAll(`[data-station-id="${stationId}"] .btn-favorite`);
        
        buttons.forEach(btn => {
            btn.classList.toggle('active', isFav);
            btn.innerHTML = isFav ? '<i class="fas fa-star"></i>' : '<i class="far fa-star"></i>';
            btn.title = isFav ? 'Remove from favorites' : 'Add to favorites';
        });
    }
}

// Initialize favorites manager
const favoritesManager = new FavoritesManager();

// Listen for favorites changes and update UI
window.addEventListener('favorites-changed', () => {
    console.log('[Favorites] Changed, updating UI');
    favoritesManager.renderPanel();
});

// Export for global access
window.favoritesManager = favoritesManager;

console.log('[Favorites] Manager initialized with', favoritesManager.getAll().length, 'favorites');

