// Sidebar Manager
class SidebarManager {
  constructor() {
    this.sidebar = document.querySelector('.sidebar');
    this.sidebarToggle = document.getElementById('sidebarToggle');
    this.app = document.getElementById('app');
    this.overlay = document.createElement('div');
    this.isMobile = window.innerWidth < 768;
    this.isCollapsed = localStorage.getItem('sidebarCollapsed') === 'true';
    this.init();
  }
  
  init() {
    if (!this.sidebarToggle) {
      this.createToggleButton();
    }
    
    this.createOverlay();
    this.setupEventListeners();
    
    // Initialize collapsible sections after a small delay to ensure DOM is ready
    setTimeout(() => {
      this.setupCollapsibleSections();
      this.enhanceTreeView();
    }, 300);
    
    // Set initial state based on saved preference or default
    this.restoreSidebarState();
    
    // Listen for theme changes
    document.addEventListener('themeChanged', () => {
      this.updateThemeClasses();
      this.enhanceTreeView(); // Re-apply tree view enhancements after theme change
    });
    
    // Initial theme class setup
    this.updateThemeClasses();
    
    // Handle dynamic content loading
    window.addEventListener('popstate', () => {
      setTimeout(() => this.enhanceTreeView(), 100);
    });
  }
  
  createToggleButton() {
    this.sidebarToggle = document.createElement('button');
    this.sidebarToggle.id = 'sidebarToggle';
    this.sidebarToggle.className = 'sidebar-toggle';
    this.sidebarToggle.innerHTML = '☰';
    this.sidebarToggle.setAttribute('title', 'Toggle sidebar (Ctrl+\\)');
    this.sidebarToggle.setAttribute('aria-label', 'Toggle sidebar');
    this.sidebarToggle.setAttribute('aria-expanded', 'true');
    this.sidebarToggle.setAttribute('aria-controls', 'sidebar');
    this.sidebarToggle.setAttribute('aria-haspopup', 'true');
    this.sidebarToggle.setAttribute('tabindex', '0');
    
    // Add keyboard event for the button itself
    this.sidebarToggle.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        this.toggleSidebar();
      }
    });
    
    document.body.insertBefore(this.sidebarToggle, document.body.firstChild);
  }
  
  createOverlay() {
    this.overlay.id = 'sidebar-overlay';
    this.overlay.className = 'sidebar-overlay';
    document.body.appendChild(this.overlay);
  }
  
  setupEventListeners() {
    // Toggle sidebar on button click
    if (this.sidebarToggle) {
      this.sidebarToggle.addEventListener('click', (e) => {
        e.preventDefault();
        this.toggleSidebar();
      });
    }
    
    // Close sidebar when clicking overlay
    this.overlay.addEventListener('click', () => this.hideSidebar());
    
    // Handle window resize
    let resizeTimer;
    window.addEventListener('resize', () => {
      clearTimeout(resizeTimer);
      resizeTimer = setTimeout(() => this.handleResize(), 100);
    });
    
    // Handle keyboard navigation
    document.addEventListener('keydown', (e) => {
      // Toggle sidebar with Ctrl+\ (backslash)
      if ((e.ctrlKey || e.metaKey) && e.key === '\\\\') {
        e.preventDefault();
        this.toggleSidebar();
      }
      // Close with Escape
      else if (e.key === 'Escape' && !this.isCollapsed) {
        this.collapseSidebar();
        // Return focus to the toggle button
        if (this.sidebarToggle) {
          this.sidebarToggle.focus();
        }
      }
    });
    
    // Close sidebar when clicking outside on mobile
    document.addEventListener('click', (e) => {
      if (this.isMobile && this.sidebar && !this.sidebar.contains(e.target) && 
          this.sidebarToggle && !this.sidebarToggle.contains(e.target)) {
        this.hideSidebar();
      }
    });
    
    // Trap focus when sidebar is open
    document.addEventListener('focusin', (e) => {
      if (!this.isCollapsed && this.sidebar) {
        const isInSidebar = this.sidebar.contains(e.target);
        const isToggleButton = e.target === this.sidebarToggle;
        
        if (!isInSidebar && !isToggleButton) {
          // Focus the first focusable element in the sidebar
          const focusable = this.sidebar.querySelector('a[href], button, [tabindex]');
          if (focusable) {
            focusable.focus();
          }
        }
      }
    });
  }
  
  setupCollapsibleSections() {
    // This will be called after Docsify has rendered the sidebar
    const observer = new MutationObserver(() => {
      if (!this.sidebar) return;
      
      const items = this.sidebar.querySelectorAll('.sidebar-nav li');
      
      items.forEach(item => {
        const link = item.querySelector('a');
        const sublist = item.querySelector('ul');
        
        if (sublist) {
          // Add collapse/expand button if not already present
          if (!item.querySelector('.collapse-btn')) {
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
        }
      });
    });
    
    // Start observing the sidebar for changes
    if (this.sidebar) {
      observer.observe(this.sidebar, { 
        childList: true, 
        subtree: true 
      });
    }
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
    if (this.isCollapsed) {
      this.expandSidebar();
    } else {
      this.collapseSidebar();
    }
  }
  
  expandSidebar() {
    if (!this.isCollapsed) return;
    
    document.body.classList.remove('sidebar-collapsed');
    this.isCollapsed = false;
    this.sidebar.classList.add('show');
    this.overlay.style.display = 'block';
    setTimeout(() => {
      this.overlay.style.opacity = '0.5';
      this.overlay.style.visibility = 'visible';
    }, 10);
    this.sidebarToggle.setAttribute('aria-expanded', 'true');
    document.body.style.overflow = 'hidden';
    this.updateToggleButton();
    
    // Save state
    localStorage.setItem('sidebarCollapsed', 'false');
    
    // Dispatch event
    document.dispatchEvent(new CustomEvent('sidebarToggled', { 
      detail: { isCollapsed: false } 
    }));
  }
  
  collapseSidebar() {
    if (this.isCollapsed) return;
    
    document.body.classList.add('sidebar-collapsed');
    this.isCollapsed = true;
    this.sidebar.classList.remove('show');
    this.overlay.style.opacity = '0';
    this.overlay.style.visibility = 'hidden';
    setTimeout(() => {
      this.overlay.style.display = 'none';
    }, 300);
    this.sidebarToggle.setAttribute('aria-expanded', 'false');
    document.body.style.overflow = '';
    this.updateToggleButton();
    
    // Save state
    localStorage.setItem('sidebarCollapsed', 'true');
    
    // Dispatch event
    document.dispatchEvent(new CustomEvent('sidebarToggled', { 
      detail: { isCollapsed: true } 
    }));
  }
  
  updateToggleButton() {
    if (!this.sidebarToggle) return;
    
    if (this.isCollapsed) {
      this.sidebarToggle.setAttribute('aria-expanded', 'false');
      this.sidebarToggle.innerHTML = '☰';
      this.sidebarToggle.setAttribute('aria-label', 'Show sidebar (Ctrl+\\)');
      
      // Update title for better accessibility
      this.sidebarToggle.title = 'Show sidebar (Ctrl+\\)';
    } else {
      this.sidebarToggle.setAttribute('aria-expanded', 'true');
      this.sidebarToggle.innerHTML = '✕';
      this.sidebarToggle.setAttribute('aria-label', 'Hide sidebar (Ctrl+\\)');
      
      // Update title for better accessibility
      this.sidebarToggle.title = 'Hide sidebar (Ctrl+\\)';
      
      // Focus management when expanding
      requestAnimationFrame(() => {
        // Focus the first focusable element in the sidebar
        const focusable = this.sidebar.querySelector('a[href], button, [tabindex]');
        if (focusable) {
          focusable.focus();
        }
      });
    }
    
    // Ensure the button is visible to screen readers
    this.sidebarToggle.setAttribute('aria-hidden', 'false');
  }
  
  handleResize() {
    const wasMobile = this.isMobile;
    this.isMobile = window.innerWidth < 1024;
    
    if (wasMobile !== this.isMobile) {
      if (this.isMobile) {
        // On mobile, hide sidebar and show toggle button
        this.hideSidebar();
      } else {
        // On desktop, show sidebar and hide overlay
        this.showSidebar();
        this.overlay.style.display = 'none';
      }
    }
  }
  
  updateThemeClasses() {
    if (this.sidebar) {
      const theme = document.documentElement.getAttribute('data-theme') || 'light';
      this.sidebar.className = theme === 'dark' ? 'dark' : 'light';
    }
  }
  
  // Restore the sidebar state from localStorage
  restoreSidebarState() {
    const sidebarState = localStorage.getItem('sidebarState');
    if (sidebarState) {
      try {
        const state = JSON.parse(sidebarState);
        if (state.collapsed !== undefined) {
          this.isCollapsed = state.collapsed;
          if (this.isCollapsed) {
            this.collapseSidebar();
          } else {
            this.expandSidebar();
          }
        }
      } catch (e) {
        console.error('Error restoring sidebar state:', e);
      }
    }
  }
  
  // Enhance the tree view with additional functionality
  enhanceTreeView() {
    if (!this.sidebar) return;
    
    // Add keyboard navigation to the sidebar
    const items = this.sidebar.querySelectorAll('li');
    items.forEach((item, index) => {
      item.setAttribute('tabindex', '0');
      
      // Handle keyboard navigation
      item.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          const link = item.querySelector('a');
          if (link) {
            link.click();
          }
        } else if (e.key === 'ArrowDown' || e.key === 'ArrowRight') {
          e.preventDefault();
          const nextItem = items[index + 1] || items[0];
          if (nextItem) nextItem.focus();
        } else if (e.key === 'ArrowUp' || e.key === 'ArrowLeft') {
          e.preventDefault();
          const prevItem = items[index - 1] || items[items.length - 1];
          if (prevItem) prevItem.focus();
        }
      });
    });
    
    // Add smooth scrolling to the active item
    const activeItem = this.sidebar.querySelector('.active');
    if (activeItem) {
      activeItem.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
    }
  }
  
  // Show the sidebar
  showSidebar() {
    if (this.sidebar) {
      this.sidebar.style.display = 'block';
      this.sidebar.setAttribute('aria-hidden', 'false');
      this.updateToggleButton();
    }
  }
  
  // Hide the sidebar
  hideSidebar() {
    if (this.sidebar) {
      this.sidebar.style.display = 'none';
      this.sidebar.setAttribute('aria-hidden', 'true');
      this.updateToggleButton();
    }
  }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
  window.sidebarManager = new SidebarManager();
});
