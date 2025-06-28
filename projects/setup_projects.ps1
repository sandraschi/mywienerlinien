# setup_projects.ps1 - Scaffold new projects with consistent structure

# Base directory
$baseDir = $PSScriptRoot

# Common files to create in each project
$commonFiles = @{
    "README.md" = @"
{0}

## Overview
{1}

## Getting Started

### Prerequisites
- Node.js 18+
- npm 9+
- Docker (optional)

### Installation

```bash
git clone <repository-url>
cd {0}
npm install
```

### Development

```bash
# Start development server
npm run dev

# Build for production
npm run build
```

## Project Structure

```
{0}/
├── src/           # Source files
├── public/        # Static files
├── tests/         # Test files
├── docs/          # Documentation
└── config/        # Configuration files
```

## License
MIT
"@

    ".gitignore" = @"
# Dependencies
node_modules/

# Build output
dist/
build/

# Environment variables
.env
.env.local

# Logs
logs
*.log
npm-debug.log*

# Editor directories and files
.vscode/*
!.vscode/extensions.json
.idea
.DS_Store
"@

    "package.json" = @'{
  "name": "{0}",
  "version": "0.1.0",
  "private": true,
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "next lint",
    "test": "jest"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "next": "^14.0.0"
  },
  "devDependencies": {
    "@types/node": "^20.0.0",
    "@types/react": "^18.2.0",
    "typescript": "^5.0.0",
    "eslint": "^8.0.0",
    "jest": "^29.0.0"
  }
}
'@
}

# Project configurations
# {0}

## Overview
{1}

## Getting Started

### Prerequisites
- Node.js 18+
- npm 9+
- Docker (optional)

### Installation

```bash
git clone <repository-url>
cd {0}
npm install
```

### Development

```bash
# Start development server
npm run dev

# Build for production
npm run build
```

## Project Structure

```
{0}/
├── src/           # Source files
├── public/        # Static files
├── tests/         # Test files
├── docs/          # Documentation
└── config/        # Configuration files
```

## License
MIT
"@
    
    ".gitignore" = @"
# Dependencies
node_modules/

# Build output
dist/
build/

# Environment variables
.env
.env.local

# Logs
logs
*.log
npm-debug.log*

# Editor directories and files
.vscode/*
!.vscode/extensions.json
.idea
.DS_Store
"@
    
    "package.json" = @'{
  "name": "{0}",
  "version": "0.1.0",
  "private": true,
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "next lint",
    "test": "jest"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "next": "^14.0.0"
  },
  "devDependencies": {
    "@types/node": "^20.0.0",
    "@types/react": "^18.2.0",
    "typescript": "^5.0.0",
    "eslint": "^8.0.0",
    "jest": "^29.0.0"
  }
}
'@
}

# Project configurations
$projects = @{
    "myHomecontrol" = @{
        description = "Home automation and control system with IoT integration"
        techStack = @("Node.js", "React", "MQTT", "Home Assistant API", "Docker")
    }
    "myMediaDashboards" = @{
        description = "Custom media dashboards for Plex, Jellyfin, and other media services"
        techStack = @("Next.js", "TypeScript", "Tailwind CSS", "Docker")
    }
    "myAIPlayground" = @{
        description = "Interactive playground for experimenting with AI/ML models"
        techStack = @("Python", "FastAPI", "React", "PyTorch", "Docker")
    }
    "myGames" = @{
        description = "Collection of browser-based games and game utilities"
        techStack = @("TypeScript", "Phaser.js", "React", "WebGL")
    }
    "myScripts" = @{
        description = "Collection of utility scripts and automation tools"
        techStack = @("Python", "PowerShell", "Bash", "Docker")
    }
}

# Create each project with its structure
foreach ($project in $projects.GetEnumerator()) {
    $projectName = $project.Key
    $projectConfig = $project.Value
    $projectDir = Join-Path $baseDir $projectName
    
    Write-Host "Creating project: $projectName" -ForegroundColor Green
    
    # Create project directory
    New-Item -ItemType Directory -Path $projectDir -Force | Out-Null
    
    # Create common directories
    @("src", "public", "tests", "docs", "config") | ForEach-Object {
        New-Item -ItemType Directory -Path (Join-Path $projectDir $_) -Force | Out-Null
    }
    
    # Create README with project-specific content
    $readmeContent = $commonFiles["README.md"] -f $projectName, $projectConfig.description
    $readmeContent += "\n## Tech Stack\n"
    $readmeContent += $projectConfig.techStack | ForEach-Object { "- $_" }
    
    $readmeContent | Out-File -FilePath (Join-Path $projectDir "README.md") -Encoding utf8
    
    # Create other common files
    $commonFiles.GetEnumerator() | Where-Object { $_.Key -ne "README.md" } | ForEach-Object {
        $content = $_.Value -f $projectName
        $content | Out-File -FilePath (Join-Path $projectDir $_.Key) -Encoding utf8
    }
    
    # Project-specific additional setup
    switch ($projectName) {
        "myHomecontrol" {
            # Additional home control specific files
            @"
# Home Control Configuration

## Supported Devices
- Smart Lights
- Thermostats
- Security Cameras
- Smart Plugs

## API Documentation
See [API.md](docs/API.md) for detailed API documentation.
"@ | Out-File -FilePath (Join-Path $projectDir "docs/DEVICES.md") -Encoding utf8
        }
        
        "myMediaDashboards" {
            # Media dashboards specific setup
            @"
# Media Dashboards

## Supported Services
- Plex
- Jellyfin
- Sonarr
- Radarr
"@ | Out-File -FilePath (Join-Path $projectDir "docs/SERVICES.md") -Encoding utf8
        }
        
        "myAIPlayground" {
            # AI playground specific setup
            @"
# AI Playground

## Available Models
- GPT-3.5
- Stable Diffusion
- LLaMA

## Quick Start

1. Install Python 3.9+
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Start the server:
   ```bash
   uvicorn src.main:app --reload
   ```
"@ | Out-File -FilePath (Join-Path $projectDir "QUICKSTART.md") -Encoding utf8
        }
    }
    
    Write-Host "Created project: $projectName" -ForegroundColor Green
}

Write-Host "`nAll projects have been created successfully!" -ForegroundColor Green
Write-Host "Navigate to each project directory and run 'npm install' to get started." -ForegroundColor Yellow
