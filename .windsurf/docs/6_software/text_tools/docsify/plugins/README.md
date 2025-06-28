# Docsify Plugins

## Overview

Docsify's plugin system allows you to extend its functionality with additional features. This guide covers both built-in and community plugins, their configuration, and best practices.

## Table of Contents

1. [Built-in Plugins](#built-in-plugins)
2. [Community Plugins](#community-plugins)
3. [Creating Custom Plugins](#creating-custom-plugins)
4. [Plugin Configuration](#plugin-configuration)
5. [Best Practices](#best-practices)
6. [Troubleshooting](#troubleshooting)

## Built-in Plugins

### Search

Add full-text search functionality to your documentation.

```javascript
window.$docsify = {
  search: {
    maxAge: 86400000, // Expiration time in milliseconds
    paths: 'auto',
    placeholder: 'Search...',
    noData: 'No Results!',
    depth: 6,
    hideOtherSidebarContent: false
  }
}
```

### Zoom Image

Enable click-to-zoom for images.

```javascript
window.$docsify = {
  zoomImage: true
}
```

### Copy to Clipboard

Add copy buttons to code blocks.

```javascript
window.$docsify = {
  copyCode: {
    buttonText: 'Copy',
    errorText: 'Error',
    successText: 'Copied!'
  }
}
```

### Pagination

Add previous/next page navigation.

```javascript
window.$docsify = {
  pagination: {
    previousText: 'Previous',
    nextText: 'Next',
    crossChapter: true,
    crossChapterText: true
  }
}
```

## Community Plugins

### Installation

1. Install via npm:
   ```bash
   npm install docsify-plugin-name --save
   ```

2. Or use CDN:
   ```html
   <script src="//cdn.jsdelivr.net/npm/docsify-plugin-name"></script>
   ```

### Recommended Plugins

| Plugin | Description |
|--------|-------------|
| [docsify-sidebar-collapse](sidebar-collapse.md) | Collapsible sidebar sections |
| [docsify-tabs](tabs.md) | Tabbed content |
| [docsify-pagination](pagination.md) | Enhanced pagination |
| [docsify-darklight-theme](darklight-theme.md) | Dark/light theme toggle |
| [docsify-mermaid](mermaid.md) | Mermaid diagram support |
| [docsify-katex](katex.md) | Math typesetting |
| [docsify-plantuml](plantuml.md) | PlantUML diagram support |

## Creating Custom Plugins

### Basic Structure

```javascript
// my-plugin.js
window.$docsify = window.$docsify || {};
window.$docsify.plugins = [].concat(function (hook, vm) {
  // Plugin code here
  hook.init(function() {
    // Runs when the script is first loaded
  });

  hook.beforeEach(function(content) {
    // Runs before each markdown file is processed
    return content;
  });

  hook.afterEach(function(html, next) {
    // Runs after each markdown file is processed
    next(html);
  });

  hook.doneEach(function() {
    // Runs after the initial page is loaded
  });

  hook.mounted(function() {
    // Runs after the initial Vue instance is mounted
  });
}, window.$docsify.plugins || []);
```

### Hooks Reference

| Hook | Description |
|------|-------------|
| `init` | Runs when the script is first loaded |
| `beforeEach` | Runs before each markdown file is processed |
| `afterEach` | Runs after each markdown file is processed |
| `doneEach` | Runs after the initial page is loaded |
| `mounted` | Runs after the initial Vue instance is mounted |
| `ready` | Runs after the router is ready |

## Plugin Configuration

### Global Configuration

```javascript
window.$docsify = {
  // Plugin configurations
  myPlugin: {
    option1: 'value1',
    option2: 'value2'
  }
}
```

### Plugin Options

Each plugin can define its own configuration options. Refer to the plugin's documentation for available options.

## Best Practices

### Performance

- Load only necessary plugins
- Use async/defer for script loading
- Minify plugin code for production

### Security

- Only use plugins from trusted sources
- Keep plugins updated
- Review plugin code before use

### Maintenance

- Document plugin configurations
- Test plugins with new Docsify versions
- Have a rollback plan

## Troubleshooting

### Common Issues

#### Plugin Not Loading
- Check browser console for errors
- Verify script is loaded correctly
- Check for version conflicts

#### Plugin Configuration Not Working
- Verify configuration syntax
- Check for typos in option names
- Ensure plugin is compatible with your Docsify version

#### Styling Issues
- Check for CSS conflicts
- Verify plugin styles are loaded
- Check z-index values for overlapping elements

### Getting Help

- Check the plugin's GitHub repository
- Search GitHub issues
- Ask in the Docsify Gitter chat

## Last Updated
2025-06-28 02:35:00

*This file was last updated manually.*
