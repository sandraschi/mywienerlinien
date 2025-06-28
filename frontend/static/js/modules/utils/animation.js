/**
 * Animation and transition utilities
 */

import { logger } from './logger.js';

// Default animation options
const DEFAULT_OPTIONS = {
    duration: 300,
    easing: 'ease-in-out',
    fill: 'forwards',
    delay: 0,
    iterations: 1,
    direction: 'normal'
};

/**
 * Animate an element using the Web Animations API
 * @param {HTMLElement} element - The element to animate
 * @param {Array|Object} keyframes - Keyframe array or object
 * @param {Object} [options] - Animation options
 * @returns {Animation} The animation object
 */
export function animateElement(element, keyframes, options = {}) {
    if (!element || !element.animate) {
        logger.warn('Animation not supported or invalid element');
        return null;
    }
    
    try {
        const mergedOptions = { ...DEFAULT_OPTIONS, ...options };
        
        // Convert keyframes object to array if needed
        let processedKeyframes = keyframes;
        if (!Array.isArray(keyframes)) {
            processedKeyframes = [keyframes];
        }
        
        // Start the animation
        const animation = element.animate(processedKeyframes, mergedOptions);
        
        // Handle animation end
        if (options.onComplete) {
            animation.onfinish = options.onComplete;
        }
        
        // Handle animation cancel
        if (options.onCancel) {
            animation.oncancel = options.onCancel;
        }
        
        return animation;
    } catch (error) {
        logger.error('Error animating element:', error);
        return null;
    }
}

/**
 * Fade in an element
 * @param {HTMLElement} element - The element to fade in
 * @param {Object} [options] - Animation options
 * @returns {Animation} The animation object
 */
export function fadeIn(element, options = {}) {
    if (!element) return null;
    
    // Ensure element is visible and has opacity 0
    element.style.display = options.display || 'block';
    element.style.opacity = '0';
    
    // Start fade in animation
    return animateElement(
        element,
        { opacity: [0, 1] },
        {
            ...options,
            onComplete: () => {
                element.style.opacity = ''; // Reset inline style
                if (options.onComplete) options.onComplete();
            }
        }
    );
}

/**
 * Fade out an element
 * @param {HTMLElement} element - The element to fade out
 * @param {Object} [options] - Animation options
 * @returns {Animation} The animation object
 */
export function fadeOut(element, options = {}) {
    if (!element) return null;
    
    // Store original display value
    const originalDisplay = window.getComputedStyle(element).display;
    
    // Start fade out animation
    return animateElement(
        element,
        { opacity: [window.getComputedStyle(element).opacity || 1, 0] },
        {
            ...options,
            onComplete: () => {
                element.style.opacity = ''; // Reset inline style
                if (options.hideAfter) {
                    element.style.display = 'none';
                }
                if (options.onComplete) options.onComplete();
            }
        }
    );
}

/**
 * Slide an element in from a direction
 * @param {HTMLElement} element - The element to slide in
 * @param {string} [from='left'] - Direction to slide from ('top', 'right', 'bottom', 'left')
 * @param {Object} [options] - Animation options
 * @returns {Animation} The animation object
 */
export function slideIn(element, from = 'left', options = {}) {
    if (!element) return null;
    
    // Ensure element is visible and positioned
    element.style.display = options.display || 'block';
    element.style.position = 'relative';
    
    // Set initial position based on direction
    const translateMap = {
        top: 'translateY(-100%)',
        right: 'translateX(100%)',
        bottom: 'translateY(100%)',
        left: 'translateX(-100%)'
    };
    
    const translate = translateMap[from] || translateMap.left;
    
    // Start slide in animation
    return animateElement(
        element,
        [
            { transform: `${translate}`, opacity: 0 },
            { transform: 'translate(0, 0)', opacity: 1 }
        ],
        {
            ...options,
            onComplete: () => {
                element.style.transform = ''; // Reset inline style
                element.style.opacity = '';
                if (options.onComplete) options.onComplete();
            }
        }
    );
}

/**
 * Slide an element out to a direction
 * @param {HTMLElement} element - The element to slide out
 * @param {string} [to='right'] - Direction to slide to ('top', 'right', 'bottom', 'left')
 * @param {Object} [options] - Animation options
 * @returns {Animation} The animation object
 */
export function slideOut(element, to = 'right', options = {}) {
    if (!element) return null;
    
    // Store original styles
    const originalStyles = {
        position: element.style.position,
        transform: element.style.transform,
        opacity: element.style.opacity,
        display: element.style.display
    };
    
    // Ensure element is positioned
    element.style.position = 'relative';
    
    // Set target position based on direction
    const translateMap = {
        top: 'translateY(-100%)',
        right: 'translateX(100%)',
        bottom: 'translateY(100%)',
        left: 'translateX(-100%)'
    };
    
    const translate = translateMap[to] || translateMap.right;
    
    // Start slide out animation
    return animateElement(
        element,
        [
            { transform: 'translate(0, 0)', opacity: 1 },
            { transform: translate, opacity: 0 }
        ],
        {
            ...options,
            onComplete: () => {
                // Reset styles
                Object.assign(element.style, originalStyles);
                if (options.hideAfter) {
                    element.style.display = 'none';
                }
                if (options.onComplete) options.onComplete();
            }
        }
    );
}

/**
 * Toggle element visibility with a fade animation
 * @param {HTMLElement} element - The element to toggle
 * @param {boolean} [show] - Force show or hide
 * @param {Object} [options] - Animation options
 * @returns {Animation} The animation object
 */
export function fadeToggle(element, show, options = {}) {
    if (show === undefined) {
        show = window.getComputedStyle(element).display === 'none';
    }
    
    if (show) {
        return fadeIn(element, options);
    } else {
        return fadeOut(element, { ...options, hideAfter: true });
    }
}

/**
 * Toggle element visibility with a slide animation
 * @param {HTMLElement} element - The element to toggle
 * @param {string} [direction='left'] - Slide direction
 * @param {boolean} [show] - Force show or hide
 * @param {Object} [options] - Animation options
 * @returns {Animation} The animation object
 */
export function slideToggle(element, direction = 'left', show, options = {}) {
    if (show === undefined) {
        show = window.getComputedStyle(element).display === 'none';
    }
    
    if (show) {
        return slideIn(element, direction, options);
    } else {
        return slideOut(element, direction, { ...options, hideAfter: true });
    }
}

/**
 * Create a pulse animation effect
 * @param {HTMLElement} element - The element to pulse
 * @param {Object} [options] - Animation options
 * @returns {Animation} The animation object
 */
export function pulse(element, options = {}) {
    return animateElement(
        element,
        [
            { transform: 'scale(1)', opacity: 1 },
            { transform: 'scale(1.05)', opacity: 0.7 },
            { transform: 'scale(1)', opacity: 1 }
        ],
        {
            duration: 600,
            iterations: options.iterations || 2,
            easing: 'ease-in-out',
            ...options
        }
    );
}

/**
 * Create a shake animation effect
 * @param {HTMLElement} element - The element to shake
 * @param {Object} [options] - Animation options
 * @returns {Animation} The animation object
 */
export function shake(element, options = {}) {
    return animateElement(
        element,
        [
            { transform: 'translateX(0)' },
            { transform: 'translateX(-5px)' },
            { transform: 'translateX(5px)' },
            { transform: 'translateX(-5px)' },
            { transform: 'translateX(5px)' },
            { transform: 'translateX(0)' }
        ],
        {
            duration: 400,
            iterations: 1,
            easing: 'ease-in-out',
            ...options
        }
    );
}

/**
 * Create a bounce animation effect
 * @param {HTMLElement} element - The element to bounce
 * @param {Object} [options] - Animation options
 * @returns {Animation} The animation object
 */
export function bounce(element, options = {}) {
    return animateElement(
        element,
        [
            { transform: 'translateY(0)' },
            { transform: 'translateY(-20px)' },
            { transform: 'translateY(0)' },
            { transform: 'translateY(-10px)' },
            { transform: 'translateY(0)' }
        ],
        {
            duration: 800,
            iterations: options.iterations || 1,
            easing: 'cubic-bezier(0.25, 0.1, 0.25, 1)',
            ...options
        }
    );
}

/**
 * Create a flip animation effect
 * @param {HTMLElement} element - The element to flip
 * @param {number} [degrees=180] - Degrees to rotate (default: 180)
 * @param {Object} [options] - Animation options
 * @returns {Animation} The animation object
 */
export function flip(element, degrees = 180, options = {}) {
    return animateElement(
        element,
        [
            { transform: 'rotateY(0)' },
            { transform: `rotateY(${degrees}deg)` }
        ],
        {
            duration: 500,
            fill: 'forwards',
            easing: 'ease-in-out',
            ...options
        }
    );
}

/**
 * Reset all animations on an element
 * @param {HTMLElement} element - The element to reset
 */
export function resetAnimations(element) {
    if (!element) return;
    
    // Cancel all running animations
    if (element.getAnimations) {
        const animations = element.getAnimations();
        for (const animation of animations) {
            animation.cancel();
        }
    }
    
    // Reset transform and opacity
    element.style.transform = '';
    element.style.opacity = '';
}

/**
 * Wait for all animations on an element to complete
 * @param {HTMLElement} element - The element to wait for
 * @returns {Promise} Promise that resolves when all animations complete
 */
export function waitForAnimations(element) {
    if (!element || !element.getAnimations) {
        return Promise.resolve();
    }
    
    const animations = element.getAnimations();
    return Promise.all(animations.map(animation => animation.finished));
}

// Export a default object with all functions for convenience
export default {
    animateElement,
    fadeIn,
    fadeOut,
    fadeToggle,
    slideIn,
    slideOut,
    slideToggle,
    pulse,
    shake,
    bounce,
    flip,
    resetAnimations,
    waitForAnimations
};
