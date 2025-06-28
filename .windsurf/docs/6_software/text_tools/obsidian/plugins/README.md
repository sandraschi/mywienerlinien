# Obsidian Plugins

## Overview
Plugins extend Obsidian's functionality, allowing you to customize and enhance your note-taking experience. This guide covers both built-in and community plugins.

## Built-in Plugins

### Core Plugins

| Plugin | Description |
|--------|-------------|
| **Backlinks** | Shows notes that link to the current note |
| **Canvas** | Infinite canvas for visual thinking |
| **Command Palette** | Quick access to commands |
| **Daily Notes** | Create and manage daily notes |
| **File Explorer** | Navigate your vault's file structure |
| **Graph View** | Visualize connections between notes |
| **Markdown Format** | Format Markdown with shortcuts |
| **Outline** | Navigate document headings |
| **Quick Switcher** | Quickly switch between notes |
| **Search** | Full-text search across your vault |
| **Tags** | Manage and navigate tags |
| **Templates** | Insert pre-defined templates |

### Enabling Built-in Plugins

1. Open Settings
2. Navigate to "Core plugins"
3. Toggle the plugins you want to enable

## Community Plugins

### Essential Plugins

| Plugin | Description |
|--------|-------------|
| **Dataview** | Query your notes like a database |
| **Templater** | Advanced templating engine |
| **Calendar** | Integrated calendar for daily notes |
| **Excalidraw** | Hand-drawn style diagrams |
| **Kanban** | Kanban boards for task management |
| **Outliner** | Better list management |
| **QuickAdd** | Quickly add notes with templates |
| **Tasks** | Full-featured task management |

### Installing Community Plugins

1. Open Settings
2. Go to "Community plugins"
3. Click "Browse"
4. Find and install plugins
5. Enable them in the "Installed plugins" tab

## Plugin Development

### Creating a Basic Plugin

1. Create a new folder in `.obsidian/plugins/your-plugin-name`
2. Create these files:
   - `main.ts` - Plugin code
   - `manifest.json` - Plugin metadata
   - `styles.css` - Plugin styles (optional)

### Example `manifest.json`

```json
{
  "id": "your-plugin-id",
  "name": "Your Plugin Name",
  "version": "1.0.0",
  "minAppVersion": "1.0.0",
  "description": "A brief description of your plugin",
  "author": "Your Name",
  "authorUrl": "https://your-website.com",
  "isDesktopOnly": false
}
```

### Example Plugin Code

```typescript
import { App, Plugin, PluginSettingTab, Setting } from 'obsidian';

interface MyPluginSettings {
  mySetting: string;
}

const DEFAULT_SETTINGS: MyPluginSettings = {
  mySetting: 'default'
};

export default class MyPlugin extends Plugin {
  settings: MyPluginSettings;

  async onload() {
    await this.loadSettings();
    
    // Add a command
    this.addCommand({
      id: 'sample-command',
      name: 'Sample Command',
      callback: () => {
        console.log('Hello from My Plugin!');
      }
    });
    
    // Add a settings tab
    this.addSettingTab(new SampleSettingTab(this.app, this));
  }
  
  async loadSettings() {
    this.settings = Object.assign({}, DEFAULT_SETTINGS, await this.loadData());
  }
  
  async saveSettings() {
    await this.saveData(this.settings);
  }
}

class SampleSettingTab extends PluginSettingTab {
  plugin: MyPlugin;
  
  constructor(app: App, plugin: MyPlugin) {
    super(app, plugin);
    this.plugin = plugin;
  }
  
  display(): void {
    const { containerEl } = this;
    containerEl.empty();
    
    new Setting(containerEl)
      .setName('Setting #1')
      .setDesc('This is a sample setting')
      .addText(text => text
        .setValue(this.plugin.settings.mySetting)
        .onChange(async (value) => {
          this.plugin.settings.mySetting = value;
          await this.plugin.saveSettings();
        }));
  }
}
```

### Testing Your Plugin

1. Enable "Developer mode" in Settings > About
2. Use the "Developer" menu to:
   - Reload the app
   - Toggle developer tools
   - Load plugin from disk

## Recommended Plugins by Category

### Note Organization
- **Tag Wrangler**: Better tag management
- **Linter**: Format and clean up your notes
- **Note Refactor**: Extract and refactor note content

### Productivity
- **Tasks**: Full-featured task management
- **Calendar**: Integrated calendar for daily notes
- **QuickAdd**: Quickly add notes with templates

### Visualization
- **Excalidraw**: Hand-drawn style diagrams
- **Mermaid**: Create diagrams and flowcharts
- **Kanban**: Kanban boards for task management

### Writing
- **Outliner**: Better list management
- **Editor Syntax Highlight**: Syntax highlighting in code blocks
- **Paste image rename**: Better image paste handling

## Plugin Management

### Updating Plugins

1. Go to Settings > Community plugins
2. Click "Check for updates"
3. Update available plugins

### Backing Up Plugins

1. Copy the `.obsidian/plugins` folder
2. Or use the "BRAT" plugin for automatic backups

### Troubleshooting Plugins

1. **Disable all plugins** and enable them one by one
2. Check the console for errors (Ctrl+Shift+I)
3. Check the plugin's GitHub page for issues
4. Try reinstalling the plugin

## Security Considerations

1. Only install plugins from trusted sources
2. Review the code of community plugins
3. Be cautious with plugins that request internet access
4. Keep your plugins updated

## Performance Impact

Some plugins can significantly impact performance:

- **Heavy Plugins**: Dataview, Excalidraw, Graph Analysis
- **Light Plugins**: Minimal Theme, Style Settings, Hotkeys

## Plugin Development Resources

- [Official Plugin Docs](https://docs.obsidian.md/Home)
- [API Reference](https://docs.obsidian.md/Reference/TypeScript+API/API)
- [Sample Plugin](https://github.com/obsidianmd/obsidian-sample-plugin)
- [Community Plugin List](https://github.com/obsidianmd/obsidian-releases/blob/master/community-plugins.json)

## Last Updated
2025-06-28 01:45:00

*This file was last updated manually.*
