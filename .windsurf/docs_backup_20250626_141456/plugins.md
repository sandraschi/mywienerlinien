# Documentation for Installed Plugins

## Table of Contents
- [Theme and UI](#theme-and-ui)
- [Content Enhancements](#content-enhancements)
- [Interactive Elements](#interactive-elements)
- [Version Control](#version-control)
- [Analytics and Integration](#analytics-and-integration)

## Theme and UI

### Dark/Light Theme Toggle
- **Plugin:** docsify-darklight-theme
- **Description:** Adds a toggle button to switch between light and dark themes
- **How to use:** Click the theme toggle button in the bottom-right corner
- **Configuration:** Automatic, no configuration needed

### Sidebar Customization
- **Plugin:** Built-in with custom CSS
- **Description:** Custom sidebar styling and behavior
- **Features:**
  - Collapsible sections
  - Fixed position
  - Responsive design

## Content Enhancements

### Mermaid Diagrams
- **Plugin:** mermaid.js
- **Description:** Create flowcharts, sequence diagrams, and more
- **Usage:**
  ```mermaid
  graph TD;
    A[Start] --> B{Is it?};
    B -->|Yes| C[OK];
    B -->|No| D[Not OK];
  ```

### PlantUML
- **Plugin:** docsify-plantuml
- **Description:** Create UML diagrams
- **Usage:**
  ```plantuml
  @startuml
  Alice -> Bob: Authentication Request
  Bob --> Alice: Authentication Response
  @enduml
  ```

### Kroki
- **Plugin:** docsify-kroki
- **Description:** Unified API for various diagram types
- **Supported formats:**
  - GraphViz
  - Ditaa
  - Vega
  - And more...

## Interactive Elements

### Charts
- **Plugin:** docsify-chart
- **Description:** Create beautiful charts
- **Usage:**
  ```chart
  ,category1,category2
  Jan, 65, 75
  Feb, 59, 65
  Mar, 80, 84
  ```

### Quizzes
- **Plugin:** docsify-quiz
- **Description:** Add interactive quizzes
- **Usage:**
  ```quiz
  # What is the capital of France?
  - [x] Paris
  - [ ] London
  - [ ] Berlin
  - [ ] Madrid
  ```

### Terminal Blocks
- **Plugin:** docsify-terminal-block
- **Description:** Styled terminal/command-line blocks
- **Usage:**
  ```terminal
  $ npm install
  $ npm start
  ```

## Version Control

### Versioning
- **Plugin:** docsify-versioning
- **Description:** Manage multiple documentation versions
- **Features:**
  - Version dropdown
  - Automatic version switching
  - Custom version labels

### Edit on GitHub
- **Plugin:** docsify-edit-link
- **Description:** Add "Edit on GitHub" links
- **Configuration:** Automatic based on repo URL

## Analytics and Integration

### Gitalk Comments
- **Plugin:** docsify-gitalk
- **Description:** Add GitHub issue-based comments
- **Features:**
  - GitHub authentication
  - Threaded comments
  - Markdown support

### GitHub Buttons
- **Plugin:** docsify-github
- **Description:** Add GitHub buttons (stars, forks, etc.)
- **Usage:**
  ```markdown
  [GitHub](https://github.com/username/repo)
  ```

### Reading Progress
- **Plugin:** docsify-progress
- **Description:** Show reading progress
- **Features:**
  - Progress bar at the top
  - Customizable colors
  - Smooth scrolling

## Troubleshooting

### Theme Toggle Not Visible
If the theme toggle button is not visible:
1. Ensure you've scrolled down the page
2. Check browser console for errors
3. Verify CSS is loading correctly

### Diagram Rendering Issues
If diagrams don't render:
1. Check for syntax errors
2. Ensure proper code block language is specified
3. Verify internet connection (for CDN resources)

## Customization
Most plugins can be customized by modifying the `window.$docsify` configuration in `index.html`. Refer to each plugin's documentation for specific options.
