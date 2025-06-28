# Simple script to fix links in one markdown file for Docsify
$filePath = "d:\Dev\repos\mywienerlinien\.windsurf\docs\ai\persons\demis_hassabis.md"
$backupPath = "$filePath.bak"
$tempPath = "$filePath.fixed"

# Create backup
Copy-Item -Path $filePath -Destination $backupPath -Force

# Read the file content
$content = Get-Content -Path $filePath -Raw

# Show original content
Write-Host "=== ORIGINAL CONTENT ==="
$content

# Fix markdown links (add leading slash, remove .md)
$fixedContent = [regex]::Replace($content, '\]\(((?!http|#)([^)]+)\.md)\)', {
    param($match)
    $path = $match.Groups[1].Value
    # Only modify if path doesn't start with / and ends with .md
    if ($path -notmatch '^/' -and $path -match '\.md$') {
        $newPath = "/" + $path -replace '\.md$', ''
        Write-Host "FIXING: [$($match.Groups[0].Value)] -> [$newPath]"
        return "]($newPath)"
    }
    return $match.Groups[0].Value
})

# Show fixed content
Write-Host "`n=== FIXED CONTENT ==="
$fixedContent

# Write to temp file
$fixedContent | Out-File -FilePath $tempPath -Encoding utf8 -NoNewline

Write-Host "`n=== CHANGES ==="
# Show diff-like output
$originalLines = $content -split "`n"
$fixedLines = $fixedContent -split "`n"

for ($i = 0; $i -lt [Math]::Max($originalLines.Count, $fixedLines.Count); $i++) {
    $originalLine = if ($i -lt $originalLines.Count) { $originalLines[$i] } else { "" }
    $fixedLine = if ($i -lt $fixedLines.Count) { $fixedLines[$i] } else { "" }
    
    if ($originalLine -ne $fixedLine) {
        Write-Host "Line $($i + 1):" -ForegroundColor Yellow
        if ($originalLine) { Write-Host "- $originalLine" -ForegroundColor Red -NoNewline; Write-Host "`n" }
        if ($fixedLine) { Write-Host "+ $fixedLine" -ForegroundColor Green }
    }
}

Write-Host "`n=== NEXT STEPS ==="
Write-Host "1. Review the changes above"
Write-Host "2. If they look correct, run:"
Write-Host "   Move-Item -Path '$tempPath' -Destination '$filePath' -Force"
Write-Host "3. If not, restore from backup:"
Write-Host "   Move-Item -Path '$backupPath' -Destination '$filePath' -Force"
