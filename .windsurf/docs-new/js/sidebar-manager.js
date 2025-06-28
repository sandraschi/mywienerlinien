// Sidebar Manager
class SidebarManager {
  constructor() {
    this.sidebar = document.getElementById('sidebar');
    this.sidebarToggle = document.createElement('button');
    this.overlay = document.createElement('div');
    this.isMobile = window.innerWidth < 768;
    this.init();
  }
  
  init() {
    this.createToggleButton();
    this.createOverlay();
    this.setupEventListeners();
    this.setupCollapsibleSections();
    this.restoreSidebarState();
    
    // Listen for theme changes
    document.addEventListener('themeChanged', () => this.updateThemeClasses());
    
    // Initial theme class setup
    this.updateThemeClasses();
  }
  
  createToggleButton() {
    this.sidebarToggle.id = 'sidebar-toggle';
    this.sidebarToggle.className = 'sidebar-toggle';
    this.sidebarToggle.innerHTML = '☰';
    this.sidebarToggle.setAttribute('aria-label', 'Toggle sidebar');
    this.sidebarToggle.setAttribute('aria-expanded', 'true');
    document.body.appendChild(this.sidebarToggle);
  }
  
  createOverlay() {
    this.overlay.id = 'sidebar-overlay';
    this.overlay.className = 'sidebar-overlay';
    document.body.appendChild(this.overlay);
  }
  
  setupEventListeners() {
    // Toggle sidebar
    this.sidebarToggle.addEventListener('click', () => this.toggleSidebar());
    
    // Close sidebar when clicking overlay
    this.overlay.addEventListener('click', () => this.hideSidebar());
    
    // Handle window resize
    window.addEventListener('resize', () => this.handleResize());
    
    // Close sidebar when clicking outside on mobile
    document.addEventListener('click', (e) => {
      if (this.isMobile && !this.sidebar.contains(e.target) && 
          e.target !== this.sidebarToggle && !this.sidebarToggle.contains(e.target)) {
        this.hideSidebar();
      }
    });
    
    // Handle keyboard navigation
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') {
        this.hideSidebar();
      }
    });
  }
  
  setupCollapsibleSections() {
    // This will be called after Docsify has rendered the sidebar
    const observer = new MutationObserver(() => {
      const items = this.sidebar.querySelectorAll('.sidebar-nav li');
      
      items.forEach(item => {
        const link = item.querySelector('a');
        const sublist = item.querySelector('ul');
        
        if (sublist) {
          // Add collapse/expand button
          const btn = document.createElement('button');
          btn.className = 'collapse-btn';
          btn.setAttribute('aria-label', 'Toggle section');
          item.insertBefore(btn, link || sublist);
          
          // Make the entire item clickable to toggle
          if (link) {
            link.style.pointerEvents = 'none';
            item.style.cursor = 'pointer';
            
            item.addEventListener('click', (e) => {
              if (e.target !== btn) {
                this.toggleSection(item);
              }
            });
          }
          
          // Toggle on button click
          btn.addEventListener('click', (e) => {
            e.stopPropagation();
            this.toggleSection(item);
          });
          
          // Initialize state
          const isCollapsed = localStorage.getItem(`sidebar-section-${link?.getAttribute('href')}`) === 'collapsed';
          if (isCollapsed) {
            item.classList.add('collapsed');
          }
        }
      });
    });
    
    // Start observing the sidebar for changes
    observer.observe(this.sidebar, { 
      childList: true, 
      subtree: true 
    });
  }
  
  toggleSection(item) {
    const wasCollapsed = item.classList.contains('collapsed');
    const link = item.querySelector('a');
    
    if (wasCollapsed) {
      item.classList.remove('collapsed');
      if (link) {
        localStorage.setItem(`sidebar-section-${link.getAttribute('href')}`, 'expanded');
      }
    } else {
      item.classList.add('collapsed');
      if (link) {
        localStorage.setItem(`sidebar-section-${link.getAttribute('href')}`, 'collapsed');
      }
    }
    
    // Update ARIA attributes
    const btn = item.querySelector('.collapse-btn');
    if (btn) {
      btn.setAttribute('aria-expanded', wasCollapsed ? 'true' : 'false');
    }
  }
  
  toggleSidebar() {
    const isVisible = document.body.classList.contains('sidebar-visible');
    
    if (isVisible) {
      this.hideSidebar();
    } else {
      this.showSidebar();
    }
  }
  
  showSidebar() {
    document.body.classList.add('sidebar-visible');
    this.overlay.classList.add('active');
    this.sidebarToggle.setAttribute('aria-expanded', 'true');
    this.saveSidebarState(true);
  }
  
  hideSidebar() {
    document.body.classList.remove('sidebar-visible');
    this.overlay.classList.remove('active');
    this.sidebarToggle.setAttribute('aria-expanded', 'false');
    this.saveSidebarState(false);
  }
  
  saveSidebarState(isVisible) {
    if (this.isMobile) {
      localStorage.setItem('sidebar-visible', isVisible ? 'true' : 'false');
    }
  }
  
  restoreSidebarState() {
    if (this.isMobile) {
      const isVisible = localStorage.getItem('sidebar-visible') === 'true';
      if (isVisible) {
        this.showSidebar();
      } else {
        this.hideSidebar();
      }
    } else {
      // Always show on desktop
      this.showSidebar();
    }
  }
  
  handleResize() {
    const wasMobile = this.isMobile;
    this.isMobile = window.innerWidth < 768;
    
    if (wasMobile && !this.isMobile) {
      // Switched to desktop
      this.showSidebar();
    } else if (!wasMobile && this.isMobile) {
      // Switched to mobile
      this.hideSidebar();
    }
  }
  
  updateThemeClasses() {
    const theme = document.documentElement.getAttribute('data-theme') || 'light';
    this.sidebar.className = theme === 'dark' ? 'dark' : 'light';
  }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
  window.sidebarManager = new SidebarManager();
});
