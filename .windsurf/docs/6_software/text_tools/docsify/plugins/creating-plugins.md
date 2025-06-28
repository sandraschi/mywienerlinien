# Creating Custom Plugins for Docsify

## Overview

This guide covers how to create custom plugins for Docsify to extend its functionality. You'll learn the plugin architecture, common patterns, and best practices for developing robust plugins.

## Table of Contents

1. [Plugin Basics](#plugin-basics)
2. [Plugin Structure](#plugin-structure)
3. [Lifecycle Hooks](#lifecycle-hooks)
4. [Creating a Simple Plugin](#creating-a-simple-plugin)
5. [Advanced Plugin Patterns](#advanced-plugin-patterns)
6. [Testing Your Plugin](#testing-your-plugin)
7. [Publishing Your Plugin](#publishing-your-plugin)
8. [Best Practices](#best-practices)
9. [Common Pitfalls](#common-pitfalls)
10. [Examples and References](#examples-and-references)

## Plugin Basics

### What is a Docsify Plugin?
A Docsify plugin is a JavaScript function that hooks into Docsify's lifecycle to add or modify functionality. Plugins can:

- Modify the rendered content
- Add new features
- Interact with the Docsify instance
- Listen to and trigger events

### How Plugins Work

1. **Registration**: Plugins are registered using `window.$docsify.plugins`
2. **Initialization**: Docsify calls each plugin function during initialization
3. **Hooks**: Plugins can hook into various lifecycle events
4. **Execution**: Plugin code runs at specific points in the Docsify lifecycle

## Plugin Structure

### Basic Plugin Template

```javascript
// Basic plugin structure
function myPlugin(hook, vm) {
  // Called when the script is loaded
  hook.init(function() {
    // Initialize your plugin
  });

  // Called before parsing markdown
  hook.beforeEach(function(content) {
    // Modify content before parsing
    return content;
  });

  // Called after markdown is parsed
  hook.afterEach(function(html, next) {
    // Modify HTML after parsing
    next(html);
  });

  // Called when the Vue instance is mounted
  hook.doneEach(function() {
    // DOM is ready
  });
}

// Register the plugin
window.$docsify = window.$docsify || {};
window.$docsify.plugins = [].concat(myPlugin, window.$docsify.plugins || []);
```

### Plugin Configuration

```javascript
function myPlugin(hook, vm) {
  // Default options
  const defaults = {
    option1: true,
    option2: 'default',
    // ...
  };

  // Merge with user options
  const options = Object.assign({}, defaults, window.$docsify.myPlugin);
  
  // Plugin implementation
}

// Configuration example
window.$docsify = {
  // Other Docsify options...
  myPlugin: {
    option1: false,
    option2: 'custom'
  },
  plugins: [myPlugin]
};
```

## Lifecycle Hooks

### Available Hooks

| Hook | Description | Parameters | Return Value |
|------|-------------|------------|--------------|
| `init` | Called when the script is loaded | `function` | - |
| `mounted` | Called after the Docsify instance is mounted | - | - |
| `beforeEach` | Called before markdown is parsed | `content` | Modified content or `undefined` |
| `afterEach` | Called after markdown is parsed | `html`, `next` | Call `next(html)` |
| `doneEach` | Called after the new page is loaded | - | - |
| `ready` | Called after the initial HTML is ready | - | - |
| `pre` | Called before the page is loaded | `markdown` | Modified markdown or `undefined` |
| `post` | Called after the page is loaded | `html` | Modified HTML or `undefined` |

### Hook Usage Examples

```javascript
function myPlugin(hook, vm) {
  // 1. init - Called when the script is loaded
  hook.init(function() {
    console.log('Plugin initialized');
  });

  // 2. mounted - Called after the Vue instance is mounted
  hook.mounted(function() {
    console.log('Vue instance mounted');
  });

  // 3. beforeEach - Modify markdown before parsing
  hook.beforeEach(function(content) {
    // Add a custom header to each page
    return '<!-- Custom Header -->\n\n' + content;
  });

  // 4. afterEach - Modify HTML after parsing
  hook.afterEach(function(html, next) {
    // Add a custom footer to each page
    next(html + '\n<footer>Custom Footer</footer>');
  });

  // 5. doneEach - Called after the new page is loaded
  hook.doneEach(function() {
    console.log('Page loaded:', vm.route.path);
  });

  // 6. ready - Called after the initial HTML is ready
  hook.ready(function() {
    console.log('Initial HTML ready');
  });
}
```

## Creating a Simple Plugin

### Example: Word Count Plugin

Let's create a plugin that shows the word count for each page.

```javascript
function wordCountPlugin(hook, vm) {
  hook.afterEach(function(html, next) {
    // Count words in the content
    const text = html.replace(/<[^>]*>?/gm, ''); // Remove HTML tags
    const wordCount = text.trim().split(/\s+/).length;
    
    // Add word count to the end of the content
    const footer = `\n<div class="word-count">Word count: ${wordCount}</div>`;
    
    next(html + footer);
  });
  
  // Add some basic styling
  hook.mounted(function() {
    const style = document.createElement('style');
    style.textContent = `
      .word-count {
        margin-top: 2rem;
        padding: 0.5rem;
        background: #f5f5f5;
        border-radius: 4px;
        font-size: 0.9em;
        color: #666;
        text-align: right;
      }
    `;
    document.head.appendChild(style);
  });
}

// Register the plugin
window.$docsify = window.$docsify || {};
window.$docsify.plugins = [].concat(wordCountPlugin, window.$docsify.plugins || []);
```

### Example: Table of Contents Generator

```javascript
function tocPlugin(hook, vm) {
  hook.mounted(function() {
    // Add TOC container
    const main = document.querySelector('.content');
    const sidebar = document.querySelector('.sidebar');
    
    if (!sidebar) return;
    
    const toc = document.createElement('div');
    toc.className = 'toc';
    
    // Insert TOC after the sidebar
    sidebar.parentNode.insertBefore(toc, sidebar.nextSibling);
    
    // Style the TOC
    const style = document.createElement('style');
    style.textContent = `
      .toc {
        position: fixed;
        right: 2rem;
        top: 6rem;
        max-width: 250px;
        max-height: calc(100vh - 8rem);
        overflow-y: auto;
        padding: 1rem;
        background: #f8f9fa;
        border-radius: 4px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
      }
      .toc ul {
        list-style: none;
        padding: 0;
        margin: 0;
      }
      .toc li {
        margin: 0.5rem 0;
      }
      .toc a {
        color: #2c3e50;
        text-decoration: none;
        font-size: 0.9em;
      }
      .toc a:hover {
        text-decoration: underline;
      }
    `;
    document.head.appendChild(style);
  });
  
  hook.doneEach(function() {
    const toc = document.querySelector('.toc');
    if (!toc) return;
    
    // Get all headings
    const headings = document.querySelectorAll('h1, h2, h3, h4, h5, h6');
    let html = '<h3>Table of Contents</h3><ul>';
    
    // Generate TOC
    Array.from(headings).forEach((heading, index) => {
      // Skip if no text content
      if (!heading.textContent.trim()) return;
      
      // Create ID if it doesn't exist
      let id = heading.id;
      if (!id) {
        id = 'heading-' + index;
        heading.id = id;
      }
      
      // Add to TOC
      const level = parseInt(heading.tagName.substring(1));
      const indent = (level - 1) * 15;
      
      html += `
        <li style="margin-left: ${indent}px">
          <a href="#${id}">${heading.textContent}</a>
        </li>`;
    });
    
    html += '</ul>';
    toc.innerHTML = html;
  });
}

// Register the plugin
window.$docsify = window.$docsify || {};
window.$docsify.plugins = [].concat(tocPlugin, window.$docsify.plugins || []);
```

## Advanced Plugin Patterns

### 1. Plugin with Dependencies

```javascript
function pluginWithDeps(hook, vm) {
  // Check for required dependencies
  if (typeof someDependency === 'undefined') {
    console.error('Some dependency is required for this plugin');
    return;
  }
  
  // Plugin implementation
  hook.doneEach(function() {
    // Use the dependency
    someDependency.doSomething();
  });
}

// Load dependency dynamically
function loadDependency() {
  return new Promise((resolve, reject) => {
    if (typeof someDependency !== 'undefined') {
      return resolve(someDependency);
    }
    
    const script = document.createElement('script');
    script.src = 'https://example.com/some-dependency.js';
    script.onload = () => resolve(someDependency);
    script.onerror = reject;
    document.head.appendChild(script);
  });
}

// Initialize plugin after dependencies are loaded
loadDependency().then(() => {
  window.$docsify = window.$docsify || {};
  window.$docsify.plugins = [].concat(pluginWithDeps, window.$docsify.plugins || []);
}).catch(console.error);
```

### 2. Plugin with Configuration

```javascript
function configurablePlugin(hook, vm) {
  // Default configuration
  const defaults = {
    enabled: true,
    theme: 'light',
    position: 'bottom-right',
    // ... other options
  };
  
  // Merge with user configuration
  const config = Object.assign({}, defaults, window.$docsify.configurablePlugin);
  
  // Skip if disabled
  if (!config.enabled) return;
  
  // Apply theme
  document.documentElement.setAttribute('data-theme', config.theme);
  
  // Plugin implementation
  hook.doneEach(function() {
    // Use config values
    console.log('Plugin position:', config.position);
  });
  
  // Expose public API
  return {
    updateConfig: function(newConfig) {
      Object.assign(config, newConfig);
      // Handle config updates
    },
    getConfig: function() {
      return { ...config }; // Return a copy
    }
  };
}

// Configuration example
window.$docsify = {
  // Other Docsify options...
  configurablePlugin: {
    theme: 'dark',
    position: 'top-left'
  },
  plugins: [configurablePlugin]
};

// Access plugin instance
const pluginInstance = window.$docsify.plugins.find(
  p => p.name === 'configurablePlugin' || p.toString().includes('configurablePlugin')
)?.prototype;

// Use plugin API
if (pluginInstance?.updateConfig) {
  pluginInstance.updateConfig({ theme: 'dark' });
}
```

### 3. Event-Based Plugin

```javascript
function eventBasedPlugin(hook, vm) {
  // Custom events
  const events = {
    on: function(event, callback) {
      document.addEventListener(`docsify:${event}`, callback);
      return this;
    },
    emit: function(event, data) {
      document.dispatchEvent(new CustomEvent(`docsify:${event}`, { detail: data }));
      return this;
    }
  };
  
  // Listen to Docsify events
  hook.mounted(function() {
    console.log('Event-based plugin mounted');
  });
  
  // Example: Add a custom button
  hook.doneEach(function() {
    const btn = document.createElement('button');
    btn.className = 'custom-plugin-btn';
    btn.textContent = 'Click Me';
    btn.style.position = 'fixed';
    btn.style.bottom = '20px';
    btn.style.right = '20px';
    btn.style.zIndex = '1000';
    
    btn.addEventListener('click', () => {
      // Emit custom event
      events.emit('button:clicked', { time: new Date() });
    });
    
    document.body.appendChild(btn);
  });
  
  // Listen for custom events
  events.on('button:clicked', (e) => {
    console.log('Button was clicked at', e.detail.time);
  });
  
  // Expose events API
  return { events };
}

// Register the plugin
window.$docsify = window.$docsify || {};
window.$docsify.plugins = [].concat(eventBasedPlugin, window.$docsify.plugins || []);
```

## Testing Your Plugin

### 1. Unit Testing

```javascript
// test/plugin.test.js
const assert = require('assert');
const jsdom = require('jsdom');
const { JSDOM } = jsdom;

// Mock Docsify environment
const { document } = (new JSDOM('<!DOCTYPE html><div id="app"></div>')).window;
global.document = document;

// Import your plugin
const myPlugin = require('../src/my-plugin.js');

describe('My Plugin', function() {
  beforeEach(function() {
    // Reset before each test
    document.body.innerHTML = '<div id="app"></div>';
  });
  
  it('should initialize correctly', function() {
    const hook = {
      init: function(cb) { cb(); },
      mounted: function(cb) { cb(); },
      doneEach: function(cb) { cb(); }
    };
    
    const vm = { route: { path: '/' } };
    
    // This should not throw
    assert.doesNotThrow(() => myPlugin(hook, vm));
  });
  
  // Add more tests...
});
```

### 2. Integration Testing

```javascript
// test/integration.test.js
const puppeteer = require('puppeteer');
const path = require('path');

const PORT = 3000;

let browser;
let page;
let server;

describe('My Plugin Integration', function() {
  this.timeout(10000);
  
  before(async function() {
    // Start a test server
    const express = require('express');
    const app = express();
    app.use(express.static(path.join(__dirname, '..')));
    server = app.listen(PORT);
    
    // Launch browser
    browser = await puppeteer.launch();
    page = await browser.newPage();
  });
  
  after(async function() {
    await browser.close();
    server.close();
  });
  
  it('should load the plugin', async function() {
    await page.goto(`http://localhost:${PORT}/`);
    
    // Test that the plugin is working
    const result = await page.evaluate(() => {
      return document.querySelector('.my-plugin-element') !== null;
    });
    
    assert.strictEqual(result, true);
  });
  
  // Add more integration tests...
});
```

## Publishing Your Plugin

### 1. Package Structure

```
my-docsify-plugin/
├── dist/
│   └── my-plugin.min.js       # Minified version
├── src/
│   └── index.js               # Source code
├── test/                      # Tests
├── .gitignore
├── package.json
├── README.md
└── webpack.config.js          # Build configuration
```

### 2. package.json Example

```json
{
  "name": "docsify-my-plugin",
  "version": "1.0.0",
  "description": "A custom Docsify plugin",
  "main": "dist/my-plugin.min.js",
  "files": ["dist"],
  "scripts": {
    "build": "webpack --mode production",
    "dev": "webpack --watch --mode development",
    "test": "mocha",
    "prepublishOnly": "npm run build"
  },
  "keywords": ["docsify", "plugin"],
  "author": "Your Name",
  "license": "MIT",
  "devDependencies": {
    "webpack": "^5.0.0",
    "webpack-cli": "^4.0.0",
    "babel-loader": "^8.0.0",
    "@babel/core": "^7.0.0",
    "@babel/preset-env": "^7.0.0",
    "mocha": "^9.0.0",
    "puppeteer": "^10.0.0"
  },
  "peerDependencies": {
    "docsify": ">=4.0.0"
  }
}
```

### 3. webpack.config.js

```javascript
const path = require('path');
const TerserPlugin = require('terser-webpack-plugin');

module.exports = {
  entry: './src/index.js',
  output: {
    path: path.resolve(__dirname, 'dist'),
    filename: 'my-plugin.min.js',
    library: 'MyDocsifyPlugin',
    libraryTarget: 'umd',
    globalObject: 'this',
    umdNamedDefine: true
  },
  module: {
    rules: [
      {
        test: /\.js$/,
        exclude: /node_modules/,
        use: {
          loader: 'babel-loader',
          options: {
            presets: ['@babel/preset-env']
          }
        }
      }
    ]
  },
  optimization: {
    minimize: true,
    minimizer: [new TerserPlugin()]
  },
  externals: {
    docsify: 'docsify'
  }
};
```

### 4. Publishing to npm

```bash
# Login to npm (if not already logged in)
npm login

# Bump version (if needed)
npm version patch  # or minor, major

# Publish
npm publish
```

## Best Practices

1. **Keep it Simple**: Focus on doing one thing well
2. **Follow SemVer**: Use semantic versioning for releases
3. **Documentation**: Provide clear usage instructions and examples
4. **Error Handling**: Handle errors gracefully
5. **Performance**: Keep the plugin lightweight and efficient
6. **Compatibility**: Test with different Docsify versions
7. **Accessibility**: Ensure your plugin is accessible
8. **Testing**: Write tests for your plugin
9. **Minification**: Provide minified versions for production
10. **License**: Include an open-source license

## Common Pitfalls

1. **Global Namespace Pollution**: Avoid polluting the global namespace
2. **Memory Leaks**: Clean up event listeners and references
3. **Race Conditions**: Handle asynchronous operations properly
4. **CSS Conflicts**: Use specific class names to avoid conflicts
5. **Browser Support**: Test in different browsers
6. **Performance Impact**: Profile your plugin's performance
7. **Documentation**: Don't forget to document all options and APIs
8. **Error Handling**: Handle edge cases and invalid inputs
9. **Versioning**: Be careful with breaking changes
10. **Dependencies**: Minimize external dependencies

## Examples and References

### Official Plugins
- [docsify-copy-code](https://github.com/jperasmus/docsify-copy-code)
- [docsify-pagination](https://github.com/imyelo/docsify-pagination)
- [docsify-tabs](https://github.com/jhildenbiddle/docsify-tabs)
- [docsify-sidebar-collapse](https://github.com/iPeng6/docsify-sidebar-collapse)

### Community Plugins
- [docsify-darklight-theme](https://github.com/jhildenbiddle/docsify-darklight-theme)
- [docsify-mermaid](https://github.com/Leward/mermaid-docsify)
- [docsify-katex](https://github.com/upupming/docsify-katex)
- [docsify-edit-on-github](https://github.com/njleonzhang/docsify-edit-on-github)

### Resources
- [Docsify Plugin API](https://docsify.js.org/#/write-a-plugin)
- [Creating a Docsify Plugin](https://docsify.js.org/#/plugins?id=write-a-plugin)
- [Awesome Docsify](https://github.com/docsifyjs/awesome-docsify)

## Last Updated
2025-06-28 03:40:00

*This file was last updated manually.*
