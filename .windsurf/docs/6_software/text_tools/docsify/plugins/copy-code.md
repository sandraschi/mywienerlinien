# Copy Code Plugin

## Overview
The copy-code plugin adds a copy button to all code blocks in your documentation, making it easy for users to copy code snippets to their clipboard with a single click.

## Features

- One-click copy for code blocks
- Visual feedback when copying
- Customizable button position and appearance
- Supports multiple code blocks per page
- Works with syntax highlighting

## Installation

Add the following to your `index.html`:

```html
<script src="//cdn.jsdelivr.net/npm/docsify-copy-code"></script>
```

## Configuration

```javascript
window.$docsify = {
  copyCode: {
    buttonText: 'Copy to clipboard',  // Button text
    errorText: 'Error',              // Error text
    successText: 'Copied!',          // Success text
    // Button position: 'top' or 'bottom'
    buttonAlign: 'right',
    // Custom button HTML
    buttonHtml: `
      <div class="code-copy-btn" aria-label="Copy code">
        <span class="copy-icon">📋</span>
        <span class="copy-text">Copy</span>
      </div>
    `,
    // Custom styles
    style: `
      .code-copy-btn {
        cursor: pointer;
        position: absolute;
        top: 0.5em;
        right: 0.5em;
        padding: 0.25em 0.5em;
        border-radius: 3px;
        background: rgba(0,0,0,0.05);
        font-size: 0.8em;
        opacity: 0;
        transition: opacity 0.2s;
      }
      pre:hover .code-copy-btn {
        opacity: 1;
      }
    `
  }
};
```

## Usage

### Basic Usage
Simply include the plugin and it will automatically add copy buttons to all code blocks.

### Custom Button Text
```javascript
copyCode: {
  buttonText: 'Copy',
  errorText: 'Failed',
  successText: 'Copied!'
}
```

### Custom Button Position
```javascript
copyCode: {
  buttonAlign: 'top' // or 'bottom'
}
```

## Advanced Customization

### Custom Button HTML
You can completely customize the button's HTML:

```javascript
copyCode: {
  buttonHtml: `
    <div class="my-copy-btn">
      <svg>...</svg>
      <span>Copy Code</span>
    </div>
  `
}
```

### Custom Styling
Add your own CSS to style the copy button:

```javascript
copyCode: {
  style: `
    .code-copy-btn {
      background: #3498db;
      color: white;
      border: none;
      border-radius: 4px;
      padding: 4px 8px;
      font-size: 12px;
      cursor: pointer;
    }
    .code-copy-btn:hover {
      background: #2980b9;
    }
  `
}
```

## Events

The plugin triggers custom events you can listen to:

```javascript
document.addEventListener('copy', function(e) {
  console.log('Content copied to clipboard');
  console.log('Copied text:', e.detail.text);
});
```

## Browser Support

- Chrome 42+
- Firefox 41+
- Edge 12+
- Safari 10+
- Opera 29+

## Troubleshooting

### Copy Button Not Appearing
1. Verify the plugin script is loaded
2. Check for JavaScript errors in the console
3. Ensure you have code blocks in your markdown (```)

### Copy Functionality Not Working
1. Check browser console for errors
2. Verify the page is served over HTTP/HTTPS (required for clipboard API)
3. Try a different browser to rule out browser-specific issues

## Accessibility

The plugin includes basic ARIA attributes for accessibility:
- `aria-label` on the copy button
- `role="button"` for proper button semantics
- Keyboard navigation support

## Example

```markdown
```javascript
// Example code
function hello() {
  console.log('Hello, world!');
}
```
```

## Last Updated
2025-06-28 00:50:00

*This file was last updated manually.*
