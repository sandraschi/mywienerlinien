# KaTeX Plugin

## Overview
The KaTeX plugin integrates the KaTeX typesetting library into Docsify, allowing you to render mathematical notation in your documentation using LaTeX syntax.

## Features

- Fast rendering of mathematical notation
- Server-side rendering support
- Responsive design
- Support for most LaTeX math mode commands
- Automatic equation numbering
- Custom macros

## Installation

1. Include KaTeX CSS and JS:

```html
<!-- KaTeX CSS -->
<link rel="stylesheet" href="//cdn.jsdelivr.net/npm/katex@0.16.0/dist/katex.min.css">
<!-- KaTeX JS -->
<script src="//cdn.jsdelivr.net/npm/katex@0.16.0/dist/katex.min.js"></script>
<!-- Docsify KaTeX plugin -->
<script src="//cdn.jsdelivr.net/npm/docsify-katex@latest/dist/docsify-katex.js"></script>
<!-- Optional: KaTeX auto-render extension -->
<script src="//cdn.jsdelivr.net/npm/katex@0.16.0/dist/contrib/auto-render.min.js"></script>
```

## Basic Usage

### Inline Math

Use `$...$` for inline math expressions:

```markdown
Euler's formula: $e^{i\pi} + 1 = 0$
```

### Display Math

Use `$$...$$` for displayed equations:

```markdown
$$
\begin{align}
  \nabla \times \mathbf{B} -\, \frac1c\, \frac{\partial\mathbf{E}}{\partial t} & = \frac{4\pi}{c}\mathbf{j} \\
  \nabla \cdot \mathbf{E} & = 4 \pi \rho \\
  \nabla \times \mathbf{E}\, +\, \frac1c\, \frac{\partial\mathbf{B}}{\partial t} & = \mathbf{0} \\
  \nabla \cdot \mathbf{B} & = 0
\end{align}
$$
```

## Configuration

```javascript
window.$docsify = {
  katex: {
    // KaTeX options (https://katex.org/docs/options.html)
    macros: {
      '\\Z': '\\mathbb{Z}',
      '\\R': '\\mathbb{R}'
    },
    throwOnError: false,
    errorColor: '#cc0000',
    delimiters: [
      {left: '$$', right: '$$', display: true},
      {left: '$', right: '$', display: false},
      {left: '\\(', right: '\\)', display: false},
      {left: '\\[', right: '\\]', display: true}
    ],
    // Plugin options
    autoRender: true,   // Auto-render math on page load
    autoRenderDelay: 0, // Delay before auto-rendering
    // Callbacks
    beforeRender: function(katex) {
      console.log('KaTeX is about to render');
    },
    afterRender: function() {
      console.log('KaTeX has finished rendering');
    },
    onError: function(error) {
      console.error('KaTeX error:', error);
    }
  }
};
```

## Advanced Usage

### Custom Macros

Define custom LaTeX macros in the configuration:

```javascript
katex: {
  macros: {
    '\\abs': '\\left|#1\\right|',
    '\\RR': '\\mathbb{R}',
    '\\CC': '\\mathbb{C}',
    '\\dd': '\\mathrm{d}'
  }
}
```

Then use them in your markdown:

```markdown
$$ \abs{\frac{d}{dx}f(x)}_{x=0} = 0 $$
```

### Manual Rendering

If you disable auto-rendering, you can render math manually:

```javascript
// Render all math in an element
DocsifyKatex.renderMathInElement(document.body);

// Render a specific element
const element = document.querySelector('.math-content');
DocsifyKatex.renderMathInElement(element);
```

## Supported LaTeX Commands

KaTeX supports most standard LaTeX math mode commands. For a complete list, see the [KaTeX Supported Functions](https://katex.org/docs/supported.html) documentation.

### Common Examples

#### Matrices

```markdown
$$
\begin{pmatrix}
  a & b \\
  c & d
\end{pmatrix}
\begin{bmatrix}
  a & b \\
  c & d
\end{bmatrix}
$$
```

#### Aligned Equations

```markdown
$$
\begin{aligned}
  f(x) &= (x+1)^2 \\
       &= x^2 + 2x + 1
\end{aligned}
$$
```

#### Chemical Equations

```markdown
$$
\ce{SO4^2- + Ba^2+ -> BaSO4 v}
$$
```

## Styling

### Custom CSS

```css
/* Math container */
.katex-display {
  margin: 1em 0;
  padding: 0.5em;
  overflow-x: auto;
  overflow-y: hidden;
}

/* Inline math */
.katex {
  font-size: 1.1em;
}

/* Dark theme support */
[data-theme="dark"] .katex {
  color: #e0e0e0;
}

/* Print styles */
@media print {
  .katex-display {
    page-break-inside: avoid;
  }
}
```

## Best Practices

1. **Use display math for complex equations** - Improves readability
2. **Define custom macros** - For frequently used notation
3. **Test rendering** - Check complex equations in different browsers
4. **Consider performance** - Large numbers of equations can impact page load
5. **Provide alternative text** - For accessibility

## Troubleshooting

### Equations Not Rendering
1. Check browser console for errors
2. Verify KaTeX and the plugin are loaded
3. Check for syntax errors in your LaTeX
4. Ensure proper delimiter usage (`$...$` vs `$$...$$`)

### Rendering Issues
1. Check for unsupported commands
2. Verify proper escaping of special characters
3. Check for CSS conflicts

## Browser Support

- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)
- IE 11 (with polyfills)

## Example

See the [KaTeX Demo](https://katex.org/#demo) for live examples and the [KaTeX Documentation](https://katex.org/docs/api.html) for the complete API reference.

## Last Updated
2025-06-28 01:05:00

*This file was last updated manually.*
