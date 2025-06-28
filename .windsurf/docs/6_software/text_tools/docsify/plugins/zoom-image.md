# Zoom Image Plugin

## Overview
The Zoom Image plugin adds the ability to zoom in on images in your Docsify documentation, providing a better viewing experience for detailed diagrams, screenshots, and other visual content.

## Features

- Click to zoom images
- Smooth animations
- Mobile-friendly pinch-to-zoom
- Keyboard navigation support
- Customizable zoom levels
- Responsive design

## Installation

Add the following to your `index.html`:

```html
<script src="//cdn.jsdelivr.net/npm/docsify-zoom-image/dist/zoom-image.min.js"></script>
```

## Basic Usage

Simply add images to your markdown as usual:

```markdown
![Example Image](path/to/image.png)
```

Images will automatically be made zoomable. Click on an image to zoom in, and click again or press Escape to zoom out.

## Configuration

```javascript
window.$docsify = {
  zoomImage: {
    // Basic options
    selector: '.markdown-section img', // Image selector
    exclude: '.no-zoom',              // Excluded images
    // Zoom behavior
    scale: 1.5,                       // Default zoom level
    maxScale: 3,                      // Maximum zoom level
    minScale: 1,                      // Minimum zoom level
    // Interaction
    wheelable: true,                  // Enable mouse wheel zoom
    draggable: true,                  // Enable drag to pan
    lockDragAxis: false,              // Lock drag to one axis
    // Animation
    duration: 200,                    // Animation duration in ms
    easing: 'ease',                   // Animation easing
    // UI
    showZoomInOutIcons: true,         // Show zoom in/out buttons
    showCloseButton: true,            // Show close button
    // Callbacks
    onZoomIn: function(img) {
      console.log('Zoomed in on image:', img.src);
    },
    onZoomOut: function() {
      console.log('Zoomed out');
    },
    // Custom templates
    templates: {
      zoomIn: '<span class="zoom-icon zoom-in">+</span>',
      zoomOut: '<span class="zoom-icon zoom-out">-</span>',
      close: '<span class="zoom-close">×</span>'
    },
    // Custom CSS class names
    classNames: {
      zoomContainer: 'zoom-container',
      zoomOverlay: 'zoom-overlay',
      zoomImage: 'zoom-img',
      zoomActive: 'zoom-active',
      zoomIn: 'zoom-in',
      zoomOut: 'zoom-out',
      close: 'zoom-close'
    },
    // Custom styles
    styles: {
      overlay: 'background-color: rgba(0, 0, 0, 0.85)',
      zIndex: 1000
    }
  }
};
```

## Advanced Usage

### Custom Image Selector

```javascript
zoomImage: {
  selector: '.markdown-section img:not(.no-zoom)'
}
```

### Custom Zoom Levels

```javascript
zoomImage: {
  scale: 1.2,     // Default zoom level (120%)
  maxScale: 4,    // Maximum zoom level (400%)
  minScale: 0.8   // Minimum zoom level (80%)
}
```

### Programmatic Control

```javascript
// Zoom an image programmatically
const img = document.querySelector('img');
DocsifyZoomImage.zoom(img, {
  scale: 2,
  x: 100,
  y: 100
});

// Close zoom
DocsifyZoomImage.close();

// Check if zoomed
const isZoomed = DocsifyZoomImage.isZoomed();
```

## Styling

### Custom CSS

```css
/* Zoom container */
.zoom-overlay {
  background-color: rgba(0, 0, 0, 0.9) !important;
  z-index: 1000;
}

/* Zoomed image */
.zoom-img {
  cursor: zoom-out;
  transition: transform 0.2s ease;
  max-width: 90%;
  max-height: 90%;
}

/* Zoom controls */
.zoom-icon {
  position: fixed;
  right: 20px;
  background: rgba(0, 0, 0, 0.5);
  color: white;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  cursor: pointer;
  z-index: 1001;
  user-select: none;
}

.zoom-in {
  bottom: 80px;
}

.zoom-out {
  bottom: 20px;
}

.zoom-close {
  top: 20px;
  right: 20px;
  font-size: 30px;
}

/* Hover effects */
.zoom-icon:hover {
  background: rgba(0, 0, 0, 0.8);
}

/* Dark theme */
[data-theme="dark"] .zoom-overlay {
  background-color: rgba(0, 0, 0, 0.95) !important;
}

/* Responsive adjustments */
@media (max-width: 768px) {
  .zoom-icon {
    width: 36px;
    height: 36px;
    font-size: 20px;
  }
  
  .zoom-close {
    font-size: 28px;
  }
}
```

## Best Practices

1. **Optimize Images** - Large images can cause performance issues
2. **Provide Alt Text** - For accessibility
3. **Consider Mobile Users** - Test touch interactions
4. **Use Appropriate Sizes** - Don't rely solely on zoom for readability
5. **Add Captions** - When necessary for context

## Troubleshooting

### Images Not Zooming
1. Check browser console for errors
2. Verify the plugin is loaded after Docsify
3. Check if the image selector matches your HTML structure

### Performance Issues
1. Optimize large images
2. Consider lazy loading for images below the fold
3. Reduce the number of zoomable images on a single page

## Browser Support

- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)
- Mobile Safari (iOS 10+)
- Chrome for Android

## Example

```markdown
# Zoomable Image Example

Here's an example of a zoomable image:

![Sample Diagram](path/to/diagram.png)

And here's an image that won't zoom (with the 'no-zoom' class):

![Non-zoomable](path/to/other.png){.no-zoom}
```

## Last Updated
2025-06-28 01:20:00

*This file was last updated manually.*
