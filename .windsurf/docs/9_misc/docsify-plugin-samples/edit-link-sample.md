# Edit Link Plugin - Complete Guide

## Introduction

The Edit Link plugin adds an "Edit this page" link to your documentation, allowing users to quickly edit the current page's source file on GitHub, GitLab, or other supported platforms.

## Basic Configuration

### GitHub Repository

```javascript
window.$docsify = {
  repo: 'username/repo', // GitHub repository
  // OR
  repo: 'https://github.com/username/repo', // Full URL
  
  // Customize the link text
  editLinkText: 'Edit this page',
  
  // Customize the link title (tooltip)
  editLinkTitle: 'Edit this page on GitHub',
  
  // Enable/disable the edit link
  editLink: true
};
```

### GitLab Repository

```javascript
window.$docsify = {
  repo: 'https://gitlab.com/username/repo',
  editLink: {
    pattern: 'https://gitlab.com/username/repo/-/edit/:branch/:path',
    text: 'Edit on GitLab'
  }
};
```

## Advanced Configuration

### Custom Edit Pattern

```javascript
window.$docsify = {
  repo: 'username/repo',
  editLink: {
    pattern: 'https://github.com/username/repo/edit/:branch/:path',
    text: 'Improve this page',
    noEmoji: false,
    position: 'top', // 'top' or 'bottom'
    
    // Custom function to generate the edit URL
    formatLink: function (repo, path) {
      // repo: The repository URL
      // path: The file path relative to the docs root
      
      // Example: Add a custom query parameter
      return repo + '/edit/main/docs/' + path + '?ref=docs';
    }
  }
};
```

### Multiple Edit Links

You can add multiple edit links for different sections:

```javascript
window.$docsify = {
  repo: 'username/repo',
  editLink: [
    {
      pattern: 'https://github.com/username/repo/edit/main/docs/:path',
      text: 'Edit on GitHub',
      match: '^docs/'
    },
    {
      pattern: 'https://gitlab.com/username/other-repo/edit/main/docs/:path',
      text: 'Edit on GitLab',
      match: '^other-docs/'
    }
  ]
};
```

## Custom Styling

### Basic Styling

```css
/* Edit link container */
.edit-link {
  display: inline-block;
  margin: 10px 0;
  font-size: 14px;
}

/* Edit link */
.edit-link a {
  color: #4CAF50;
  text-decoration: none;
  display: inline-flex;
  align-items: center;
  padding: 4px 8px;
  border-radius: 4px;
  transition: all 0.3s ease;
  border: 1px solid #e0e0e0;
}

.edit-link a:hover {
  background-color: #f5f5f5;
  color: #388E3C;
  text-decoration: none;
}

/* Icon */
.edit-link svg {
  margin-right: 4px;
  width: 14px;
  height: 14px;
  fill: currentColor;
}

/* Dark theme support */
[data-theme="dark"] .edit-link a {
  color: #81C784;
  border-color: #424242;
}

[data-theme="dark"] .edit-link a:hover {
  background-color: #333;
  color: #A5D6A7;
}
```

### Advanced Styling with Icons

```css
/* Add an icon using pseudo-elements */
.edit-link a::before {
  content: '✏️';
  margin-right: 4px;
  font-size: 0.9em;
}

/* Or use a custom icon font */
@import url('https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css');

.edit-link a::before {
  content: '\f044'; /* FontAwesome edit icon */
  font-family: 'Font Awesome 5 Free';
  font-weight: 900;
  margin-right: 6px;
  font-size: 0.9em;
}
```

## Custom Position

### Top of the Page

```javascript
window.$docsify = {
  // ... other config
  plugins: [
    function(hook, vm) {
      hook.mounted(function() {
        // Add edit link to the top of the content
        const content = document.querySelector('.content');
        if (content) {
          const editLink = document.createElement('div');
          editLink.className = 'edit-link-top';
          editLink.innerHTML = `
            <a href="${vm.config.repo}/edit/main/${vm.route.file}" target="_blank">
              ✏️ Edit this page
            </a>
          `;
          content.insertBefore(editLink, content.firstChild);
        }
      });
    }
  ]
};
```

### Floating Button

```css
/* Floating edit button */
.edit-link-float {
  position: fixed;
  bottom: 20px;
  right: 20px;
  z-index: 100;
  background: #4CAF50;
  color: white !important;
  padding: 10px 15px;
  border-radius: 50px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.2);
  display: flex;
  align-items: center;
  text-decoration: none;
  transition: all 0.3s ease;
}

.edit-link-float:hover {
  background: #388E3C;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0,0,0,0.25);
  color: white;
  text-decoration: none;
}

.edit-link-float::before {
  content: '✏️';
  margin-right: 6px;
}
```

## Best Practices

1. **Clear Labeling**
   - Use clear, action-oriented text (e.g., "Edit this page", "Improve this doc")
   - Consider adding an icon for better visibility

2. **Positioning**
   - Place the edit link where users expect it (top or bottom of the page)
   - Make sure it's visible but not distracting

3. **Accessibility**
   - Add appropriate ARIA labels
   - Ensure sufficient color contrast
   - Make the link keyboard-navigable

4. **Mobile Considerations**
   - Ensure the link is tappable on mobile devices
   - Consider a floating button for better mobile UX

## Troubleshooting

- **Link not appearing?**
  - Check if the `repo` is correctly configured
  - Verify the file exists in the repository
  - Check for JavaScript errors in the console

- **Incorrect URL?**
  - Verify the `pattern` matches your repository structure
  - Check if the branch name is correct
  - Ensure the path is being generated correctly

- **Styling issues?**
  - Check for CSS conflicts
  - Ensure your custom styles have higher specificity
  - Verify the theme compatibility

## Example Configurations

### GitHub Pages

```javascript
window.$docsify = {
  repo: 'username/repo',
  editLink: {
    pattern: 'https://github.com/username/repo/edit/main/docs/:path',
    text: 'Edit this page on GitHub',
    noEmoji: true
  }
};
```

### GitLab Pages

```javascript
window.$docsify = {
  repo: 'https://gitlab.com/username/repo',
  editLink: {
    pattern: 'https://gitlab.com/username/repo/-/edit/main/docs/:path',
    text: 'Edit on GitLab',
    position: 'bottom'
  }
};
```

### Custom Repository

```javascript
window.$docsify = {
  editLink: {
    pattern: 'https://custom-git.example.com/org/repo/edit/:branch/:path',
    text: 'Edit this page',
    // Custom text based on the current page
    formatText: function (path) {
      return 'Edit: ' + path.split('/').pop();
    }
  }
};
```

---

For more information, visit the [docsify-edit-link GitHub repository](https://github.com/njleonzhang/docsify-edit-link).
