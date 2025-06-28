# This script rewrites all markdown files with corrected, root-relative links.
# It creates new files with a _fixed.md suffix and leaves original files untouched.

$ErrorActionPreference = "Stop"
$LogFile = "d:\\Dev\\repos\\mywienerlinien\\.windsurf\\logs\\rewrite_links_ps.log"
$DocsRoot = "d:\\Dev\\repos\\mywienerlinien\\.windsurf\\docs"

# Clear previous log file for a clean run
if (Test-Path $LogFile) {
    Clear-Content $LogFile
}

# Function for robust logging
function Write-Log {
    param ([string]$Message)
    $Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $LogMessage = "$Timestamp - $Message"
    # Write to both console and log file
    Add-Content -Path $LogFile -Value $LogMessage
    Write-Host $LogMessage
}

try {
    Write-Log "--- Starting Link Rewriter (PowerShell) ---"
    # Get all .md files, excluding any previous _fixed.md files
    $files = Get-ChildItem -Path $DocsRoot -Recurse -Filter "*.md" | Where-Object { $_.Name -notlike "*_fixed.md" }

    foreach ($file in $files) {
        try {
            Write-Log "Processing file: $($file.FullName)"
            $fileContent = Get-Content -Path $file.FullName -Raw
            $fileDir = $file.DirectoryName
            $originalContent = $fileContent
            $changesMade = 0

            # Regex to find all markdown links: [text](target)
            $matches = [regex]::Matches($fileContent, '\[([^\]]+)\]\(([^)]+)\)')

            foreach ($match in $matches) {
                $fullMatch = $match.Groups[0].Value
                $linkText = $match.Groups[1].Value
                $linkTarget = $match.Groups[2].Value.Trim()

                # Skip external links, anchor links, or non-markdown links
                if ($linkTarget.StartsWith("http") -or $linkTarget.StartsWith("#") -or -not $linkTarget -or -not $linkTarget.EndsWith(".md")) {
                    continue
                }

                # Check if link is already valid from the root directory
                $rootRelativePath = Join-Path -Path $DocsRoot -ChildPath $linkTarget -Resolve
                if (Test-Path $rootRelativePath) {
                    continue # Link is already correct
                }

                # Check if link is valid from the file's own directory (i.e., it's a file-relative link that needs fixing)
                $fileRelativePath = Join-Path -Path $fileDir -ChildPath $linkTarget -Resolve
                if (Test-Path $fileRelativePath) {
                    # Convert the full, resolved path to a path relative to the docs root
                    $correctPath = (Resolve-Path -Path $fileRelativePath -Relative -RelativeTo $DocsRoot).TrimStart(".\") -replace '\\','/'
                    $newLink = "[$linkText]($correctPath)"
                    Write-Log "  FIXING: '$linkTarget' -> '$correctPath'"
                    $fileContent = $fileContent.Replace($fullMatch, $newLink)
                    $changesMade++
                } else {
                    Write-Log "  BROKEN: Link target '$linkTarget' not found from either root or file path."
                }
            }

            if ($changesMade -gt 0) {
                $newFilePath = $file.FullName.Replace(".md", "_fixed.md")
                Write-Log "  Writing $changesMade change(s) to $newFilePath"
                Set-Content -Path $newFilePath -Value $fileContent -Encoding UTF8 -Force
            } else {
                Write-Log "  No changes needed for this file."
            }
        } catch {
            Write-Log "ERROR processing file $($file.FullName): $($_.Exception.Message)"
        }
    }
    Write-Log "--- Script Finished ---"
}
catch {
    Write-Log "CRITICAL SCRIPT ERROR: An unhandled exception occurred. $($_.Exception.Message)"
}
