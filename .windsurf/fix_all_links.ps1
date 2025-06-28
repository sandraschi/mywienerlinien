# Script to fix all markdown links in the documentation
$docsRoot = "d:\\Dev\\repos\\mywienerlinien\\.windsurf\\docs"
$logFile = "d:\\Dev\\repos\\mywienerlinien\\.windsurf\\logs\\link_fix_summary_$(Get-Date -Format 'yyyyMMdd_HHmmss').log"
$changedFiles = 0
$totalLinksFixed = 0

# Create logs directory if it doesn't exist
$logDir = Split-Path -Parent $logFile
if (-not (Test-Path $logDir)) {
    New-Item -ItemType Directory -Path $logDir -Force | Out-Null
}

# Function to process a single file
function Process-MarkdownFile {
    param (
        [string]$filePath
    )
    
    $content = Get-Content -Path $filePath -Raw
    $originalContent = $content
    $changesMade = 0
    $fileLog = @()
    
    # Find all markdown links
    $matches = [regex]::Matches($content, '\[([^\]]+)\]\(((?!http|#)([^)]+)\.md)\)')
    
    foreach ($match in $matches) {
        $fullMatch = $match.Groups[0].Value
        $linkText = $match.Groups[1].Value
        $linkTarget = $match.Groups[2].Value
        
        # Skip if already has leading slash
        if ($linkTarget -notmatch '^/') {
            $newLink = "[$linkText](/$linkTarget)" -replace '\.md$', ''
            $content = $content.Replace($fullMatch, $newLink)
            $fileLog += "  FIXED: $fullMatch -> $newLink"
            $changesMade++
            $script:totalLinksFixed++
        }
    }
    
    # Only write if changes were made
    if ($changesMade -gt 0) {
        # Create backup
        $backupPath = "$filePath.bak"
        if (-not (Test-Path $backupPath)) {
            Copy-Item -Path $filePath -Destination $backupPath -Force
        }
        
        # Write changes
        $content | Out-File -FilePath $filePath -Encoding utf8 -NoNewline
        
        $script:changedFiles++
        return @{
            Path = $filePath
            Changes = $changesMade
            Log = $fileLog
        }
    }
    
    return $null
}

# Start processing
Write-Host "Starting link fix process..." -ForegroundColor Cyan
Write-Host "Documentation root: $docsRoot"
Write-Host "Log file: $logFile"
Write-Host ""

# Process all markdown files
$files = Get-ChildItem -Path $docsRoot -Filter "*.md" -Recurse | Where-Object { $_.FullName -notlike '*.bak' }
$processedFiles = 0
$fileResults = @()

foreach ($file in $files) {
    $result = Process-MarkdownFile -filePath $file.FullName
    if ($null -ne $result) {
        $fileResults += $result
    }
    $processedFiles++
    Write-Progress -Activity "Processing files" -Status "$processedFiles of $($files.Count) files processed" -PercentComplete (($processedFiles / $files.Count) * 100)
}

# Generate report
$report = @"
=== LINK FIX SUMMARY ===
Date: $(Get-Date)
Total files processed: $($files.Count)
Files modified: $changedFiles
Total links fixed: $totalLinksFixed

=== MODIFIED FILES ===
"@

foreach ($result in $fileResults) {
    $report += "`n$($result.Path) ($($result.Changes) links fixed):`n"
    $report += $result.Log -join "`n"
}

# Write log file
$report | Out-File -FilePath $logFile -Encoding utf8

# Show summary
Write-Host "`n=== PROCESS COMPLETE ===" -ForegroundColor Green
Write-Host "Total files processed: $($files.Count)"
Write-Host "Files modified: $changedFiles"
Write-Host "Total links fixed: $totalLinksFixed"
Write-Host "`nFull report saved to: $logFile"

# Show how to revert changes if needed
Write-Host "`n=== TO REVERT CHANGES ===" -ForegroundColor Yellow
Write-Host "To restore all files from backup, run:"
Write-Host "Get-ChildItem -Path '$docsRoot' -Filter '*.bak' -Recurse | ForEach-Object { Move-Item -Path `$_.FullName -Destination (`$_.FullName -replace '\.bak$', '') -Force }"

# Show log file location
Write-Host "`nPress any key to view the log file..."
$null = $Host.UI.RawUI.ReadKey('NoEcho,IncludeKeyDown')
notepad $logFile
