// Main Application
class DocsApp {
  constructor() {
    this.config = window.docsConfig;
    this.initialized = false;
    
    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', () => this.init());
    } else {
      this.init();
    }
  }
  
  async init() {
    if (this.initialized) return;
    this.initialized = true;
    
    try {
      // Initialize components
      await this.loadPlugins();
      this.setupRouter();
      this.setupEventListeners();
      
      console.log('Documentation app initialized');
    } catch (error) {
      console.error('Failed to initialize app:', error);
    }
  }
  
  async loadPlugins() {
    // Load plugins based on config
    const plugins = [
      // Core plugins
      'search',
      'copy-code',
      'themeable',
      'sidebar-collapse',
      'pagination',
      'zoom-image'
    ];
    
    // Load each plugin
    for (const plugin of plugins) {
      try {
        await this.loadPlugin(plugin);
      } catch (error) {
        console.warn(`Failed to load plugin: ${plugin}`, error);
      }
    }
  }
  
  async loadPlugin(name) {
    return new Promise((resolve, reject) => {
      // In a real app, this would load the plugin from a CDN or local file
      console.log(`Loading plugin: ${name}`);
      // Simulate plugin loading
      setTimeout(resolve, 100);
    });
  }
  
  setupRouter() {
    // Simple hash-based router
    window.addEventListener('hashchange', () => this.handleRoute());
    this.handleRoute(); // Initial route
  }
  
  handleRoute() {
    const path = window.location.hash.slice(1) || '/';
    console.log('Route changed:', path);
    
    // Update active nav item
    document.querySelectorAll('.sidebar-nav a').forEach(link => {
      link.classList.toggle('active', link.getAttribute('href') === `#${path}`);
    });
    
    // In a real app, this would load the appropriate content
    this.loadContent(path);
  }
  
  async loadContent(path) {
    // In a real app, this would fetch the Markdown content
    const content = `
      # ${path === '/' ? 'Welcome' : path.slice(1).charAt(0).toUpperCase() + path.slice(2)}
      
      This is the ${path === '/' ? 'home' : path} page content.
      
      ## Features
      - Responsive design
      - Dark/Light theme
      - Search functionality
      - Easy navigation
      
      > Documentation is powered by Docsify
    `;
    
    document.getElementById('content').innerHTML = content;
    
    // In a real app, this would initialize syntax highlighting, etc.
    if (window.Prism) {
      Prism.highlightAll();
    }
  }
  
  setupEventListeners() {
    // Theme change event
    document.addEventListener('themeChange', (e) => {
      console.log('Theme changed to:', e.detail.theme);
    });
    
    // Search functionality
    const searchInput = document.getElementById('search-input');
    if (searchInput) {
      searchInput.addEventListener('input', (e) => {
        this.handleSearch(e.target.value);
      });
    }
  }
  
  handleSearch(query) {
    console.log('Search:', query);
    // In a real app, this would filter the navigation
  }
}

// Initialize the app
window.app = new DocsApp();
