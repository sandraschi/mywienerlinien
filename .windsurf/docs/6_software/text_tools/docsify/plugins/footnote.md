# Footnote Plugin

## Overview
The Footnote plugin adds support for Markdown footnotes in your Docsify documentation, allowing you to add references, citations, and additional information without cluttering the main content.

## Features

- Simple Markdown syntax for footnotes
- Automatic numbering
- Backlinks from footnotes to their references
- Responsive design
- Customizable appearance

## Installation

Add the following to your `index.html`:

```html
<script src="//cdn.jsdelivr.net/npm/docsify-footnote/dist/plugin.min.js"></script>
```

## Basic Usage

### Inline Footnotes

```markdown
Here's a simple footnote[^1] and another one[^longnote].

[^1]: This is the first footnote.
[^longnote]: Here's one with multiple blocks.

    Subsequent paragraphs are indented to show they belong to the same footnote.
```

### Reference-Style Footnotes

```markdown
Here's a simple footnote[^1] and another one[^longnote].

[^1]: This is the first footnote.
[^longnote]: Here's one with multiple blocks.

    Subsequent paragraphs are indented to show they belong to the same footnote.
```

## Configuration

```javascript
window.$docsify = {
  footnote: {
    // Basic options
    prefix: 'footnote-',  // Prefix for footnote IDs
    title: 'Footnotes',   // Title for the footnotes section
    // Position: 'bottom' (default), 'section', or 'end'
    position: 'bottom',
    // Styling
    className: 'footnotes',
    // Callbacks
    onInit: function() {
      console.log('Footnote plugin initialized');
    },
    // Custom template
    template: `
      <section class="footnotes">
        <h2>{{title}}</h2>
        <ol>
          {{#each footnotes}}
            <li id="{{id}}">
              {{{content}}}
              <a href="#{{refId}}" class="footnote-backref">↩</a>
            </li>
          {{/each}}
        </ol>
      </section>
    `,
    // Filter which footnotes to process
    filter: function(footnote) {
      // Example: Skip footnotes with specific content
      return !footnote.content.includes('skip-me');
    },
    // Custom renderer
    renderer: function(footnotes, template) {
      // Custom rendering logic
      return template
        .replace('{{title}}', this.title)
        .replace('{{#each footnotes}}', footnotes.map(fn => 
          `<li id="${fn.id}">${fn.content}<a href="#${fn.refId}" class="footnote-backref">↩</a></li>`
        ).join(''));
    }
  }
};
```

## Advanced Usage

### Multiple References to the Same Footnote

```markdown
You can use the same footnote multiple times[^note1][^note1].

[^note1]: This is a reusable footnote.
```

### Inline Footnotes with Custom IDs

```markdown
Here's a footnote with a custom ID[^custom-id].

[^custom-id]: This is a footnote with a custom ID.
```

### Styling

```css
/* Footnotes container */
.footnotes {
  margin-top: 2em;
  padding-top: 1em;
  border-top: 1px solid #eee;
  font-size: 0.9em;
  color: #666;
}

/* Footnote title */
.footnotes h2 {
  font-size: 1.2em;
  margin-bottom: 0.5em;
}

/* Footnote list */
.footnotes ol {
  padding-left: 1.5em;
}

/* Footnote item */
.footnotes li {
  margin-bottom: 0.5em;
  position: relative;
  padding-left: 1em;
  text-indent: -1em;
}

/* Footnote reference in text */
.footnote-ref {
  font-size: 0.75em;
  vertical-align: super;
  line-height: 1;
  margin-left: 0.2em;
  color: #42b983;
  text-decoration: none;
  font-weight: bold;
}

/* Backlink from footnote to reference */
.footnote-backref {
  margin-left: 0.5em;
  text-decoration: none;
  color: #42b983;
  font-weight: bold;
}

/* Hover states */
.footnote-ref:hover,
.footnote-backref:hover {
  text-decoration: underline;
}

/* Dark theme */
[data-theme="dark"] .footnotes {
  border-color: #444;
  color: #aaa;
}

[data-theme="dark"] .footnote-ref,
[data-theme="dark"] .footnote-backref {
  color: #4d9375;
}
```

## Best Practices

1. **Keep footnotes concise** - They should provide additional context, not essential information
2. **Use meaningful references** - Make it clear what the footnote refers to
3. **Limit their use** - Too many footnotes can be distracting
4. **Test rendering** - Check how they appear on different devices
5. **Consider accessibility** - Ensure good color contrast and keyboard navigation

## Troubleshooting

### Footnotes Not Appearing
1. Check browser console for errors
2. Verify the plugin is loaded after Docsify
3. Ensure proper Markdown syntax is used

### Formatting Issues
1. Check for missing or extra spaces
2. Verify proper indentation for multi-line footnotes
3. Check for conflicting CSS rules

## Browser Support

- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)
- IE 11 (with polyfills)

## Example

```markdown
Here's a paragraph with a footnote[^1] and another reference to the same footnote[^1].

[^1]: This is a footnote that can be referenced multiple times.

Here's another footnote[^second] with multiple paragraphs.

[^second]: This is a more detailed footnote.

    Additional paragraphs in a footnote must be indented.
    
    > Blockquotes can be used in footnotes too.
```

## Last Updated
2025-06-28 01:15:00

*This file was last updated manually.*
