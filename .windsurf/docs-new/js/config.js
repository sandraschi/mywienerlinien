// Docsify Configuration
window.$docsify = {
  name: 'Documentation',
  repo: '',
  loadSidebar: true,
  subMaxLevel: 3,
  auto2top: true,
  coverpage: false,
  onlyCover: false,
  notFoundPage: true,
  executeScript: true,
  noEmoji: false,
  mergeNavbar: true,
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
  },
  
  // Plugins
  plugins: [
    // Will be populated by plugins.js
  ]
};

// Theme configuration
document.documentElement.setAttribute('data-theme', localStorage.getItem('docs-theme') || 'light');
