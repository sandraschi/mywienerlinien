/**
 * Date and time utilities
 */

import { logger } from './logger.js';

// Time constants (in milliseconds)
const SECOND = 1000;
const MINUTE = 60 * SECOND;
const HOUR = 60 * MINUTE;
const DAY = 24 * HOUR;
const WEEK = 7 * DAY;

// Date format strings
const FORMATS = {
    DATE: 'YYYY-MM-DD',
    TIME: 'HH:mm',
    DATETIME: 'YYYY-MM-DD HH:mm',
    ISO: 'YYYY-MM-DDTHH:mm:ss.SSSZ',
    DISPLAY_DATE: 'DD.MM.YYYY',
    DISPLAY_DATETIME: 'DD.MM.YYYY HH:mm',
    DISPLAY_TIME: 'HH:mm:ss',
    DISPLAY_SHORT_TIME: 'HH:mm'
};

// Weekday names
const WEEKDAYS = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
const WEEKDAYS_SHORT = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
const WEEKDAYS_MIN = ['Su', 'Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa'];
const MONTHS = [
    'January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December'
];
const MONTHS_SHORT = [
    'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
    'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'
];

/**
 * Format a date string according to the specified format
 * @param {Date|string|number} date - The date to format
 * @param {string} [format='YYYY-MM-DD'] - The format string
 * @returns {string} The formatted date string
 */
export function formatDate(date, format = FORMATS.DATE) {
    try {
        const d = parseDate(date);
        
        if (!d || isNaN(d.getTime())) {
            logger.warn('Invalid date provided to formatDate:', date);
            return '';
        }
        
        const year = d.getFullYear();
        const month = d.getMonth() + 1;
        const day = d.getDate();
        const hours = d.getHours();
        const minutes = d.getMinutes();
        const seconds = d.getSeconds();
        const milliseconds = d.getMilliseconds();
        const dayOfWeek = d.getDay();
        
        // Padding helper
        const pad = (num, size = 2) => String(num).padStart(size, '0');
        
        // Format tokens
        const tokens = {
            // Year
            'YYYY': year,
            'YY': String(year).slice(-2),
            
            // Month
            'MMMM': MONTHS[d.getMonth()],
            'MMM': MONTHS_SHORT[d.getMonth()],
            'MM': pad(month),
            'M': month,
            
            // Day
            'DD': pad(day),
            'D': day,
            'Do': getOrdinalSuffix(day),
            'dddd': WEEKDAYS[dayOfWeek],
            'ddd': WEEKDAYS_SHORT[dayOfWeek],
            'dd': WEEKDAYS_MIN[dayOfWeek],
            'd': dayOfWeek,
            
            // Time
            'HH': pad(hours),
            'H': hours,
            'hh': pad(hours % 12 || 12),
            'h': hours % 12 || 12,
            'mm': pad(minutes),
            'm': minutes,
            'ss': pad(seconds),
            's': seconds,
            'SSS': pad(milliseconds, 3),
            'A': hours < 12 ? 'AM' : 'PM',
            'a': hours < 12 ? 'am' : 'pm'
        };
        
        // Replace tokens in the format string
        let result = format;
        for (const [token, value] of Object.entries(tokens)) {
            result = result.replace(new RegExp(token, 'g'), value);
        }
        
        return result;
    } catch (error) {
        logger.error('Error formatting date:', error);
        return '';
    }
}

/**
 * Parse a date from various input types
 * @param {Date|string|number} date - The date to parse
 * @returns {Date} The parsed Date object
 */
export function parseDate(date) {
    if (!date) return new Date(NaN);
    if (date instanceof Date) return new Date(date);
    if (typeof date === 'number') return new Date(date);
    if (typeof date === 'string') {
        // Try parsing ISO date string
        const parsed = new Date(date);
        if (!isNaN(parsed.getTime())) return parsed;
        
        // Try parsing common date formats
        // DD.MM.YYYY or DD-MM-YYYY or DD/MM/YYYY
        const match = date.match(/^(\d{1,2})[.\-/](\d{1,2})[.\-/](\d{2,4})/);
        if (match) {
            const [, day, month, year] = match;
            const fullYear = year.length === 2 ? `20${year}` : year;
            return new Date(`${fullYear}-${month.padStart(2, '0')}-${day.padStart(2, '0')}T00:00:00`);
        }
        
        // Try parsing time string (HH:mm)
        const timeMatch = date.match(/^(\d{1,2}):(\d{2})/);
        if (timeMatch) {
            const now = new Date();
            return new Date(now.getFullYear(), now.getMonth(), now.getDate(), 
                          parseInt(timeMatch[1], 10), parseInt(timeMatch[2], 10));
        }
    }
    
    return new Date(NaN);
}

/**
 * Get the ordinal suffix for a day of the month
 * @private
 */
function getOrdinalSuffix(day) {
    if (day >= 11 && day <= 13) {
        return `${day}th`;
    }
    
    switch (day % 10) {
        case 1: return `${day}st`;
        case 2: return `${day}nd`;
        case 3: return `${day}rd`;
        default: return `${day}th`;
    }
}

/**
 * Get the start of a unit of time
 * @param {Date|string} date - The date
 * @param {string} unit - The unit of time ('year', 'month', 'week', 'day', 'hour', 'minute', 'second')
 * @returns {Date} The start of the unit
 */
export function startOf(date, unit) {
    const d = parseDate(date);
    if (isNaN(d.getTime())) return d;
    
    const result = new Date(d);
    
    switch (unit.toLowerCase()) {
        case 'year':
            result.setMonth(0);
            // falls through
        case 'month':
            result.setDate(1);
            // falls through
        case 'day':
            result.setHours(0, 0, 0, 0);
            break;
            
        case 'week':
            // Set to Sunday of the current week
            result.setDate(d.getDate() - d.getDay());
            result.setHours(0, 0, 0, 0);
            break;
            
        case 'hour':
            result.setMinutes(0, 0, 0);
            break;
            
        case 'minute':
            result.setSeconds(0, 0);
            break;
            
        case 'second':
            result.setMilliseconds(0);
            break;
    }
    
    return result;
}

/**
 * Add time to a date
 * @param {Date|string} date - The date to add to
 * @param {number} amount - The amount to add
 * @param {string} unit - The unit of time ('year', 'month', 'week', 'day', 'hour', 'minute', 'second')
 * @returns {Date} The new date
 */
export function add(date, amount, unit) {
    const d = parseDate(date);
    if (isNaN(d.getTime())) return d;
    
    const result = new Date(d);
    
    switch (unit.toLowerCase()) {
        case 'year':
            result.setFullYear(result.getFullYear() + amount);
            break;
            
        case 'month':
            const newMonth = result.getMonth() + amount;
            result.setMonth(newMonth);
            
            // Handle month overflow (e.g., Jan 31 + 1 month = Feb 28/29)
            if (result.getMonth() !== (newMonth % 12 + 12) % 12) {
                result.setDate(0); // Last day of previous month
            }
            break;
            
        case 'week':
            result.setDate(result.getDate() + amount * 7);
            break;
            
        case 'day':
            result.setDate(result.getDate() + amount);
            break;
            
        case 'hour':
            result.setTime(result.getTime() + amount * HOUR);
            break;
            
        case 'minute':
            result.setTime(result.getTime() + amount * MINUTE);
            break;
            
        case 'second':
            result.setTime(result.getTime() + amount * SECOND);
            break;
            
        case 'millisecond':
            result.setTime(result.getTime() + amount);
            break;
            
        default:
            logger.warn(`Unknown time unit: ${unit}`);
    }
    
    return result;
}

/**
 * Subtract time from a date
 * @param {Date|string} date - The date to subtract from
 * @param {number} amount - The amount to subtract
 * @param {string} unit - The unit of time ('year', 'month', 'week', 'day', 'hour', 'minute', 'second')
 * @returns {Date} The new date
 */
export function subtract(date, amount, unit) {
    return add(date, -amount, unit);
}

/**
 * Get the difference between two dates in the specified unit
 * @param {Date|string} date1 - The first date
 * @param {Date|string} [date2=new Date()] - The second date (defaults to now)
 * @param {string} [unit='millisecond'] - The unit of time ('year', 'month', 'week', 'day', 'hour', 'minute', 'second')
 * @returns {number} The difference in the specified unit
 */
export function difference(date1, date2 = new Date(), unit = 'millisecond') {
    const d1 = parseDate(date1);
    const d2 = parseDate(date2);
    
    if (isNaN(d1.getTime()) || isNaN(d2.getTime())) {
        return NaN;
    }
    
    const diffMs = d2 - d1;
    
    switch (unit.toLowerCase()) {
        case 'year':
            return d2.getFullYear() - d1.getFullYear();
            
        case 'month':
            return (d2.getFullYear() - d1.getFullYear()) * 12 + 
                   (d2.getMonth() - d1.getMonth());
                   
        case 'week':
            return Math.floor(diffMs / WEEK);
            
        case 'day':
            return Math.floor(diffMs / DAY);
            
        case 'hour':
            return Math.floor(diffMs / HOUR);
            
        case 'minute':
            return Math.floor(diffMs / MINUTE);
            
        case 'second':
            return Math.floor(diffMs / SECOND);
            
        case 'millisecond':
        default:
            return diffMs;
    }
}

/**
 * Check if a date is before another date
 * @param {Date|string} date - The date to check
 * @param {Date|string} [compareDate=new Date()] - The date to compare against (defaults to now)
 * @returns {boolean} True if the date is before the compare date
 */
export function isBefore(date, compareDate = new Date()) {
    const d = parseDate(date);
    const compare = parseDate(compareDate);
    
    if (isNaN(d.getTime()) || isNaN(compare.getTime())) {
        return false;
    }
    
    return d < compare;
}

/**
 * Check if a date is after another date
 * @param {Date|string} date - The date to check
 * @param {Date|string} [compareDate=new Date()] - The date to compare against (defaults to now)
 * @returns {boolean} True if the date is after the compare date
 */
export function isAfter(date, compareDate = new Date()) {
    const d = parseDate(date);
    const compare = parseDate(compareDate);
    
    if (isNaN(d.getTime()) || isNaN(compare.getTime())) {
        return false;
    }
    
    return d > compare;
}

/**
 * Check if a date is between two other dates
 * @param {Date|string} date - The date to check
 * @param {Date|string} startDate - The start date
 * @param {Date|string} endDate - The end date
 * @param {string} [unit] - The unit of time to compare
 * @param {string} [inclusivity='[)'] - The inclusivity of the comparison
 * @returns {boolean} True if the date is between the start and end dates
 */
export function isBetween(date, startDate, endDate, unit, inclusivity = '[)') {
    const d = parseDate(date);
    const start = parseDate(startDate);
    const end = parseDate(endDate);
    
    if (isNaN(d.getTime()) || isNaN(start.getTime()) || isNaN(end.getTime())) {
        return false;
    }
    
    // If unit is provided, compare only the specified unit
    if (unit) {
        const startValue = startOf(start, unit).getTime();
        const endValue = startOf(end, unit).getTime();
        const value = startOf(d, unit).getTime();
        
        switch (inclusivity) {
            case '()': return value > startValue && value < endValue;
            case '[)': return value >= startValue && value < endValue;
            case '(]': return value > startValue && value <= endValue;
            case '[]': return value >= startValue && value <= endValue;
            default: return false;
        }
    }
    
    // Otherwise, do a simple date comparison
    switch (inclusivity) {
        case '()': return d > start && d < end;
        case '[)': return d >= start && d < end;
        case '(]': return d > start && d <= end;
        case '[]': return d >= start && d <= end;
        default: return false;
    }
}

/**
 * Check if a date is today
 * @param {Date|string} date - The date to check
 * @returns {boolean} True if the date is today
 */
export function isToday(date) {
    const d = parseDate(date);
    if (isNaN(d.getTime())) return false;
    
    const today = new Date();
    return d.getDate() === today.getDate() &&
           d.getMonth() === today.getMonth() &&
           d.getFullYear() === today.getFullYear();
}

/**
 * Check if a date is in the future
 * @param {Date|string} date - The date to check
 * @returns {boolean} True if the date is in the future
 */
export function isFuture(date) {
    return isAfter(date);
}

/**
 * Check if a date is in the past
 * @param {Date|string} date - The date to check
 * @returns {boolean} True if the date is in the past
 */
export function isPast(date) {
    return isBefore(date);
}

/**
 * Get the minimum date from an array of dates
 * @param {...(Date|string)} dates - The dates to compare
 * @returns {Date} The minimum date
 */
export function min(...dates) {
    const validDates = dates
        .map(parseDate)
        .filter(d => !isNaN(d.getTime()));
        
    if (validDates.length === 0) return new Date(NaN);
    
    return new Date(Math.min(...validDates.map(d => d.getTime())));
}

/**
 * Get the maximum date from an array of dates
 * @param {...(Date|string)} dates - The dates to compare
 * @returns {Date} The maximum date
 */
export function max(...dates) {
    const validDates = dates
        .map(parseDate)
        .filter(d => !isNaN(d.getTime()));
        
    if (validDates.length === 0) return new Date(NaN);
    
    return new Date(Math.max(...validDates.map(d => d.getTime())));
}

/**
 * Check if a value is a valid date
 * @param {*} value - The value to check
 * @returns {boolean} True if the value is a valid date
 */
export function isValidDate(value) {
    if (!value) return false;
    
    const date = parseDate(value);
    return !isNaN(date.getTime());
}

// Export constants
export {
    FORMATS,
    WEEKDAYS,
    WEEKDAYS_SHORT,
    WEEKDAYS_MIN,
    MONTHS,
    MONTHS_SHORT,
    SECOND,
    MINUTE,
    HOUR,
    DAY,
    WEEK
};

// Export a default object with all functions for convenience
export default {
    // Core functions
    formatDate,
    parseDate,
    startOf,
    add,
    subtract,
    difference,
    
    // Comparison functions
    isBefore,
    isAfter,
    isBetween,
    isToday,
    isFuture,
    isPast,
    
    // Utility functions
    min,
    max,
    isValidDate,
    
    // Constants
    FORMATS,
    WEEKDAYS,
    WEEKDAYS_SHORT,
    WEEKDAYS_MIN,
    MONTHS,
    MONTHS_SHORT,
    SECOND,
    MINUTE,
    HOUR,
    DAY,
    WEEK
};
