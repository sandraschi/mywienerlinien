<#
.SYNOPSIS
    Fixes broken links in markdown documentation.
.DESCRIPTION
    Scans all markdown files in the documentation directory, identifies broken links,
    and replaces them with a 'We're sorry' page link.
.NOTES
    Author: AI Assistant
    Last Updated: $(Get-Date -Format 'yyyy-MM-dd')
#>

#region Configuration
$script:config = @{
    RootDir = Join-Path -Path $PSScriptRoot -ChildPath '..\..\docs' -Resolve
    LogsDir = Join-Path -Path $PSScriptRoot -ChildPath '..\logs'
    SorryPage = '/sorry.html'
    LogFile = "link_fix_$(Get-Date -Format 'yyyyMMdd_HHmmss').log"
}

# Ensure configuration paths are absolute
$script:config.RootDir = [System.IO.Path]::GetFullPath($script:config.RootDir)
$script:config.LogsDir = [System.IO.Path]::GetFullPath($script:config.LogsDir)
$script:config.LogFile = Join-Path -Path $script:config.LogsDir -ChildPath $script:config.LogFile

#region Functions

<#
.SYNOPSIS
    Initializes the script environment.
#>
function Initialize-Environment {
    [CmdletBinding()]
    param()
    
    try {
        # Create logs directory if it doesn't exist
        if (-not (Test-Path -Path $script:config.LogsDir)) {
            $null = New-Item -ItemType Directory -Path $script:config.LogsDir -Force
        }
        
        # Start transcript
        Start-Transcript -Path $script:config.LogFile -Append
        Write-Log -Message 'Script started' -Level INFO
        
        return $true
    }
    catch {
        Write-Error "Failed to initialize environment: $_"
        return $false
    }
}

<#
.SYNOPSIS
    Writes a log message with timestamp.
.PARAMETER Message
    The message to log.
.PARAMETER Level
    The log level (INFO, WARNING, ERROR).
#>
function Write-Log {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [string]$Message,
        
        [Parameter(Mandatory = $false)]
        [ValidateSet('INFO', 'WARNING', 'ERROR')]
        [string]$Level = 'INFO'
    )
    
    $timestamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
    $logMessage = "[$timestamp] [$Level] $Message"
    
    switch ($Level) {
        'ERROR' { Write-Host $logMessage -ForegroundColor Red }
        'WARNING' { Write-Host $logMessage -ForegroundColor Yellow }
        default { Write-Host $logMessage -ForegroundColor Cyan }
    }
    
    # Write to log file if transcript is active
    if ((Get-Command -Name 'Get-Transcript' -ErrorAction SilentlyContinue) -and 
        (Get-Transcript).Status -eq 'Started') {
        $logMessage | Out-File -FilePath $script:config.LogFile -Append -Encoding utf8
    }
}

<#
.SYNOPSIS
    Tests if a link is valid.
.PARAMETER Link
    The link to test.
.PARAMETER BasePath
    The base path for relative links.
#>
function Test-Link {
    [CmdletBinding()]
    [OutputType([bool])]
    param (
        [Parameter(Mandatory = $true)]
        [string]$Link,
        
        [Parameter(Mandatory = $true)]
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
            $fullPath.StartsWith($script:config.RootDir, [System.StringComparison]::InvariantCultureIgnoreCase)) {
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

<#
.SYNOPSIS
    Fixes broken links in a markdown file.
.PARAMETER FilePath
    Path to the markdown file to process.
#>
function Repair-FileLinks {
    [CmdletBinding()]
    [OutputType([bool])]
    param (
        [Parameter(Mandatory = $true)]
        [ValidateScript({ Test-Path -Path $_ -PathType Leaf }) ]
        [string]$FilePath
    )
    
    try {
        $fileDir = Split-Path -Parent -Path $FilePath
        $fileName = Split-Path -Leaf -Path $FilePath
        
        # Read file with explicit UTF-8 encoding
        $content = Get-Content -Path $FilePath -Raw -Encoding UTF8
        if (-not $content) {
            Write-Log -Message "File is empty: $fileName" -Level WARNING
            return $false
        }
        
        $modified = $false
        
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
                return "[$linkText]($($script:config.SorryPage))"
            }
            
            return $match.Value
        })
        
        # Save changes if needed
        if ($script:modified) {
            $newContent | Out-File -FilePath $FilePath -Encoding UTF8 -NoNewline -Force
            Write-Log -Message "Fixed links in $fileName" -Level INFO
            return $true
        }
        
        return $false
    }
    catch {
        Write-Log -Message "Error processing file '$FilePath': $_" -Level ERROR
        return $false
    }
}

<#
.SYNOPSIS
    Main script execution.
#>
function Start-LinkFix {
    [CmdletBinding()]
    param()
    
    # Initialize counters
    $script:totalFiles = 0
    $script:fixedFiles = 0
    $script:brokenLinks = 0
    $script:modified = $false
    
    try {
        # Find all markdown files
        Write-Log -Message "Searching for markdown files in: $($script:config.RootDir)"
        $markdownFiles = Get-ChildItem -Path $script:config.RootDir -Filter '*.md' -Recurse -File -ErrorAction Stop
        $script:totalFiles = $markdownFiles.Count
        
        if ($script:totalFiles -eq 0) {
            Write-Log -Message 'No markdown files found.' -Level WARNING
            return
        }
        
        Write-Log -Message "Found $($script:totalFiles) markdown files to check" -Level INFO
        
        # Process each file
        $progress = 0
        foreach ($file in $markdownFiles) {
            $progress++
            $percentComplete = [math]::Round(($progress / $script:totalFiles) * 100, 2)
            Write-Progress -Activity 'Processing files' -Status "$progress of $($script:totalFiles) ($percentComplete%)" -PercentComplete $percentComplete
            
            if (Repair-FileLinks -FilePath $file.FullName) {
                $script:fixedFiles++
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
        Log File: $($script:config.LogFile)
        "@
        
        Write-Log -Message $summary -Level INFO
    }
    catch {
        Write-Log -Message "Error in main execution: $_" -Level ERROR
        throw
    }
    finally {
        Write-Progress -Activity 'Processing files' -Completed
    }
}

<#
.SYNOPSIS
    Creates a 'We're sorry' page if it doesn't exist.
#>
function Initialize-SorryPage {
    [CmdletBinding()]
    param()
    
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
        $sorryPagePath = Join-Path -Path $script:config.RootDir -ChildPath $script:config.SorryPage.TrimStart('/\\')
        
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

#endregion

#region Main Execution

try {
    # Initialize environment
    if (-not (Initialize-Environment)) {
        exit 1
    }
    
    # Start the main process
    Start-LinkFix
}
catch {
    Write-Log -Message "Fatal error: $_" -Level ERROR
    exit 1
}
finally {
    # Ensure transcript is stopped if it was started
    if ((Get-Command -Name 'Stop-Transcript' -ErrorAction SilentlyContinue) -and 
        (Get-Transcript).Status -eq 'Started') {
        try {
            Stop-Transcript -ErrorAction SilentlyContinue
        }
        catch {
            # Ignore errors during transcript stop
        }
    }
    
    # Ensure progress bar is cleared
    if ($host.Name -eq 'ConsoleHost') {
        Write-Progress -Activity 'Processing files' -Completed
    }
}

#endregion
