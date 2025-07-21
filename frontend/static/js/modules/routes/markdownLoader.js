/**
 * Loads route data from markdown files
 */

import { logger } from '../utils/logger.js';
import { ROUTE_TYPES } from '../../../constants.js';

// Cache for markdown data
let markdownCache = {
    bus: null,
    tram: null,
    metro: null,
    nightbus: null
};

/**
 * Load route data from markdown files
 * @returns {Promise<Array>} Array of route objects
 */
export async function loadRoutesFromMarkdown() {
    try {
        logger.info('Loading routes from markdown files...');
        
        // Load each markdown file in parallel
        const [busRoutes, tramRoutes, metroRoutes, nightbusRoutes] = await Promise.all([
            loadMarkdownFile('busroutes.md'),
            loadMarkdownFile('tramroutes.md'),
            loadMarkdownFile('tuberoutes.md'),
            loadMarkdownFile('nightbusroutes.md')
        ]);
        
        // Parse the markdown content
        const busRoutesParsed = parseMarkdownRoutes(busRoutes, ROUTE_TYPES.BUS);
        const tramRoutesParsed = parseMarkdownRoutes(tramRoutes, ROUTE_TYPES.TRAM);
        const metroRoutesParsed = parseMarkdownRoutes(metroRoutes, ROUTE_TYPES.METRO);
        const nightbusRoutesParsed = parseMarkdownRoutes(nightbusRoutes, ROUTE_TYPES.NIGHTBUS);
        
        logger.info(`Parsed routes: ${busRoutesParsed.length} bus, ${tramRoutesParsed.length} tram, ${metroRoutesParsed.length} metro, ${nightbusRoutesParsed.length} nightbus`);
        
        // Combine all routes
        let allRoutes = [
            ...busRoutesParsed,
            ...tramRoutesParsed,
            ...metroRoutesParsed,
            ...nightbusRoutesParsed
        ];
        
        // Filter out duplicates (keep the first occurrence of each route ID)
        const uniqueRoutes = [];
        const seenIds = new Set();
        
        for (const route of allRoutes) {
            const routeId = route.id.toLowerCase();
            if (!seenIds.has(routeId)) {
                seenIds.add(routeId);
                uniqueRoutes.push(route);
            } else {
                logger.debug(`Skipping duplicate route: ${route.id}`);
            }
        }
        
        logger.info(`Loaded ${uniqueRoutes.length} unique routes from markdown files`);
        return uniqueRoutes;
        
    } catch (error) {
        logger.error('Failed to load routes from markdown:', error);
        throw error;
    }
}

/**
 * Load a markdown file
 * @private
 */
async function loadMarkdownFile(filename) {
    try {
        const response = await fetch(`/data/${filename}`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return await response.text();
    } catch (error) {
        logger.error(`Failed to load markdown file ${filename}:`, error);
        return ''; // Return empty string if file can't be loaded
    }
}

/**
 * Parse markdown content into route objects
 * @private
 */
function parseMarkdownRoutes(markdown, type) {
    if (!markdown) return [];
    
    const routes = [];
    const lines = markdown.split('\n');
    let currentRoute = null;
    
    for (let i = 0; i < lines.length; i++) {
        const line = lines[i].trim();
        
        // Check for route header (e.g., "## Line U1")
        const routeHeaderMatch = line.match(/^##\s+Line\s+(\w+)(?:\s+(?:-|–)\s+([^-]+))?(?:\s+\(([^)]+)\))?/i);
        if (routeHeaderMatch) {
            // Save previous route if exists
            if (currentRoute) {
                if (currentRoute.stops.length > 0 || currentRoute.coordinates.length > 0) {
                    routes.push(currentRoute);
                    logger.debug(`Added route: ${currentRoute.id} with ${currentRoute.stops.length} stops and ${currentRoute.coordinates.length} coordinates`);
                } else {
                    logger.debug(`Skipping empty route: ${currentRoute.id}`);
                }
            }
            
            // Extract route details
            const routeId = routeHeaderMatch[1].toLowerCase();
            const routeName = routeHeaderMatch[1];
            const routeDescription = routeHeaderMatch[2] ? `${routeHeaderMatch[2].trim()}${routeHeaderMatch[3] ? ` (${routeHeaderMatch[3]})` : ''}` : '';
            
            // Start new route
            currentRoute = {
                id: routeId,
                name: routeName,
                type: type,
                description: routeDescription,
                coordinates: [],
                stops: []
            };
            
            logger.debug(`Starting new route: ${routeId} (${type})`);
            continue;
        }
        
        // Check for coordinates line (e.g., "- Coordinates: 48.1234, 16.1234")
        const coordsMatch = line.match(/Coordinates:\s*([\d.]+),\s*([\d.]+)/i);
        if (coordsMatch && currentRoute) {
            const lat = parseFloat(coordsMatch[1]);
            const lng = parseFloat(coordsMatch[2]);
            if (!isNaN(lat) && !isNaN(lng)) {
                currentRoute.coordinates.push([lat, lng]);
            }
            continue;
        }
        
        // Check for stop line (e.g., "1. Station Name - 48.1234, 16.1234")
        const stopMatch = line.match(/^\d+\.\s+([^-]+)-\s*([\d.]+),\s*([\d.]+)/);
        if (stopMatch && currentRoute) {
            currentRoute.stops.push({
                name: stopMatch[1].trim(),
                lat: parseFloat(stopMatch[2]),
                lng: parseFloat(stopMatch[3])
            });
        }
    }
    
    // Add the last route
    if (currentRoute) {
        routes.push(currentRoute);
    }
    
    return routes;
}

// Export the main function
export default loadRoutesFromMarkdown;
