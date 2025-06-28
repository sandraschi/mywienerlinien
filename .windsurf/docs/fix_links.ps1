# Fix-Links.ps1
# This script fixes cross-linking issues in markdown files

# Get the directory where this script is located
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$docsRoot = $scriptDir

# Create a backup of all markdown files before making changes
$timestamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$backupDir = Join-Path $docsRoot "..\docs_links_backup_$timestamp"
New-Item -ItemType Directory -Path $backupDir -Force | Out-Null

Write-Host "Creating backup of all markdown files to $backupDir" -ForegroundColor Cyan
Get-ChildItem -Path $docsRoot -Filter "*.md" -Recurse | ForEach-Object {
    $relativePath = $_.FullName.Substring($docsRoot.Length).TrimStart('\\')
    $backupPath = Join-Path $backupDir $relativePath
    $backupDirPath = Split-Path -Parent $backupPath
    
    if (-not (Test-Path $backupDirPath)) {
        New-Item -ItemType Directory -Path $backupDirPath -Force | Out-Null
    }
    
    Copy-Item -Path $_.FullName -Destination $backupPath -Force
}

# Function to get all markdown files recursively
function Get-MarkdownFiles {
    param (
        [string]$rootPath = $docsRoot
    )
    
    Get-ChildItem -Path $rootPath -Filter "*.md" -Recurse | 
        Where-Object { $_.FullName -notlike '*\node_modules\*' -and $_.FullName -notlike '*\.git\*' }
}

# Function to repair links in a single markdown file
function Repair-FileLinks {
    param (
        [string]$filePath
    )
    
    $content = Get-Content -Path $filePath -Raw
    if (-not $content) { return $false }
    
    $fileDir = [System.IO.Path]::GetDirectoryName($filePath)
    $relativePath = $filePath.Substring($docsRoot.Length).Replace('\', '/')
    $changesMade = $false
    
    # Fix markdown links [text](url)
    $content = [regex]::Replace($content, '\[([^\]]+)\]\(([^)]+)\)', {
        param($match)
        $linkText = $match.Groups[1].Value
        $linkUrl = $match.Groups[2].Value
        
        # Skip external links, anchors, and mailto links
        if ($linkUrl -match '^(https?://|#|mailto:|ftp://)' -or $linkUrl -match '^[a-zA-Z]:\\') {
            return $match.Value
        }
        
        # Skip empty links
        if ([string]::IsNullOrWhiteSpace($linkUrl)) {
            return $match.Value
        }
        
        # Handle relative paths
        $fullPath = if ($linkUrl.StartsWith('/')) {
            Join-Path $docsRoot $linkUrl.TrimStart('/')
        } else {
            Join-Path $fileDir $linkUrl
        }
        
        # Handle fragment links
        $fragment = ''
        if ($linkUrl -match '^([^#]+)(#.+)$') {
            $linkUrl = $matches[1]
            $fragment = $matches[2]
            $fullPath = if ($linkUrl.StartsWith('/')) {
                Join-Path $docsRoot $linkUrl.TrimStart('/')
            } else {
                Join-Path $fileDir $linkUrl
            }
        }
        
        # Check if it's a directory and has a README.md
        if (Test-Path $fullPath -PathType Container) {
            $readmePath = Join-Path $fullPath 'README.md'
            if (Test-Path $readmePath) {
                $relativePath = [System.IO.Path]::GetRelativePath($fileDir, $readmePath).Replace('\', '/')
                if (-not $relativePath.StartsWith('.')) { $relativePath = "./$relativePath" }
                $changesMade = $true
                return "[$linkText]($relativePath$fragment)"
            }
        }
        # Check if it's a markdown file without extension
        elseif (-not [System.IO.Path]::HasExtension($fullPath)) {
            $mdPath = "$fullPath.md"
            if (Test-Path $mdPath) {
                $relativePath = [System.IO.Path]::GetRelativePath($fileDir, $mdPath).Replace('\', '/')
                if (-not $relativePath.StartsWith('.')) { $relativePath = "./$relativePath" }
                $changesMade = $true
                return "[$linkText]($relativePath$fragment)"
            }
        }
        # Check if the file exists with the current path
        elseif (Test-Path $fullPath) {
            $relativePath = [System.IO.Path]::GetRelativePath($fileDir, $fullPath).Replace('\', '/')
            if (-not $relativePath.StartsWith('.')) { $relativePath = "./$relativePath" }
            $changesMade = $true
            return "[$linkText]($relativePath$fragment)"
        }
        
        return $match.Value
    })
    
    # Fix image links
    $content = [regex]::Replace($content, '!\[([^\]]*)\]\(([^)]+)\)', {
        param($match)
        $altText = $match.Groups[1].Value
        $imgPath = $match.Groups[2].Value
        
        # Skip external URLs
        if ($imgPath -match '^(https?://|ftp://)') {
            return $match.Value
        }
        
        # Handle relative paths
        $fullPath = if ($imgPath.StartsWith('/')) {
            Join-Path $docsRoot $imgPath.TrimStart('/')
        } else {
            Join-Path $fileDir $imgPath
        }
        
        if (Test-Path $fullPath) {
            $relativePath = [System.IO.Path]::GetRelativePath($fileDir, $fullPath).Replace('\', '/')
            if (-not $relativePath.StartsWith('.')) { $relativePath = "./$relativePath" }
            $changesMade = $true
            return "![$altText]($relativePath)"
        }
        
        return $match.Value
    })
    
    # Save the file if changes were made
    if ($changesMade) {
        Write-Host "Fixed links in: $relativePath" -ForegroundColor Green
        $content | Set-Content -Path $filePath -NoNewline -Encoding UTF8
        return $true
    }
    return $false
}

# Fix links in all markdown files
Write-Host "\nFixing links in markdown files..." -ForegroundColor Cyan
$markdownFiles = Get-MarkdownFiles -rootPath $docsRoot
$totalFiles = $markdownFiles.Count
$current = 0

foreach ($file in $markdownFiles) {
    $current++
    $progress = [math]::Round(($current / $totalFiles) * 100, 2)
    Write-Progress -Activity "Fixing links" -Status "Processing $($file.Name) ($current of $totalFiles)" -PercentComplete $progress
    
    try {
        Repair-FileLinks -filePath $file.FullName
    }
    catch {
        Write-Host "Error processing $($file.FullName): $_" -ForegroundColor Red
    }
}

Write-Progress -Activity "Fixing links" -Completed
Write-Host "\nLink fixing completed! Backup created at: $backupDir" -ForegroundColor Green
