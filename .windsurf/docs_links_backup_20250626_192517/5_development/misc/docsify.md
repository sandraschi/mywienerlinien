# Docsify Documentation Guide

## Table of Contents
- [Introduction](#introduction)
- [Quick Start](#quick-start)
- [Project Structure](#project-structure)
- [Configuration](#configuration)
- [Sidebar Management](#sidebar-management)
- [Auto-Generating Sidebars](#auto-generating-sidebars)
- [Customization](#customization)
- [Plugins](#plugins)
- [Deployment](#deployment)
- [Best Practices](#best-practices)

## Introduction

[Docsify](https://docsify.js.org/) is a powerful documentation site generator that converts Markdown files into a fully functional website with no static HTML generation required. It's perfect for:

- Project documentation
- Knowledge bases
- API documentation
- Technical documentation

Key features:
- No build process required
- Simple and lightweight
- Full-text search
- Multiple themes
- Plugin system
- SEO friendly

## Quick Start

### Installation

1. Install Node.js (required for npm)
2. Install docsify-cli globally:
   ```bash
   npm install -g docsify-cli
   ```

### Initialize a New Site

```bash
# Create a new directory
mkdir my-docs
cd my-docs

# Initialize a new docsify site
docsify init .
```

This creates:
- `index.html` - Main HTML file
- `README.md` - Homepage content
- `.nojekyll` - Prevents GitHub Pages from ignoring files starting with underscore

### Serve Locally

```bash
docsify serve .
```

Visit `http://localhost:3000` to see your documentation.

## Project Structure

```
my-docs/
├── .nojekyll
├── index.html
├── README.md
├── _sidebar.md      # Optional
├── _coverpage.md    # Optional
├── assets/          # Static files
└── guide/
    ├── getting-started.md
    └── configuration.md
```

## Configuration

### Basic `index.html`

```html
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>My Docs</title>
  <meta http-equiv="X-UA-Compatible" content="IE=edge,chrome=1">
  <meta name="viewport" content="width=device-width, user-scalable=no, initial-scale=1.0, maximum-scale=1.0, minimum-scale=1.0">
  <link rel="stylesheet" href="//cdn.jsdelivr.net/npm/docsify@4/themes/vue.css">
</head>
<body>
  <div id="app"></div>
  <script>
    window.$docsify = {
      name: 'My Docs',
      repo: 'user/repo',
      loadSidebar: true,
      subMaxLevel: 3,
      search: 'auto',
      auto2top: true,
      coverpage: true
    }
  </script>
  <script src="//cdn.jsdelivr.net/npm/docsify@4"></script>
  <script src="//cdn.jsdelivr.net/npm/docsify/lib/plugins/search.min.js"></script>
</body>
</html>
```

## Sidebar Management

### Manual Sidebar (`_sidebar.md`)

```markdown
- [Home](/)
- [Guide](guide/)
  - [Getting Started](guide/getting-started)
  - [Configuration](guide/configuration)
- [API Reference](api/)
  - [Endpoints](api/endpoints)
  - [Authentication](api/authentication)
```

### Auto-Generating Sidebars

For dynamic sidebar generation, you can use a build script. Create a `build-sidebar.js`:

```javascript
const fs = require('fs');
const path = require('path');

function generateSidebar(dir, basePath = '') {
  const files = fs.readdirSync(dir);
  let sidebar = [];
  
  files.forEach(file => {
    const fullPath = path.join(dir, file);
    const stat = fs.statSync(fullPath);
    
    if (stat.isDirectory()) {
      // Skip hidden directories
      if (file.startsWith('.')) return;
      
      const children = generateSidebar(fullPath, path.join(basePath, file));
      if (children.length > 0) {
        sidebar.push({
          title: file.charAt(0).toUpperCase() + file.slice(1).replace(/-/g, ' '),
          children: children
        });
      }
    } else if (file.endsWith('.md') && file !== 'README.md' && !file.startsWith('_')) {
      const name = path.basename(file, '.md');
      const displayName = name
        .split('-')
        .map(word => word.charAt(0).toUpperCase() + word.slice(1))
        .join(' ');
      
      sidebar.push({
        title: displayName,
        path: path.join(basePath, name).replace(/\\/g, '/')
      });
    }
  });
  
  return sidebar;
}

const sidebar = generateSidebar('.');
const sidebarContent = [];

function formatSidebar(items, level = 0) {
  items.forEach(item => {
    const indent = '  '.repeat(level);
    if (item.children) {
      sidebarContent.push(`${indent}- ${item.title}`);
      formatSidebar(item.children, level + 1);
    } else {
      sidebarContent.push(`${indent}- [${item.title}](${item.path})`);
    }
  });
}

formatSidebar(sidebar);

// Write to _sidebar.md
fs.writeFileSync('_sidebar.md', sidebarContent.join('\n'));
```

Run with:
```bash
node build-sidebar.js
```

## Customization

### Themes

Docsify comes with several themes:
- `vue.css` (default)
- `buble.css`
- `dark.css`
- `pure.css`

Change the theme in `index.html`:
```html
<link rel="stylesheet" href="//cdn.jsdelivr.net/npm/docsify@4/themes/dark.css">
```

### Custom CSS

Add a `style.css` file and include it in `index.html`:

```html
<link rel="stylesheet" href="style.css">
```

## Plugins

### Search

Enable in `index.html`:
```html
<script>
  window.$docsify = {
    search: 'auto', // or 'auto', 'auto-escaped', or options object
  };
</script>
<script src="//cdn.jsdelivr.net/npm/docsify/lib/plugins/search.min.js"></script>
```

### Google Analytics

```html
<script>
  window.$docsify = {
    ga: 'UA-XXXXX-Y'
  };
</script>
<script src="//cdn.jsdelivr.net/npm/docsify/lib/plugins/ga.min.js"></script>
```

## Deployment

### GitHub Pages

1. Create a `gh-pages` branch
2. Push your docs to this branch
3. Enable GitHub Pages in your repository settings

### Netlify

1. Connect your repository to Netlify
2. Set the build command to: `docsify serve .`
3. Set the publish directory to: `.`

## Best Practices

1. **Organize Content**
   - Group related content in directories
   - Use consistent naming (kebab-case for files)
   - Keep README.md in each directory

2. **Versioning**
   - Use Git tags for versions
   - Create a `versions` directory for multiple versions
   - Update the sidebar for each version

3. **Performance**
   - Split large documents into smaller ones
   - Use relative links
   - Optimize images

4. **SEO**
   - Add meta descriptions
   - Use meaningful page titles
   - Create a sitemap

5. **Accessibility**
   - Use semantic HTML
   - Add alt text to images
   - Ensure sufficient color contrast

## Troubleshooting

- **Sidebar not updating**: Clear your browser cache
- **Changes not showing**: Ensure the server is running and you've saved files
- **404 errors**: Check file paths and case sensitivity

## Resources

- [Official Documentation](https://docsify.js.org/)
- [GitHub Repository](https://github.com/docsifyjs/docsify/)
- [Awesome Docsify](https://github.com/docsifyjs/awesome-docsify)
