# Tailwind UI

Tailwind UI is a collection of professionally designed, pre-built components that you can drop into your Tailwind CSS projects. It's built by the creators of Tailwind CSS and provides accessible, responsive components that follow modern web standards.

## Table of Contents
- [Introduction](#introduction)
- [Installation](#installation)
- [Getting Started](#getting-started)
- [Core Concepts](#core-concepts)
- [Component Gallery](#component-gallery)
- [Customization](#customization)
- [Dark Mode](#dark-mode)
- [Responsive Design](#responsive-design)
- [Accessibility](#accessibility)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)
- [Resources](#resources)

## Introduction

Tailwind UI is a premium component library built on top of Tailwind CSS. It provides:

- 500+ professionally designed, fully responsive UI components
- Accessible HTML markup out of the box
- Built with Tailwind CSS v3.0+ in mind
- Designed to work with any framework (React, Vue, Svelte, etc.)
- Regular updates with new components and improvements

## Installation

### Prerequisites
- Node.js 12.13.0 or later
- A Tailwind UI license (purchase required)
- Tailwind CSS v3.0 or later installed in your project

### Setting Up

1. **Install Tailwind CSS** (if not already installed):
   ```bash
   npm install -D tailwindcss@latest postcss@latest autoprefixer@latest
   npx tailwindcss init
   ```

2. **Download Tailwind UI Components**
   - Log in to your Tailwind UI account
   - Navigate to the component you want to use
   - Copy the HTML/JSX/Vue code
   - Paste into your project

3. **Configure Tailwind CSS**
   Update your `tailwind.config.js` to include Tailwind UI's required plugins:
   ```javascript
   module.exports = {
     content: [
       './src/**/*.{html,js,jsx,ts,tsx}',
       // Add any other template paths here
     ],
     theme: {
       extend: {},
     },
     plugins: [
       require('@tailwindcss/forms'),
       require('@tailwindcss/typography'),
       // Add other plugins as needed
     ],
   }
   ```

## Getting Started

### Basic Example
Here's a simple navigation bar component:

```jsx
import React from 'react';

function Navbar() {
  return (
    <nav className="bg-white shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex-shrink-0 flex items-center">
            <span className="text-xl font-bold text-gray-900">Your Logo</span>
          </div>
          <div className="hidden sm:ml-6 sm:flex sm:space-x-8">
            <a
              href="#"
              className="border-indigo-500 text-gray-900 inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium"
            >
              Dashboard
            </a>
            <a
              href="#"
              className="border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700 inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium"
            >
              Team
            </a>
            <a
              href="#"
              className="border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700 inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium"
            >
              Projects
            </a>
          </div>
        </div>
      </div>
    </nav>
  );
}

export default Navbar;
```

## Core Concepts

### Utility-First Approach
Tailwind UI is built on Tailwind CSS's utility-first approach, where you style elements by applying pre-existing classes directly in your HTML.

### Component Structure
Each Tailwind UI component is:
- Self-contained with all necessary styles
- Built with accessibility in mind
- Fully responsive
- Easy to customize

### Customization
Customize components by:
1. Modifying the utility classes
2. Using Tailwind's configuration file
3. Adding custom CSS when needed

## Component Gallery

### Navigation
- Navbars
- Sidebar navigation
- Pagination
- Tabs
- Breadcrumbs

### Form Elements
- Input fields
- Select menus
- Checkboxes and radio buttons
- Toggles
- File inputs
- Form layouts

### Data Display
- Tables
- Lists
- Cards
- Stats
- Calendars
- Timelines

### Feedback
- Alerts
- Toasts
- Empty states
- Loading states
- Progress indicators

### Overlays
- Modals
- Dialogs
- Popovers
- Tooltips
- Dropdowns
- Slide-overs

### Marketing
- Headers
- Feature sections
- Testimonials
- Pricing tables
- CTAs
- Logos

## Customization

### Colors
Customize colors in `tailwind.config.js`:

```javascript
module.exports = {
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#f0f9ff',
          100: '#e0f2fe',
          200: '#bae6fd',
          300: '#7dd3fc',
          400: '#38bdf8',
          500: '#0ea5e9',
          600: '#0284c7',
          700: '#0369a1',
          800: '#075985',
          900: '#0c4a6e',
        },
      },
    },
  },
};
```

### Typography
Customize typography using Tailwind's `@tailwindcss/typography` plugin:

```javascript
// tailwind.config.js
module.exports = {
  theme: {
    extend: {
      typography: (theme) => ({
        DEFAULT: {
          css: {
            color: theme('colors.gray.800'),
            a: {
              color: theme('colors.blue.600'),
              '&:hover': {
                color: theme('colors.blue.800'),
              },
            },
          },
        },
      }),
    },
  },
  plugins: [
    require('@tailwindcss/typography'),
  ],
};
```

## Dark Mode

### Configuration
Enable dark mode in `tailwind.config.js`:

```javascript
// tailwind.config.js
module.exports = {
  darkMode: 'class', // or 'media' for system preference
  // ...
};
```

### Usage
Use the `dark:` variant to apply styles in dark mode:

```jsx
<div className="bg-white dark:bg-gray-800">
  <h1 className="text-gray-900 dark:text-white">Dark Mode Example</h1>
  <p className="text-gray-600 dark:text-gray-300">This is some text.</p>
</div>
```

### Toggle Dark Mode
Here's a simple dark mode toggle component:

```jsx
import { useState, useEffect } from 'react';
import { SunIcon, MoonIcon } from '@heroicons/react/24/outline';

export default function DarkModeToggle() {
  const [darkMode, setDarkMode] = useState(false);

  useEffect(() => {
    // Check for dark mode preference at the OS level
    if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
      setDarkMode(true);
    }
    
    // Listen for changes in the OS theme
    const darkModeMediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    const handleChange = (e) => setDarkMode(e.matches);
    darkModeMediaQuery.addEventListener('change', handleChange);
    
    // Clean up
    return () => darkModeMediaQuery.removeEventListener('change', handleChange);
  }, []);

  useEffect(() => {
    if (darkMode) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [darkMode]);

  return (
    <button
      onClick={() => setDarkMode(!darkMode)}
      className="p-2 rounded-lg text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700"
      aria-label={darkMode ? 'Switch to light mode' : 'Switch to dark mode'}
    >
      {darkMode ? (
        <SunIcon className="h-6 w-6" />
      ) : (
        <MoonIcon className="h-6 w-6" />
      )}
    </button>
  );
}
```

## Responsive Design

### Breakpoints
Tailwind's default breakpoints:
- `sm`: 640px
- `md`: 768px
- `lg`: 1024px
- `xl`: 1280px
- `2xl`: 1536px

### Example
```jsx
<div className="w-full md:w-1/2 lg:w-1/3 xl:w-1/4 p-4">
  <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
    <h3 className="text-lg font-medium text-gray-900 dark:text-white">Responsive Card</h3>
    <p className="mt-2 text-gray-600 dark:text-gray-300">
      This card will take up full width on mobile, half width on medium screens,
      one-third width on large screens, and one-quarter width on extra large screens.
    </p>
  </div>
</div>
```

## Accessibility

### Keyboard Navigation
All interactive components are keyboard accessible:
- Buttons and links are focusable
- Dropdowns and modals manage focus properly
- ARIA attributes are included where needed

### ARIA Attributes
Example of a custom accessible button:

```jsx
<button
  type="button"
  className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
  aria-label="Save changes"
  aria-busy="false"
  disabled={isLoading}
>
  {isLoading ? 'Saving...' : 'Save Changes'}
</button>
```

## Best Practices

### Component Composition
Break down complex UIs into smaller, reusable components:

```jsx
// components/Card.jsx
function Card({ title, description, icon: Icon }) {
  return (
    <div className="bg-white dark:bg-gray-800 overflow-hidden shadow rounded-lg">
      <div className="p-5">
        <div className="flex items-center">
          {Icon && (
            <div className="flex-shrink-0">
              <Icon className="h-6 w-6 text-gray-400" aria-hidden="true" />
            </div>
          )}
          <div className="ml-5 w-0 flex-1">
            <h3 className="text-lg font-medium text-gray-900 dark:text-white">
              {title}
            </h3>
            <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
              {description}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Card;
```

### Performance

1. **Purge CSS**
   Configure PurgeCSS to remove unused styles in production:
   ```javascript
   // tailwind.config.js
   module.exports = {
     purge: [
       './src/**/*.{js,jsx,ts,tsx}',
       './public/index.html',
     ],
     // ...
   };
   ```

2. **Code Splitting**
   Use dynamic imports for better performance:
   ```jsx
   import dynamic from 'next/dynamic';
   
   const HeavyComponent = dynamic(() => import('../components/HeavyComponent'));
   ```

## Troubleshooting

### Common Issues

1. **Styles Not Applying**
   - Ensure Tailwind CSS is properly installed and configured
   - Check that your content paths in `tailwind.config.js` are correct
   - Run the build process to regenerate your CSS

2. **Dark Mode Not Working**
   - Verify `darkMode` is set in `tailwind.config.js`
   - Ensure the `dark` class is being toggled on the `html` element
   - Check for conflicting styles that might be overriding dark mode

3. **Build Errors**
   - Make sure all required dependencies are installed
   - Check for syntax errors in your configuration files
   - Update to the latest versions of Tailwind CSS and related packages

## Resources

- [Official Documentation](https://tailwindui.com/documentation)
- [Tailwind CSS Docs](https://tailwindcss.com/docs)
- [Tailwind UI Components](https://tailwindui.com/components)
- [Hero Icons](https://heroicons.com/)
- [Tailwind Play](https://play.tailwindcss.com/)

## License

Tailwind UI requires a paid license for commercial use. Please refer to the [Tailwind UI License](https://tailwindui.com/license) for more information.
