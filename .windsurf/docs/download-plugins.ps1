# Script to download all required Docsify plugins
$ErrorActionPreference = "Stop"

# Create plugins directory if it doesn't exist
$pluginsDir = Join-Path $PSScriptRoot "plugins"
if (-not (Test-Path $pluginsDir)) {
    New-Item -ItemType Directory -Path $pluginsDir | Out-Null
}

# Base URL for CDN
$baseUrl = "https://cdn.jsdelivr.net/npm/"

# List of plugins to download
$plugins = @(
    "docsify@4/lib/docsify.min.js",
    "docsify-sidebar-collapse/dist/docsify-sidebar-collapse.min.js",
    "docsify-copy-code/dist/docsify-copy-code.min.js",
    "docsify-tabs@1/dist/docsify-tabs.min.js",
    "docsify-pagination/dist/docsify-pagination.min.js",
    "docsify-edit-link/dist/docsify-edit-link.min.js",
    "docsify-mermaid/dist/docsify-mermaid.min.js",
    "docsify-katex/dist/docsify-katex.js",
    "docsify-footnote/dist/docsify-footnote.min.js",
    "docsify-pdf-embed/dist/pdf-embed.min.js",
    "mermaid/dist/mermaid.min.js",
    "katex/dist/katex.min.js",
    "katex/dist/contrib/auto-render.min.js",
    "prismjs/prism.js",
    "prismjs/components/prism-bash.min.js",
    "prismjs/components/prism-python.min.js",
    "prismjs/components/prism-json.min.js",
    "prismjs/components/prism-yaml.min.js",
    "prismjs/components/prism-powershell.min.js",
    "prismjs/plugins/line-numbers/prism-line-numbers.min.js",
    "zoom-image/dist/zoom-image.min.js"
)

# Download each plugin
foreach ($plugin in $plugins) {
    $fileName = Split-Path $plugin -Leaf
    $outputPath = Join-Path $pluginsDir $fileName
    $url = $baseUrl + $plugin
    
    Write-Host "Downloading $plugin..."
    try {
        Invoke-WebRequest -Uri $url -OutFile $outputPath -UseBasicParsing
        Write-Host "  -> Saved to $outputPath"
    } catch {
        Write-Host "  !! Failed to download $plugin" -ForegroundColor Red
        Write-Host "     $($_.Exception.Message)" -ForegroundColor Red
    }
}

Write-Host "\nDownload complete!" -ForegroundColor Green
