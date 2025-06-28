# debug_links.ps1
$docsRoot = "d:\Dev\repos\mywienerlinien\.windsurf\docs"
$linkRegex = '\[([^\]]*)\]\(([^)]*)\)'

$testFile = "d:\Dev\repos\mywienerlinien\.windsurf\docs\ai\persons\demis_hassabis.md"

Write-Host "Analyzing file: $testFile"
$fileContent = Get-Content -Path $testFile -Raw

$matches = [regex]::Matches($fileContent, $linkRegex)

Write-Host "Found $($matches.Count) matches."

foreach ($match in $matches) {
    Write-Host "--- Match Found ---"
    $linkTarget = $match.Groups[2].Value
    Write-Host "Link Target (from regex): '$linkTarget'"

    if ($linkTarget.EndsWith('.md') -and !$linkTarget.StartsWith('http') -and !$linkTarget.StartsWith('/')) {
        Write-Host "Link is a relative MD file."
        
        $containingDir = Split-Path -Path $testFile -Parent
        Write-Host "Containing Dir: $containingDir"
        
        $path_to_resolve = Join-Path -Path $containingDir -ChildPath $linkTarget
        Write-Host "Path to Resolve: $path_to_resolve"

        $absoluteTargetPath = Resolve-Path -Path $path_to_resolve -ErrorAction SilentlyContinue
        Write-Host "Absolute Target Path: $absoluteTargetPath"
        
        if ($null -ne $absoluteTargetPath) {
            $newRelativePath = (Get-Item -Path $absoluteTargetPath).FullName.Replace($docsRoot, '').Replace('\', '/')
            if ($newRelativePath.StartsWith('/')) {
                $newRelativePath = $newRelativePath.Substring(1)
            }
            Write-Host "New Relative Path: '$newRelativePath'"

            if ($linkTarget -ne $newRelativePath) {
                Write-Host "CHANGE DETECTED: '$linkTarget' -> '$newRelativePath'"
            } else {
                Write-Host "NO CHANGE NEEDED."
            }
        } else {
            Write-Warning "Could not resolve path."
        }
    } else {
        Write-Host "Link is not a relative MD file. Skipping."
    }
    Write-Host "-------------------"
}
