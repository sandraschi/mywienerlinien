# Pagination Plugin

## Overview
The Pagination plugin adds previous/next page navigation to your Docsify documentation, making it easier for users to navigate through content in a linear fashion.

## Features

- Automatic detection of previous/next pages
- Customizable navigation text and styling
- Keyboard navigation support
- Responsive design
- Configurable position and visibility

## Installation

Add the following to your `index.html`:

```html
<script src="//cdn.jsdelivr.net/npm/docsify-pagination/dist/docsify-pagination.min.js"></script>
```

## Basic Usage

By default, the pagination will be added to the bottom of each page with default styling:

```markdown
# Page 1
Content of page 1

<!-- Automatically adds pagination -->
```

## Configuration

```javascript
window.$docsify = {
  pagination: {
    // Main options
    crossChapter: true,      // Enable cross-chapter navigation
    crossChapterText: true,  // Show chapter name in pagination
    previousText: 'Previous', // Text for previous button
    nextText: 'Next',        // Text for next button
    // Position: 'top', 'bottom', or 'both'
    position: 'bottom',
    // Custom templates
    template: `
      <nav class="pagination">
        <a class="pagination-item" href=":previous" :disabled="!hasPrevious">
          <span class="pagination-label">Previous</span>
          <span class="pagination-title">{{previousTitle}}</span>
        </a>
        <a class="pagination-item" href=":next" :disabled="!hasNext">
          <span class="pagination-label">Next</span>
          <span class="pagination-title">{{nextTitle}}</span>
        </a>
      </nav>
    `,
    // Callbacks
    onPageChange: function(newPage, oldPage) {
      console.log('Page changed from', oldPage, 'to', newPage);
    },
    // Custom class names
    className: 'pagination',
    previousClassName: 'pagination-previous',
    nextClassName: 'pagination-next',
    disabledClassName: 'disabled',
    // Customize the order of pages
    getPageOrder: function(pages) {
      // Custom sorting logic
      return pages.sort((a, b) => a.title.localeCompare(b.title));
    },
    // Filter which pages should be included in navigation
    filter: function(page) {
      // Exclude pages with 'draft' in the front matter
      return !(page.frontmatter && page.frontmatter.draft);
    }
  }
};
```

## Advanced Usage

### Custom Position

You can specify where the pagination should appear:

```javascript
pagination: {
  position: 'top' // 'top', 'bottom', or 'both'
}
```

### Custom Templates

Create a custom template using the `template` option. The template can include:

- `:previous` - URL of the previous page
- `:next` - URL of the next page
- `{{previousTitle}}` - Title of the previous page
- `{{nextTitle}}` - Title of the next page
- `:hasPrevious` - Boolean indicating if there is a previous page
- `:hasNext` - Boolean indicating if there is a next page

### Styling

```css
/* Pagination container */
.docsify-pagination-container {
  margin: 2em 0;
  padding: 1em 0;
  border-top: 1px solid #eee;
  border-bottom: 1px solid #eee;
}

/* Pagination navigation */
.pagination {
  display: flex;
  justify-content: space-between;
  list-style: none;
  padding: 0;
  margin: 0;
}

/* Pagination items */
.pagination-item {
  display: flex;
  flex-direction: column;
  padding: 0.75em 1em;
  border-radius: 4px;
  text-decoration: none;
  color: #2c3e50;
  transition: all 0.2s ease;
}

.pagination-item:hover {
  background: #f5f5f5;
  text-decoration: none;
}

/* Disabled state */
.pagination-item[disabled] {
  pointer-events: none;
  opacity: 0.5;
}

/* Labels */
.pagination-label {
  font-size: 0.8em;
  color: #7f8c8d;
  margin-bottom: 0.25em;
}

/* Titles */
.pagination-title {
  font-weight: 500;
}

/* Dark theme */
[data-theme="dark"] .pagination-item {
  color: #e0e0e0;
}

[data-theme="dark"] .pagination-item:hover {
  background: #2d2d2d;
}

/* Responsive */
@media (max-width: 768px) {
  .pagination {
    flex-direction: column;
    gap: 0.5em;
  }
  
  .pagination-item {
    padding: 0.5em;
  }
}
```

## Keyboard Navigation

The plugin adds keyboard navigation by default:

- **Left Arrow**: Go to previous page
- **Right Arrow**: Go to next page

## Best Practices

1. **Consistent Structure** - Organize your documentation in a logical order
2. **Clear Labels** - Use descriptive page titles
3. **Mobile-Friendly** - Test pagination on different screen sizes
4. **Accessibility** - Ensure proper contrast and keyboard navigation
5. **Performance** - Consider disabling for very large documentation sets

## Troubleshooting

### Pagination Not Appearing
1. Check browser console for errors
2. Verify the plugin is loaded after Docsify
3. Ensure you have multiple pages in your documentation

### Incorrect Page Order
1. Check your `_sidebar.md` for correct page order
2. Verify the `getPageOrder` function if using custom sorting
3. Check for any filters that might be excluding pages

## Browser Support

- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)
- IE 11 (with polyfills)

## Example

```markdown
# Page 1

This is the first page content.

<!-- Pagination will appear here -->
```

## Last Updated
2025-06-28 01:10:00

*This file was last updated manually.*
