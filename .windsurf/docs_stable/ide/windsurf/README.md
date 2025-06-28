# Windsurf IDE Setup

This guide covers the setup and usage of the Windsurf IDE, a specialized development environment tailored for Windsurf projects.

## Table of Contents
- [Installation](#installation)
- [Features](#features)
- [Project Setup](#project-setup)
- [Custom Commands](#custom-commands)
- [Integration with Windsurf Services](#integration-with-windsurf-services)
- [Troubleshooting](#troubleshooting)

## Installation

### Prerequisites
- Windows 10/11 or macOS 10.15+
- Node.js 16.x or later
- Git 2.30.0 or later

### Windows Installation
1. Download the latest Windsurf IDE installer from the [releases page](https://github.com/windsurf-ide/windsurf/releases)
2. Run the installer (`Windsurf-Setup-x.x.x.exe`)
3. Follow the installation wizard prompts
4. Launch Windsurf IDE from the Start menu

### macOS Installation
```bash
# Using Homebrew
brew install --cask windsurf-ide

# Or download directly
# 1. Download the .dmg file from releases
# 2. Open the downloaded .dmg
# 3. Drag Windsurf.app to Applications
```

### Linux Installation
```bash
# Debian/Ubuntu
wget https://github.com/windsurf-ide/windsurf/releases/latest/download/windsurf-ide_amd64.deb
sudo apt install ./windsurf-ide_amd64.deb

# Arch Linux (AUR)
yay -S windsurf-ide
```

## Features

### Core Features
- **Unified Development Environment**: All Windsurf tools in one place
- **Smart Code Navigation**: Jump to definitions, references, and implementations
- **Integrated Terminal**: Access to command line without leaving the IDE
- **Version Control**: Built-in Git integration with visual diff tools
- **Task Runner**: Run and manage project tasks directly from the IDE
- **Extension Marketplace**: Add functionality through extensions

### Windsurf-Specific Features
- **Project Templates**: Quick start with pre-configured templates
- **Service Management**: Start/stop Windsurf services with one click
- **Environment Management**: Switch between different project environments
- **Log Viewer**: Integrated log viewing with filtering and search
- **API Explorer**: Test and document APIs directly in the IDE

## Agentic IDE Deep Dive

For a comprehensive understanding of the agentic paradigm that powers the Windsurf IDE, explore our deep dive guides:

-   [**Overview**](/ide/windsurf/./deep_dive/overview.md): Understand the core philosophy and vision behind the agentic IDE.
-   [**Architecture**](/ide/windsurf/./deep_dive/architecture.md): A look under the hood at the components that enable agentic collaboration.
-   [**Pros and Cons**](/ide/windsurf/./deep_dive/pros_cons.md): A balanced perspective on the advantages and challenges of this new workflow.
-   [**Tips and Tricks**](/ide/windsurf/./deep_dive/tips_tricks.md): Master the art of pair programming with an AI agent.
-   [**Do's and Don'ts**](/ide/windsurf/./deep_dive/dos_donts.md): Best practices for a productive and smooth experience.
-   [**Community and Resources**](/ide/windsurf/./deep_dive/community.md): Connect with the Windsurf ecosystem.
-   [**Press and Community Reception**](/ide/windsurf/./deep_dive/press_reception.md): See what the industry is saying about the agentic IDE.

## Project Setup

### Creating a New Project
1. Click "File" > "New Project"
2. Select a template (Web App, API, Library, etc.)
3. Enter project details (name, location, etc.)
4. Click "Create"

### Opening an Existing Project
1. Click "File" > "Open Folder"
2. Navigate to your project directory
3. Select the folder and click "Open"
4. The IDE will detect the project type and load the appropriate settings

### Project Configuration
Windsurf IDE looks for a `.windsurf` directory in your project root. Key configuration files:

- `.windsurf/ide.json` - IDE-specific settings
- `.windsurf/tasks.json` - Task definitions
- `.windsurf/launch.json` - Debug configurations

Example `.windsurf/ide.json`:
```json
{
  "name": "my-windsurf-project",
  "version": "1.0.0",
  "services": ["redis", "postgres"],
  "commands": {
    "start": "npm start",
    "test": "npm test",
    "build": "npm run build"
  },
  "extensions": [
    "windsurf.windsurf-tools",
    "esbenp.prettier-vscode"
  ]
}
```

## Custom Commands

### Adding Custom Commands
1. Open Command Palette (`Ctrl+Shift+P` or `Cmd+Shift+P`)
2. Type "Tasks: Configure Task" and press Enter
3. Select "Create tasks.json file from template"
4. Choose "Windsurf"
5. Add your custom commands to the `tasks` array

Example `tasks.json`:
```json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "Start Development",
      "type": "shell",
      "command": "npm run dev",
      "group": {
        "kind": "build",
        "isDefault": true
      },
      "presentation": {
        "reveal": "always",
        "panel": "shared"
      }
    }
  ]
}
```

### Running Commands
- **Command Palette**: `Ctrl+Shift+P` then type the command name
- **Terminal**: Use the integrated terminal to run commands directly
- **Task Runner**: `Ctrl+Shift+B` to run the default build task

## Integration with Windsurf Services

### Service Management
1. Open the "Windsurf" view in the sidebar
2. View running services in the "Services" section
3. Click the play/stop icons to control services

### Environment Variables
1. Create a `.env` file in your project root
2. Add your environment variables:
   ```
   DB_HOST=localhost
   DB_PORT=5432
   DB_NAME=mydb
   ```
3. Restart the IDE to load new variables

## Debugging

### Setting Up Debugging
1. Click the "Run and Debug" icon in the sidebar
2. Click "create a launch.json file"
3. Select your environment (Node.js, Python, etc.)
4. Configure the launch settings as needed

### Common Debugging Tasks
- **Set Breakpoints**: Click in the gutter next to line numbers
- **Step Through Code**: Use the debug toolbar to step over, into, or out of functions
- **Inspect Variables**: View and modify variables in the "Variables" panel
- **Debug Console**: Execute code in the context of the current debug session

## Troubleshooting

### Common Issues

#### IDE Not Starting
1. Check system requirements
2. Try running from command line with `--verbose` flag
3. Check logs in `~/.windsurf/logs/`

#### Extensions Not Loading
1. Check the Extensions view for errors
2. Try disabling other extensions
3. Clear extension cache:
   - Close the IDE
   - Delete the `~/.windsurf/extensions` directory
   - Restart the IDE

#### Performance Issues
1. Increase memory allocation:
   - Edit `windsurf-ide.vmoptions` in the installation directory
   - Add: `-Xmx4G` (adjust the number based on your system)
2. Disable unused extensions
3. Exclude large directories from file watching:
   ```json
   {
     "files.watcherExclude": {
       "**/node_modules": true,
       "**/.git": true
     }
   }
   ```

## Keyboard Shortcuts

### Navigation
- `Ctrl+P` - Quick open file
- `Ctrl+Shift+E` - Explorer
- `Ctrl+Shift+F` - Search
- `Ctrl+Shift+X` - Extensions

### Editor
- `F12` - Go to definition
- `Alt+Left` - Go back
- `Ctrl+Space` - Trigger suggestion
- `F2` - Rename symbol

### Debugging
- `F5` - Start/continue
- `F9` - Toggle breakpoint
- `F10` - Step over
- `F11` - Step into
- `Shift+F11` - Step out

## Getting Help

- [Documentation](https://docs.windsurf.io)
- [GitHub Issues](https://github.com/windsurf-ide/windsurf/issues)
- [Community Forum](https://community.windsurf.io)

