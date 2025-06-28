/**
 * Logging utility with consistent formatting and log levels
 */

// Log levels
const LOG_LEVELS = {
    DEBUG: 0,
    INFO: 1,
    WARN: 2,
    ERROR: 3,
    NONE: 4
};

// Current log level (default to INFO in production, DEBUG in development)
let currentLogLevel = process.env.NODE_ENV === 'production' 
    ? LOG_LEVELS.INFO 
    : LOG_LEVELS.DEBUG;

/**
 * Set the current log level
 * @param {string} level - The log level to set ('debug', 'info', 'warn', 'error', 'none')
 */
export function setLogLevel(level) {
    const normalizedLevel = String(level).toUpperCase();
    
    if (LOG_LEVELS[normalizedLevel] !== undefined) {
        currentLogLevel = LOG_LEVELS[normalizedLevel];
        console.log(`[Logger] Log level set to: ${normalizedLevel}`);
    } else {
        console.warn(`[Logger] Invalid log level: ${level}`);
    }
}

/**
 * Log a debug message
 * @param {string} message - The message to log
 * @param {...any} args - Additional arguments to log
 */
export function debug(message, ...args) {
    if (currentLogLevel <= LOG_LEVELS.DEBUG) {
        console.debug(`%c[DEBUG] ${message}`, 'color: #666; font-style: italic;', ...args);
    }
}

/**
 * Log an info message
 * @param {string} message - The message to log
 * @param {...any} args - Additional arguments to log
 */
export function info(message, ...args) {
    if (currentLogLevel <= LOG_LEVELS.INFO) {
        console.info(`%c[INFO] ${message}`, 'color: #2196F3;', ...args);
    }
}

/**
 * Log a warning message
 * @param {string} message - The message to log
 * @param {...any} args - Additional arguments to log
 */
export function warn(message, ...args) {
    if (currentLogLevel <= LOG_LEVELS.WARN) {
        console.warn(`%c[WARN] ${message}`, 'color: #FF9800; font-weight: bold;', ...args);
    }
}

/**
 * Log an error message
 * @param {string} message - The message to log
 * @param {Error} [error] - Optional error object
 * @param {...any} args - Additional arguments to log
 */
export function error(message, error, ...args) {
    if (currentLogLevel <= LOG_LEVELS.ERROR) {
        console.error(`%c[ERROR] ${message}`, 'color: #F44336; font-weight: bold;', ...args);
        
        if (error instanceof Error) {
            console.error(error);
            
            // Log additional error details if available
            if (error.stack) {
                console.error(error.stack);
            }
            
            if (error.cause) {
                console.error('Caused by:', error.cause);
            }
        } else if (error) {
            console.error('Error details:', error);
        }
    }
}

/**
 * Create a scoped logger with a specific prefix
 * @param {string} scope - The scope/context for the logger
 * @returns {Object} An object with logging methods
 */
export function createLogger(scope) {
    const prefix = `[${scope}]`;
    
    return {
        debug: (message, ...args) => debug(`${prefix} ${message}`, ...args),
        info: (message, ...args) => info(`${prefix} ${message}`, ...args),
        warn: (message, ...args) => warn(`${prefix} ${message}`, ...args),
        error: (message, error, ...args) => error(`${prefix} ${message}`, error, ...args)
    };
}

// Export the default logger
export const logger = createLogger('App');

// Export log levels
export { LOG_LEVELS };
