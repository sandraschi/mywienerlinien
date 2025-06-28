# Simple test script for broken link checking

# Configuration
$rootDir = "D:\Dev\repos\mywienerlinien\docs"
$logsDir = "D:\Dev\repos\mywienerlinien\.windsurf\logs"
$logFile = "test_fix_links_$(Get-Date -Format 'yyyyMMdd_HHmmss').log"
$logPath = Join-Path -Path $logsDir -ChildPath $logFile

# Ensure logs directory exists
if (-not (Test-Path -Path $logsDir)) {
    New-Item -ItemType Directory -Path $logsDir -Force | Out-Null
}

# Create a log function
function Write-Log {
    param([string]$Message)
    $timestamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
    $logMessage = "[$timestamp] $Message"
    
    # Write to console
    Write-Host $logMessage -ForegroundColor Cyan
    
    # Write to log file
    $logMessage | Out-File -FilePath $logPath -Append -Encoding utf8
}

# Main script
Write-Host "=== Test Broken Links Script ===" -ForegroundColor Green
Write-Host "Root Directory: $rootDir" -ForegroundColor Cyan
Write-Host "Log File: $logPath" -ForegroundColor Cyan
Write-Host ""

Write-Log "Starting test script..."

# Check if root directory exists
if (-not (Test-Path -Path $rootDir)) {
    Write-Log "ERROR: Root directory not found: $rootDir"
    exit 1
}

# Count markdown files
try {
    $markdownFiles = Get-ChildItem -Path $rootDir -Filter '*.md' -Recurse -File -ErrorAction Stop
    $fileCount = $markdownFiles.Count
    
    Write-Log "Found $fileCount markdown files in $rootDir"
    
    if ($fileCount -gt 0) {
        Write-Log "First 5 files:"
        $markdownFiles | Select-Object -First 5 | ForEach-Object {
            Write-Log "  - $($_.FullName)"
        }
    }
    
    Write-Log "Test script completed successfully."
}
catch {
    Write-Log "ERROR: $_"
    exit 1
}

Write-Host "\nTest script completed. Check the log file for details: $logPath" -ForegroundColor Green
