# setup_simple.ps1 - Simple project scaffolding script

# Base directory
$baseDir = $PSScriptRoot

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

# Create each project directory
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
    
    # Create README
    $readmeContent = @"
# $projectName

## Overview
$($projectConfig.description)

## Tech Stack
$($projectConfig.techStack -join "`n- " | ForEach-Object { "- $_" })

## Getting Started

### Prerequisites
- Node.js 18+
- npm 9+
- Docker (optional)

### Installation

```bash
git clone <repository-url>
cd $projectName
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
$projectName/
├── src/           # Source files
├── public/        # Static files
├── tests/         # Test files
├── docs/          # Documentation
└── config/        # Configuration files
```

## License
MIT
"@
    
    $readmeContent | Out-File -FilePath (Join-Path $projectDir "README.md") -Encoding utf8
    
    # Create .gitignore
    @"
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
"@ | Out-File -FilePath (Join-Path $projectDir ".gitignore") -Encoding utf8
    
    # Create basic package.json
    @"
{
  "name": "$($projectName.ToLower())",
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
"@ | Out-File -FilePath (Join-Path $projectDir "package.json") -Encoding utf8
    
    Write-Host "Created project: $projectName" -ForegroundColor Green
}

Write-Host "`nAll projects have been created successfully!" -ForegroundColor Green
Write-Host "Navigate to each project directory and run 'npm install' to get started." -ForegroundColor Yellow
