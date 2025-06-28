# fix_links_dry_run.ps1

$docsRoot = "d:\Dev\repos\mywienerlinien\.windsurf\docs"
$linkRegex = '\[([^\]]*)\]\(([^)]*)\)' # Simpler regex to capture all links

Write-Host "Starting link analysis (dry run)..."

Get-ChildItem -Path $docsRoot -Recurse -Filter "*.md" | Where-Object { $_.Name -ne '_sidebar.md' } | ForEach-Object {
    $file = $_;
    $originalContent = Get-Content -Path $file.FullName -Raw
    
    $matches = [regex]::Matches($originalContent, $linkRegex)
    
    if ($matches.Count -gt 0) {
        $foundChangeInFile = $false
        foreach ($match in $matches) {
            $fullMatch = $match.Value
            $linkText = $match.Groups[1].Value
            $linkTarget = $match.Groups[2].Value

            # Check if it's a relative link to a markdown file that needs fixing
            if ($linkTarget.EndsWith('.md') -and !$linkTarget.StartsWith('http') -and !$linkTarget.StartsWith('/')) {
                
                $containingDir = Split-Path -Path $file.FullName -Parent
                $absoluteTargetPath = $null
                try {
                    $absoluteTargetPath = Resolve-Path -Path (Join-Path -Path $containingDir -ChildPath $linkTarget) -ErrorAction Stop
                } catch {
                    # This link is broken, can't resolve it.
                    Write-Warning "Could not resolve link '$linkTarget' in file $($file.FullName)"
                    continue
                }
                
                if ($null -ne $absoluteTargetPath) {
                    $newRelativePath = (Get-Item -Path $absoluteTargetPath).FullName.Replace($docsRoot, '').Replace('\', '/')
                    
                    if ($newRelativePath.StartsWith('/')) {
                        $newRelativePath = $newRelativePath.Substring(1)
                    }

                    # If the old path is different from the new one, report it
                    if ($linkTarget -ne $newRelativePath) {
                        if (-not $foundChangeInFile) {
                            Write-Host "--- Found potential changes in: $($file.FullName) ---"
                            $foundChangeInFile = $true
                        }
                        Write-Host "  [FROM]: $fullMatch"
                        Write-Host "  [TO]  : [$linkText]($newRelativePath)"
                    }
                }
            }
        }
    }
}

Write-Host "Link analysis completed."
