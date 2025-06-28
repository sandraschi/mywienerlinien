# Roo Code IDE Setup

This guide covers the setup and usage of Roo Code IDE, a specialized development environment designed for Windsurf project workflows.

## Table of Contents
- [Installation](#installation)
- [Features](#features)
- [Project Onboarding](#project-onboarding)
- [Built-in Tools](#built-in-tools)
- [Custom Commands](#custom-commands)
- [Troubleshooting](#troubleshooting)

## Installation

### Prerequisites
- Windows 10/11 or macOS 10.15+
- Node.js 16.x or later
- Git 2.30.0 or later
- Docker (for containerized development)

### Windows Installation
1. Download the Roo Code installer from the [official website](https://roocode.io/download)
2. Run `RooCode-Setup-x.x.x.exe`
3. Follow the installation wizard
4. Launch Roo Code from the Start menu

### macOS Installation
```bash
# Using Homebrew
brew install --cask roocode

# Or download the .dmg file manually
# 1. Download from https://roocode.io/download/mac
# 2. Open the .dmg file
# 3. Drag Roo Code.app to Applications
```

### Linux Installation
```bash
# Debian/Ubuntu
wget https://download.roocode.io/linux/roocode_amd64.deb
sudo dpkg -i roocode_amd64.deb

# Arch Linux (AUR)
yay -S roocode
```

## Features

### Core Features
- **Unified Development Workspace**: All project tools in one interface
- **Smart Project Navigation**: Context-aware file and symbol navigation
- **Integrated Terminal**: Full terminal access with multiple sessions
- **Container Support**: Built-in Docker integration
- **Database Tools**: Visual database management
- **API Testing**: Built-in REST client

### Roo-Specific Features
- **Project Templates**: Quick start with Windsurf-optimized templates
- **Service Management**: One-click service controls
- **Environment Management**: Switch between dev, test, and prod environments
- **Task Automation**: Run and manage project tasks
- **Extension Marketplace**: Add functionality through extensions

## Project Onboarding

### First-Time Setup
1. Launch Roo Code
2. Click "Open Workspace"
3. Select your project directory
4. Roo will detect the project type and suggest setup steps

### Workspace Configuration
Roo Code looks for a `.roo` directory in your project root. Key files:

- `.roo/workspace.json` - Workspace settings
- `.roo/tasks.json` - Task definitions
- `.roo/launch.json` - Debug configurations

Example `.roo/workspace.json`:
```json
{
  "name": "my-windsurf-project",
  "version": "1.0.0",
  "environments": {
    "dev": {
      "extends": "base",
      "envFile": ".env.development"
    },
    "prod": {
      "extends": "base",
      "envFile": ".env.production"
    }
  },
  "services": ["redis", "postgres"],
  "extensions": [
    "roo.windsurf-pack",
    "esbenp.prettier-vscode"
  ]
}
```

## Built-in Tools

### Service Management
1. Open the "Services" view in the sidebar
2. View running services
3. Start/stop services with the action buttons

### Database Explorer
1. Open the "Database" view
2. Click "+" to add a connection
3. Enter connection details
4. Browse and query your databases

### API Testing
1. Open the "API" view
2. Create a new request file (`.http`)
3. Write your HTTP requests
4. Click "Send Request" to test

## Custom Commands

### Adding Commands
1. Create or edit `.roo/commands.json`
2. Define your commands:

```json
{
  "version": "1.0.0",
  "commands": [
    {
      "command": "dev",
      "description": "Start development server",
      "script": "npm run dev",
      "group": "development"
    },
    {
      "command": "test",
      "description": "Run tests",
      "script": "npm test",
      "group": "testing"
    }
  ]
}
```

### Running Commands
1. Open Command Palette (`Ctrl+Shift+P` or `Cmd+Shift+P`)
2. Type "Roo: Run Command"
3. Select your command

## Debugging

### Setting Up Debugging
1. Click the "Run and Debug" icon in the sidebar
2. Click "create a launch.json file"
3. Select your environment
4. Configure the launch settings

### Debugging Features
- **Breakpoints**: Click in the gutter to set breakpoints
- **Watch Window**: Monitor variables and expressions
- **Call Stack**: View the call hierarchy
- **Debug Console**: Execute code in the current context

## Troubleshooting

### Common Issues

#### IDE Not Starting
1. Check system requirements
2. Try running from command line with `--verbose`
3. Check logs in `~/.roo/logs/`

#### Extension Problems
1. Open Extensions view
2. Check for errors in the extension status
3. Try reinstalling the extension

#### Performance Issues
1. Increase memory allocation:
   - Edit `roo.vmoptions` in the installation directory
   - Add: `-Xmx4G`
2. Disable unused extensions
3. Exclude large directories:
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
- `Ctrl+P` / `Cmd+P` - Quick open file
- `Ctrl+Shift+E` / `Cmd+Shift+E` - Explorer
- `Ctrl+Shift+F` / `Cmd+Shift+F` - Search
- `Ctrl+Shift+X` / `Cmd+Shift+X` - Extensions

### Editor
- `F12` - Go to definition
- `Alt+Left` / `Ctrl+-` - Go back
- `Ctrl+Space` - Trigger suggestion
- `F2` - Rename symbol

### Debugging
- `F5` - Start/continue
- `F9` - Toggle breakpoint
- `F10` - Step over
- `F11` - Step into
- `Shift+F11` - Step out

## Getting Help

- [Documentation](https://docs.roocode.io)
- [GitHub Issues](https://github.com/roocode/roocode/issues)
- [Community Forum](https://community.roocode.io)
