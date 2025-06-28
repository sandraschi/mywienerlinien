# Manual link fix for README.md

# Configuration
$docsDir = "D:\Dev\repos\mywienerlinien\.windsurf\docs"
$readmePath = Join-Path -Path $docsDir -ChildPath "README.md"
$backupPath = "$readmePath.backup_$(Get-Date -Format 'yyyyMMdd_HHmmss').md"

# Create backup of original file
Copy-Item -Path $readmePath -Destination $backupPath -Force
Write-Host "Created backup at: $backupPath" -ForegroundColor Cyan

# Read the content
$content = Get-Content -Path $readmePath -Raw

# Define manual replacements for each link
$replacements = @{
    # Top-level section links
    "/1_news" = "1_news/README.md"
    "/1_news/releases" = "1_news/releases/README.md"
    "/2_notes" = "2_notes/README.md"
    "/2_notes/flows" = "2_notes/flows/README.md"
    "/2_notes/ideas" = "2_notes/ideas/README.md"
    "/2_notes/meeting-notes" = "2_notes/meeting-notes/README.md"
    "/2_notes/how-tos" = "2_notes/how-tos/README.md"
    "/2_notes/troubleshooting" = "2_notes/troubleshooting/README.md"
    "/3_ai" = "3_ai/README.md"
    "/3_ai/basics" = "3_ai/basics/README.md"
    "/3_ai/companies" = "3_ai/companies/README.md"
    "/3_ai/hardware" = "3_ai/hardware/README.md"
    "/3_ai/hosted_llms" = "3_ai/hosted_llms/README.md"
    "/3_ai/local_llms" = "3_ai/local_llms/README.md"
    "/3_ai/news" = "3_ai/news/README.md"
    "/3_ai/papers" = "3_ai/papers/README.md"
    "/3_ai/persons" = "3_ai/persons/README.md"
    "/3_ai/speech" = "3_ai/speech/README.md"
    "/3_ai/image_and_video" = "3_ai/image_and_video/README.md"
    "/3_ai/controversies" = "3_ai/controversies/README.md"
    "/5_development" = "5_development/README.md"
    "/5_development/api" = "5_development/api/README.md"
    "/5_development/architecture" = "5_development/architecture/README.md"
    "/5_development/docker" = "5_development/docker/README.md"
    "/5_development/frameworks" = "5_development/frameworks/README.md"
    "/5_development/guides" = "5_development/guides/README.md"
    "/5_development/ide" = "5_development/ide/README.md"
    "/5_development/low_code_no_code" = "5_development/low_code_no_code/README.md"
    "/5_development/ui_libraries" = "5_development/ui_libraries/README.md"
    "/6_software" = "6_software/README.md"
    "/6_software/development_tools" = "6_software/development_tools/README.md"
    "/6_software/operating_systems" = "6_software/operating_systems/README.md"
    "/6_software/security" = "6_software/security/README.md"
    "/7_projects" = "7_projects/README.md"
    "/7_projects/S&S_docs" = "7_projects/S&S_docs/README.md"
    "/7_projects/wiener_linien" = "7_projects/wiener_linien/README.md"
    "/8_robotics" = "8_robotics/README.md"
    "/8_robotics/canine" = "8_robotics/canine/README.md"
    "/8_robotics/humanoid" = "8_robotics/humanoid/README.md"
    "/8_robotics/industrial_logistics" = "8_robotics/industrial_logistics/README.md"
    "/9_misc/resources" = "9_misc/resources/README.md"
    "/9_misc/proposed_rules" = "9_misc/proposed_rules/README.md"
    "/9_misc/archive" = "9_misc/archive/README.md"
    
    # Other specific links
    "wiener_linien/WIENER_LINIEN_API_GUIDE.md" = "7_projects/wiener_linien/WIENER_LINIEN_API_GUIDE.md"
    "wiener_linien/gtfs.md" = "7_projects/wiener_linien/gtfs.md"
    "flows/bugs/250621_rules_reading_issue/bug.md" = "2_notes/flows/bugs/250621_rules_reading_issue/bug.md"
    "flows/bugs/250621_rules_reading_issue/analysis.md" = "2_notes/flows/bugs/250621_rules_reading_issue/analysis.md"
    "global_services/documentation_standards.md" = "5_development/global_services/documentation_standards.md"
    "global_services/template_library.md" = "5_development/global_services/template_library.md"
    "ide/README.md" = "5_development/ide/README.md"
    "../grafana/import_dashboard.ps1" = "../grafana/import_dashboard.ps1"
}

# Apply replacements
$updatedContent = $content
foreach ($oldLink in $replacements.Keys) {
    $newLink = $replacements[$oldLink]
    $escapedOldLink = [regex]::Escape($oldLink)
    $updatedContent = [regex]::Replace($updatedContent, "\($escapedOldLink(?:/|\\)?([^)]*)\)", {
        param($match)
        $suffix = $match.Groups[1].Value
        if (-not [string]::IsNullOrWhiteSpace($suffix)) {
            "($newLink$suffix)"
        } else {
            "($newLink)"
        }
    })
    
    Write-Host "Replaced: $oldLink -> $newLink" -ForegroundColor Yellow
}

# Save the updated content
$updatedContent | Out-File -FilePath $readmePath -Encoding utf8 -NoNewline

Write-Host "\nLinks in README.md have been updated." -ForegroundColor Green
Write-Host "Original file backed up to: $backupPath" -ForegroundColor Cyan
Write-Host "\nVerifying links..." -ForegroundColor Cyan

# Run the link checker to verify the fixes
& "$PSScriptRoot\check_links.ps1"
