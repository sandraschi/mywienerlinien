# Script to fix links in README.md - Version 2

# Configuration
$docsDir = "D:\Dev\repos\mywienerlinien\.windsurf\docs"
$readmePath = Join-Path -Path $docsDir -ChildPath "README.md"
$backupPath = "$readmePath.backup_$(Get-Date -Format 'yyyyMMdd_HHmmss').md"

# Create backup of original file
Copy-Item -Path $readmePath -Destination $backupPath -Force
Write-Host "Created backup at: $backupPath" -ForegroundColor Cyan

# Read the content
$content = Get-Content -Path $readmePath -Raw

# Function to check if a path is a directory
function Test-IsDirectory {
    param([string]$path)
    
    $fullPath = Join-Path -Path $docsDir -ChildPath $path.TrimStart('/')
    return (Test-Path -Path $fullPath -PathType Container)
}

# Function to fix a single link
function Fix-Link {
    param([string]$link)
    
    # Skip external links, anchors, and mailto links
    if ($link -match '^(https?://|#|mailto:)' -or [string]::IsNullOrWhiteSpace($link)) {
        return $link
    }
    
    # Remove leading slash if present
    $cleanLink = $link.TrimStart('/')
    
    # Check if it's a directory
    if (Test-IsDirectory -path $cleanLink) {
        # For directories, link to the README.md inside
        return "$cleanLink/README.md"
    }
    
    # Check if it's a file that exists
    $fullPath = Join-Path -Path $docsDir -ChildPath $cleanLink
    if (Test-Path -Path $fullPath -PathType Leaf) {
        return $cleanLink
    }
    
    # Check if file with .md extension exists
    if (-not ($cleanLink -match '\.md$')) {
        $mdPath = "$cleanLink.md"
        $fullMdPath = Join-Path -Path $docsDir -ChildPath $mdPath
        if (Test-Path -Path $fullMdPath -PathType Leaf) {
            return $mdPath
        }
    }
    
    # If we get here, return the original link
    return $link
}

# Process all markdown links
$updatedContent = [regex]::Replace($content, '\[(?<text>[^\]]+)\]\((?<url>[^)]+)\)', {
    param($match)
    
    $text = $match.Groups['text'].Value
    $url = $match.Groups['url'].Value
    
    # Skip external links, anchors, and mailto links
    if ($url -match '^(https?://|#|mailto:)' -or [string]::IsNullOrWhiteSpace($url)) {
        return $match.Value
    }
    
    $fixedUrl = Fix-Link -link $url
    
    # Only update if the URL was changed
    if ($fixedUrl -ne $url) {
        Write-Host "Fixed link: [$text]($url) -> [$text]($fixedUrl)" -ForegroundColor Yellow
        return "[$text]($fixedUrl)"
    }
    
    return $match.Value
})

# Save the updated content
$updatedContent | Out-File -FilePath $readmePath -Encoding utf8 -NoNewline

Write-Host "\nLinks in README.md have been updated." -ForegroundColor Green
Write-Host "Original file backed up to: $backupPath" -ForegroundColor Cyan
Write-Host "\nVerifying links..." -ForegroundColor Cyan

# Run the link checker to verify the fixes
& "$PSScriptRoot\check_links.ps1"
