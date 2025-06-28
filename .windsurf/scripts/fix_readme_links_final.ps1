# Script to fix README.md links - Final Version

# Configuration
$docsDir = "D:\Dev\repos\mywienerlinien\.windsurf\docs"
$readmePath = Join-Path -Path $docsDir -ChildPath "README.md"
$backupPath = "$readmePath.backup_$(Get-Date -Format 'yyyyMMdd_HHmmss').md"

# Create backup of original file
Copy-Item -Path $readmePath -Destination $backupPath -Force
Write-Host "Created backup at: $backupPath" -ForegroundColor Cyan

# Read the content
$content = Get-Content -Path $readmePath -Raw

# Fix 1: Remove .md/README.md from links
$content = $content -replace '\.md/README\.md', ''

# Fix 2: Fix links that have .md.md at the end
$content = $content -replace '(\.md)\.md([^/]|$)', '$1$2'

# Save the updated content
$content | Out-File -FilePath $readmePath -Encoding utf8 -NoNewline

Write-Host "\nLinks in README.md have been updated." -ForegroundColor Green
Write-Host "Original file backed up to: $backupPath" -ForegroundColor Cyan
Write-Host "\nVerifying links..." -ForegroundColor Cyan

# Run the link checker to verify the fixes
& "$PSScriptRoot\check_links.ps1"
