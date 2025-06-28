# create_project_docs.ps1 - Script to generate consistent documentation for all projects

# Base directory for project documentation
$docsBase = "d:\Dev\repos\mywienerlinien\.windsurf\docs\7_projects"

# Project configurations
$projects = @{
    "myHomecontrol" = @{
        description = "Home automation and control system with IoT integration"
        repo = ""
    }
    "myMediaDashboards" = @{
        description = "Custom media dashboards for Plex, Jellyfin, and other media services"
        repo = ""
    }
    "myAIPlayground" = @{
        description = "Interactive playground for experimenting with AI/ML models"
        repo = "D:\Dev\repos\myai"
    }
    "myGames" = @{
        description = "Collection of browser-based games and game utilities"
        repo = ""
    }
    "myScripts" = @{
        description = "Collection of utility scripts and automation tools"
        repo = "D:\Dev\repos\myscripts"
    }
}

# Create documentation for each project
foreach ($project in $projects.GetEnumerator()) {
    $projectName = $project.Key
    $projectConfig = $project.Value
    $projectDir = Join-Path $docsBase $projectName
    
    Write-Host "Creating documentation for: $projectName" -ForegroundColor Cyan
    
    # Ensure project directory exists
    if (-not (Test-Path $projectDir)) {
        New-Item -ItemType Directory -Path $projectDir -Force | Out-Null
    }
    
    # Create/Update PRD.md
    $prdContent = @"
# $projectName - Product Requirements Document (PRD)

## 1. Overview
$($projectConfig.description)

## 2. Problem Statement
*Describe the problem this project aims to solve*

## 3. Target Users
*List and describe the primary users of the system*

## 4. Features
### 4.1 Core Features
- *Feature 1*
- *Feature 2*
- *Feature 3*

### 4.2 Future Features
- *Planned enhancements*

## 5. Technical Requirements
### 5.1 Frontend
- *Technical specifications*

### 5.2 Backend
- *Technical specifications*

## 6. Integration Points
*List of external services and APIs to be integrated*

## 7. Success Metrics
*How will we measure the success of this project?*

## 8. Timeline
*High-level project timeline*

## 9. Repository
$($projectConfig.repo)
"@

    $prdContent | Out-File -FilePath (Join-Path $projectDir "PRD.md") -Encoding utf8 -Force
    
    # Create/Update README.md
    $readmeContent = @"
# $projectName

## Description
$($projectConfig.description)

## Project Status
*Status: Planning*

## Getting Started
*Instructions for getting started with the project*

## Documentation
- [Product Requirements Document](PRD.md)
- [API Documentation](#) *(coming soon)*
- [User Guide](#) *(coming soon)*

## Repository
$($projectConfig.repo)

## License
*License information will be added here*
"@

    $readmeContent | Out-File -FilePath (Join-Path $projectDir "README.md") -Encoding utf8 -Force
}

Write-Host "`nDocumentation generation complete!" -ForegroundColor Green
