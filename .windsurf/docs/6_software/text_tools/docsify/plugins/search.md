# Search Plugin

## Overview
The search plugin adds real-time search functionality to your Docsify documentation, allowing users to quickly find content across all pages.

## Features

- Real-time search as you type
- Fuzzy matching for better results
- Search result highlighting
- Customizable search paths
- Support for multiple languages

## Installation

Add the following to your `index.html`:

```html
<script src="//cdn.jsdelivr.net/npm/docsify/lib/plugins/search.min.js"></script>
```

## Configuration

```javascript
window.$docsify = {
  search: {
    maxAge: 86400000,           // Expiration time for the cache
    paths: 'auto',              // or 'auto'|Array|Function
    placeholder: 'Search...',   // Search input placeholder
    noData: 'No results!',      // No results text
    depth: 2,                   // Search depth for headings
    hideOtherSidebarContent: false, // Hide other content when searching
    namespace: 'docsify',       // Custom namespace for localStorage
    pathNamespaces: [],         // Namespaces to include in search
    // Advanced options
    filter: null,               // Custom filter function
    alias: {},                  // Route alias
    // Localization
    placeholder: {
      '/zh-cn/': '搜索',
      '/': 'Search'
    }
  }
};
```

## Usage

### Basic Search
By default, the search box will be added to the navigation bar.

### Custom Search Paths
```javascript
search: {
  paths: [
    '/',                   // Root path
    '/guide',             // Specific section
    '/api'                // API documentation
  ]
}
```

### Custom Search Input
If you want to use your own search input:

```html
<input type="search" id="search" placeholder="Search...">
<script>
  window.$docsify = {
    search: {
      // Your search config
    }
  };
  
  // Initialize search
  document.addEventListener('DOMContentLoaded', function() {
    const search = window.Docsify.dom.find('#search');
    if (search) {
      search.addEventListener('input', function(e) {
        // Trigger search
        window.Docsify.search.search(search.value);
      });
    }
  });
</script>
```

## Advanced Configuration

### Custom Search Filter
```javascript
search: {
  filter: function(path) {
    // Only search in markdown files
    return /.*\.md$/.test(path);
  }
}
```

### Search Highlighting
Search results are automatically highlighted. You can customize the highlight style:

```css
.app-nav > ul > li.search {
  /* Style the search input */
}

.search a:hover {
  /* Style search results on hover */
}

.search .search-keyword {
  /* Style matched keywords */
  background: rgba(255, 235, 0, 0.3);
  font-style: normal;
}
```

## Performance Considerations

1. **Index Size**: Large documentation sets may impact performance
2. **Cache**: The search index is cached in localStorage
3. **Dynamic Loading**: Only loads search data for the current path by default

## Troubleshooting

### Search Not Working
1. Check the browser console for errors
2. Verify the search plugin is properly included
3. Ensure your content is being indexed (check Network tab)

### Missing Results
1. Check if the path is included in search.paths
2. Verify the filter function (if used) isn't excluding content
3. Clear the search cache in localStorage

## Example

See the [official Docsify documentation](https://docsify.js.org/#/plugins) for a live example.

## Last Updated
2025-06-28 00:45:00

*This file was last updated manually.*
