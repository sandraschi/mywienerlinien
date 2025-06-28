// Theme Manager
class ThemeManager {
  constructor() {
    this.themeToggle = document.getElementById('themeToggle');
    this.currentTheme = localStorage.getItem('docs-theme') || 'light';
    this.init();
  }
  
  init() {
    // Set initial theme
    this.setTheme(this.currentTheme);
    
    // Setup event listeners
    if (this.themeToggle) {
      this.themeToggle.addEventListener('click', () => this.toggleTheme());
    }
    
    // Listen for system theme changes
    this.watchSystemTheme();
    
    // Listen for theme changes from other components
    document.addEventListener('themeChange', (e) => {
      if (e.detail && e.detail.theme) {
        this.setTheme(e.detail.theme);
      }
    });
  }
  
  setTheme(theme) {
    this.currentTheme = theme;
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('docs-theme', theme);
    
    // Update toggle button
    if (this.themeToggle) {
      this.themeToggle.textContent = theme === 'dark' ? '☀️' : '🌙';
      this.themeToggle.setAttribute('title', `Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`);
    }
    
    // Dispatch event for other components
    document.dispatchEvent(new CustomEvent('themeChanged', { 
      detail: { theme } 
    }));
    
    console.log(`Theme set to: ${theme}`);
  }
  
  toggleTheme() {
    this.setTheme(this.currentTheme === 'dark' ? 'light' : 'dark');
  }
  
  watchSystemTheme() {
    // Only watch if no preference is set
    if (!localStorage.getItem('docs-theme') && window.matchMedia) {
      const darkModeMediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
      
      const setSystemTheme = (e) => {
        this.setTheme(e.matches ? 'dark' : 'light');
      };
      
      // Set initial value
      setSystemTheme({ matches: darkModeMediaQuery.matches });
      
      // Listen for changes
      darkModeMediaQuery.addEventListener('change', setSystemTheme);
    }
  }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
  window.themeManager = new ThemeManager();
});
