// Main Application Initialization

// Wait for the DOM to be fully loaded
document.addEventListener('DOMContentLoaded', () => {
  console.log('Initializing documentation...');
  
  // Initialize Docsify first
  initDocsify();
  
  // Initialize managers after Docsify is ready
  window.$docsify = window.$docsify || {};
  window.$docsify.plugins = (window.$docsify.plugins || []).concat(function(hook, vm) {
    hook.doneEach(function() {
      // Initialize sidebar manager after content is loaded
      if (!window.sidebarManager) {
        window.sidebarManager = new SidebarManager();
      }
      
      // Initialize theme manager
      if (!window.themeManager) {
        window.themeManager = new ThemeManager();
      }
      
      // Initialize appearance manager
      if (!window.appearanceManager) {
        window.appearanceManager = new AppearanceManager();
      }
      
      // Initialize plugins
      if (window.initPlugins) {
        window.initPlugins();
      }
      
      // Force update of the sidebar
      if (window.sidebarManager) {
        setTimeout(() => {
          window.sidebarManager.enhanceTreeView();
        }, 100);
      }
    });
  });
  
  console.log('Documentation initialized');
});

// Initialize Docsify
function initDocsify() {
  // Configuration is in config.js
  console.log('Initializing Docsify...');
  
  // Set up mutation observer to handle dynamic content
  setupMutationObserver();
  
  // Add event listeners for Docsify events
  setupDocsifyEvents();
  
  // Initialize Docsify if not already initialized
  if (!window.Docsify) {
    console.error('Docsify not loaded! Make sure docsify.min.js is included before main.js');
    return;
  }
  
  // Manually trigger a re-render
  console.log('Triggering Docsify initialization...');
  const app = document.getElementById('app');
  if (app) {
    window.Docsify.dom.find('body').removeClass('ready');
    window.Docsify.init(app);
  }
}

// Set up mutation observer to handle dynamically loaded content
function setupMutationObserver() {
  const observer = new MutationObserver((mutations) => {
    mutations.forEach((mutation) => {
      // Handle new nodes added to the DOM
      if (mutation.addedNodes.length) {
        // Re-apply syntax highlighting
        if (window.Prism) {
          window.Prism.highlightAll();
        }
        
        // Update any custom components
        updateCustomComponents();
      }
    });
  });
  
  // Start observing the document with the configured parameters
  observer.observe(document.body, { 
    childList: true, 
    subtree: true 
  });
}

// Set up Docsify event listeners
function setupDocsifyEvents() {
  // This will be called when the docsify script is loaded
  if (window.Docsify) {
    // Hook into Docsify's lifecycle
    window.Docsify.hooks.beforeEach((content) => {
      // Process content before it's rendered
      return content;
    });
    
    window.Docsify.hooks.doneEach(() => {
      // Code to run after each route change
      updateActiveNavItem();
      scrollToAnchor();
      updateCustomComponents();
    });
    
    window.Docsify.hooks.mounted(() => {
      // Code to run when the docsify instance is mounted
      console.log('Docsify mounted');
    });
  }
}

// Update active navigation item
function updateActiveNavItem() {
  const currentPath = window.location.hash.substring(1) || '/';
  
  // Remove active class from all nav items
  document.querySelectorAll('.sidebar-nav a').forEach(link => {
    link.classList.remove('active');
  });
  
  // Add active class to current nav item
  const currentLink = document.querySelector(`.sidebar-nav a[href="${currentPath}"]`);
  if (currentLink) {
    currentLink.classList.add('active');
    
    // Expand parent sections
    let parent = currentLink.parentElement;
    while (parent && !parent.classList.contains('sidebar-nav')) {
      if (parent.tagName === 'LI' && parent.querySelector('ul')) {
        parent.classList.remove('collapsed');
      }
      parent = parent.parentElement;
    }
  }
}

// Scroll to anchor if present in URL
function scrollToAnchor() {
  const hash = window.location.hash;
  if (hash) {
    const id = hash.substring(1);
    const element = document.getElementById(id);
    if (element) {
      // Small delay to ensure the page has rendered
      setTimeout(() => {
        element.scrollIntoView({ behavior: 'smooth' });
      }, 100);
    }
  }
}

// Update custom components
function updateCustomComponents() {
  // Add any custom component updates here
  // For example, adding tooltips, custom buttons, etc.
  
  // Example: Add tooltips to elements with data-tooltip attribute
  document.querySelectorAll('[data-tooltip]').forEach(element => {
    element.setAttribute('title', element.getAttribute('data-tooltip'));
  });
}

// Utility function to load scripts dynamically
function loadScript(url, callback) {
  return new Promise((resolve, reject) => {
    const script = document.createElement('script');
    script.src = url;
    script.onload = () => {
      if (callback) callback();
      resolve();
    };
    script.onerror = () => {
      console.error(`Failed to load script: ${url}`);
      reject(new Error(`Script load error for ${url}`));
    };
    document.body.appendChild(script);
  });
}

// Utility function to load stylesheets dynamically
function loadStylesheet(url) {
  return new Promise((resolve, reject) => {
    const link = document.createElement('link');
    link.rel = 'stylesheet';
    link.href = url;
    link.onload = resolve;
    link.onerror = () => {
      console.error(`Failed to load stylesheet: ${url}`);
      reject(new Error(`Stylesheet load error for ${url}`));
    };
    document.head.appendChild(link);
  });
}

// Make utility functions available globally
window.utils = {
  loadScript,
  loadStylesheet
};
