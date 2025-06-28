/**
 * Appearance Manager
 * Handles appearance-related functionality including:
 * - Font size adjustments
 * - Line height adjustments
 * - Font family changes
 * - High contrast mode
 * - Reduced motion preference
 */

class AppearanceManager {
  constructor() {
    // DOM Elements
    this.selectors = {
      fontSize: 'select[name="fontSize"]',
      lineHeight: 'select[name="lineHeight"]',
      fontFamily: 'select[name="fontFamily"]',
      highContrast: 'input[name="highContrast"]',
      reduceMotion: 'input[name="reduceMotion"]',
      html: 'html',
      body: 'body'
    };
    
    // Default values
    this.defaults = {
      fontSize: 'medium',
      lineHeight: 'normal',
      fontFamily: 'sans',
      highContrast: false,
      reduceMotion: false
    };
    
    // Initialize
    this.init();
  }
  
  init() {
    // Cache DOM elements
    this.cacheElements();
    
    // Load saved preferences
    this.loadPreferences();
    
    // Set up event listeners
    this.setupEventListeners();
    
    // Apply initial styles
    this.applyStyles();
  }
  
  cacheElements() {
    // Cache form controls
    this.elements = {};
    Object.entries(this.selectors).forEach(([key, selector]) => {
      this.elements[key] = document.querySelector(selector);
    });
  }
  
  setupEventListeners() {
    // Font size change
    if (this.elements.fontSize) {
      this.elements.fontSize.addEventListener('change', (e) => {
        this.setFontSize(e.target.value);
        this.savePreferences();
      });
    }
    
    // Line height change
    if (this.elements.lineHeight) {
      this.elements.lineHeight.addEventListener('change', (e) => {
        this.setLineHeight(e.target.value);
        this.savePreferences();
      });
    }
    
    // Font family change
    if (this.elements.fontFamily) {
      this.elements.fontFamily.addEventListener('change', (e) => {
        this.setFontFamily(e.target.value);
        this.savePreferences();
      });
    }
    
    // High contrast toggle
    if (this.elements.highContrast) {
      this.elements.highContrast.addEventListener('change', (e) => {
        this.toggleHighContrast(e.target.checked);
        this.savePreferences();
      });
    }
    
    // Reduce motion toggle
    if (this.elements.reduceMotion) {
      this.elements.reduceMotion.addEventListener('change', (e) => {
        this.toggleReduceMotion(e.target.checked);
        this.savePreferences();
      });
    }
    
    // Listen for system preference changes
    this.setupMediaQueryListeners();
  }
  
  setupMediaQueryListeners() {
    // Check for system preference for reduced motion
    const motionQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
    motionQuery.addEventListener('change', () => {
      this.toggleReduceMotion(motionQuery.matches);
    });
    
    // Initial check
    if (motionQuery.matches) {
      this.toggleReduceMotion(true);
    }
  }
  
  // Style application methods
  setFontSize(size) {
    const sizes = {
      'small': '14px',
      'medium': '16px',
      'large': '18px',
      'xlarge': '20px'
    };
    
    if (this.elements.html && sizes[size]) {
      this.elements.html.style.fontSize = sizes[size];
      
      // Update the select element to reflect the current value
      if (this.elements.fontSize) {
        this.elements.fontSize.value = size;
      }
    }
  }
  
  setLineHeight(height) {
    const heights = {
      'tight': '1.3',
      'normal': '1.6',
      'loose': '2.0'
    };
    
    if (this.elements.body && heights[height]) {
      this.elements.body.style.lineHeight = heights[height];
      
      // Update the select element to reflect the current value
      if (this.elements.lineHeight) {
        this.elements.lineHeight.value = height;
      }
    }
  }
  
  setFontFamily(family) {
    const families = {
      'system': '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif',
      'sans': '"SF Pro Display", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif',
      'serif': 'Georgia, "Times New Roman", Times, serif',
      'mono': '"SF Mono", "Roboto Mono", "Fira Code", "Fira Mono", "Droid Sans Mono", monospace'
    };
    
    if (this.elements.body && families[family]) {
      this.elements.body.style.fontFamily = families[family];
      
      // Update the select element to reflect the current value
      if (this.elements.fontFamily) {
        this.elements.fontFamily.value = family;
      }
    }
  }
  
  toggleHighContrast(enable) {
    if (this.elements.body) {
      if (enable) {
        this.elements.body.classList.add('high-contrast');
      } else {
        this.elements.body.classList.remove('high-contrast');
      }
      
      // Update the checkbox to reflect the current state
      if (this.elements.highContrast) {
        this.elements.highContrast.checked = enable;
      }
    }
  }
  
  toggleReduceMotion(enable) {
    if (this.elements.html) {
      if (enable) {
        this.elements.html.classList.add('reduce-motion');
      } else {
        this.elements.html.classList.remove('reduce-motion');
      }
      
      // Update the checkbox to reflect the current state
      if (this.elements.reduceMotion) {
        this.elements.reduceMotion.checked = enable;
      }
    }
  }
  
  // Preferences management
  savePreferences() {
    const preferences = {
      fontSize: this.elements.fontSize ? this.elements.fontSize.value : this.defaults.fontSize,
      lineHeight: this.elements.lineHeight ? this.elements.lineHeight.value : this.defaults.lineHeight,
      fontFamily: this.elements.fontFamily ? this.elements.fontFamily.value : this.defaults.fontFamily,
      highContrast: this.elements.highContrast ? this.elements.highContrast.checked : this.defaults.highContrast,
      reduceMotion: this.elements.reduceMotion ? this.elements.reduceMotion.checked : this.defaults.reduceMotion
    };
    
    try {
      localStorage.setItem('appearancePreferences', JSON.stringify(preferences));
    } catch (e) {
      console.warn('Could not save appearance preferences to localStorage', e);
    }
  }
  
  loadPreferences() {
    try {
      const saved = localStorage.getItem('appearancePreferences');
      if (saved) {
        const preferences = JSON.parse(saved);
        
        // Apply each preference
        if (preferences.fontSize) this.setFontSize(preferences.fontSize);
        if (preferences.lineHeight) this.setLineHeight(preferences.lineHeight);
        if (preferences.fontFamily) this.setFontFamily(preferences.fontFamily);
        if (preferences.highContrast !== undefined) this.toggleHighContrast(preferences.highContrast);
        if (preferences.reduceMotion !== undefined) this.toggleReduceMotion(preferences.reduceMotion);
      }
    } catch (e) {
      console.warn('Could not load appearance preferences', e);
    }
  }
  
  applyStyles() {
    // Apply any initial styles if needed
    const computedStyle = window.getComputedStyle(document.documentElement);
    
    // If no font size is set, apply the default
    if (!computedStyle.getPropertyValue('--base-font-size')) {
      this.setFontSize(this.defaults.fontSize);
    }
    
    // If no line height is set, apply the default
    if (!computedStyle.getPropertyValue('--line-height')) {
      this.setLineHeight(this.defaults.lineHeight);
    }
    
    // If no font family is set, apply the default
    if (!computedStyle.getPropertyValue('--font-family')) {
      this.setFontFamily(this.defaults.fontFamily);
    }
  }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
  window.appearanceManager = new AppearanceManager();
});
