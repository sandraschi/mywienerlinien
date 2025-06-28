<#
.SYNOPSIS
    Migrates the documentation to the new structure
.DESCRIPTION
    This script reorganizes the documentation directory structure according to the new schema.
    It creates the new directory structure, moves files, and updates references.
.NOTES
    Version: 1.0
    Author: Windsurf AI Team
#>

# Stop on error
$ErrorActionPreference = 'Stop'

# Configuration
$rootDir = "$PSScriptRoot\.."
$docsDir = "$rootDir\docs"
$backupDir = "$rootDir\docs_backup_$(Get-Date -Format 'yyyyMMdd_HHmmss')"

# Create new directory structure
function New-DirectoryStructure {
    Write-Host "Creating new directory structure..." -ForegroundColor Cyan
    
    $newDirs = @(
        "1_news",
        "2_notes/meeting-notes",
        "2_notes/ideas",
        "3_ai/companies",
        "3_ai/persons",
        "3_ai/opinion",
        "3_ai/news",
        "3_ai/research",
        "4_development/architecture",
        "4_development/api",
        "4_development/guides",
        "5_dev_tools/windsurf/docs",
        "5_dev_tools/windsurf/scripts",
        "5_dev_tools/windsurf/design",
        "5_dev_tools/ide",
        "5_dev_tools/docker",
        "5_dev_tools/ci-cd",
        "6_tools/automation",
        "6_tools/media",
        "6_tools/file_tools",
        "flows"
    )

    foreach ($dir in $newDirs) {
        $fullPath = Join-Path $docsDir $dir
        if (-not (Test-Path $fullPath)) {
            New-Item -ItemType Directory -Path $fullPath -Force | Out-Null
        }
    }
}

# Backup existing docs
function Backup-Docs {
    Write-Host "Creating backup of current docs..." -ForegroundColor Cyan
    
    # Create backup directory
    New-Item -ItemType Directory -Path $backupDir -Force | Out-Null
    
    # Copy current docs to backup
    Copy-Item -Path "$docsDir\*" -Destination $backupDir -Recurse -Force
    
    Write-Host "Backup created at: $backupDir" -ForegroundColor Green
}

# Migrate content to new structure
function Migrate-Content {
    Write-Host "Migrating content to new structure..." -ForegroundColor Cyan
    
    # Example migration - customize based on actual content
    # Move AI-related content
    if (Test-Path "$docsDir\ai") {
        Move-Item -Path "$docsDir\ai\*" -Destination "$docsDir\3_ai\" -Force
    }
    
    # Move development tools
    if (Test-Path "$docsDir\dev_tools") {
        Move-Item -Path "$docsDir\dev_tools\*" -Destination "$docsDir\5_dev_tools\" -Force
    }
    
    # Move Windsurf-specific docs
    if (Test-Path "$docsDir\.windsurf") {
        Move-Item -Path "$docsDir\.windsurf\*" -Destination "$docsDir\5_dev_tools\windsurf\" -Force
    }
    
    # Move flows to root
    if (Test-Path "$docsDir\flows") {
        # If flows directory already exists in root, merge contents
        if (Test-Path "$docsDir\flows_root") {
            Copy-Item -Path "$docsDir\flows\*" -Destination "$docsDir\flows_root\" -Recurse -Force
            Remove-Item -Path "$docsDir\flows" -Recurse -Force
            Rename-Item -Path "$docsDir\flows_root" -NewName "flows"
        } else {
            Move-Item -Path "$docsDir\flows" -Destination "$docsDir\flows_root" -Force
            Rename-Item -Path "$docsDir\flows_root" -NewName "flows"
        }
    }
}

# Update sidebar and links
function Update-References {
    Write-Host "Updating sidebar and references..." -ForegroundColor Cyan
    
    $sidebarPath = Join-Path $docsDir "_sidebar.md"
    
    if (Test-Path $sidebarPath) {
        # Backup original sidebar
        Copy-Item -Path $sidebarPath -Destination "$sidebarPath.bak" -Force
        
        # Read and update sidebar content
        $content = Get-Content -Path $sidebarPath -Raw
        
        # Example replacements - customize based on actual structure
        $content = $content -replace '\[AI\]\(/ai/)', '[AI](/3_ai/)'
        $content = $content -replace '\[Development Tools\]\(/dev_tools/)', '[Development Tools](/5_dev_tools/)'
        
        # Save updated sidebar
        $content | Set-Content -Path $sidebarPath -NoNewline
    }
    
    # Update any other references in markdown files
    Get-ChildItem -Path $docsDir -Recurse -Include "*.md" | ForEach-Object {
        $fileContent = Get-Content -Path $_.FullName -Raw
        $updatedContent = $fileContent -replace '\(/ai/)', '(/3_ai/)' `
                                    -replace '\(/dev_tools/)', '(/5_dev_tools/)'
        $updatedContent | Set-Content -Path $_.FullName -NoNewline
    }
}

# Main execution
try {
    Write-Host "Starting documentation migration..." -ForegroundColor Cyan
    
    # Create backup first
    Backup-Docs
    
    # Create new directory structure
    New-DirectoryStructure
    
    # Migrate content
    Migrate-Content
    
    # Update references
    Update-References
    
    Write-Host "Migration completed successfully!" -ForegroundColor Green
    Write-Host "Backup available at: $backupDir" -ForegroundColor Green
    Write-Host "Please review the changes and test the documentation." -ForegroundColor Yellow
} catch {
    Write-Host "Error during migration: $_" -ForegroundColor Red
    Write-Host "Check the backup at: $backupDir" -ForegroundColor Yellow
    exit 1
}
