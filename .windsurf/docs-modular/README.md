# Modular Documentation

A modular, maintainable documentation system built with HTML, CSS, and JavaScript.

## Project Structure

```
docs-modular/
├── assets/
│   ├── css/
│   │   └── main.css          # Main styles
│   ├── js/
│   │   └── main.js           # Main application logic
│   └── img/                  # Images and icons
├── components/               # Reusable UI components
│   ├── sidebar.js            # Sidebar component
│   └── ...
├── config/                   # Configuration files
│   └── config.js             # App configuration
├── content/                  # Documentation content (Markdown)
├── plugins/                  # Third-party plugins
└── index.html                # Main HTML file
```

## Features

- **Modular Architecture**: Components are organized for maintainability
- **Responsive Design**: Works on desktop and mobile devices
- **Theming**: Light and dark theme support
- **Search**: Client-side search functionality
- **Plugin System**: Easy to extend with plugins

## Getting Started

1. Clone the repository
2. Open `index.html` in a web server (for local development, you can use Live Server in VS Code)

## Development

### Adding a New Page

1. Add a new Markdown file in the `content/` directory
2. Update the navigation in `components/sidebar.js`

### Adding a Plugin

1. Add the plugin files to the `plugins/` directory
2. Update the plugin configuration in `config/config.js`
3. Load the plugin in `assets/js/main.js`

## Building for Production

For production, you might want to:

1. Minify CSS and JavaScript
2. Optimize images
3. Bundle and tree-shake dependencies

## License

MIT License
