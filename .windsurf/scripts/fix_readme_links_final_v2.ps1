# Script to fix README.md links - Final Version 2

# Configuration
$docsDir = "D:\\Dev\\repos\\mywienerlinien\\.windsurf\\docs"
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
    
    $fullPath = Join-Path -Path $docsDir -ChildPath $path.TrimStart('/\\')
    return (Test-Path -Path $fullPath -PathType Container)
}

# Process all markdown links
$updatedContent = [regex]::Replace($content, '\[(?<text>[^\]]+)\]\((?<url>[^)#]+)(?<fragment>#[^)]*)?\)', {
    param($match)
    
    $text = $match.Groups['text'].Value
    $url = $match.Groups['url'].Value
    $fragment = $match.Groups['fragment'].Value
    
    # Skip external links, anchors, and mailto links
    if ($url -match '^(https?://|#|mailto:)' -or [string]::IsNullOrWhiteSpace($url)) {
        return $match.Value
    }
    
    # Skip links that already have .md or .md# in them
    if ($url -match '\.md(?:#|$)' -or $url -match '^[^/]+$') {
        return $match.Value
    }
    
    # Check if it's a directory
    if (Test-IsDirectory -path $url) {
        $newUrl = "$url/README.md$fragment"
        Write-Host "Fixed link: [$text]($url$fragment) -> [$text]($newUrl)" -ForegroundColor Yellow
        return "[$text]($newUrl)"
    }
    
    return $match.Value
})

# Save the updated content
$updatedContent | Out-File -FilePath $readmePath -Encoding utf8 -NoNewline

Write-Host "\nLinks in README.md have been updated." -ForegroundColor Green
Write-Host "Original file backed up to: $backupPath" -ForegroundColor Cyan
Write-Host "\nVerifying links..." -ForegroundColor Cyan

# Run the link checker to verify the fixes
& "$PSScriptRoot\\check_links.ps1"
