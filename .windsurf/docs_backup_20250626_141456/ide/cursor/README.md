# Cursor IDE Setup

This guide covers the setup and usage of Cursor IDE, an AI-powered code editor with deep Git integration, for Windsurf projects.

## Table of Contents
- [Installation](#installation)
- [Features](#features)
- [Project Setup](#project-setup)
- [AI-Assisted Development](#ai-assisted-development)
- [Git Integration](#git-integration)
- [Custom Workflows](#custom-workflows)
- [Troubleshooting](#troubleshooting)

## Installation

### Prerequisites
- Windows 10/11, macOS 10.15+, or Linux
- Git 2.30.0 or later
- Node.js 16.x or later (for JavaScript/TypeScript projects)

### Windows Installation
1. Download the latest Cursor installer from [cursor.sh](https://cursor.sh)
2. Run the installer (`Cursor-Setup-x.x.x.exe`)
3. Follow the installation wizard
4. Launch Cursor from the Start menu

### macOS Installation
```bash
# Using Homebrew
brew install --cask cursor

# Or download directly
# 1. Download the .dmg file from cursor.sh
# 2. Open the downloaded .dmg
# 3. Drag Cursor.app to Applications
```

### Linux Installation
```bash
# Debian/Ubuntu
wget https://dl.cursor.sh/linux/deb/cursor_latest_amd64.deb
sudo dpkg -i cursor_latest_amd64.deb

# Arch Linux (AUR)
yay -S cursor
```

## Features

### AI-Powered Development
- **Code Completion**: Context-aware code suggestions
- **Chat Interface**: Natural language to code
- **Code Review**: AI-powered code reviews
- **Documentation Generation**: Auto-generate documentation

### Git Integration
- Visual diff tools
- Commit message generation
- Branch management
- Conflict resolution assistance

### Editor Features
- Multiple cursors
- Command palette
- Extensions support
- Integrated terminal
- Debugging tools

## Project Setup

### Opening a Project
1. Click "File" > "Open Folder"
2. Select your project directory
3. Cursor will automatically detect the project type

### Recommended Extensions
1. Open Extensions view (`Ctrl+Shift+X` or `Cmd+Shift+X`)
2. Search for and install:
   - ESLint
   - Prettier
   - Docker
   - YAML
   - GitLens

### Configuration
Create a `.cursor` directory in your project root for Cursor-specific settings:

```json
// .cursor/config.json
{
  "$schema": "https://cursor.sh/schema/cursor.schema.json",
  "editor": {
    "formatOnSave": true,
    "defaultFormatter": "esbenp.prettier-vscode"
  },
  "ai": {
    "codeCompletion": {
      "enabled": true,
      "provider": "openai"
    },
    "chat": {
      "model": "gpt-4"
    }
  },
  "files": {
    "exclude": ["node_modules", ".git"]
  }
}
```

## AI-Assisted Development

### Using the Chat Interface
1. Open the chat panel (`Ctrl+L` or `Cmd+L`)
2. Type your question or request
3. Use `@` to reference files or code

### Code Generation
1. Create a new file with `.prompt` extension
2. Describe what you want to generate
3. Right-click and select "Generate Code"

### Code Review
1. Select code in the editor
2. Right-click and select "AI: Code Review"
3. Review the suggestions in the chat panel

## Git Integration

### Visual Git Tools
1. Click the Git icon in the sidebar
2. View changes, stage files, and make commits
3. Resolve merge conflicts with the visual tool

### AI-Generated Commit Messages
1. Stage your changes
2. Click the "Generate Commit Message" button
3. Review and edit the suggested message
4. Commit your changes

## Custom Workflows

### Creating Snippets
1. Open Command Palette (`Ctrl+Shift+P` or `Cmd+Shift+P`)
2. Search for "Preferences: Configure User Snippets"
3. Select the language for your snippet
4. Add your snippet in JSON format

### Task Automation
1. Create a `.cursor/tasks.json` file
2. Define your tasks:

```json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "Start Development",
      "type": "shell",
      "command": "npm run dev",
      "group": "build",
      "isBackground": true,
      "problemMatcher": []
    }
  ]
}
```

## Troubleshooting

### Common Issues

#### AI Features Not Working
1. Check your internet connection
2. Verify your API key is set:
   - Open Command Palette
   - Search for "Cursor: Set API Key"
   - Enter your API key

#### Performance Issues
1. Disable unused extensions
2. Increase memory allocation:
   - Close Cursor
   - Edit the launcher script (location varies by OS)
   - Add: `--max-memory=4096`
3. Exclude large directories:
   ```json
   {
     "files.watcherExclude": {
       "**/node_modules": true,
       "**/.git": true
     }
   }
   ```

#### Git Integration Problems
1. Ensure Git is in your system PATH
2. Verify your Git configuration:
   ```bash
   git config --global user.name "Your Name"
   git config --global user.email "your.email@example.com"
   ```
3. Check for Git authentication issues

## Keyboard Shortcuts

### Navigation
- `Ctrl+P` / `Cmd+P` - Quick open file
- `Ctrl+Shift+E` / `Cmd+Shift+E` - Explorer
- `Ctrl+Shift+F` / `Cmd+Shift+F` - Search
- `Ctrl+Shift+X` / `Cmd+Shift+X` - Extensions

### Editor
- `F12` - Go to definition
- `Alt+Left` / `Ctrl+-` - Go back
- `Ctrl+Space` - Trigger suggestion
- `F2` - Rename symbol

### AI Features
- `Ctrl+L` / `Cmd+L` - Open chat
- `Alt+\` - Toggle AI suggestions
- `Alt+C` - Open code actions

## Getting Help

- [Documentation](https://docs.cursor.sh)
- [GitHub Issues](https://github.com/getcursor/cursor/issues)
- [Community Forum](https://community.cursor.sh)
