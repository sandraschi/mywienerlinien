# Script to fix links in README.md

# Configuration
$docsDir = "D:\Dev\repos\mywienerlinien\.windsurf\docs"
$readmePath = Join-Path -Path $docsDir -ChildPath "README.md"
$backupPath = "$readmePath.backup_$(Get-Date -Format 'yyyyMMdd_HHmmss').md"

# Create backup of original file
Copy-Item -Path $readmePath -Destination $backupPath -Force
Write-Host "Created backup at: $backupPath" -ForegroundColor Cyan

# Read the content
$content = Get-Content -Path $readmePath -Raw

# Define link replacements - update paths to include .md extension and make relative
$replacements = @{
    '\[(.*?)\]\(/([^)]+)\)' = '[$1]($2/README.md)'  # Absolute paths to relative with README.md
    '\[(.*?)\]\(([^)]+)/\)' = '[$1]($2/README.md)'     # Directory links to README.md
    '\[(.*?)\]\(([^)]+)\)' = '[$1]($2.md)'            # Other links to .md
}

# Apply replacements
$updatedContent = $content
foreach ($pattern in $replacements.Keys) {
    $updatedContent = [regex]::Replace($updatedContent, $pattern, {
        param($match)
        $replacement = $replacements[$pattern]
        $replacement -replace '\$1', $match.Groups[1].Value -replace '\$2', $match.Groups[2].Value
    })
}

# Special case for links that should not have .md (like external links)
$updatedContent = $updatedContent -replace '(\[[^\]]+\])\(([^)]+\.(?:png|jpg|jpeg|gif|svg|pdf|html?|zip|exe|msi))([^)]*)\)', '$1($2$3)'

# Save the updated content
$updatedContent | Out-File -FilePath $readmePath -Encoding utf8 -NoNewline

Write-Host "Links in README.md have been updated." -ForegroundColor Green
Write-Host "Original file backed up to: $backupPath" -ForegroundColor Cyan
