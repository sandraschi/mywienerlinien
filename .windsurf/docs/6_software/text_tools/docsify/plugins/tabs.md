# Tabs Plugin

## Overview
The tabs plugin allows you to organize content into tabbed interfaces within your documentation, making it easier to present related information in a compact and organized manner.

## Features

- Create tabbed interfaces with minimal syntax
- Support for nested tabs
- Responsive design
- Customizable appearance
- Keyboard navigation
- Deep linking to specific tabs

## Installation

Add the following to your `index.html`:

```html
<script src="//cdn.jsdelivr.net/npm/docsify-tabs@1"></script>
```

## Basic Usage

### Simple Tabs

````markdown
<!-- tabs:start -->

#### **English**
Hello!

#### **French**
Bonjour!

#### **Spanish**
¡Hola!

<!-- tabs:end -->
````

### Grouped Tabs

````markdown
<!-- tabs:start -->

#### **Tab A**
Content A

#### **Tab B**
Content B

<!-- tabs:end -->

Some content between tab groups

<!-- tabs:start -->

#### **Tab C**
Content C

#### **Tab D**
Content D

<!-- tabs:end -->
````

## Configuration

```javascript
window.$docsify = {
  tabs: {
    persist    : true,     // Persist active tab to localStorage
    sync       : true,     // Synchronize tab groups
    theme      : 'classic',// or 'material'
    tabComments: false,    // Show comments in tab labels
    tabHeadings: true,     // Use headings as tab labels
    // Callbacks
    onTabChange: function(tab) {
      console.log('Tab changed to:', tab);
    },
    // Styling
    styles: {
      nav: 'border-bottom: 1px solid #ddd;',
      tab: 'padding: 0.5em 1em;',
      active: 'border-bottom: 2px solid #42b983;'
    }
  }
};
```

## Advanced Usage

### Nested Tabs

````markdown
<!-- tabs:start -->

#### **Languages**

<!-- tabs:start -->

##### **English**
Hello!

##### **French**
Bonjour!

<!-- tabs:end -->

#### **Frameworks**

<!-- tabs:start -->

##### **React**
A JavaScript library

##### **Vue**
The Progressive JavaScript Framework

<!-- tabs:end -->

<!-- tabs:end -->
````

### Custom Tab Labels

````markdown
<!-- tabs:start -->

#### :fontawesome-brands-js: JavaScript

```javascript
console.log('Hello, World!');
```

#### :fontawesome-brands-python: Python

```python
print("Hello, World!")
```

<!-- tabs:end -->
````

## Styling

### Custom CSS

```css
/* Container */
.docsify-tabs {
  margin: 1em 0;
  border-radius: 4px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

/* Navigation */
.docsify-tabs__nav {
  border-bottom: 1px solid #e0e0e0;
  background: #f8f9fa;
  border-radius: 4px 4px 0 0;
}

/* Tabs */
.docsify-tabs__tab {
  padding: 0.75em 1.5em;
  font-weight: 500;
  color: #666;
  transition: all 0.2s ease;
}

.docsify-tabs__tab:hover {
  color: #2c3e50;
}

/* Active Tab */
.docsify-tabs__tab--active {
  color: #42b983;
  border-bottom: 2px solid #42b983;
}

/* Tab Content */
.docsify-tabs__content {
  padding: 1.5em;
  border: 1px solid #e0e0e0;
  border-top: none;
  border-radius: 0 0 4px 4px;
  background: #fff;
}
```

## JavaScript API

### Methods

```javascript
// Initialize tabs on a specific element
DocsifyTabs.init(element, options);

// Get all tab instances
const tabs = DocsifyTabs.instances;

// Programmatically switch to a tab
tabs[0].switchTo(2); // Switch to third tab in first group

// Events
document.addEventListener('docsifyTabsTabChange', function(e) {
  console.log('Tab changed:', e.detail);
});
```

## Best Practices

1. **Keep tab labels short and descriptive**
2. **Limit the number of tabs** (5-7 maximum)
3. **Use consistent styling** across your documentation
4. **Test on mobile** to ensure good responsiveness
5. **Consider accessibility** with proper ARIA attributes

## Troubleshooting

### Tabs Not Working
1. Check the browser console for errors
2. Ensure the plugin is loaded after Docsify
3. Verify the tab markers (`<!-- tabs:start -->` and `<!-- tabs:end -->`) are correct

### Styling Issues
1. Check for CSS conflicts
2. Ensure your custom styles have higher specificity
3. Verify the theme is properly loaded

## Browser Support

- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)
- IE 11 (with polyfills)

## Example

See the [official documentation](https://jhildenbiddle.github.io/docsify-tabs/) for live examples and additional configuration options.

## Last Updated
2025-06-28 00:55:00

*This file was last updated manually.*
