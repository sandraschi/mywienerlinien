/**
 * API client for making HTTP requests and handling WebSocket connections
 */

import { logger } from './logger.js';

// Default request timeout in milliseconds
const DEFAULT_TIMEOUT = 10000;

/**
 * Make an HTTP request with timeout and error handling
 * @param {string} url - The URL to request
 * @param {Object} options - Fetch options
 * @param {number} timeout - Request timeout in milliseconds
 * @returns {Promise<Response>} The fetch response
 * @throws {Error} If the request fails or times out
 */
export async function fetchWithTimeout(url, options = {}, timeout = DEFAULT_TIMEOUT) {
    try {
        const controller = new AbortController();
        const id = setTimeout(() => controller.abort(), timeout);
        
        logger.debug(`Fetching: ${url}`, { options, timeout });
        
        const response = await fetch(url, {
            ...options,
            signal: controller.signal,
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                ...(options.headers || {})
            },
            credentials: 'same-origin'
        });
        
        clearTimeout(id);
        
        if (!response.ok) {
            const error = new Error(`HTTP error! status: ${response.status}`);
            error.status = response.status;
            error.response = response;
            throw error;
        }
        
        return response;
        
    } catch (error) {
        if (error.name === 'AbortError') {
            throw new Error(`Request timed out after ${timeout}ms`);
        }
        logger.error(`API request failed: ${error.message}`, error);
        throw error;
    }
}

/**
 * Make a GET request
 * @param {string} url - The URL to request
 * @param {Object} [params] - Query parameters
 * @param {Object} [options] - Additional fetch options
 * @returns {Promise<Object>} The parsed JSON response
 */
export async function get(url, params = {}, options = {}) {
    try {
        const queryString = new URLSearchParams(params).toString();
        const fullUrl = queryString ? `${url}?${queryString}` : url;
        
        const response = await fetchWithTimeout(fullUrl, {
            ...options,
            method: 'GET'
        });
        
        return await response.json();
        
    } catch (error) {
        logger.error(`GET request failed: ${url}`, error);
        throw error;
    }
}

/**
 * Make a POST request
 * @param {string} url - The URL to request
 * @param {Object} data - The data to send
 * @param {Object} [options] - Additional fetch options
 * @returns {Promise<Object>} The parsed JSON response
 */
export async function post(url, data = {}, options = {}) {
    try {
        const response = await fetchWithTimeout(url, {
            ...options,
            method: 'POST',
            body: JSON.stringify(data),
            headers: {
                'Content-Type': 'application/json',
                ...(options.headers || {})
            }
        });
        
        // Handle empty responses
        const text = await response.text();
        return text ? JSON.parse(text) : {};
        
    } catch (error) {
        logger.error(`POST request failed: ${url}`, error);
        throw error;
    }
}

/**
 * Make a PUT request
 * @param {string} url - The URL to request
 * @param {Object} data - The data to send
 * @param {Object} [options] - Additional fetch options
 * @returns {Promise<Object>} The parsed JSON response
 */
export async function put(url, data = {}, options = {}) {
    try {
        const response = await fetchWithTimeout(url, {
            ...options,
            method: 'PUT',
            body: JSON.stringify(data),
            headers: {
                'Content-Type': 'application/json',
                ...(options.headers || {})
            }
        });
        
        // Handle empty responses
        const text = await response.text();
        return text ? JSON.parse(text) : {};
        
    } catch (error) {
        logger.error(`PUT request failed: ${url}`, error);
        throw error;
    }
}

/**
 * Make a DELETE request
 * @param {string} url - The URL to request
 * @param {Object} [options] - Additional fetch options
 * @returns {Promise<Object>} The parsed JSON response
 */
export async function del(url, options = {}) {
    try {
        const response = await fetchWithTimeout(url, {
            ...options,
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json',
                ...(options.headers || {})
            }
        });
        
        // Handle empty responses
        const text = await response.text();
        return text ? JSON.parse(text) : {};
        
    } catch (error) {
        logger.error(`DELETE request failed: ${url}`, error);
        throw error;
    }
}

/**
 * Create a WebSocket connection with reconnection and error handling
 * @param {string} url - The WebSocket URL
 * @param {Object} callbacks - Event callbacks
 * @param {Function} callbacks.onMessage - Called when a message is received
 * @param {Function} [callbacks.onOpen] - Called when the connection is opened
 * @param {Function} [callbacks.onClose] - Called when the connection is closed
 * @param {Function} [callbacks.onError] - Called when an error occurs
 * @param {number} [reconnectDelay=5000] - Delay before reconnecting in milliseconds
 * @returns {Object} WebSocket controller with close method
 */
export function createWebSocket(url, {
    onMessage,
    onOpen = () => {},
    onClose = () => {},
    onError = () => {}
} = {}, reconnectDelay = 5000) {
    let socket = null;
    let reconnectAttempts = 0;
    let reconnectTimer = null;
    let isManualClose = false;
    
    const connect = () => {
        if (socket) {
            return;
        }
        
        try {
            logger.debug(`Connecting to WebSocket: ${url}`);
            socket = new WebSocket(url);
            
            socket.onopen = (event) => {
                logger.info('WebSocket connected');
                reconnectAttempts = 0;
                onOpen(event);
            };
            
            socket.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    onMessage(data, event);
                } catch (error) {
                    logger.error('Failed to parse WebSocket message:', error);
                }
            };
            
            socket.onclose = (event) => {
                logger.info('WebSocket disconnected', {
                    code: event.code,
                    reason: event.reason,
                    wasClean: event.wasClean
                });
                
                socket = null;
                onClose(event);
                
                // Attempt to reconnect if this wasn't a manual close
                if (!isManualClose) {
                    const delay = Math.min(reconnectDelay * (reconnectAttempts + 1), 30000); // Max 30s delay
                    logger.info(`Attempting to reconnect in ${delay}ms...`);
                    
                    reconnectTimer = setTimeout(() => {
                        reconnectAttempts++;
                        connect();
                    }, delay);
                }
            };
            
            socket.onerror = (error) => {
                logger.error('WebSocket error:', error);
                onError(error);
            };
            
        } catch (error) {
            logger.error('Failed to create WebSocket:', error);
            onError(error);
            
            // Schedule reconnection attempt
            if (!isManualClose) {
                const delay = Math.min(reconnectDelay * (reconnectAttempts + 1), 30000);
                logger.info(`Attempting to reconnect in ${delay}ms...`);
                
                reconnectTimer = setTimeout(() => {
                    reconnectAttempts++;
                    connect();
                }, delay);
            }
        }
    };
    
    // Start the connection
    connect();
    
    // Return controller object
    return {
        /**
         * Close the WebSocket connection
         * @param {number} [code] - Close code
         * @param {string} [reason] - Close reason
         */
        close: (code, reason) => {
            isManualClose = true;
            
            if (reconnectTimer) {
                clearTimeout(reconnectTimer);
                reconnectTimer = null;
            }
            
            if (socket) {
                socket.close(code, reason);
                socket = null;
            }
        },
        
        /**
         * Send a message through the WebSocket
         * @param {*} data - The data to send (will be JSON stringified)
         * @returns {boolean} True if the message was sent, false otherwise
         */
        send: (data) => {
            if (socket && socket.readyState === WebSocket.OPEN) {
                try {
                    const message = typeof data === 'string' ? data : JSON.stringify(data);
                    socket.send(message);
                    return true;
                } catch (error) {
                    logger.error('Failed to send WebSocket message:', error);
                    return false;
                }
            }
            logger.warn('WebSocket is not connected');
            return false;
        },
        
        /**
         * Get the current WebSocket state
         * @returns {number} The WebSocket readyState or -1 if not connected
         */
        getState: () => {
            return socket ? socket.readyState : -1;
        },
        
        /**
         * Reconnect the WebSocket
         */
        reconnect: () => {
            if (socket) {
                socket.close();
            } else {
                isManualClose = false;
                connect();
            }
        }
    };
}

/**
 * Create an API client with a base URL and default headers
 * @param {string} baseUrl - The base URL for all requests
 * @param {Object} defaultHeaders - Default headers to include in all requests
 * @returns {Object} An API client object with HTTP methods
 */
export function createApiClient(baseUrl, defaultHeaders = {}) {
    const base = baseUrl.endsWith('/') ? baseUrl.slice(0, -1) : baseUrl;
    
    return {
        get: (path, params = {}, options = {}) => {
            const url = path.startsWith('http') ? path : `${base}${path}`;
            return get(url, params, {
                ...options,
                headers: { ...defaultHeaders, ...(options.headers || {}) }
            });
        },
        
        post: (path, data = {}, options = {}) => {
            const url = path.startsWith('http') ? path : `${base}${path}`;
            return post(url, data, {
                ...options,
                headers: { ...defaultHeaders, ...(options.headers || {}) }
            });
        },
        
        put: (path, data = {}, options = {}) => {
            const url = path.startsWith('http') ? path : `${base}${path}`;
            return put(url, data, {
                ...options,
                headers: { ...defaultHeaders, ...(options.headers || {}) }
            });
        },
        
        delete: (path, options = {}) => {
            const url = path.startsWith('http') ? path : `${base}${path}`;
            return del(url, {
                ...options,
                headers: { ...defaultHeaders, ...(options.headers || {}) }
            });
        },
        
        createWebSocket: (path, callbacks, reconnectDelay) => {
            const wsUrl = new URL(path, base.replace(/^http/, 'ws'));
            return createWebSocket(wsUrl.toString(), callbacks, reconnectDelay);
        }
    };
}

// Default export for backward compatibility
export default {
    fetch: fetchWithTimeout,
    get,
    post,
    put,
    delete: del,
    createWebSocket,
    createApiClient
};
