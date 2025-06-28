// Main Application Initialization

// Wait for the DOM to be fully loaded
document.addEventListener('DOMContentLoaded', () => {
  console.log('Initializing documentation...');
  
  // Initialize managers
  window.themeManager = new ThemeManager();
  window.sidebarManager = new SidebarManager();
  
  // Initialize Docsify
  initDocsify();
  
  // Add any additional initialization code here
  console.log('Documentation initialized');
});

// Initialize Docsify
function initDocsify() {
  // Configuration is in config.js
  
  // Add window.$docsify if it doesn't exist
  window.$docsify = window.$docsify || {};
  
  // Set up mutation observer to handle dynamic content
  setupMutationObserver();
  
  // Add event listeners for Docsify events
  setupDocsifyEvents();
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
