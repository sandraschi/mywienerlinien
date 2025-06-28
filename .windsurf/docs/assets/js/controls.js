// Enhanced UI Controls for Docsify
const DocsifyControls = {
  settings: {
    theme: 'system',
    fontSize: 'medium',
    plugins: {
      search: true,
      zoom: true,
      copy: true,
      collapse: true
    },
    sidebarState: 'expanded',
  },

  // Initialize controls
  init() {
    this.loadSettings();
    this.setupEventListeners();
    this.applyAllSettings();
    this.updateUI();
    console.log('Docsify Controls initialized');
  },

  // Load settings from localStorage
  loadSettings() {
    const savedSettings = localStorage.getItem('docsifyControls');
    if (savedSettings) {
      try {
        const parsed = JSON.parse(savedSettings);
        this.settings = {
          ...this.settings,
          ...parsed,
          plugins: {
            ...this.settings.plugins,
            ...(parsed.plugins || {})
          }
        };
      } catch (e) {
        console.error('Failed to load settings:', e);
      }
    }
  },

  // Save settings to localStorage
  saveSettings() {
    try {
      localStorage.setItem('docsifyControls', JSON.stringify(this.settings));
    } catch (e) {
      console.error('Failed to save settings:', e);
    }
  },

  // Set up event listeners
  setupEventListeners() {
    console.log('Setting up event listeners...');
    
    // Theme radio buttons
    const themeRadios = document.querySelectorAll('input[name="theme"]');
    if (themeRadios.length > 0) {
      themeRadios.forEach(radio => {
        radio.addEventListener('change', (e) => {
          this.settings.theme = e.target.value;
          this.saveSettings();
          this.applyTheme();
        });
      });
    } else {
      console.warn('No theme radio buttons found');
    }
    
    // Font size select
    const fontSizeSelect = document.querySelector('select[name="fontSize"]');
    if (fontSizeSelect) {
      fontSizeSelect.value = this.settings.fontSize;
      fontSizeSelect.addEventListener('change', (e) => {
        this.settings.fontSize = e.target.value;
        this.saveSettings();
        this.applyFontSize();
      });
    } else {
      console.warn('Font size select not found');
    }
    
    // Plugin toggles
    const pluginCheckboxes = document.querySelectorAll('input[type="checkbox"][name^="plugin-"]');
    if (pluginCheckboxes.length > 0) {
      pluginCheckboxes.forEach(checkbox => {
        const pluginName = checkbox.name.replace('plugin-', '');
        checkbox.checked = this.settings.plugins[pluginName] !== false;
        
        checkbox.addEventListener('change', (e) => {
          this.settings.plugins[pluginName] = e.target.checked;
          this.saveSettings();
          this.togglePlugin(pluginName, e.target.checked);
        });
      });
    } else {
      console.warn('No plugin checkboxes found');
    }
    
    // Controls panel toggle
    const controlsToggle = document.getElementById('controlsToggle');
    const controlsPanel = document.getElementById('controlsPanel');
    const closeControls = document.getElementById('closeControls');
    
    if (controlsToggle && controlsPanel) {
      // Toggle controls panel
      const togglePanel = (e) => {
        if (e) e.preventDefault();
        controlsPanel.classList.toggle('visible');
        controlsToggle.classList.toggle('active');
        document.body.classList.toggle('controls-visible', controlsPanel.classList.contains('visible'));
        
        // Save panel state
        if (controlsPanel.classList.contains('visible')) {
          controlsPanel.style.display = 'block';
          setTimeout(() => controlsPanel.style.opacity = 1, 10);
        } else {
          controlsPanel.style.opacity = 0;
          setTimeout(() => controlsPanel.style.display = 'none', 300);
        }
      };
      
      // Initialize panel state
      controlsPanel.style.display = 'none';
      controlsPanel.style.opacity = 0;
      
      // Click handler for toggle button
      controlsToggle.addEventListener('click', togglePanel);
      
      // Close button
      if (closeControls) {
        closeControls.addEventListener('click', (e) => {
          e.preventDefault();
          togglePanel();
        });
      }
      
      // Close panel when clicking outside
      document.addEventListener('click', (e) => {
        if (controlsPanel.classList.contains('visible') && 
            !controlsPanel.contains(e.target) && 
            e.target !== controlsToggle) {
          togglePanel();
        }
      });
      
      // Prevent panel clicks from closing it
      controlsPanel.addEventListener('click', (e) => {
        e.stopPropagation();
      });
      
      console.log('Controls panel initialized');
    } else {
      console.warn('Controls panel elements not found');
    }
  },

  // Apply all settings
  applyAllSettings() {
    // Apply theme first as it affects other elements
    this.applyTheme();
    
    // Then apply font size
    this.applyFontSize();
    
    // Apply plugin settings
    Object.entries(this.settings.plugins).forEach(([plugin, enabled]) => {
      this.togglePlugin(plugin, enabled);
    });
    
    // Ensure theme is applied after other settings
    setTimeout(() => this.applyTheme(), 100);
  },

  // Update UI to reflect current settings
  updateUI() {
    // Set theme radio button
    const themeRadio = document.querySelector(`input[name="theme"][value="${this.settings.theme}"]`);
    if (themeRadio) themeRadio.checked = true;
    
    // Set plugin checkboxes
    Object.entries(this.settings.plugins).forEach(([plugin, enabled]) => {
      const checkbox = document.querySelector(`input[name="plugin-${plugin}"]`);
      if (checkbox) checkbox.checked = enabled;
    });
    
    // Set font size select
    const fontSizeSelect = document.querySelector('select[name="fontSize"]');
    if (fontSizeSelect) fontSizeSelect.value = this.settings.fontSize;
  },

  // Theme controls
  applyTheme() {
    const theme = this.getEffectiveTheme();
    // Update root data-theme attribute
    document.documentElement.setAttribute('data-theme', theme);
    
    // Force update by toggling dark class on html element
    document.documentElement.classList.toggle('dark-theme', theme === 'dark');
    
    // Force a reflow to ensure styles are recalculated
    document.body.offsetHeight;
    
    // Update theme-specific variables
    const root = document.documentElement;
    if (theme === 'dark') {
      // These will be overridden by the CSS variables, but set as fallbacks
      root.style.setProperty('--sidebar-bg', '#252526');
      root.style.setProperty('--sidebar-text', '#e0e0e0');
      root.style.setProperty('--sidebar-active', '#2a2d2e');
      root.style.setProperty('--sidebar-hover', '#2d2d2d');
    } else {
      root.style.setProperty('--sidebar-bg', '#f5f7fa');
      root.style.setProperty('--sidebar-text', '#364149');
      root.style.setProperty('--sidebar-active', '#e6f7ff');
      root.style.setProperty('--sidebar-hover', '#e6f7ff');
    }
  },

  getEffectiveTheme() {
    if (this.settings.theme === 'system') {
      return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    }
    return this.settings.theme;
  },
  
  // Font size controls
  applyFontSize() {
    const sizes = {
      small: '14px',
      medium: '16px',
      large: '18px'
    };
    
    document.documentElement.style.setProperty('--base-font-size', sizes[this.settings.fontSize] || '16px');
  },
  
  // Plugin controls
  togglePlugin(plugin, enabled) {
    switch (plugin) {
      case 'search':
        this.toggleSearch(enabled);
        break;
      case 'zoom':
        this.toggleZoom(enabled);
        break;
      case 'copy':
        this.toggleCopyCode(enabled);
        break;
      case 'collapse':
        this.toggleSidebarCollapse(enabled);
        break;
    }
  },
  
  toggleSearch(enabled) {
    const searchInput = document.querySelector('.sidebar .search input');
    if (searchInput) {
      searchInput.style.display = enabled ? 'block' : 'none';
    }
  },
  
  toggleZoom(enabled) {
    const images = document.querySelectorAll('img:not(.emoji)');
    images.forEach(img => {
      if (enabled) {
        img.classList.add('zoomable');
      } else {
        img.classList.remove('zoomable');
      }
    });
  },
  
  toggleCopyCode(enabled) {
    const codeBlocks = document.querySelectorAll('pre[data-lang]');
    codeBlocks.forEach(block => {
      if (enabled && !block.querySelector('.copy-code-button')) {
        const button = document.createElement('button');
        button.className = 'copy-code-button';
        button.textContent = 'Copy';
        button.addEventListener('click', this.copyCode);
        block.style.position = 'relative';
        block.appendChild(button);
      } else if (!enabled) {
        const button = block.querySelector('.copy-code-button');
        if (button) button.remove();
      }
    });
  },
  
  toggleSidebarCollapse(enabled) {
    const sidebar = document.querySelector('.sidebar');
    if (sidebar) {
      if (enabled) {
        sidebar.classList.add('collapsible');
      } else {
        sidebar.classList.remove('collapsible');
      }
    }
  },
  
  // Utility function to copy code
  copyCode(e) {
    const button = e.target;
    const pre = button.parentElement;
    const code = pre.querySelector('code');
    const text = code.innerText;
    
    navigator.clipboard.writeText(text).then(() => {
      button.textContent = 'Copied!';
      setTimeout(() => {
        button.textContent = 'Copy';
      }, 2000);
    }).catch(err => {
      console.error('Failed to copy text: ', err);
    });
  }
};

// Initialize when the DOM is fully loaded
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => DocsifyControls.init());
} else {
  DocsifyControls.init();
}
