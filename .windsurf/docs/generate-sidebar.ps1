# PowerShell script to generate _sidebar.md based on directory structure
$docsDir = "D:\Dev\repos\mywienerlinien\.windsurf\docs"
$sidebarPath = Join-Path $docsDir "_sidebar.md"
$excludeDirs = @('node_modules', '.git', '.github', '_media', 'assets', 'css', 'js', 'plugins', 'flows', 'junk')

function Get-MarkdownFiles {
    param (
        [string]$directory,
        [int]$level = 0,
        [bool]$isTopLevel = $false
    )
    
    $indent = '  ' * $level
    $content = @()
    
    # Always include directories that don't start with underscore and aren't excluded
    $directories = Get-ChildItem -Path $directory -Directory | 
                   Where-Object { $_.Name -notlike "_*" -and 
                                $excludeDirs -notcontains $_.Name } |
                   Sort-Object Name
    
    # Get all markdown files in current directory (except _*.md and README.md)
    $files = Get-ChildItem -Path $directory -File -Filter "*.md" |
             Where-Object { $_.Name -notlike "_*" -and $_.Name -ne "README.md" } |
             Sort-Object Name
    
    # Process each directory
    foreach ($dir in $directories) {
        $dirName = $dir.Name
        $readmePath = Join-Path $dir.FullName "README.md"
        
        if (Test-Path $readmePath) {
            $content += "$indent- [**$dirName**]($($dir.Name)/)"
        } else {
            $content += "$indent- **$dirName**"
        }
        
        # Recursively process subdirectories and files
        $subContent = Get-MarkdownFiles -directory $dir.FullName -level ($level + 1) -isTopLevel $false
        if ($subContent) {
            $content += $subContent
        }
    }
    
    # Add files in current directory
    foreach ($file in $files) {
        $fileName = [System.IO.Path]::GetFileNameWithoutExtension($file.Name)
        $filePath = $file.FullName.Substring($docsDir.Length).Replace('\', '/')
        $content += "$indent- [$fileName]($filePath)"
    }
    
    return $content
}

# Generate the sidebar content
$sidebarContent = @"
# Navigation

- [Home](/)

"@

# Get all top-level directories that start with a number and aren't excluded
$mainSections = Get-ChildItem -Path $docsDir -Directory |
                Where-Object { $_.Name -match '^\d' -and $excludeDirs -notcontains $_.Name } |
                Select-Object -ExpandProperty Name |
                Sort-Object

foreach ($section in $mainSections) {
    $sectionPath = Join-Path $docsDir $section
    if (Test-Path $sectionPath) {
        $sectionName = $section -replace '^\d+_', '' -replace '_', ' '
        $sectionName = (Get-Culture).TextInfo.ToTitleCase($sectionName.ToLower())
        $sidebarContent += "
## $sectionName"
        
        # Process the top-level section (isTopLevel=$false to include all subdirectories)
        $sectionContent = Get-MarkdownFiles -directory $sectionPath -level 0 -isTopLevel $false
        if ($sectionContent) {
            $sidebarContent += "`n" + ($sectionContent -join "`n")
        }
    }
}

# Add Flows section at the end
$sidebarContent += @"

## Flows

- [All Flows](/flows/)
"@

# Write to _sidebar.md
$sidebarContent | Out-File -FilePath $sidebarPath -Encoding utf8

Write-Host "Sidebar generated successfully at: $sidebarPath"
