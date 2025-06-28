# debug_links_v2.ps1
# This is a READ-ONLY diagnostic script. It will not change any files.

$ErrorActionPreference = "Stop"

$docsRoot = "d:\Dev\repos\mywienerlinien\.windsurf\docs"
# Corrected Regex:
# \[          - matches the literal [
# ([^\]]+)   - captures one or more characters that are not a ]
# \]          - matches the literal ]
# \(          - matches the literal (
# ([^)]+)    - captures one or more characters that are not a )
# \)          - matches the literal )
$linkRegex = "\[([^\]]+)\]\(([^)]+)\)"

$testFile = "d:\Dev\repos\mywienerlinien\.windsurf\docs\ai\persons\demis_hassabis.md"

Write-Host "--- STARTING DIAGNOSTIC RUN ---"
Write-Host "Analyzing file: $testFile"

if (-not (Test-Path $testFile)) {
    Write-Error "Test file does not exist: $testFile"
    return
}

$fileContent = Get-Content -Path $testFile -Raw

$matches = [regex]::Matches($fileContent, $linkRegex)

Write-Host "Found $($matches.Count) potential markdown links in the file."

if ($matches.Count -eq 0) {
    Write-Warning "No links found. The regex might still be incorrect or the file has no links."
}

foreach ($match in $matches) {
    Write-Host "---------------------------------"
    $fullMatch = $match.Value
    $linkText = $match.Groups[1].Value
    $linkTarget = $match.Groups[2].Value

    Write-Host "Match: '$fullMatch'"
    Write-Host "  - Text: '$linkText'"
    Write-Host "  - Target: '$linkTarget'"

    # Check if it's a relative link to a markdown file that needs fixing
    if ($linkTarget.EndsWith('.md') -and !$linkTarget.StartsWith('http') -and !$linkTarget.StartsWith('/')) {
        Write-Host "  - Verdict: Is a relative MD file. Proceeding with analysis."
        
        $containingDir = Split-Path -Path $testFile -Parent
        $path_to_resolve = Join-Path -Path $containingDir -ChildPath $linkTarget
        
        Write-Host "  - Path to resolve: '$path_to_resolve'"

        $absoluteTargetPath = $null
        if (Test-Path $path_to_resolve) {
            $absoluteTargetPath = (Resolve-Path -Path $path_to_resolve).Path
            Write-Host "  - Resolved absolute path: '$absoluteTargetPath'"
            
            $newRelativePath = $absoluteTargetPath.Replace($docsRoot, '').Replace('\', '/')
            if ($newRelativePath.StartsWith('/')) {
                $newRelativePath = $newRelativePath.Substring(1)
            }
            Write-Host "  - Calculated new root-relative path: '$newRelativePath'"

            if ($linkTarget -ne $newRelativePath) {
                Write-Host "  - CHANGE DETECTED: '$linkTarget' should be '$newRelativePath'"
            } else {
                Write-Host "  - NO CHANGE NEEDED."
            }
        } else {
            Write-Warning "  - WARNING: Could not resolve path '$path_to_resolve'. The link is broken."
        }
    } else {
        Write-Host "  - Verdict: Not a relative MD file. Skipping."
    }
}
Write-Host "--- DIAGNOSTIC RUN COMPLETE ---"
