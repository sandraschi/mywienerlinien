# Script to fix remaining broken links in README.md

# Configuration
$docsDir = "D:\Dev\repos\mywienerlinien\.windsurf\docs"
$readmePath = Join-Path -Path $docsDir -ChildPath "README.md"
$backupPath = "$readmePath.backup_$(Get-Date -Format 'yyyyMMdd_HHmmss').md"

# Create backup of original file
Copy-Item -Path $readmePath -Destination $backupPath -Force
Write-Host "Created backup at: $backupPath" -ForegroundColor Cyan

# Read the content
$content = Get-Content -Path $readmePath -Raw

# Define patterns to fix
$patterns = @(
    @{
        Pattern = '\[(?<text>[^\]]+)\]\((?<url>1_news)(?<fragment>#[^)]*)?\)'
        Replacement = '[$1]($2/README.md$3)'
    },
    @{
        Pattern = '\[(?<text>[^\]]+)\]\((?<url>1_news/releases)(?<fragment>#[^)]*)?\)'
        Replacement = '[$1]($2/README.md$3)'
    },
    @{
        Pattern = '\[(?<text>[^\]]+)\]\((?<url>2_notes)(?<fragment>#[^)]*)?\)'
        Replacement = '[$1]($2/README.md$3)'
    },
    @{
        Pattern = '\[(?<text>[^\]]+)\]\((?<url>2_notes/how-tos)(?<fragment>#[^)]*)?\)'
        Replacement = '[$1]($2/README.md$3)'
    },
    @{
        Pattern = '\[(?<text>[^\]]+)\]\((?<url>2_notes/troubleshooting)(?<fragment>#[^)]*)?\)'
        Replacement = '[$1]($2/README.md$3)'
    },
    @{
        Pattern = '\[(?<text>[^\]]+)\]\((?<url>2_notes/contributing)(?<fragment>#[^)]*)?\)'
        Replacement = '[$1]($2/README.md$3)'
    },
    @{
        Pattern = '\[(?<text>[^\]]+)\]\((?<url>3_ai)(?<fragment>#[^)]*)?\)'
        Replacement = '[$1]($2/README.md$3)'
    },
    @{
        Pattern = '\[(?<text>[^\]]+)\]\((?<url>5_development)(?<fragment>#[^)]*)?\)'
        Replacement = '[$1]($2/README.md$3)'
    },
    @{
        Pattern = '\[(?<text>[^\]]+)\]\((?<url>5_development/containers)(?<fragment>#[^)]*)?\)'
        Replacement = '[$1]($2/README.md$3)'
    },
    @{
        Pattern = '\[(?<text>[^\]]+)\]\((?<url>6_software)(?<fragment>#[^)]*)?\)'
        Replacement = '[$1]($2/README.md$3)'
    },
    @{
        Pattern = '\[(?<text>[^\]]+)\]\((?<url>6_software/development_tools/terminal)(?<fragment>#[^)]*)?\)'
        Replacement = '[$1]($2/README.md$3)'
    },
    @{
        Pattern = '\[(?<text>[^\]]+)\]\((?<url>7_projects)(?<fragment>#[^)]*)?\)'
        Replacement = '[$1]($2/README.md$3)'
    },
    @{
        Pattern = '\[(?<text>[^\]]+)\]\((?<url>8_robotics)(?<fragment>#[^)]*)?\)'
        Replacement = '[$1]($2/README.md$3)'
    },
    @{
        Pattern = '\[(?<text>[^\]]+)\]\((?<url>9_misc/resources)(?<fragment>#[^)]*)?\)'
        Replacement = '[$1]($2/README.md$3)'
    },
    @{
        Pattern = '\[(?<text>[^\]]+)\]\((?<url>9_misc/archive)(?<fragment>#[^)]*)?\)'
        Replacement = '[$1]($2/README.md$3)'
    },
    @{
        Pattern = '\[(?<text>[^\]]+)\]\((?<url>5_development/global_services/documentation_standards\.md)(?<fragment>#[^)]*)?\)'
        Replacement = '[$1]($2$3)'
    },
    @{
        Pattern = '\[(?<text>[^\]]+)\]\((?<url>5_development/global_services/template_library\.md)(?<fragment>#[^)]*)?\)'
        Replacement = '[$1]($2$3)'
    },
    @{
        Pattern = '\[(?<text>[^\]]+)\]\((?<url>7_projects/wiener_linien/WIENER_LINIEN_API_GUIDE\.md)(?<fragment>#[^)]*)?\)'
        Replacement = '[$1]($2$3)'
    },
    @{
        Pattern = '\[(?<text>[^\]]+)\]\((?<url>2_notes/flows/bugs/250621_rules_reading_issue/analysis\.md)(?<fragment>#[^)]*)?\)'
        Replacement = '[$1]($2$3)'
    },
    @{
        Pattern = '\[(?<text>[^\]]+)\]\((?<url>\.\./grafana/import_dashboard\.ps1\.md)(?<fragment>#[^)]*)?\)'
        Replacement = '[$1]($2$3)'
    }
)

# Apply replacements
$updatedContent = $content
foreach ($pattern in $patterns) {
    $updatedContent = [regex]::Replace($updatedContent, $pattern.Pattern, {
        param($match)
        $text = $match.Groups['text'].Value
        $url = $match.Groups['url'].Value
        $fragment = $match.Groups['fragment'].Value
        $newUrl = $pattern.Replacement -replace '\$1', $text -replace '\$2', $url -replace '\$3', $fragment
        Write-Host "Fixed link: [$text]($url$fragment) -> $newUrl" -ForegroundColor Yellow
        return $newUrl
    })
}

# Save the updated content
$updatedContent | Out-File -FilePath $readmePath -Encoding utf8 -NoNewline

Write-Host "\nLinks in README.md have been updated." -ForegroundColor Green
Write-Host "Original file backed up to: $backupPath" -ForegroundColor Cyan
Write-Host "\nVerifying links..." -ForegroundColor Cyan

# Run the link checker to verify the fixes
& "$PSScriptRoot\check_links.ps1"
