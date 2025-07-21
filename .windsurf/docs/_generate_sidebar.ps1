# PowerShell script to generate _sidebar.md with all subdirectories and markdown files
$rootPath = $PSScriptRoot
$outputFile = Join-Path -Path $rootPath -ChildPath "_sidebar.md"
$baseUrl = "/"

function Get-MarkdownFiles {
    param (
        [string]$directory,
        [int]$depth = 0
    )
    
    $indent = '  ' * $depth
    $content = @()
    
    # Get all directories and sort them
    $directories = Get-ChildItem -Path $directory -Directory | Sort-Object Name
    
    # Get all markdown files in current directory (except _sidebar.md and README.md)
    $files = Get-ChildItem -Path $directory -File -Filter "*.md" | 
             Where-Object { $_.Name -ne "_sidebar.md" -and $_.Name -ne "README.md" } |
             Sort-Object Name
    
    # Add README.md first if it exists
    $readme = Get-ChildItem -Path $directory -File -Filter "README.md" -ErrorAction SilentlyContinue
    if ($readme) {
        $relativePath = $readme.FullName.Substring($rootPath.Length).Replace('\', '/')
        $displayName = if ($depth -eq 0) { "Overview" } else { (Get-Culture).TextInfo.ToTitleCase(($readme.BaseName -replace '_', ' ').ToLower()) }
        $content += "${indent}- [$displayName]($relativePath)"
    }
    
    # Add other markdown files
    foreach ($file in $files) {
        $relativePath = $file.FullName.Substring($rootPath.Length).Replace('\', '/')
        $displayName = (Get-Culture).TextInfo.ToTitleCase(($file.BaseName -replace '_', ' ').ToLower())
        $content += "${indent}- [$displayName]($relativePath)"
    }
    
    # Process subdirectories
    foreach ($dir in $directories) {
        $dirName = (Get-Culture).TextInfo.ToTitleCase(($dir.Name -replace '^\d+_', '' -replace '_', ' ').ToLower())
        $subContent = Get-MarkdownFiles -directory $dir.FullName -depth ($depth + 1)
        
        if ($subContent) {
            $content += "${indent}- $dirName"
            $content += $subContent
        }
    }
    
    return $content
}

# Generate the sidebar content
$sidebarContent = @("- [Home]($baseUrl)")

# Process each top-level directory that starts with a digit
$topLevelDirs = Get-ChildItem -Path $rootPath -Directory | Where-Object { $_.Name -match '^\d+_' } | Sort-Object Name

foreach ($dir in $topLevelDirs) {
    $dirName = $dir.Name -replace '^\d+_', '' -replace '_', ' '
    $sectionNumber = ($dir.Name -split '_')[0]
    $sectionContent = Get-MarkdownFiles -directory $dir.FullName -depth 1
    
    if ($sectionContent) {
        $sidebarContent += "- ${sectionNumber}. $dirName"
        $sidebarContent += $sectionContent
    }
}

# Write to _sidebar.md
$sidebarContent | Out-File -FilePath $outputFile -Encoding utf8 -Force

Write-Host "_sidebar.md has been generated successfully!"
