// Docsify Plugins Configuration

// This file initializes and configures all Docsify plugins

// Wait for Docsify to be ready
document.addEventListener('DOMContentLoaded', () => {
  // Initialize plugins after Docsify is loaded
  window.$docsify = window.$docsify || {};
  
  // Ensure plugins array exists
  window.$docsify.plugins = (window.$docsify.plugins || []).concat([
    // Search Plugin
    function(hook, vm) {
      hook.init(() => {
        // Load search plugin
        const searchPlugin = document.createElement('script');
        searchPlugin.src = 'https://cdn.jsdelivr.net/npm/docsify/lib/plugins/search.min.js';
        document.body.appendChild(searchPlugin);
      });
    },
    
    // Copy Code Plugin
    function(hook, vm) {
      hook.init(() => {
        // Load copy code plugin
        const copyCodePlugin = document.createElement('script');
        copyCodePlugin.src = 'https://cdn.jsdelivr.net/npm/docsify-copy-code';
        document.body.appendChild(copyCodePlugin);
      });
    },
    
    // Zoom Image Plugin
    function(hook, vm) {
      hook.init(() => {
        // Load zoom image plugin
        const zoomImage = document.createElement('script');
        zoomImage.src = 'https://cdn.jsdelivr.net/npm/docsify-zoom-image';
        document.body.appendChild(zoomImage);
      });
    },
    
    // Sidebar Collapse Plugin
    function(hook, vm) {
      hook.init(() => {
        // Load sidebar collapse plugin
        const sidebarCollapse = document.createElement('script');
        sidebarCollapse.src = 'https://cdn.jsdelivr.net/npm/docsify-sidebar-collapse/dist/docsify-sidebar-collapse.min.js';
        document.body.appendChild(sidebarCollapse);
      });
    },
    
    // Pagination Plugin
    function(hook, vm) {
      hook.init(() => {
        // Load pagination plugin
        const pagination = document.createElement('script');
        pagination.src = 'https://cdn.jsdelivr.net/npm/docsify-pagination/dist/docsify-pagination.min.js';
        document.body.appendChild(pagination);
      });
    },
    
    // Edit on GitHub Plugin
    function(hook, vm) {
      hook.init(() => {
        if (window.$docsify.repo) {
          const editOnGithub = document.createElement('script');
          editOnGithub.src = 'https://cdn.jsdelivr.net/npm/docsify/lib/plugins/edit-on-github.js';
          document.body.appendChild(editOnGithub);
        }
      });
    },
    
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
        // Load Prism.js for syntax highlighting
        const prismCss = document.createElement('link');
        prismCss.rel = 'stylesheet';
        prismCss.href = 'https://cdn.jsdelivr.net/npm/prismjs@1.29.0/themes/prism-tomorrow.min.css';
        document.head.appendChild(prismCss);
        
        const prismJs = document.createElement('script');
        prismJs.src = 'https://cdn.jsdelivr.net/npm/prismjs@1.29.0/prism.min.js';
        document.body.appendChild(prismJs);
        
        // Load additional language support
        const languages = ['javascript', 'python', 'bash', 'json', 'yaml'];
        languages.forEach(lang => {
          const script = document.createElement('script');
          script.src = `https://cdn.jsdelivr.net/npm/prismjs@1.29.0/components/prism-${lang}.min.js`;
          document.body.appendChild(script);
        });
      });
      
      hook.doneEach(() => {
        // Re-apply syntax highlighting after content is loaded
        if (window.Prism) {
          window.Prism.highlightAll();
        }
      });
    }
  ]);
  
  // Initialize Docsify
  if (window.Docsify) {
    window.Docsify.init();
  }
});
