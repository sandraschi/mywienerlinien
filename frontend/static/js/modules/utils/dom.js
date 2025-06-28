/**
 * DOM manipulation utilities
 */

import { logger } from './logger.js';

/**
 * Create a new DOM element with attributes and children
 * @param {string} tag - The HTML tag name
 * @param {Object} [attrs] - Element attributes
 * @param {string|HTMLElement|Array} [children] - Child elements or text content
 * @returns {HTMLElement} The created element
 */
export function createElement(tag, attrs = {}, children = []) {
    try {
        const element = document.createElement(tag);
        
        // Set attributes
        for (const [key, value] of Object.entries(attrs)) {
            if (value === null || value === undefined) continue;
            
            if (key === 'className') {
                element.className = value;
            } else if (key === 'style' && typeof value === 'object') {
                Object.assign(element.style, value);
            } else if (key.startsWith('data-')) {
                element.setAttribute(key, value);
            } else if (key === 'html') {
                element.innerHTML = value;
            } else if (typeof value === 'function' && key.startsWith('on')) {
                const eventType = key.substring(2).toLowerCase();
                element.addEventListener(eventType, value);
            } else if (value !== false) {
                element.setAttribute(key, value === true ? '' : value);
            }
        }
        
        // Add children
        const childrenArray = Array.isArray(children) ? children : [children];
        
        for (const child of childrenArray) {
            if (!child && child !== 0) continue;
            
            if (typeof child === 'string' || typeof child === 'number') {
                element.appendChild(document.createTextNode(child));
            } else if (child instanceof HTMLElement) {
                element.appendChild(child);
            } else if (child instanceof NodeList || Array.isArray(child)) {
                child.forEach(node => {
                    if (node) element.appendChild(node);
                });
            }
        }
        
        return element;
    } catch (error) {
        logger.error('Failed to create element:', error);
        throw error;
    }
}

/**
 * Get an element by selector, with optional parent
 * @param {string} selector - CSS selector
 * @param {HTMLElement} [parent=document] - Parent element to search within
 * @returns {HTMLElement|null} The found element or null
 */
export function $(selector, parent = document) {
    try {
        return parent.querySelector(selector);
    } catch (error) {
        logger.error(`Failed to find element with selector '${selector}':`, error);
        return null;
    }
}

/**
 * Get all elements matching a selector, with optional parent
 * @param {string} selector - CSS selector
 * @param {HTMLElement} [parent=document] - Parent element to search within
 * @returns {NodeList} List of matching elements
 */
export function $$(selector, parent = document) {
    try {
        return parent.querySelectorAll(selector);
    } catch (error) {
        logger.error(`Failed to find elements with selector '${selector}':`, error);
        return [];
    }
}

/**
 * Add one or more classes to an element
 * @param {HTMLElement} element - The target element
 * @param {...string} classNames - Class names to add
 * @returns {HTMLElement} The element
 */
export function addClass(element, ...classNames) {
    if (!element || !element.classList) return element;
    
    try {
        element.classList.add(...classNames.filter(Boolean));
        return element;
    } catch (error) {
        logger.error('Failed to add class:', error);
        return element;
    }
}

/**
 * Remove one or more classes from an element
 * @param {HTMLElement} element - The target element
 * @param {...string} classNames - Class names to remove
 * @returns {HTMLElement} The element
 */
export function removeClass(element, ...classNames) {
    if (!element || !element.classList) return element;
    
    try {
        element.classList.remove(...classNames.filter(Boolean));
        return element;
    } catch (error) {
        logger.error('Failed to remove class:', error);
        return element;
    }
}

/**
 * Toggle a class on an element
 * @param {HTMLElement} element - The target element
 * @param {string} className - Class name to toggle
 * @param {boolean} [force] - Force add or remove the class
 * @returns {HTMLElement} The element
 */
export function toggleClass(element, className, force) {
    if (!element || !element.classList) return element;
    
    try {
        element.classList.toggle(className, force);
        return element;
    } catch (error) {
        logger.error('Failed to toggle class:', error);
        return element;
    }
}

/**
 * Check if an element has a specific class
 * @param {HTMLElement} element - The target element
 * @param {string} className - Class name to check
 * @returns {boolean} True if the element has the class
 */
export function hasClass(element, className) {
    if (!element || !element.classList) return false;
    return element.classList.contains(className);
}

/**
 * Set or get the text content of an element
 * @param {HTMLElement} element - The target element
 * @param {string} [text] - Text to set (optional)
 * @returns {string|HTMLElement} The text content or the element
 */
export function text(element, text) {
    if (!element) return '';
    
    if (text === undefined) {
        return element.textContent || '';
    }
    
    try {
        element.textContent = text;
        return element;
    } catch (error) {
        logger.error('Failed to set text content:', error);
        return element;
    }
}

/**
 * Set or get the HTML content of an element
 * @param {HTMLElement} element - The target element
 * @param {string} [html] - HTML to set (optional)
 * @returns {string|HTMLElement} The HTML content or the element
 */
export function html(element, html) {
    if (!element) return '';
    
    if (html === undefined) {
        return element.innerHTML || '';
    }
    
    try {
        element.innerHTML = html;
        return element;
    } catch (error) {
        logger.error('Failed to set HTML content:', error);
        return element;
    }
}

/**
 * Set or get the value of a form element
 * @param {HTMLElement} element - The form element
 * @param {string} [value] - Value to set (optional)
 * @returns {string|HTMLElement} The value or the element
 */
export function val(element, value) {
    if (!element) return '';
    
    if (value === undefined) {
        return element.value || '';
    }
    
    try {
        element.value = value;
        return element;
    } catch (error) {
        logger.error('Failed to set value:', error);
        return element;
    }
}

/**
 * Show an element by removing the 'hidden' class and setting display to the specified value
 * @param {HTMLElement} element - The element to show
 * @param {string} [display=''] - Display value (e.g., 'block', 'flex', 'inline')
 * @returns {HTMLElement} The element
 */
export function show(element, display = '') {
    if (!element) return null;
    
    try {
        removeClass(element, 'hidden');
        
        if (display) {
            element.style.display = display;
        } else if (element.style.display === 'none') {
            element.style.display = ''; // Reset to default
        }
        
        return element;
    } catch (error) {
        logger.error('Failed to show element:', error);
        return element;
    }
}

/**
 * Hide an element by adding the 'hidden' class
 * @param {HTMLElement} element - The element to hide
 * @returns {HTMLElement} The element
 */
export function hide(element) {
    if (!element) return null;
    
    try {
        addClass(element, 'hidden');
        return element;
    } catch (error) {
        logger.error('Failed to hide element:', error);
        return element;
    }
}

/**
 * Toggle element visibility
 * @param {HTMLElement} element - The element to toggle
 * @param {boolean} [force] - Force show or hide
 * @returns {HTMLElement} The element
 */
export function toggle(element, force) {
    if (!element) return null;
    
    try {
        const isHidden = hasClass(element, 'hidden') || element.style.display === 'none';
        const shouldShow = force !== undefined ? force : isHidden;
        
        if (shouldShow) {
            return show(element);
        } else {
            return hide(element);
        }
    } catch (error) {
        logger.error('Failed to toggle element:', error);
        return element;
    }
}

/**
 * Add an event listener to an element
 * @param {HTMLElement|Window|Document} target - The target element
 * @param {string} event - The event name
 * @param {Function} handler - The event handler
 * @param {Object} [options] - Event listener options
 * @returns {Function} A function to remove the event listener
 */
export function on(target, event, handler, options) {
    if (!target || !event || !handler) return () => {};
    
    try {
        const wrappedHandler = (e) => {
            try {
                return handler(e);
            } catch (error) {
                logger.error(`Error in event handler for '${event}':`, error);
            }
        };
        
        target.addEventListener(event, wrappedHandler, options);
        
        // Return a function to remove the event listener
        return () => {
            target.removeEventListener(event, wrappedHandler, options);
        };
    } catch (error) {
        logger.error(`Failed to add event listener for '${event}':`, error);
        return () => {};
    }
}

/**
 * Remove an event listener from an element
 * @param {HTMLElement|Window|Document} target - The target element
 * @param {string} event - The event name
 * @param {Function} handler - The event handler
 * @param {Object} [options] - Event listener options
 */
export function off(target, event, handler, options) {
    if (!target || !event || !handler) return;
    
    try {
        target.removeEventListener(event, handler, options);
    } catch (error) {
        logger.error(`Failed to remove event listener for '${event}':`, error);
    }
}

/**
 * Trigger a custom event on an element
 * @param {HTMLElement|Window|Document} target - The target element
 * @param {string} event - The event name
 * @param {Object} [detail] - Event detail object
 * @param {boolean} [bubbles=true] - Whether the event bubbles
 * @returns {boolean} False if event is cancelable and one of the handlers called preventDefault()
 */
export function trigger(target, event, detail = {}, bubbles = true) {
    if (!target || !event) return false;
    
    try {
        const customEvent = new CustomEvent(event, {
            detail,
            bubbles,
            cancelable: true
        });
        
        return target.dispatchEvent(customEvent);
    } catch (error) {
        logger.error(`Failed to trigger event '${event}':`, error);
        return false;
    }
}

/**
 * Get the closest parent element matching a selector
 * @param {HTMLElement} element - The starting element
 * @param {string} selector - CSS selector to match
 * @param {HTMLElement} [context=document] - The context to search within
 * @returns {HTMLElement|null} The closest matching element or null
 */
export function closest(element, selector, context = document) {
    if (!element || !selector) return null;
    
    try {
        if (element.closest) {
            return element.closest(selector);
        }
        
        // Fallback for older browsers
        let el = element;
        while (el && el !== context) {
            if (el.matches(selector)) {
                return el;
            }
            el = el.parentElement;
        }
        
        return null;
    } catch (error) {
        logger.error('Failed to find closest element:', error);
        return null;
    }
}

/**
 * Check if an element matches a selector
 * @param {HTMLElement} element - The element to check
 * @param {string} selector - CSS selector to match
 * @returns {boolean} True if the element matches the selector
 */
export function matches(element, selector) {
    if (!element || !selector) return false;
    
    try {
        return (
            element.matches ||
            element.matchesSelector ||
            element.msMatchesSelector ||
            element.mozMatchesSelector ||
            element.webkitMatchesSelector ||
            element.oMatchesSelector
        ).call(element, selector);
    } catch (error) {
        logger.error('Failed to match selector:', error);
        return false;
    }
}

/**
 * Get the computed style of an element
 * @param {HTMLElement} element - The target element
 * @param {string} [property] - Specific CSS property to get
 * @returns {string|CSSStyleDeclaration} The computed style
 */
export function getStyle(element, property) {
    if (!element) return '';
    
    try {
        const style = window.getComputedStyle(element);
        return property ? style.getPropertyValue(property) : style;
    } catch (error) {
        logger.error('Failed to get computed style:', error);
        return '';
    }
}

/**
 * Set one or more CSS properties on an element
 * @param {HTMLElement} element - The target element
 * @param {string|Object} property - CSS property name or object of properties
 * @param {string} [value] - CSS value (if property is a string)
 * @returns {HTMLElement} The element
 */
export function css(element, property, value) {
    if (!element || !property) return element;
    
    try {
        if (typeof property === 'string') {
            element.style[property] = value;
        } else if (typeof property === 'object') {
            Object.assign(element.style, property);
        }
        
        return element;
    } catch (error) {
        logger.error('Failed to set CSS:', error);
        return element;
    }
}

/**
 * Get or set attributes on an element
 * @param {HTMLElement} element - The target element
 * @param {string|Object} name - Attribute name or object of attributes
 * @param {string} [value] - Attribute value (if name is a string)
 * @returns {string|HTMLElement} The attribute value or the element
 */
export function attr(element, name, value) {
    if (!element || !name) return element;
    
    try {
        // Get attribute value
        if (typeof name === 'string' && value === undefined) {
            return element.getAttribute(name);
        }
        
        // Set single attribute
        if (typeof name === 'string') {
            if (value === null || value === undefined) {
                element.removeAttribute(name);
            } else {
                element.setAttribute(name, value);
            }
        } 
        // Set multiple attributes
        else if (typeof name === 'object') {
            for (const [key, val] of Object.entries(name)) {
                if (val === null || val === undefined) {
                    element.removeAttribute(key);
                } else {
                    element.setAttribute(key, val);
                }
            }
        }
        
        return element;
    } catch (error) {
        logger.error('Failed to handle attributes:', error);
        return element;
    }
}

/**
 * Remove an attribute from an element
 * @param {HTMLElement} element - The target element
 * @param {string} name - Attribute name to remove
 * @returns {HTMLElement} The element
 */
export function removeAttr(element, name) {
    return attr(element, name, null);
}

/**
 * Check if an element has an attribute
 * @param {HTMLElement} element - The target element
 * @param {string} name - Attribute name to check
 * @returns {boolean} True if the element has the attribute
 */
export function hasAttr(element, name) {
    if (!element || !name) return false;
    return element.hasAttribute(name);
}

// Export a default object with all functions for convenience
export default {
    $,
    $$,
    addClass,
    attr,
    closest,
    createElement,
    css,
    getStyle,
    hasAttr,
    hasClass,
    hide,
    html,
    matches,
    off,
    on,
    removeAttr,
    removeClass,
    show,
    text,
    toggle,
    toggleClass,
    trigger,
    val
};
