// Sidebar Component
class Sidebar {
  constructor() {
    this.sidebar = document.getElementById('sidebar');
    this.toggleBtn = document.createElement('button');
    this.overlay = document.createElement('div');
    this.config = window.docsConfig;
    
    this.init();
  }
  
  init() {
    this.createSidebar();
    this.createToggleButton();
    this.createOverlay();
    this.setupEventListeners();
    this.loadSidebarContent();
    this.restoreState();
  }
  
  createSidebar() {
    this.sidebar.innerHTML = `
      <div class="sidebar-header">
        <h2>${this.config.title}</h2>
      </div>
      <div class="sidebar-content">
        <div class="sidebar-search">
          <input type="text" placeholder="Search..." id="search-input">
        </div>
        <nav class="sidebar-nav" id="sidebar-nav">
          <!-- Navigation will be loaded here -->
        </nav>
      </div>
      <div class="sidebar-footer">
        <button id="theme-toggle" class="theme-toggle" title="Toggle theme">🌓</button>
      </div>
    `;
  }
  
  createToggleButton() {
    this.toggleBtn.id = 'sidebar-toggle';
    this.toggleBtn.className = 'sidebar-toggle';
    this.toggleBtn.innerHTML = '☰';
    this.toggleBtn.setAttribute('aria-label', 'Toggle sidebar');
    document.body.appendChild(this.toggleBtn);
  }
  
  createOverlay() {
    this.overlay.id = 'sidebar-overlay';
    this.overlay.className = 'sidebar-overlay';
    document.body.appendChild(this.overlay);
  }
  
  loadSidebarContent() {
    // This would typically load content from _sidebar.md
    const nav = document.getElementById('sidebar-nav');
    if (nav) {
      nav.innerHTML = `
        <ul>
          <li><a href="#/" class="active">Home</a></li>
          <li><a href="#/guide">Guide</a></li>
          <li><a href="#/api">API Reference</a></li>
          <li class="divider"></li>
          <li><a href="https://github.com/your/repo" target="_blank">GitHub</a></li>
        </ul>
      `;
    }
  }
  
  setupEventListeners() {
    // Toggle sidebar
    this.toggleBtn.addEventListener('click', () => this.toggle());
    
    // Close sidebar when clicking overlay
    this.overlay.addEventListener('click', () => this.hide());
    
    // Handle window resize
    window.addEventListener('resize', () => this.handleResize());
    
    // Theme toggle
    const themeToggle = document.getElementById('theme-toggle');
    if (themeToggle) {
      themeToggle.addEventListener('click', () => this.toggleTheme());
    }
  }
  
  toggle() {
    document.body.classList.toggle('sidebar-visible');
    this.overlay.classList.toggle('active');
    this.saveState();
  }
  
  show() {
    document.body.classList.add('sidebar-visible');
    this.overlay.classList.add('active');
    this.saveState();
  }
  
  hide() {
    document.body.classList.remove('sidebar-visible');
    this.overlay.classList.remove('active');
    this.saveState();
  }
  
  toggleTheme() {
    const currentTheme = document.documentElement.getAttribute('data-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    
    document.documentElement.setAttribute('data-theme', newTheme);
    localStorage.setItem('docs-theme', newTheme);
    
    // Dispatch event for other components
    document.dispatchEvent(new CustomEvent('themeChange', { detail: { theme: newTheme } }));
  }
  
  handleResize() {
    if (window.innerWidth > 768) {
      this.hide();
    }
  }
  
  saveState() {
    const isVisible = document.body.classList.contains('sidebar-visible');
    localStorage.setItem('sidebar-visible', isVisible);
  }
  
  restoreState() {
    const isVisible = localStorage.getItem('sidebar-visible') === 'true';
    if (isVisible) {
      this.show();
    }
  }
}

// Initialize sidebar when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
  window.sidebar = new Sidebar();
});
