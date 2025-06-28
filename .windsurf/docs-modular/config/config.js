// Documentation Configuration
window.docsConfig = {
  // App Settings
  title: 'Documentation',
  description: 'Project Documentation',
  basePath: '',
  
  // Theme Settings
  theme: {
    light: {
      primary: '#42b983',
      sidebarBg: '#f5f7fa',
      contentBg: '#ffffff',
      text: '#2c3e50',
      link: '#42b983'
    },
    dark: {
      primary: '#42b983',
      sidebarBg: '#2d2d2d',
      contentBg: '#1a1a1a',
      text: '#e0e0e0',
      link: '#6ea8fe'
    }
  },
  
  // Plugins Configuration
  plugins: {
    search: {
      maxAge: 86400000, // 24 hours
      paths: 'auto',
      placeholder: 'Search...',
      noData: 'No results!',
      depth: 4
    },
    copyCode: {
      buttonText: 'Copy',
      errorText: 'Error',
      successText: 'Copied!'
    },
    // Add more plugin configs as needed
  },
  
  // Navigation
  nav: [
    { title: 'Home', path: '/' },
    { title: 'Guide', path: '/guide' },
    { title: 'API', path: '/api' }
  ]
};

// Initialize theme
(function() {
  const savedTheme = localStorage.getItem('docs-theme') || 'light';
  document.documentElement.setAttribute('data-theme', savedTheme);
})();
