<#
.SYNOPSIS
    Simple script to fix broken links in markdown files.
.DESCRIPTION
    Scans all markdown files in the documentation directory, identifies broken links,
    and replaces them with a 'We're sorry' page link.
#>

# Configuration
$scriptPath = $MyInvocation.MyCommand.Path
$scriptDir = Split-Path -Path $scriptPath -Parent
$config = @{
    RootDir = "D:\Dev\repos\mywienerlinien\docs"
    LogsDir = Join-Path -Path $scriptDir -ChildPath '..\logs'
    SorryPage = '/sorry.html'
    LogFile = "link_fix_$(Get-Date -Format 'yyyyMMdd_HHmmss').log"
}

# Ensure logs directory exists
if (-not (Test-Path -Path $config.LogsDir)) {
    $null = New-Item -ItemType Directory -Path $config.LogsDir -Force
}

# Initialize counters
$script:totalFiles = 0
$script:fixedFiles = 0
$script:brokenLinks = 0

function Write-Log {
    param(
        [string]$Message,
        [string]$Level = 'INFO'
    )
    
    $timestamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
    $logMessage = "[$timestamp] [$Level] $Message"
    
    # Write to console using Write-Host for better visibility
    switch ($Level) {
        'ERROR' { Write-Host $logMessage -ForegroundColor Red }
        'WARNING' { Write-Host $logMessage -ForegroundColor Yellow }
        default { Write-Host $logMessage -ForegroundColor Cyan }
    }
    
    # Ensure logs directory exists
    if (-not (Test-Path -Path $config.LogsDir)) {
        New-Item -ItemType Directory -Path $config.LogsDir -Force | Out-Null
    }
    
    # Write to log file
    $logMessage | Out-File -FilePath (Join-Path -Path $config.LogsDir -ChildPath $config.LogFile) -Append -Encoding utf8
}

function Test-Link {
    param (
        [string]$Link,
        [string]$BasePath
    )
    
    try {
        # Skip external links, anchors, and mailto links
        if ($Link -match '^(https?://|#|mailto:)' -or [string]::IsNullOrWhiteSpace($Link)) {
            return $true
        }
        
        # Handle relative paths
        $fullPath = Join-Path -Path $BasePath -ChildPath $Link
        $fullPath = [System.IO.Path]::GetFullPath($fullPath)
        
        # Check if path exists and is within the root directory
        if ((Test-Path -Path $fullPath) -and 
            $fullPath.StartsWith($config.RootDir, [System.StringComparison]::InvariantCultureIgnoreCase)) {
            return $true
        }
        
        Write-Log -Message "Broken link found: $Link" -Level WARNING
        return $false
    }
    catch {
        Write-Log -Message "Error testing link '$Link': $_" -Level ERROR
        return $false
    }
}

function Initialize-SorryPage {
    $sorryContent = @"
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Page Not Found</title>
    <style>
        body { 
            font-family: Arial, sans-serif; 
            line-height: 1.6; 
            max-width: 800px; 
            margin: 0 auto; 
            padding: 2rem; 
            text-align: center;
        }
        h1 { color: #2c3e50; }
        .container { margin-top: 2rem; }
        .btn {
            display: inline-block;
            background: #3498db;
            color: white;
            padding: 0.5rem 1rem;
            text-decoration: none;
            border-radius: 4px;
            margin-top: 1rem;
        }
        .btn:hover { background: #2980b9; }
    </style>
</head>
<body>
    <h1>We're Sorry</h1>
    <p>The page you're looking for cannot be found or has been moved.</p>
    <div class="container">
        <p>This might be because:</p>
        <ul style="text-align: left; max-width: 500px; margin: 1rem auto;">
            <li>The page has been moved or deleted</li>
            <li>There might be a typo in the URL</li>
            <li>The content is still under development</li>
        </ul>
        <a href="/" class="btn">Return to Home</a>
    </div>
</body>
</html>
"@

    try {
        $sorryPagePath = Join-Path -Path $config.RootDir -ChildPath $config.SorryPage.TrimStart('/\\')
        
        if (-not (Test-Path -Path $sorryPagePath)) {
            $sorryDir = Split-Path -Path $sorryPagePath -Parent
            if (-not (Test-Path -Path $sorryDir)) {
                $null = New-Item -ItemType Directory -Path $sorryDir -Force -ErrorAction Stop
            }
            
            $sorryContent | Out-File -FilePath $sorryPagePath -Encoding UTF8 -Force -ErrorAction Stop
            Write-Log -Message "Created 'We're sorry' page at $sorryPagePath" -Level INFO
        }
        return $true
    }
    catch {
        Write-Log -Message "Failed to create 'We're sorry' page: $_" -Level ERROR
        return $false
    }
}

# Main script execution
try {
    # Ensure logs directory exists
    if (-not (Test-Path -Path $config.LogsDir)) {
        New-Item -ItemType Directory -Path $config.LogsDir -Force | Out-Null
    }
    
    # Clear previous log file if it exists
    $logPath = Join-Path -Path $config.LogsDir -ChildPath $config.LogFile
    if (Test-Path -Path $logPath) {
        Remove-Item -Path $logPath -Force
    }
    
    Write-Host "=== Starting Broken Link Check ===" -ForegroundColor Green
    Write-Host "Root Directory: $($config.RootDir)" -ForegroundColor Cyan
    Write-Host "Log File: $logPath" -ForegroundColor Cyan
    Write-Host ""
    
    Write-Log -Message "Starting broken link check..."
    
    # Find all markdown files
    Write-Host "Root directory: $($config.RootDir)" -ForegroundColor Cyan
    Write-Host "Logs directory: $($config.LogsDir)" -ForegroundColor Cyan
    
    if (-not (Test-Path -Path $config.RootDir)) {
        $errorMessage = "Root directory not found: $($config.RootDir)"
        Write-Host $errorMessage -ForegroundColor Red
        exit 1
    }
    
    Write-Host "Searching for markdown files in: $($config.RootDir)" -ForegroundColor Cyan
    $markdownFiles = Get-ChildItem -Path $config.RootDir -Filter '*.md' -Recurse -File -ErrorAction Stop
    
    # Write file count to console
    Write-Host "Found $($markdownFiles.Count) markdown files to process" -ForegroundColor Cyan
    
    # If no files found, exit
    if ($markdownFiles.Count -eq 0) {
        Write-Host "No markdown files found in the specified directory." -ForegroundColor Yellow
        exit 0
    }
    
    # Log first 5 files as a sample
    Write-Host "Sample files to be processed:" -ForegroundColor Cyan
    $markdownFiles | Select-Object -First 5 | ForEach-Object { 
        Write-Host "  - $($_.FullName)" -ForegroundColor Cyan
    }
    $script:totalFiles = $markdownFiles.Count
    
    if ($script:totalFiles -eq 0) {
        Write-Log -Message 'No markdown files found.' -Level WARNING
        exit 0
    }
    
    Write-Log -Message "Found $($script:totalFiles) markdown files to check" -Level INFO
    
    # Process each file
    $progress = 0
    foreach ($file in $markdownFiles) {
        $progress++
        $percentComplete = [math]::Round(($progress / $script:totalFiles) * 100, 2)
        Write-Progress -Activity 'Processing files' -Status "$progress of $($script:totalFiles) ($percentComplete%)" -PercentComplete $percentComplete
        
        try {
            $fileDir = Split-Path -Parent -Path $file.FullName
            $fileName = Split-Path -Leaf -Path $file.FullName
            
            # Read file with explicit UTF-8 encoding
            $content = Get-Content -Path $file.FullName -Raw -Encoding UTF8
            if (-not $content) {
                Write-Log -Message "File is empty: $fileName" -Level WARNING
                continue
            }
            
            $modified = $false
            $newContent = $content
            
            # Pattern to match markdown links [text](url)
            $linkPattern = '\[([^\]]+?)\]\(([^)]+?)\)'
            
            # Process each link
            $newContent = [regex]::Replace($content, $linkPattern, {
                param($match)
                
                $linkText = $match.Groups[1].Value
                $url = $match.Groups[2].Value
                
                # Skip empty, anchor, or external links
                if ([string]::IsNullOrWhiteSpace($url) -or 
                    $url -eq '#' -or 
                    $url -match '^(https?://|mailto:)' -or
                    $url -match '^[a-z]+:' -and -not $url.StartsWith('#')) {
                    return $match.Value
                }
                
                # Test the link
                if (-not (Test-Link -Link $url -BasePath $fileDir)) {
                    Write-Log -Message "Fixing link in $fileName : $url" -Level WARNING
                    $script:brokenLinks++
                    $script:modified = $true
                    return "[$linkText]($($config.SorryPage))"
                }
                
                return $match.Value
            })
            
            # Save changes if needed
            if ($script:modified) {
                $newContent | Out-File -FilePath $file.FullName -Encoding UTF8 -NoNewline -Force
                Write-Log -Message "Fixed links in $fileName" -Level INFO
                $script:fixedFiles++
            }
        }
        catch {
            Write-Log -Message "Error processing file '$($file.FullName)': $_" -Level ERROR
        }
    }
    
    # Create sorry page if needed
    if ($script:brokenLinks -gt 0) {
        Initialize-SorryPage
    }
    
    # Display summary
    $summary = @"
Link Fix Summary
=================
Files Processed: $($script:totalFiles)
Files Modified: $($script:fixedFiles)
Broken Links Found: $($script:brokenLinks)
Log File: $(Join-Path -Path $config.LogsDir -ChildPath $config.LogFile)
"@
    
    Write-Log -Message $summary -Level INFO
}
catch {
    Write-Log -Message "Fatal error: $_" -Level ERROR
    exit 1
}
finally {
    Write-Progress -Activity 'Processing files' -Completed
}
