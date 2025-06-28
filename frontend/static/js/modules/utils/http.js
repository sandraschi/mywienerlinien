/**
 * HTTP client with caching, retries, and request cancellation
 */

import { logger } from './logger.js';
import { storage } from './browserStorage.js';

// Default request options
const DEFAULT_OPTIONS = {
    method: 'GET',
    headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    },
    mode: 'cors',
    cache: 'default',
    credentials: 'same-origin',
    redirect: 'follow',
    referrerPolicy: 'no-referrer',
    timeout: 30000, // 30 seconds
    retries: 1,
    retryDelay: 1000, // 1 second
    cacheTTL: 0, // No caching by default
    cacheKey: null, // Auto-generated from URL and params if not provided
    responseType: 'json', // 'json', 'text', 'blob', 'arraybuffer', 'formData'
    withCredentials: false,
    params: null, // Query parameters (object)
    data: null, // Request body (for POST, PUT, PATCH)
    abortSignal: null, // AbortSignal for request cancellation
    onProgress: null, // Progress callback
    validateStatus: (status) => status >= 200 && status < 300
};

// Cache for in-memory storage
const memoryCache = new Map();

/**
 * Generate a cache key from URL and params
 * @private
 */
function generateCacheKey(url, params) {
    const queryString = params ? `?${new URLSearchParams(params).toString()}` : '';
    return `${url}${queryString}`;
}

/**
 * Get cached response
 * @private
 */
function getCachedResponse(cacheKey) {
    try {
        // Try memory cache first
        if (memoryCache.has(cacheKey)) {
            const { data, timestamp, ttl } = memoryCache.get(cacheKey);
            
            // Check if cache is still valid
            if (!ttl || (Date.now() - timestamp < ttl)) {
                return data;
            }
            
            // Cache expired, remove it
            memoryCache.delete(cacheKey);
            return null;
        }
        
        // Try persistent cache
        const cacheData = storage.get(`http_cache_${cacheKey}`);
        if (cacheData) {
            const { data, timestamp, ttl } = cacheData;
            
            // Check if cache is still valid
            if (!ttl || (Date.now() - timestamp < ttl)) {
                return data;
            }
            
            // Cache expired, remove it
            storage.remove(`http_cache_${cacheKey}`);
        }
        
        return null;
    } catch (error) {
        logger.error('Error getting cached response:', error);
        return null;
    }
}

/**
 * Cache a response
 * @private
 */
function cacheResponse(cacheKey, data, ttl = 0) {
    if (!cacheKey) return;
    
    try {
        const cacheData = {
            data,
            timestamp: Date.now(),
            ttl
        };
        
        // Cache in memory
        memoryCache.set(cacheKey, cacheData);
        
        // Also cache in persistent storage if TTL is more than 5 minutes
        if (ttl > 300000) {
            storage.set(`http_cache_${cacheKey}`, cacheData, { ttl });
        }
    } catch (error) {
        logger.error('Error caching response:', error);
    }
}

/**
 * Clear the HTTP cache
 * @param {string} [key] - Optional key to clear a specific cache entry
 */
export function clearCache(key) {
    try {
        if (key) {
            memoryCache.delete(key);
            storage.remove(`http_cache_${key}`);
        } else {
            memoryCache.clear();
            
            // Clear all cache entries with the http_cache_ prefix
            const keysToRemove = [];
            
            for (const key of storage.keys()) {
                if (key.startsWith('http_cache_')) {
                    keysToRemove.push(key);
                }
            }
            
            storage.removeMultiple(keysToRemove);
        }
    } catch (error) {
        logger.error('Error clearing HTTP cache:', error);
    }
}

/**
 * Create an AbortController if not provided
 * @private
 */
function createAbortController(abortSignal) {
    if (abortSignal) {
        return { signal: abortSignal, controller: null };
    }
    
    const controller = new AbortController();
    return { signal: controller.signal, controller };
}

/**
 * Make an HTTP request
 * @param {string} url - The URL to request
 * @param {Object} [options] - Request options
 * @returns {Promise} A promise that resolves with the response
 */
export async function request(url, options = {}) {
    const mergedOptions = { ...DEFAULT_OPTIONS, ...options };
    const {
        method = 'GET',
        headers = {},
        params = null,
        data = null,
        timeout = 30000,
        retries = 1,
        retryDelay = 1000,
        cacheTTL = 0,
        cacheKey = null,
        responseType = 'json',
        withCredentials = false,
        abortSignal = null,
        onProgress = null,
        validateStatus,
        ...fetchOptions
    } = mergedOptions;
    
    // Generate cache key if not provided
    const finalCacheKey = cacheKey || generateCacheKey(url, params);
    
    // Check cache for GET requests
    if (method.toUpperCase() === 'GET' && cacheTTL > 0) {
        const cachedData = getCachedResponse(finalCacheKey);
        if (cachedData !== null) {
            return {
                data: cachedData,
                status: 200,
                statusText: 'OK (from cache)',
                headers: {},
                config: mergedOptions,
                fromCache: true
            };
        }
    }
    
    // Create URL with query parameters
    const urlObj = new URL(url, window.location.origin);
    
    if (params) {
        Object.entries(params).forEach(([key, value]) => {
            if (value !== undefined && value !== null) {
                urlObj.searchParams.append(key, String(value));
            }
        });
    }
    
    // Set up request body
    let body = null;
    
    if (data) {
        if (headers['Content-Type']?.includes('application/json')) {
            body = JSON.stringify(data);
        } else if (data instanceof FormData || data instanceof URLSearchParams) {
            body = data;
            // Let the browser set the Content-Type header with boundary for FormData
            delete headers['Content-Type'];
        } else {
            body = data;
        }
    }
    
    // Set up abort controller
    const { signal, controller } = createAbortController(abortSignal);
    
    // Set up timeout
    let timeoutId;
    if (timeout > 0) {
        const timeoutPromise = new Promise((_, reject) => {
            timeoutId = setTimeout(() => {
                const error = new Error(`Timeout of ${timeout}ms exceeded`);
                error.code = 'ETIMEDOUT';
                reject(error);
            }, timeout);
        });
    }
    
    // Set up progress tracking for downloads
    let response;
    
    const makeRequest = async (attempt = 0) => {
        try {
            // Merge headers
            const mergedHeaders = {
                ...(DEFAULT_OPTIONS.headers || {}),
                ...headers
            };
            
            // Make the request
            const fetchPromise = fetch(urlObj.toString(), {
                ...fetchOptions,
                method,
                headers: mergedHeaders,
                body,
                signal,
                credentials: withCredentials ? 'include' : 'same-origin'
            });
            
            // Race between fetch and timeout
            response = timeout ? await Promise.race([fetchPromise, timeoutPromise]) : await fetchPromise;
            
            // Clear timeout if request completed in time
            if (timeoutId) {
                clearTimeout(timeoutId);
            }
            
            // Handle response
            if (!response.ok && !validateStatus(response.status)) {
                const error = new Error(`Request failed with status ${response.status}`);
                error.response = response;
                error.status = response.status;
                
                // Retry on 5xx errors or 429 (Too Many Requests)
                if ((response.status >= 500 || response.status === 429) && attempt < retries) {
                    logger.warn(`Request failed with status ${response.status}, retrying... (${attempt + 1}/${retries})`);
                    await new Promise(resolve => setTimeout(resolve, retryDelay * (attempt + 1)));
                    return makeRequest(attempt + 1);
                }
                
                throw error;
            }
            
            // Parse response
            let responseData;
            
            try {
                switch (responseType) {
                    case 'json':
                        responseData = await response.json();
                        break;
                    case 'text':
                        responseData = await response.text();
                        break;
                    case 'blob':
                        responseData = await response.blob();
                        break;
                    case 'arraybuffer':
                        responseData = await response.arrayBuffer();
                        break;
                    case 'formData':
                        responseData = await response.formData();
                        break;
                    default:
                        responseData = await response.text();
                }
            } catch (parseError) {
                logger.error('Error parsing response:', parseError);
                throw new Error('Failed to parse response');
            }
            
            // Cache the response if needed
            if (method.toUpperCase() === 'GET' && cacheTTL > 0) {
                cacheResponse(finalCacheKey, responseData, cacheTTL);
            }
            
            // Return the response
            return {
                data: responseData,
                status: response.status,
                statusText: response.statusText,
                headers: response.headers,
                config: mergedOptions,
                fromCache: false
            };
            
        } catch (error) {
            // Clear timeout on error
            if (timeoutId) {
                clearTimeout(timeoutId);
            }
            
            // Handle abort
            if (error.name === 'AbortError') {
                throw new Error('Request was aborted');
            }
            
            // Retry on network errors
            if (attempt < retries && !error.response) {
                logger.warn(`Network error, retrying... (${attempt + 1}/${retries})`, error);
                await new Promise(resolve => setTimeout(resolve, retryDelay * (attempt + 1)));
                return makeRequest(attempt + 1);
            }
            
            throw error;
        }
    };
    
    try {
        return await makeRequest();
    } finally {
        // Clean up
        if (timeoutId) {
            clearTimeout(timeoutId);
        }
    }
}

/**
 * Make a GET request
 * @param {string} url - The URL to request
 * @param {Object} [params] - Query parameters
 * @param {Object} [options] - Request options
 * @returns {Promise} A promise that resolves with the response
 */
export function get(url, params, options = {}) {
    return request(url, {
        ...options,
        method: 'GET',
        params: { ...params, ...(options.params || {}) }
    });
}

/**
 * Make a POST request
 * @param {string} url - The URL to request
 * @param {Object} [data] - Request body
 * @param {Object} [options] - Request options
 * @returns {Promise} A promise that resolves with the response
 */
export function post(url, data, options = {}) {
    return request(url, {
        ...options,
        method: 'POST',
        data
    });
}

/**
 * Make a PUT request
 * @param {string} url - The URL to request
 * @param {Object} [data] - Request body
 * @param {Object} [options] - Request options
 * @returns {Promise} A promise that resolves with the response
 */
export function put(url, data, options = {}) {
    return request(url, {
        ...options,
        method: 'PUT',
        data
    });
}

/**
 * Make a PATCH request
 * @param {string} url - The URL to request
 * @param {Object} [data] - Request body
 * @param {Object} [options] - Request options
 * @returns {Promise} A promise that resolves with the response
 */
export function patch(url, data, options = {}) {
    return request(url, {
        ...options,
        method: 'PATCH',
        data
    });
}

/**
 * Make a DELETE request
 * @param {string} url - The URL to request
 * @param {Object} [options] - Request options
 * @returns {Promise} A promise that resolves with the response
 */
export function del(url, options = {}) {
    return request(url, {
        ...options,
        method: 'DELETE'
    });
}

/**
 * Create an HTTP client with default options
 * @param {Object} defaultOptions - Default options for all requests
 * @returns {Object} An object with request methods
 */
export function createHttpClient(defaultOptions = {}) {
    return {
        request: (url, options) => request(url, { ...defaultOptions, ...options }),
        get: (url, params, options) => get(url, params, { ...defaultOptions, ...options }),
        post: (url, data, options) => post(url, data, { ...defaultOptions, ...options }),
        put: (url, data, options) => put(url, data, { ...defaultOptions, ...options }),
        patch: (url, data, options) => patch(url, data, { ...defaultOptions, ...options }),
        delete: (url, options) => del(url, { ...defaultOptions, ...options })
    };
}

// Create a default HTTP client
export const http = createHttpClient({
    baseURL: '/api',
    headers: {
        'X-Requested-With': 'XMLHttpRequest'
    },
    timeout: 10000,
    retries: 1,
    retryDelay: 1000
});

// Export a default object with all functions for convenience
export default {
    request,
    get,
    post,
    put,
    patch,
    delete: del,
    createHttpClient,
    clearCache,
    http
};
