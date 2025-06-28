# Visual Studio Code (VSCode) Setup

This guide covers the setup and configuration of Visual Studio Code for optimal development with the Windsurf project.

## Table of Contents
- [Installation](#installation)
- [Recommended Extensions](#recommended-extensions)
- [Workspace Configuration](#workspace-configuration)
- [Debugging](#debugging)
- [Remote Development](#remote-development)
- [Keybindings](#keybindings)
- [Troubleshooting](#troubleshooting)

## Installation

### Windows
1. Download the [VSCode installer](https://code.visualstudio.com/download)
2. Run the installer with default settings
3. Add to PATH when prompted

### macOS
```bash
brew install --cask visual-studio-code
```

### Linux
```bash
sudo apt update
sudo apt install code  # or code-insiders
```

## Recommended Extensions

### Essential Extensions
- **GitLens** - Enhanced Git capabilities
  ```
  ext install eamodio.gitlens
  ```
- **EditorConfig** - Consistent coding styles
  ```
  ext install editorconfig.editorconfig
  ```
- **ESLint** - JavaScript/TypeScript linting
  ```
  ext install dbaeumer.vscode-eslint
  ```
- **Prettier** - Code formatter
  ```
  ext install esbenp.prettier-vscode
  ```

### Language Support
- **Python**
  ```
  ext install ms-python.python
  ```
- **Docker**
  ```
  ext install ms-azuretools.vscode-docker
  ```
- **YAML**
  ```
  ext install redhat.vscode-yaml
  ```

### Windsurf Specific
- **Windsurf Tools**
  ```
  ext install windsurf.windsurf-tools
  ```

## Workspace Configuration

### Recommended Settings
Add these to your workspace `.vscode/settings.json`:

```json
{
  "editor.tabSize": 2,
  "editor.insertSpaces": true,
  "editor.detectIndentation": false,
  "files.trimTrailingWhitespace": true,
  "files.insertFinalNewline": true,
  "files.trimFinalNewlines": true,
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.fixAll.eslint": true
  },
  "eslint.validate": ["javascript", "typescript", "javascriptreact", "typescriptreact"],
  "[javascript]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  },
  "[json]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  },
  "[yaml]": {
    "editor.defaultFormatter": "redhat.vscode-yaml"
  },
  "terminal.integrated.defaultProfile.windows": "Git Bash",
  "terminal.integrated.shell.windows": "C:\\Program Files\\Git\\bin\\bash.exe"
}
```

## Debugging

### Launch Configuration
Create `.vscode/launch.json`:

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "type": "node",
      "request": "launch",
      "name": "Debug Current File",
      "program": "${file}",
      "skipFiles": ["<node_internals>/**"]
    },
    {
      "type": "node",
      "request": "launch",
      "name": "Debug Tests",
      "program": "${workspaceFolder}/node_modules/.bin/jest",
      "args": ["--runInBand", "--config", "jest.config.js"],
      "console": "integratedTerminal",
      "internalConsoleOptions": "neverOpen",
      "cwd": "${workspaceFolder}"
    }
  ]
}
```

## Remote Development

### Using Remote - Containers
1. Install the Remote - Containers extension
   ```
   ext install ms-vscode-remote.remote-containers
   ```
2. Open command palette (Ctrl+Shift+P)
3. Select "Remote-Containers: Open Folder in Container..."
4. Select your project folder

### SSH Remote Development
1. Install the Remote - SSH extension
   ```
   ext install ms-vscode-remote.remote-ssh
   ```
2. Connect to your remote host
3. Open your project folder

## Keybindings

### Navigation
- `Ctrl+P` - Quick open file
- `Ctrl+Shift+P` - Command palette
- `Ctrl+Shift+E` - Explorer
- `Ctrl+B` - Toggle sidebar

### Editor
- `Ctrl+\` - Split editor
- `Ctrl+1`/`Ctrl+2` - Switch between editor groups
- `Alt+↑/↓` - Move line up/down
- `Shift+Alt+↑/↓` - Copy line up/down

### Git
- `Ctrl+Shift+G` - Git view
- `F1` then `Git: Stage All Changes`
- `F1` then `Git: Commit`
- `F1` then `Git: Push`

## Troubleshooting

### Common Issues

#### Extensions not loading
1. Check VSCode's developer tools (Help > Toggle Developer Tools)
2. Try reloading the window (Ctrl+R)
3. Check extension logs in the Output panel

#### Performance Issues
1. Disable extensions one by one to find the culprit
2. Check for large files in your workspace
3. Increase memory allocation in settings:
   ```json
   "terminal.integrated.windowsEnableConpty": false,
   "files.watcherExclude": {
     "**/.git/objects/**": true,
     "**/node_modules/**": true
   }
   ```

#### Git Authentication Issues
1. Ensure Git is properly configured:
   ```bash
   git config --global user.name "Your Name"
   git config --global user.email "your.email@example.com"
   ```
2. Set up SSH keys if using SSH authentication
3. For HTTPS, configure credential helper:
   ```bash
   git config --global credential.helper wincred  # Windows
   git config --global credential.helper osxkeychain  # macOS
   ```

## Additional Resources

- [VSCode Documentation](https://code.visualstudio.com/docs)
- [Keyboard Shortcuts Reference](https://code.visualstudio.com/docs/getstarted/keybindings)
- [Debugging in VSCode](https://code.visualstudio.com/docs/editor/debugging)
- [Remote Development](https://code.visualstudio.com/docs/remote/remote-overview)
