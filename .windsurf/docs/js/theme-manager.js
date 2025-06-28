// Theme Manager
class ThemeManager {
  constructor() {
    // UI Elements
    this.themeToggle = document.getElementById('themeToggle');
    this.consoleToggle = document.getElementById('consoleToggle');
    this.consolePanel = document.getElementById('consolePanel');
    this.consoleOutput = document.getElementById('consoleOutput');
    this.consoleInput = document.getElementById('consoleInput');
    this.executeButton = document.getElementById('executeCommand');
    this.clearButton = document.getElementById('clearConsole');
    
    // State
    this.currentTheme = localStorage.getItem('docs-theme') || 'light';
    this.consoleOpen = false;
    this.commandHistory = [];
    this.historyIndex = -1;
    
    // Initialize
    this.init();
  }
  
  init() {
    console.log('Initializing ThemeManager...');
    
    // Set initial theme
    this.setTheme(this.currentTheme);
    
    // Setup event listeners
    if (this.themeToggle) {
      console.log('Theme toggle button found, adding click handler');
      this.themeToggle.addEventListener('click', (e) => {
        e.preventDefault();
        this.toggleTheme();
      });
    } else {
      console.warn('Theme toggle button not found!');
    }
    
    // Setup console functionality
    if (this.consoleToggle) {
      console.log('Console toggle button found, initializing console...');
      this.consoleToggle.addEventListener('click', (e) => {
        e.preventDefault();
        this.toggleConsole();
      });
      
      // Initialize console functionality
      this.initConsole();
    } else {
      console.warn('Console toggle button not found!');
    }
    
    // Listen for system theme changes
    this.watchSystemTheme();
    
    // Listen for theme changes from other components
    document.addEventListener('themeChange', (e) => {
      if (e.detail && e.detail.theme) {
        this.setTheme(e.detail.theme);
      }
    });
    
    // Override console methods to also log to our console panel
    this.overrideConsoleMethods();
    
    console.log('ThemeManager initialized');
  }
  
  // Override console methods to also log to our console panel
  overrideConsoleMethods() {
    const originalConsole = {
      log: console.log,
      info: console.info,
      warn: console.warn,
      error: console.error,
      debug: console.debug
    };
    
    // Override each console method
    ['log', 'info', 'warn', 'error', 'debug'].forEach(method => {
      console[method] = (...args) => {
        // Call the original console method
        originalConsole[method](...args);
        
        // Log to our console panel
        const message = args.map(arg => 
          typeof arg === 'object' ? JSON.stringify(arg, null, 2) : String(arg)
        ).join(' ');
        
        this.logToConsole(message, method === 'log' ? 'info' : method);
      };
    });
  }
  
  setTheme(theme) {
    console.log(`Setting theme to: ${theme}`);
    this.currentTheme = theme;
    
    // Update document classes for Docsify
    const html = document.documentElement;
    html.setAttribute('data-theme', theme);
    
    // Also set the theme class on the html element for Docsify compatibility
    if (theme === 'dark') {
      html.classList.add('dark-theme');
      html.classList.remove('light-theme');
    } else {
      html.classList.add('light-theme');
      html.classList.remove('dark-theme');
    }
    
    // Save to localStorage
    localStorage.setItem('docs-theme', theme);
    
    // Update toggle button
    if (this.themeToggle) {
      this.themeToggle.textContent = theme === 'dark' ? '☀️' : '🌙';
      this.themeToggle.setAttribute('title', `Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`);
      console.log('Updated theme toggle button appearance');
    }
    
    // Dispatch event for other components
    document.dispatchEvent(new CustomEvent('themeChanged', { 
      detail: { theme } 
    }));
    
    // Force Docsify to update if it's loaded
    if (window.Docsify) {
      const app = document.getElementById('app');
      if (app) {
        const event = new Event('_sidebar');
        window.dispatchEvent(event);
      }
    }
    
    console.log(`Theme set to: ${theme}`);
  }
  
  toggleTheme() {
    console.log('Toggling theme...');
    this.setTheme(this.currentTheme === 'dark' ? 'light' : 'dark');
  }
  
  toggleConsole() {
    console.log('Toggling console...');
    this.consoleOpen = !this.consoleOpen;
    
    if (this.consolePanel) {
      this.consolePanel.classList.toggle('visible', this.consoleOpen);
      console.log(`Console panel ${this.consoleOpen ? 'shown' : 'hidden'}`);
      
      // Focus input when console is shown
      if (this.consoleOpen && this.consoleInput) {
        setTimeout(() => this.consoleInput.focus(), 100);
      }
    } else {
      console.warn('Console panel element not found!');
    }
    
    // Update console toggle button
    if (this.consoleToggle) {
      this.consoleToggle.textContent = this.consoleOpen ? '✕' : '>';
      this.consoleToggle.setAttribute('title', this.consoleOpen ? 'Hide console' : 'Show console');
      this.consoleToggle.classList.toggle('active', this.consoleOpen);
    }
  }
  
  // Initialize console functionality
  initConsole() {
    if (!this.consoleInput || !this.executeButton || !this.clearButton) {
      console.warn('Console elements not found!');
      return;
    }
    
    // Execute command on button click
    this.executeButton.addEventListener('click', () => this.executeCommand());
    
    // Execute command on Enter key
    this.consoleInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        this.executeCommand();
      } else if (e.key === 'ArrowUp') {
        // Navigate command history up
        e.preventDefault();
        this.navigateHistory(1);
      } else if (e.key === 'ArrowDown') {
        // Navigate command history down
        e.preventDefault();
        this.navigateHistory(-1);
      }
    });
    
    // Clear console output
    this.clearButton.addEventListener('click', () => {
      if (this.consoleOutput) {
        this.consoleOutput.innerHTML = '';
        this.logToConsole('Console cleared', 'info');
      }
    });
    
    // Initial console message
    this.logToConsole('Console initialized. Type "help" for available commands.', 'info');
  }
  
  // Execute a console command
  executeCommand() {
    const command = this.consoleInput.value.trim();
    if (!command) return;
    
    // Add to history if not a duplicate of the last command
    if (this.commandHistory[0] !== command) {
      this.commandHistory.unshift(command);
      this.historyIndex = -1; // Reset history navigation
    }
    
    // Clear input
    this.consoleInput.value = '';
    
    // Log the command
    this.logToConsole(`> ${command}`, 'command');
    
    // Process the command
    this.processCommand(command);
  }
  
  // Process console commands
  processCommand(command) {
    const parts = command.split(' ');
    const cmd = parts[0].toLowerCase();
    const args = parts.slice(1);
    
    switch (cmd) {
      case 'help':
        this.logToConsole('Available commands:', 'info');
        this.logToConsole('  help - Show this help message', 'info');
        this.logToConsole('  clear - Clear the console', 'info');
        this.logToConsole('  theme [light|dark|system] - Get or set the theme', 'info');
        this.logToConsole('  version - Show version information', 'info');
        break;
        
      case 'clear':
        if (this.consoleOutput) {
          this.consoleOutput.innerHTML = '';
        }
        break;
        
      case 'theme':
        if (args.length === 0) {
          this.logToConsole(`Current theme: ${this.currentTheme}`, 'info');
        } else {
          const theme = args[0].toLowerCase();
          if (['light', 'dark', 'system'].includes(theme)) {
            this.setTheme(theme === 'system' ? 
              (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light') : 
              theme);
            this.logToConsole(`Theme set to: ${theme}`, 'success');
          } else {
            this.logToConsole(`Invalid theme: ${theme}. Use 'light', 'dark', or 'system'`, 'error');
          }
        }
        break;
        
      case 'version':
        this.logToConsole(`Docsify Console v1.0.0`, 'info');
        this.logToConsole(`Docsify: ${window.Docsify?.version || 'unknown'}`, 'info');
        break;
        
      default:
        this.logToConsole(`Unknown command: ${cmd}. Type 'help' for available commands.`, 'error');
    }
  }
  
  // Log a message to the console
  logToConsole(message, type = 'log') {
    if (!this.consoleOutput) return;
    
    const line = document.createElement('div');
    line.className = `console-${type}`;
    line.textContent = message;
    
    this.consoleOutput.appendChild(line);
    this.consoleOutput.scrollTop = this.consoleOutput.scrollHeight;
  }
  
  // Navigate command history
  navigateHistory(direction) {
    if (this.commandHistory.length === 0) return;
    
    // Update history index
    this.historyIndex = Math.max(-1, 
      Math.min(this.commandHistory.length - 1, this.historyIndex + direction));
    
    // Set input value or clear if at the end of history
    if (this.consoleInput) {
      this.consoleInput.value = this.historyIndex >= 0 ? 
        this.commandHistory[this.historyIndex] : '';
    }
  }
  
  watchSystemTheme() {
    // Only watch if no preference is set
    if (!localStorage.getItem('docs-theme') && window.matchMedia) {
      console.log('Setting up system theme preference watcher');
      const darkModeMediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
      
      const setSystemTheme = (e) => {
        console.log('System theme preference changed:', e.matches ? 'dark' : 'light');
        this.setTheme(e.matches ? 'dark' : 'light');
      };
      
      // Set initial value
      setSystemTheme({ matches: darkModeMediaQuery.matches });
      
      // Listen for changes
      darkModeMediaQuery.addEventListener('change', setSystemTheme);
    } else {
      console.log('System theme preference watcher not needed (user preference set)');
    }
  }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
  window.themeManager = new ThemeManager();
});
