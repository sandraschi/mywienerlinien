// Docsify Plugins Configuration

// Wait for the DOM to be fully loaded
document.addEventListener('DOMContentLoaded', () => {
  // Ensure $docsify exists
  window.$docsify = window.$docsify || {};
  
  // Initialize plugins array if it doesn't exist
  window.$docsify.plugins = (window.$docsify.plugins || []).concat([
    // Search Plugin (built into Docsify)
    
    // Copy Code Plugin
    function(hook, vm) {
      hook.mounted(() => {
        // Plugin is loaded via script tag in index.html
      });
    },
    
    // Zoom Image Plugin
    function(hook, vm) {
      hook.mounted(() => {
        // Plugin is loaded via script tag in index.html
      });
    },
    
    // Sidebar Collapse Plugin
    function(hook, vm) {
      hook.mounted(() => {
        // Plugin is loaded via script tag in index.html
      });
    },
    
    // Edit on GitHub Plugin (handled by Docsify core)
    
    // Custom plugin for handling external links
    function(hook, vm) {
      hook.doneEach(() => {
        // Add external link icon to all external links
        document.querySelectorAll('a[href^="http"]:not([href*="' + window.location.host + '"])')
          .forEach(link => {
            link.setAttribute('target', '_blank');
            link.setAttribute('rel', 'noopener');
            
            // Add external link icon
            if (!link.querySelector('.external-icon')) {
              const icon = document.createElement('span');
              icon.className = 'external-icon';
              icon.innerHTML = ' ↗';
              icon.setAttribute('aria-hidden', 'true');
              link.appendChild(icon);
            }
          });
      });
    },
    
    // Custom plugin for syntax highlighting
    function(hook, vm) {
      hook.mounted(() => {
        // Prism.js is loaded via script and link tags in index.html
      });
      
      hook.doneEach(() => {
        // Re-apply syntax highlighting after content is loaded
        if (window.Prism) {
          window.Prism.highlightAll();
        }
      });
    }
  ]);
  
  // Initialize Docsify if it's available
  if (window.Docsify) {
    window.Docsify.init();
  }
});
