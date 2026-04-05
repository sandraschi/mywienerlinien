# MyWienerLinien - Start Scripts

This document explains how to use the start scripts to manage both the Wiener Linien app and the Docsify documentation.

## Quick Start

### Windows Batch File (Recommended for Windows)

```cmd
# Open interactive menu
start.bat

# Or run specific commands
start.bat 3  # Start both applications
```

### PowerShell Script (Recommended for PowerShell users)

```powershell
# Open interactive menu
.\start.ps1

# Or run specific commands
.\start.ps1 start    # Start both applications
.\start.ps1 stop     # Stop both applications
.\start.ps1 status   # Show status
```

## Available Scripts

### 1. `start.bat` - Windows Batch File
- **Interactive menu** with numbered options
- **Color-coded** output for better readability
- **Easy navigation** between different actions
- **Automatic directory management**

### 2. `start.ps1` - PowerShell Script
- **Interactive menu** with colored output
- **Command-line parameters** for automation
- **Better error handling** and logging
- **Cross-platform compatibility**

## Menu Options

Both scripts provide the same functionality through an interactive menu:

| Option | Description | Action |
|--------|-------------|--------|
| `1` | Start Wiener Linien App | Starts the Flask app on port 3080 |
| `2` | Start Docsify Documentation | Starts the documentation on port 3301 |
| `3` | Start Both Applications | Starts both apps simultaneously |
| `4` | Stop Wiener Linien App | Stops the Flask app |
| `5` | Stop Docsify Documentation | Stops the documentation |
| `6` | Stop All Applications | Stops both apps |
| `7` | Show Status | Displays health and status of both apps |
| `8` | Show Logs | View real-time logs from either app |
| `9` | Build/Rebuild Applications | Rebuild Docker images |
| `0` | Exit | Close the application manager |

## Command Line Usage

### PowerShell Script Parameters

```powershell
# Interactive menu (default)
.\start.ps1

# Start both applications
.\start.ps1 start

# Stop both applications
.\start.ps1 stop

# Show status
.\start.ps1 status

# Show logs
.\start.ps1 logs

# Build applications
.\start.ps1 build

# Interactive menu
.\start.ps1 menu
```

### Batch File Usage

```cmd
# Interactive menu (default)
start.bat

# The batch file is primarily designed for interactive use
# Use the menu system for best experience
```

## Application URLs

Once started, the applications will be available at:

- **Wiener Linien App**: http://localhost:3080
  - Main application interface
  - Real-time vehicle tracking
  - Disruption alerts
  - API endpoints

- **Docsify Documentation**: http://localhost:3301
  - Comprehensive documentation
  - Search functionality
  - Theme toggle (light/dark)
  - Interactive console

## Features

### 🎯 **Unified Management**
- Single interface to manage both applications
- Consistent commands across both apps
- Automatic directory navigation

### 🔄 **Health Monitoring**
- Real-time status checking
- Health check integration
- Automatic restart on failure

### 📊 **Logging & Debugging**
- Live log viewing
- Separate log streams for each app
- Error tracking and reporting

### 🏗️ **Build Management**
- One-click rebuilds
- Individual or combined builds
- Clean rebuilds with cache clearing

### 🎨 **User Experience**
- Color-coded output
- Clear status messages
- Interactive menus
- Progress indicators

## Prerequisites

Before using the start scripts, ensure you have:

1. **Docker Desktop** installed and running
2. **PowerShell** (for PowerShell script) or **Command Prompt** (for batch file)
3. **Sufficient system resources** (at least 2GB RAM available)

## Troubleshooting

### Script Won't Run

1. **Check file permissions**:
   ```cmd
   # For PowerShell
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
   ```

2. **Verify Docker is running**:
   ```cmd
   docker --version
   docker-compose --version
   ```

3. **Check file paths**:
   - Ensure you're in the root directory (`mywienerlinien`)
   - Verify `frontend/` and `.windsurf/docs/` directories exist

### Applications Won't Start

1. **Check port availability**:
   ```cmd
   netstat -an | findstr :3080
   netstat -an | findstr :3301
   ```

2. **Check Docker status**:
   ```cmd
   docker ps
   docker-compose ps
   ```

3. **View application logs**:
   ```cmd
   # Use option 8 in the menu
   # Or run directly:
   .\start.ps1 logs
   ```

### Build Issues

1. **Clean and rebuild**:
   ```cmd
   # Use option 9 in the menu
   # Or run directly:
   .\start.ps1 build
   ```

2. **Check Docker disk space**:
   ```cmd
   docker system df
   ```

3. **Clear Docker cache**:
   ```cmd
   docker system prune -a
   ```

## Advanced Usage

### Automation

You can use the PowerShell script in automated workflows:

```powershell
# Start applications in CI/CD pipeline
.\start.ps1 start

# Check status in monitoring script
.\start.ps1 status

# Stop applications during deployment
.\start.ps1 stop
```

### Customization

Both scripts can be customized by editing the source files:

- **start.bat** - Modify batch commands and paths
- **start.ps1** - Modify PowerShell functions and parameters

### Integration

The scripts integrate with existing Docker management:

```cmd
# Use existing individual scripts
cd frontend
.\start_wiener_linien.bat status

cd ..\.windsurf\docs
docker-compose ps
```

## Support

If you encounter issues:

1. **Check the troubleshooting section** above
2. **Review application logs** using option 8
3. **Verify Docker Desktop** is running properly
4. **Ensure sufficient system resources** are available
5. **Check file permissions** and execution policies

## File Structure

```
mywienerlinien/
├── start.bat              # Windows batch file
├── start.ps1              # PowerShell script
├── README_Start_Scripts.md # This file
├── frontend/
│   ├── start_wiener_linien.bat
│   ├── start_wiener_linien.ps1
│   └── ...
└── .windsurf/
    └── docs/
        ├── docker-compose.yml
        └── ...
``` 
