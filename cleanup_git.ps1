# Script to clean up large files from git history

# Set error action preference
$ErrorActionPreference = "Stop"

# Define paths
$repoPath = "d:\Dev\repos\mywienerlinien"
$backupDir = Join-Path $repoPath "backup"

# Create backup directory if it doesn't exist
if (-not (Test-Path $backupDir)) {
    New-Item -ItemType Directory -Path $backupDir | Out-Null
    Write-Host "Created backup directory: $backupDir"
}

# Define large files to remove from git history
$largeFiles = @(
    "scripts/gtfs_data_backup_20250720_224110/gtfs.zip",
    "scripts/gtfs_data_backup_20250720_224110/wienerlinien-gtfs.zip",
    "scripts/gtfs_data_backup_20250720_224110/extracted/stop_times.txt"
)

# Backup and remove each large file
foreach ($file in $largeFiles) {
    $sourcePath = Join-Path $repoPath $file
    $backupPath = Join-Path $backupDir (Split-Path $file -Leaf)
    
    if (Test-Path $sourcePath) {
        # Backup the file
        Copy-Item -Path $sourcePath -Destination $backupPath -Force
        Write-Host "Backed up $file to $backupPath"
        
        # Remove the file from git tracking
        git rm --cached $sourcePath
        Write-Host "Removed $file from git tracking"
    } else {
        Write-Host "File not found: $sourcePath"
    }
}

# Add .gitignore rule to prevent re-adding these files
$gitignorePath = Join-Path $repoPath ".gitignore"
$gitignoreRules = @"
# Large files to exclude
scripts/gtfs_data_backup_20250720_224110/gtfs.zip
scripts/gtfs_data_backup_20250720_224110/wienerlinien-gtfs.zip
scripts/gtfs_data_backup_20250720_224110/extracted/stop_times.txt
"@

# Append to .gitignore if not already present
if (-not (Select-String -Path $gitignorePath -Pattern "gtfs_data_backup" -SimpleMatch)) {
    Add-Content -Path $gitignorePath -Value $gitignoreRules
    Write-Host "Updated .gitignore to exclude large files"
}

# Commit the changes
git commit -m "Remove large files from git tracking"

Write-Host "Cleanup complete. You can now push your changes."
