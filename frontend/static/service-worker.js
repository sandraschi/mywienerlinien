// Service Worker for Wiener Linien Live Map PWA
// Version: 1.0.0
// Date: 2025-12-03

const CACHE_VERSION = 'wl-live-v1';
const CACHE_STATIC = `${CACHE_VERSION}-static`;
const CACHE_DYNAMIC = `${CACHE_VERSION}-dynamic`;
const CACHE_OFFLINE = `${CACHE_VERSION}-offline`;

// Static assets to cache on install
const STATIC_ASSETS = [
    '/',
    '/static/css/main.css',
    '/static/css/map.css',
    '/static/css/responsive.css',
    '/static/js/map.js',
    '/static/js/main.js',
    '/static/manifest.json',
    '/offline.html'  // Fallback offline page
];

// Dynamic caching for API responses (short TTL)
const API_CACHE_PATTERNS = [
    /\/api\/stations/,
    /\/api\/lines/,
    /\/api\/routes/
];

// Never cache (always network)
const NETWORK_ONLY_PATTERNS = [
    /\/api\/vehicles/,  // Always fresh vehicle data
    /\/api\/stops\/nearby/,  // User location dependent
    /\/api\/disruptions/,  // Real-time disruptions
    /\/ws\//  // WebSocket connections
];

// Install event - cache static assets
self.addEventListener('install', (event) => {
    console.log('[SW] Installing Service Worker v' + CACHE_VERSION);
    
    event.waitUntil(
        caches.open(CACHE_STATIC)
            .then((cache) => {
                console.log('[SW] Caching static assets');
                return cache.addAll(STATIC_ASSETS);
            })
            .catch((err) => {
                console.error('[SW] Failed to cache static assets:', err);
            })
    );
    
    // Force activation immediately
    self.skipWaiting();
});

// Activate event - clean old caches
self.addEventListener('activate', (event) => {
    console.log('[SW] Activating Service Worker v' + CACHE_VERSION);
    
    event.waitUntil(
        caches.keys()
            .then((cacheNames) => {
                return Promise.all(
                    cacheNames
                        .filter((name) => name.startsWith('wl-live-') && name !== CACHE_STATIC && name !== CACHE_DYNAMIC && name !== CACHE_OFFLINE)
                        .map((name) => {
                            console.log('[SW] Deleting old cache:', name);
                            return caches.delete(name);
                        })
                );
            })
    );
    
    // Take control immediately
    return self.clients.claim();
});

// Fetch event - network first with fallback
self.addEventListener('fetch', (event) => {
    const { request } = event;
    const url = new URL(request.url);
    
    // Skip non-GET requests
    if (request.method !== 'GET') {
        return;
    }
    
    // Network only for specific patterns
    if (NETWORK_ONLY_PATTERNS.some(pattern => pattern.test(url.pathname))) {
        event.respondWith(fetch(request));
        return;
    }
    
    // Static assets - cache first
    if (STATIC_ASSETS.some(asset => url.pathname === asset || url.pathname.startsWith('/static/'))) {
        event.respondWith(cacheFirst(request, CACHE_STATIC));
        return;
    }
    
    // API responses - network first with cache fallback (short TTL)
    if (API_CACHE_PATTERNS.some(pattern => pattern.test(url.pathname))) {
        event.respondWith(networkFirstWithTimeout(request, CACHE_DYNAMIC, 3000));
        return;
    }
    
    // Default - network first with cache fallback
    event.respondWith(networkFirst(request, CACHE_DYNAMIC));
});

// Cache first strategy
async function cacheFirst(request, cacheName) {
    try {
        const cache = await caches.open(cacheName);
        const cachedResponse = await cache.match(request);
        
        if (cachedResponse) {
            console.log('[SW] Cache hit:', request.url);
            return cachedResponse;
        }
        
        console.log('[SW] Cache miss, fetching:', request.url);
        const networkResponse = await fetch(request);
        
        if (networkResponse.ok) {
            cache.put(request, networkResponse.clone());
        }
        
        return networkResponse;
    } catch (error) {
        console.error('[SW] Cache first failed:', error);
        return offlineFallback(request);
    }
}

// Network first strategy
async function networkFirst(request, cacheName) {
    try {
        const networkResponse = await fetch(request);
        
        if (networkResponse.ok) {
            const cache = await caches.open(cacheName);
            cache.put(request, networkResponse.clone());
        }
        
        return networkResponse;
    } catch (error) {
        console.log('[SW] Network failed, trying cache:', request.url);
        const cache = await caches.open(cacheName);
        const cachedResponse = await cache.match(request);
        
        if (cachedResponse) {
            return cachedResponse;
        }
        
        return offlineFallback(request);
    }
}

// Network first with timeout
async function networkFirstWithTimeout(request, cacheName, timeout = 3000) {
    try {
        const networkPromise = fetch(request);
        const timeoutPromise = new Promise((_, reject) =>
            setTimeout(() => reject(new Error('Network timeout')), timeout)
        );
        
        const networkResponse = await Promise.race([networkPromise, timeoutPromise]);
        
        if (networkResponse.ok) {
            const cache = await caches.open(cacheName);
            cache.put(request, networkResponse.clone());
        }
        
        return networkResponse;
    } catch (error) {
        console.log('[SW] Network timeout/failed, trying cache:', request.url);
        const cache = await caches.open(cacheName);
        const cachedResponse = await cache.match(request);
        
        if (cachedResponse) {
            return cachedResponse;
        }
        
        return offlineFallback(request);
    }
}

// Offline fallback
async function offlineFallback(request) {
    const url = new URL(request.url);
    
    // Return offline page for HTML requests
    if (request.headers.get('accept')?.includes('text/html')) {
        const cache = await caches.open(CACHE_OFFLINE);
        const offlinePage = await cache.match('/offline.html');
        if (offlinePage) {
            return offlinePage;
        }
    }
    
    // Return 503 for failed requests
    return new Response(
        JSON.stringify({
            error: 'Offline',
            message: 'You are currently offline. Please check your connection.'
        }),
        {
            status: 503,
            headers: { 'Content-Type': 'application/json' }
        }
    );
}

// Background sync for offline actions (future enhancement)
self.addEventListener('sync', (event) => {
    console.log('[SW] Background sync:', event.tag);
    
    if (event.tag === 'sync-favorites') {
        event.waitUntil(syncFavorites());
    }
});

async function syncFavorites() {
    // Placeholder for syncing favorite stations when back online
    console.log('[SW] Syncing favorites...');
}

// Push notifications (future enhancement)
self.addEventListener('push', (event) => {
    console.log('[SW] Push notification received');
    
    const data = event.data ? event.data.json() : {};
    const title = data.title || 'Wiener Linien';
    const options = {
        body: data.body || 'New update available',
        icon: '/static/images/icon-192.png',
        badge: '/static/images/badge.png',
        data: data.url || '/'
    };
    
    event.waitUntil(
        self.registration.showNotification(title, options)
    );
});

// Notification click handler
self.addEventListener('notificationclick', (event) => {
    event.notification.close();
    
    event.waitUntil(
        clients.openWindow(event.notification.data || '/')
    );
});

