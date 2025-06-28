/**
 * Main application entry point
 */

import { CONFIG } from './config.js';
import { initMap } from './modules/map/index.js';
import { initRoutes } from './modules/routes/index.js';
import { initStations } from './modules/stations/index.js';
import { initVehicles } from './modules/vehicles/index.js';
import { initUI } from './modules/ui/index.js';
import { logger } from './modules/utils/logger.js';

// Initialize application when DOM is ready
document.addEventListener('DOMContentLoaded', async () => {
    try {
        logger.info('Initializing application...');
        
        // Initialize core modules
        const map = await initMap('map', CONFIG.MAP);
        
        // Initialize feature modules
        await Promise.all([
            initRoutes(map),
            initStations(map),
            initVehicles(map),
            initUI()
        ]);
        
        logger.info('Application initialized successfully');
        
    } catch (error) {
        logger.error('Failed to initialize application:', error);
        // Show error message to user
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-message';
        errorDiv.textContent = 'Failed to initialize the application. Please refresh the page or try again later.';
        document.body.prepend(errorDiv);
    }
});

// Handle service worker registration for PWA
if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('/service-worker.js')
            .then(registration => {
                logger.info('ServiceWorker registration successful');
            })
            .catch(error => {
                logger.warn('ServiceWorker registration failed:', error);
            });
    });
}
