// Debug function to log to console with timestamp
function debugLog(...args) {
  console.log(`[${new Date().toISOString()}]`, ...args);
}

// Check if _sidebar.md exists and is accessible
fetch('_sidebar.md')
  .then(response => {
    if (!response.ok) {
      debugLog('Error: Could not load _sidebar.md -', response.status, response.statusText);
    } else {
      debugLog('_sidebar.md loaded successfully');
    }
  })
  .catch(error => {
    debugLog('Error checking _sidebar.md:', error);
  });

// Docsify configuration
window.$docsify = {
  // Debug hooks
  hooks: {
    init: function() {
      debugLog('Docsify init hook called');
    },
    mounted: function() {
      debugLog('Docsify mounted hook called');
    },
    ready: function() {
      debugLog('Docsify ready hook called');
      // Check if sidebar element exists
      const sidebar = document.querySelector('.sidebar');
      debugLog('Sidebar element:', sidebar);
      if (sidebar) {
        debugLog('Sidebar HTML:', sidebar.innerHTML);
      }
    },
    'beforeEach': function(content, next) {
      debugLog('Loading content:', content);
      next(content);
    },
    'afterEach': function(html, next) {
      debugLog('Content loaded:', html ? 'Content received' : 'No content');
      next(html);
    }
  },
  name: 'Windsurf Documentation',
  repo: '',
  basePath: '/',
  
  // Core settings
  loadSidebar: true,    // Enable sidebar
  autoHeader: true,     // Auto generate header anchors
  auto2top: true,       // Scroll to top on route change
  coverpage: false,     // Disable coverpage
  onlyCover: false,     // Don't show only coverpage
  notFoundPage: '404.md',
  executeScript: true,  // Execute script tags in markdown
  noEmoji: false,       // Allow emojis
  mergeNavbar: false,   // Don't merge navbar with sidebar on mobile
  relativePath: true,   // Use relative paths
  
  // Sidebar configuration
  loadSidebar: false,          // We're generating the sidebar dynamically
  subMaxLevel: 6,              // Maximum nested level for headers
  maxLevel: 6,                 // Maximum header level to include
  
  // Collapsible sidebar configuration
  sidebarDisplayLevel: 1,      // Show all levels by default
  collapseSidebar: true,       // Enable collapsible sidebar
  
  // Navigation settings
  auto2top: true,              // Scroll to top on route change
  loadNavbar: false,           // Disable navbar if not used
  mergeNavbar: false,          // Don't merge navbar with sidebar on mobile
  
  // Alias configuration
  alias: {
    '/.*/_sidebar.md': '/_sidebar.md',  // Fallback for nested _sidebar.md
    '/.*/README.md': '/README.md'       // Fallback for README.md
  },
  formatUpdated: '{MM}/{DD} {HH}:{mm}',
  externalLinkTarget: '_blank',
  externalLinkRel: 'noopener',
  
  // Theme configuration
  themeable: {
    readyTransition: true,
    responsiveTables: true
  },
  
  // Search configuration
  search: {
    maxAge: 86400000, // 24 hours
    paths: 'auto',
    placeholder: 'Search...',
    noData: 'No results!',
    depth: 4,
    hideOtherSidebarContent: false,
  },
  
  // Copy code plugin
  copyCode: {
    buttonText: 'Copy',
    errorText: 'Error',
    successText: 'Copied!'
  },
  
  // Pagination
  pagination: {
    previousText: 'Previous',
    nextText: 'Next',
    crossChapter: true,
    crossChapterText: true
  }
};

// Set initial theme
document.documentElement.setAttribute('data-theme', localStorage.getItem('docs-theme') || 'light');
