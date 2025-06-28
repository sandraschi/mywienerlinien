<#
.SYNOPSIS
    Creates a backup of the Windsurf documentation
.DESCRIPTION
    This script creates a timestamped backup of the documentation directory
    and optionally syncs it to a remote location.
.NOTES
    Version: 1.1
    Author: Windsurf AI Team
#>

param (
    [Parameter(Mandatory=$false)]
    [string]$BackupDir = "D:\Backups\Docs",
    
    [Parameter(Mandatory=$false)]
    [switch]$CloudSync,
    
    [Parameter(Mandatory=$false)]
    [int]$KeepDays = 30
)

$ErrorActionPreference = 'Stop'

# Create backup directory if it doesn't exist
$dateString = Get-Date -Format "yyyyMMdd_HHmmss"
$backupPath = Join-Path $BackupDir $dateString

Write-Host "Creating backup in $backupPath" -ForegroundColor Cyan
New-Item -ItemType Directory -Path $backupPath -Force | Out-Null

# Copy documentation
$sourceDir = "$PSScriptRoot\..\.windsurf\docs"
$destinationDir = Join-Path $backupPath "docs"

Write-Host "Copying documentation..." -ForegroundColor Cyan
Copy-Item -Path $sourceDir -Destination $destinationDir -Recurse -Force

# Create a README with backup info
@"
# Documentation Backup

- **Date**: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")
- **Source**: $sourceDir
- **Backup Location**: $backupPath
- **Size**: $([math]::Round((Get-ChildItem -Path $destinationDir -Recurse | Measure-Object -Property Length -Sum).Sum / 1MB, 2)) MB

## How to Restore

### Option 1: Manual Copy
1. Copy the contents of the 'docs' folder to your target location
2. Start the documentation server

### Option 2: Using PowerShell
```powershell
# Stop any running documentation server
# Then restore from backup
Copy-Item -Path "$backupPath\docs\*" -Destination "path\to\your\docs" -Recurse -Force
```
"@ | Out-File -FilePath (Join-Path $backupPath "README.md") -Encoding utf8

# Clean up old backups
if ($KeepDays -gt 0) {
    Write-Host "Cleaning up backups older than $KeepDays days..." -ForegroundColor Cyan
    $cutoffDate = (Get-Date).AddDays(-$KeepDays)
    Get-ChildItem -Path $BackupDir -Directory | 
        Where-Object { $_.CreationTime -lt $cutoffDate } | 
        Remove-Item -Recurse -Force
}

# Cloud sync if enabled
if ($CloudSync) {
    try {
        Write-Host "Syncing to cloud..." -ForegroundColor Cyan
        # Example using rclone - adjust as needed
        if (Get-Command rclone -ErrorAction SilentlyContinue) {
            rclone sync $backupPath "your-remote:path/to/backups/$dateString"
        } else {
            Write-Warning "rclone not found. Install it from https://rclone.org/"
        }
    } catch {
        Write-Error "Cloud sync failed: $_"
    }
}

Write-Host "`nBackup completed successfully!" -ForegroundColor Green
Write-Host "Location: $backupPath" -ForegroundColor Cyan
Write-Host (Get-ChildItem -Path $backupPath -Recurse | 
    Measure-Object -Property Length -Sum | 
    Select-Object @{Name="Size";Expression={"$([math]::Round($_.Sum / 1MB, 2)) MB"}}).Size -ForegroundColor Cyan
