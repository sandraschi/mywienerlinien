# Build-Sidebar.ps1
# Script to generate a dynamic sidebar for Docsify documentation
# Scans the docs directory and creates a structured sidebar with collapsible sections
# Focuses on top-level folders starting with digits and handles special flow directories

# Configuration
$docsRoot = Join-Path $PSScriptRoot "..\..\.windsurf\docs"
$excludeDirs = @(".git", "node_modules", "_assets", "_media", "_static", "plugins", "css", "js", "img", "images")
$specialDirs = @("research", "bugs")  # Directories that need special handling

# Helper function to format a title from a filename
function Format-Title {
    param ([string]$text)
    # Remove date prefix if exists (YYYY-MM-DD_)
    $text = $text -replace '^\d{4}-\d{2}-\d{2}_', ''
    # Convert snake_case and kebab-case to Title Case
    $text = $text -replace '[_-]', ' ' -replace '\b(\p{Ll})', { $_.Value.ToUpper() }
    return $text.Trim()
}

# Helper function to get directory structure
function Get-DirectoryStructure {
    param (
        [string]$path,
        [int]$level = 0,
        [string]$relativePath = ""
    )

    $output = @()
    
    # Get directories, sorted by name, with numeric directories first
    $items = Get-ChildItem -Path $path -Directory -Force | 
        Where-Object { $excludeDirs -notcontains $_.Name } |
        Sort-Object { 
            if ($_.Name -match '^\d') { "0$($_.Name)" } 
            else { "1$($_.Name)" } 
        }
    
    foreach ($item in $items) {
        $itemPath = if ($relativePath) { "$relativePath/$($item.Name)" } else { $item.Name }
        $isSpecialDir = $specialDirs -contains $item.Name
        
        # Check for markdown files or special directories
        $hasMarkdown = (Get-ChildItem -Path $item.FullName -Filter "*.md" -File -Recurse -Depth 0).Count -gt 0
        
        if ($hasMarkdown -or $isSpecialDir) {
            $indent = "  " * $level
            $title = Format-Title $item.Name
            
            # Handle special directories (research, bugs, etc.)
            if ($isSpecialDir) {
                $output += ""  # Add a blank line before special sections
                $output += "$indent- **$title**"
                
                # Get subdirectories sorted by date (newest first)
                $subDirs = Get-ChildItem -Path $item.FullName -Directory | 
                    Sort-Object { $_.Name } -Descending
                
                foreach ($subDir in $subDirs) {
                    $subTitle = Format-Title $subDir.Name
                    $output += "$indent  - [$subTitle](/$itemPath/$($subDir.Name)/README.md)"
                    
                    # Add README link if it exists
                    $readmePath = Join-Path $subDir.FullName "README.md"
                    if (Test-Path $readmePath) {
                        $readmeContent = Get-Content $readmePath -Raw
                        if ($readmeContent -match '(?m)^#\s+(.+)$') {
                            $readmeTitle = $matches[1].Trim()
                            $output[-1] = "$indent  - [$readmeTitle](/$itemPath/$($subDir.Name)/README.md)"
                        }
                    }
                    
                    # Add chunk files if they exist
                    $chunkFiles = Get-ChildItem -Path $subDir.FullName -Filter "chunk_*.md" | 
                        Sort-Object Name
                    foreach ($chunk in $chunkFiles) {
                        $chunkTitle = Format-Title ($chunk.BaseName -replace '^chunk_\d+_', '')
                        $output += "$indent    - [$chunkTitle](/$itemPath/$($subDir.Name)/$($chunk.Name))"
                    }
                }
            }
            # Handle regular directories
            else {
                $readmePath = Join-Path $item.FullName "README.md"
                $hasReadme = Test-Path $readmePath
                
                if ($hasReadme) {
                    $readmeContent = Get-Content $readmePath -Raw
                    if ($readmeContent -match '(?m)^#\s+(.+)$') {
                        $title = $matches[1].Trim()
                    }
                    $output += "$indent- [$title](/$itemPath/README.md)"
                } else {
                    $output += "$indent- [$title](/$itemPath/)"
                }
                
                # Recursively process subdirectories
                $subOutput = Get-DirectoryStructure -path $item.FullName -level ($level + 1) -relativePath $itemPath
                if ($subOutput) {
                    $output += $subOutput
                }
            }
        }
    }
    
    return $output
}

# Main script execution
try {
    Write-Host "Generating sidebar..." -ForegroundColor Cyan
    
    # Start with the main navigation header
    $sidebarContent = @(
        "# Navigation",
        "",
        "- [Home](README.md)"
    )
    
    # Get the main documentation structure
    $mainContent = Get-DirectoryStructure -path $docsRoot
    $sidebarContent += $mainContent
    
    # Add a separator before external links
    $sidebarContent += @(
        "",
        "---",
        "## External Links",
        "- [GitHub Repository](https://github.com/your-org/your-repo)",
        "- [Project Board](https://github.com/orgs/your-org/projects/1)",
        ""
    )
    
    # Create a timestamped version of the sidebar
    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $timestampedSidebarPath = Join-Path $docsRoot "_sidebar_${timestamp}.md"
    
    # Write to timestamped sidebar file
    $sidebarContent | Out-File -FilePath $timestampedSidebarPath -Encoding utf8 -Force -NoNewline:$false
    
    # Ensure consistent line endings
    $content = [System.IO.File]::ReadAllText($timestampedSidebarPath) -replace "`r`n", "`n" -replace "`n", "`r`n"
    [System.IO.File]::WriteAllText($timestampedSidebarPath, $content, [System.Text.Encoding]::UTF8)
    
    Write-Host "✅ Timestamped sidebar generated successfully at: $timestampedSidebarPath" -ForegroundColor Green
    Write-Host "   To use this sidebar, rename it to '_sidebar.md'" -ForegroundColor Yellow
} catch {
    Write-Host "❌ Error generating sidebar: $_" -ForegroundColor Red
    exit 1
}
