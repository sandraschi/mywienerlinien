/**
 * Internationalization (i18n) utilities
 */

import { logger } from './logger.js';
import { storage } from './browserStorage.js';

// Default language (English)
const DEFAULT_LANGUAGE = 'en';

// Supported languages with their display names
const SUPPORTED_LANGUAGES = {
    en: { name: 'English', nativeName: 'English' },
    de: { name: 'German', nativeName: 'Deutsch' },
    // Add more languages as needed
};

// Default translations (English)
const DEFAULT_TRANSLATIONS = {
    en: {
        // Common
        'common.loading': 'Loading...',
        'common.error': 'An error occurred',
        'common.retry': 'Retry',
        'common.cancel': 'Cancel',
        'common.save': 'Save',
        'common.close': 'Close',
        'common.yes': 'Yes',
        'common.no': 'No',
        'common.ok': 'OK',
        'common.back': 'Back',
        'common.next': 'Next',
        'common.previous': 'Previous',
        
        // Navigation
        'nav.home': 'Home',
        'nav.routes': 'Routes',
        'nav.stations': 'Stations',
        'nav.departures': 'Departures',
        'nav.disruptions': 'Disruptions',
        'nav.favorites': 'Favorites',
        'nav.settings': 'Settings',
        
        // Map
        'map.zoomIn': 'Zoom in',
        'map.zoomOut': 'Zoom out',
        'map.fullscreen': 'Fullscreen',
        'map.exitFullscreen': 'Exit fullscreen',
        'map.currentLocation': 'Current location',
        'map.searchPlaceholder': 'Search for a station or address',
        'map.noResults': 'No results found',
        
        // Station
        'station.departures': 'Departures',
        'station.noDepartures': 'No departures in the next hour',
        'station.platform': 'Platform',
        'station.direction': 'Direction',
        'station.departureTime': 'Departure',
        'station.delay': 'Delay',
        'station.arrival': 'Arrival',
        'station.departure': 'Departure',
        'station.facilities': 'Facilities',
        'station.elevator': 'Elevator',
        'station.escalator': 'Escalator',
        'station.wheelchair': 'Wheelchair accessible',
        'station.toilet': 'Toilet',
        'station.parking': 'Parking',
        'station.bikeParking': 'Bike parking',
        
        // Route
        'route.duration': 'Duration',
        'route.distance': 'Distance',
        'route.transfers': 'Transfers',
        'route.walkingDistance': 'Walking distance',
        'route.departureTime': 'Departure time',
        'route.arrivalTime': 'Arrival time',
        'route.walk': 'Walk',
        'route.take': 'Take',
        'route.towards': 'towards',
        'route.getOffAt': 'Get off at',
        'route.changeAt': 'Change at',
        'route.platform': 'Platform',
        'route.departureIn': 'Departure in {minutes} min',
        'route.departureNow': 'Departure now',
        'route.departureDelayed': 'Delayed by {minutes} min',
        'route.departureCancelled': 'Cancelled',
        
        // Transport types
        'transport.metro': 'Metro',
        'transport.tram': 'Tram',
        'transport.bus': 'Bus',
        'transport.nightBus': 'Night Bus',
        'transport.rail': 'Rail',
        'transport.suburban': 'Suburban',
        'transport.express': 'Express',
        'transport.walking': 'Walking',
        'transport.bike': 'Bike',
        
        // Settings
        'settings.language': 'Language',
        'settings.theme': 'Theme',
        'settings.theme.light': 'Light',
        'settings.theme.dark': 'Dark',
        'settings.theme.system': 'System',
        'settings.map': 'Map',
        'settings.mapType': 'Map type',
        'settings.mapType.streets': 'Streets',
        'settings.mapType.satellite': 'Satellite',
        'settings.mapType.light': 'Light',
        'settings.mapType.dark': 'Dark',
        'settings.notifications': 'Notifications',
        'settings.notifications.enable': 'Enable notifications',
        'settings.notifications.departures': 'Departure alerts',
        'settings.notifications.disruptions': 'Service disruptions',
        'settings.data': 'Data',
        'settings.data.cache': 'Clear cache',
        'settings.data.reset': 'Reset all settings',
        'settings.about': 'About',
        'settings.version': 'Version',
        'settings.privacy': 'Privacy Policy',
        'settings.terms': 'Terms of Service',
        
        // Errors
        'error.network': 'Network error. Please check your connection.',
        'error.server': 'Server error. Please try again later.',
        'error.location': 'Could not get your location. Please check your browser settings.',
        'error.noRoute': 'No route found. Please try different locations or times.',
        'error.noStations': 'No stations found near your location.',
        'error.noDepartures': 'No departures found for this station.',
        'error.offline': 'You are currently offline. Some features may not be available.',
        
        // Days
        'day.monday': 'Monday',
        'day.tuesday': 'Tuesday',
        'day.wednesday': 'Wednesday',
        'day.thursday': 'Thursday',
        'day.friday': 'Friday',
        'day.saturday': 'Saturday',
        'day.sunday': 'Sunday',
        'day.today': 'Today',
        'day.tomorrow': 'Tomorrow',
        'day.now': 'Now',
        
        // Time
        'time.minute': 'minute',
        'time.minutes': 'minutes',
        'time.hour': 'hour',
        'time.hours': 'hours',
        'time.day': 'day',
        'time.days': 'days',
        'time.week': 'week',
        'time.weeks': 'weeks',
        'time.justNow': 'just now',
        'time.ago': '{time} ago',
        'time.in': 'in {time}',
        'time.lessThanMinute': 'less than a minute',
        'time.about': 'about {time}',
        
        // Units
        'unit.meter': 'm',
        'unit.kilometer': 'km',
        'unit.minute': 'min',
        'unit.hour': 'h',
        'unit.day': 'd',
        'unit.week': 'w',
        'unit.month': 'mo',
        'unit.year': 'yr',
        
        // Months
        'month.january': 'January',
        'month.february': 'February',
        'month.march': 'March',
        'month.april': 'April',
        'month.may': 'May',
        'month.june': 'June',
        'month.july': 'July',
        'month.august': 'August',
        'month.september': 'September',
        'month.october': 'October',
        'month.november': 'November',
        'month.december': 'December',
        
        // Directions
        'direction.north': 'North',
        'direction.northeast': 'Northeast',
        'direction.east': 'East',
        'direction.southeast': 'Southeast',
        'direction.south': 'South',
        'direction.southwest': 'Southwest',
        'direction.west': 'West',
        'direction.northwest': 'Northwest'
    },
    // German translations would go here
    de: {
        // Common
        'common.loading': 'Wird geladen...',
        'common.error': 'Ein Fehler ist aufgetreten',
        'common.retry': 'Wiederholen',
        'common.cancel': 'Abbrechen',
        'common.save': 'Speichern',
        'common.close': 'Schließen',
        'common.yes': 'Ja',
        'common.no': 'Nein',
        'common.ok': 'OK',
        'common.back': 'Zurück',
        'common.next': 'Weiter',
        'common.previous': 'Zurück',
        
        // Navigation
        'nav.home': 'Startseite',
        'nav.routes': 'Routen',
        'nav.stations': 'Stationen',
        'nav.departures': 'Abfahrten',
        'nav.disruptions': 'Störungen',
        'nav.favorites': 'Favoriten',
        'nav.settings': 'Einstellungen',
        
        // Map
        'map.zoomIn': 'Vergrößern',
        'map.zoomOut': 'Verkleinern',
        'map.fullscreen': 'Vollbild',
        'map.exitFullscreen': 'Vollbild beenden',
        'map.currentLocation': 'Aktueller Standort',
        'map.searchPlaceholder': 'Nach einer Station oder Adresse suchen',
        'map.noResults': 'Keine Ergebnisse gefunden',
        
        // Station
        'station.departures': 'Abfahrten',
        'station.noDepartures': 'Keine Abfahrten in der nächsten Stunde',
        'station.platform': 'Steig',
        'station.direction': 'Richtung',
        'station.departureTime': 'Abfahrt',
        'station.delay': 'Verspätung',
        'station.arrival': 'Ankunft',
        'station.departure': 'Abfahrt',
        'station.facilities': 'Ausstattung',
        'station.elevator': 'Aufzug',
        'station.escalator': 'Rolltreppe',
        'station.wheelchair': 'Rollstuhlgerecht',
        'station.toilet': 'WC',
        'station.parking': 'Parkplatz',
        'station.bikeParking': 'Fahrradabstellplatz',
        
        // Transport types
        'transport.metro': 'U-Bahn',
        'transport.tram': 'Straßenbahn',
        'transport.bus': 'Bus',
        'transport.nightBus': 'Nachtbus',
        'transport.rail': 'Zug',
        'transport.suburban': 'S-Bahn',
        'transport.express': 'Express',
        'transport.walking': 'Zu Fuß',
        'transport.bike': 'Fahrrad'
    }
};

// Current language
let currentLanguage = DEFAULT_LANGUAGE;

// Translations cache
let translations = { ...DEFAULT_TRANSLATIONS };

// Event target for language change events
const eventTarget = new EventTarget();

/**
 * Get the current language
 * @returns {string} The current language code
 */
export function getLanguage() {
    return currentLanguage;
}

/**
 * Get all supported languages
 * @returns {Object} Object with language codes and their display names
 */
export function getSupportedLanguages() {
    return { ...SUPPORTED_LANGUAGES };
}

/**
 * Check if a language is supported
 * @param {string} lang - The language code to check
 * @returns {boolean} True if the language is supported
 */
export function isLanguageSupported(lang) {
    return Object.prototype.hasOwnProperty.call(SUPPORTED_LANGUAGES, lang);
}

/**
 * Set the current language
 * @param {string} lang - The language code to set
 * @returns {Promise} A promise that resolves when the language is set
 */
export async function setLanguage(lang) {
    if (!isLanguageSupported(lang)) {
        logger.warn(`Language '${lang}' is not supported`);
        return false;
    }
    
    if (lang === currentLanguage) {
        return true;
    }
    
    // Try to load translations if not already loaded
    if (!translations[lang]) {
        try {
            // In a real app, you would load translations from a file or API
            // const response = await fetch(`/locales/${lang}.json`);
            // translations[lang] = await response.json();
            
            // For now, we'll just use the default translations
            translations[lang] = DEFAULT_TRANSLATIONS[lang] || {};
        } catch (error) {
            logger.error(`Failed to load translations for '${lang}':`, error);
            return false;
        }
    }
    
    // Update current language
    const previousLanguage = currentLanguage;
    currentLanguage = lang;
    
    // Save to storage
    try {
        storage.set('language', lang);
    } catch (error) {
        logger.error('Failed to save language preference:', error);
    }
    
    // Dispatch language change event
    eventTarget.dispatchEvent(new CustomEvent('languageChanged', {
        detail: {
            language: lang,
            previousLanguage
        }
    }));
    
    return true;
}

/**
 * Load the user's preferred language from storage or browser settings
 * @returns {Promise} A promise that resolves when the language is loaded
 */
export async function loadLanguage() {
    try {
        // Try to get language from storage
        const savedLanguage = storage.get('language');
        
        if (savedLanguage && isLanguageSupported(savedLanguage)) {
            return setLanguage(savedLanguage);
        }
        
        // Try to detect browser language
        const browserLanguage = (navigator.language || navigator.userLanguage || '').split('-')[0];
        
        if (browserLanguage && isLanguageSupported(browserLanguage)) {
            return setLanguage(browserLanguage);
        }
        
        // Fall back to default language
        return setLanguage(DEFAULT_LANGUAGE);
    } catch (error) {
        logger.error('Failed to load language:', error);
        return setLanguage(DEFAULT_LANGUAGE);
    }
}

/**
 * Translate a key with optional parameters
 * @param {string} key - The translation key
 * @param {Object} [params] - Optional parameters for the translation
 * @param {string} [defaultValue] - Default value if translation is not found
 * @returns {string} The translated string
 */
export function t(key, params = {}, defaultValue = '') {
    if (!key) return '';
    
    // Get translation for current language or fall back to default language
    let translation = translations[currentLanguage]?.[key] || 
                     translations[DEFAULT_LANGUAGE]?.[key] || 
                     defaultValue || 
                     key;
    
    // Replace parameters in the translation
    if (params && typeof params === 'object') {
        Object.entries(params).forEach(([param, value]) => {
            const regex = new RegExp(`\\{${param}\\}`, 'g');
            translation = translation.replace(regex, String(value));
        });
    }
    
    return translation;
}

/**
 * Add translations for a language
 * @param {string} lang - The language code
 * @param {Object} newTranslations - The translations to add
 * @param {boolean} [merge=true] - Whether to merge with existing translations
 */
export function addTranslations(lang, newTranslations, merge = true) {
    if (!lang || !newTranslations || typeof newTranslations !== 'object') {
        return;
    }
    
    if (!translations[lang]) {
        translations[lang] = {};
    }
    
    if (merge) {
        translations[lang] = { ...translations[lang], ...newTranslations };
    } else {
        translations[lang] = { ...newTranslations };
    }
}

/**
 * Add an event listener for language changes
 * @param {Function} callback - The callback function
 * @returns {Function} A function to remove the event listener
 */
export function onLanguageChange(callback) {
    if (typeof callback !== 'function') {
        return () => {};
    }
    
    const handler = (event) => {
        callback(event.detail);
    };
    
    eventTarget.addEventListener('languageChanged', handler);
    
    // Return a function to remove the event listener
    return () => {
        eventTarget.removeEventListener('languageChanged', handler);
    };
}

/**
 * Format a number according to the current locale
 * @param {number} number - The number to format
 * @param {Object} [options] - Intl.NumberFormat options
 * @returns {string} The formatted number
 */
export function formatNumber(number, options = {}) {
    try {
        return new Intl.NumberFormat(currentLanguage, options).format(number);
    } catch (error) {
        logger.error('Error formatting number:', error);
        return String(number);
    }
}

/**
 * Format a date according to the current locale
 * @param {Date|number|string} date - The date to format
 * @param {Object} [options] - Intl.DateTimeFormat options
 * @returns {string} The formatted date
 */
export function formatDate(date, options = {}) {
    try {
        const dateObj = date instanceof Date ? date : new Date(date);
        return new Intl.DateTimeFormat(currentLanguage, options).format(dateObj);
    } catch (error) {
        logger.error('Error formatting date:', error);
        return String(date);
    }
}

/**
 * Format a time according to the current locale
 * @param {Date|number|string} time - The time to format
 * @param {Object} [options] - Intl.DateTimeFormat options
 * @returns {string} The formatted time
 */
export function formatTime(time, options = {}) {
    const timeOptions = {
        hour: '2-digit',
        minute: '2-digit',
        ...options
    };
    
    return formatDate(time, timeOptions);
}

/**
 * Format a relative time (e.g., "2 hours ago")
 * @param {Date|number|string} date - The date to format
 * @param {Object} [options] - Options
 * @param {string} [options.style='long'] - The style ('long' or 'short')
 * @returns {string} The formatted relative time
 */
export function formatRelativeTime(date, options = {}) {
    const { style = 'long' } = options;
    const dateObj = date instanceof Date ? date : new Date(date);
    const now = new Date();
    const diffInMs = now - dateObj;
    const diffInSeconds = Math.round(diffInMs / 1000);
    const diffInMinutes = Math.round(diffInSeconds / 60);
    const diffInHours = Math.round(diffInMinutes / 60);
    const diffInDays = Math.round(diffInHours / 24);
    
    // Future times
    if (diffInMs < 0) {
        const absDiffInSeconds = Math.abs(diffInSeconds);
        const absDiffInMinutes = Math.abs(diffInMinutes);
        const absDiffInHours = Math.abs(diffInHours);
        const absDiffInDays = Math.abs(diffInDays);
        
        if (absDiffInSeconds < 60) {
            return t('time.justNow');
        } else if (absDiffInMinutes < 60) {
            return t('time.in', { time: t(`time.${absDiffInMinutes === 1 ? 'minute' : 'minutes'}`, { count: absDiffInMinutes }) });
        } else if (absDiffInHours < 24) {
            return t('time.in', { time: t(`time.${absDiffInHours === 1 ? 'hour' : 'hours'}`, { count: absDiffInHours }) });
        } else if (absDiffInDays === 1) {
            return t('time.tomorrow');
        } else if (absDiffInDays < 7) {
            return t('time.in', { time: t(`time.${absDiffInDays === 1 ? 'day' : 'days'}`, { count: absDiffInDays }) });
        } else {
            return formatDate(dateObj, { dateStyle: style });
        }
    }
    
    // Past times
    if (diffInSeconds < 60) {
        return t('time.justNow');
    } else if (diffInMinutes < 60) {
        return t('time.ago', { time: t(`time.${diffInMinutes === 1 ? 'minute' : 'minutes'}`, { count: diffInMinutes }) });
    } else if (diffInHours < 24) {
        return t('time.ago', { time: t(`time.${diffInHours === 1 ? 'hour' : 'hours'}`, { count: diffInHours }) });
    } else if (diffInDays === 1) {
        return t('time.yesterday');
    } else if (diffInDays < 7) {
        return t('time.ago', { time: t(`time.${diffInDays === 1 ? 'day' : 'days'}`, { count: diffInDays }) });
    } else {
        return formatDate(dateObj, { dateStyle: style });
    }
}

// Initialize the i18n module
(async () => {
    try {
        await loadLanguage();
    } catch (error) {
        logger.error('Failed to initialize i18n:', error);
    }
})();

// Export a default object with all functions for convenience
export default {
    t,
    getLanguage,
    setLanguage,
    loadLanguage,
    getSupportedLanguages,
    isLanguageSupported,
    addTranslations,
    onLanguageChange,
    formatNumber,
    formatDate,
    formatTime,
    formatRelativeTime
};
