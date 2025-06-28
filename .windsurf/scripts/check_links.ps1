# Simple script to check links in markdown files

# Configuration
$rootDir = "D:\Dev\repos\mywienerlinien\.windsurf\docs"
$readmePath = Join-Path -Path $rootDir -ChildPath "README.md"
$outputFile = "D:\Dev\repos\mywienerlinien\.windsurf\scripts\broken_links_report_$(Get-Date -Format 'yyyyMMdd_HHmmss').txt"

# Create a list to store broken links
$brokenLinks = @()

# Function to check if a link is valid
function Test-MarkdownLink {
    param (
        [string]$link,
        [string]$basePath
    )
    
    # Skip external links, anchors, and mailto links
    if ($link -match '^(https?://|#|mailto:)' -or [string]::IsNullOrWhiteSpace($link)) {
        return $true
    }
    
    # Handle relative paths
    if ($link -match '^/') {
        $fullPath = Join-Path -Path $rootDir -ChildPath $link.TrimStart('/')
    } else {
        $fullPath = Join-Path -Path $basePath -ChildPath $link
    }
    
    # Handle anchor links
    $pathWithoutAnchor = $fullPath -replace '#.*$', ''
    
    # Check if it's a directory (trailing slash)
    if ($pathWithoutAnchor -match '/$' -or $pathWithoutAnchor -match '\\$') {
        $pathWithoutAnchor = $pathWithoutAnchor.TrimEnd('/\')
        if (Test-Path -Path $pathWithoutAnchor -PathType Container) {
            return $true
        }
    }
    
    # Check if file exists (with or without .md extension)
    if (Test-Path -Path $pathWithoutAnchor -PathType Leaf) {
        return $true
    }
    
    # Check with .md extension
    if (-not ($pathWithoutAnchor -match '\.md$')) {
        $mdPath = "$pathWithoutAnchor.md"
        if (Test-Path -Path $mdPath -PathType Leaf) {
            return $true
        }
    }
    
    return $false
}

# Read the README file
Write-Host "Checking links in: $readmePath" -ForegroundColor Cyan
$content = Get-Content -Path $readmePath -Raw

# Find all markdown links [text](url)
$linkPattern = '\[(?<text>[^\]]+?)\]\((?<url>[^)]+?)\)'
$matches = [regex]::Matches($content, $linkPattern)

Write-Host "Found $($matches.Count) links to check..." -ForegroundColor Cyan

# Check each link
foreach ($match in $matches) {
    $linkText = $match.Groups['text'].Value
    $linkUrl = $match.Groups['url'].Value
    
    # Skip external links for now
    if ($linkUrl -match '^https?://') {
        Write-Host "[EXTERNAL] $linkUrl" -ForegroundColor DarkGray
        continue
    }
    
    $isValid = Test-MarkdownLink -link $linkUrl -basePath (Split-Path -Path $readmePath)
    
    if (-not $isValid) {
        $brokenLinks += @{
            Text = $linkText
            Url = $linkUrl
            Line = $content.Substring(0, $match.Index).Split("`n").Count
        }
        Write-Host "[BROKEN] $linkUrl" -ForegroundColor Red
    } else {
        Write-Host "[OK] $linkUrl" -ForegroundColor Green
    }
}

# Generate report
if ($brokenLinks.Count -gt 0) {
    $report = "# Broken Links Report`n"
    $report += "Generated: $(Get-Date)`n"
    $report += "File: $readmePath`n"
    $report += "Total Links Checked: $($matches.Count)`n"
    $report += "Broken Links: $($brokenLinks.Count)`n`n"
    
    $report += "## Broken Links`n"
    foreach ($item in $brokenLinks) {
        $report += "- **$($item.Text)**`n"
        $report += "  - URL: $($item.Url)`n"
        $report += "  - Line: $($item.Line)`n"
    }
    
    $report | Out-File -FilePath $outputFile -Encoding utf8
    
    Write-Host "`nFound $($brokenLinks.Count) broken links. Report saved to: $outputFile" -ForegroundColor Yellow
    Write-Host "You can open the report with: notepad $outputFile" -ForegroundColor Cyan
} else {
    Write-Host "`nNo broken links found!" -ForegroundColor Green
}
