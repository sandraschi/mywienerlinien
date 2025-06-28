# Create plugins directory if it doesn't exist
$pluginsDir = ".windsurf\docs\plugins"
if (-not (Test-Path -Path $pluginsDir)) {
    New-Item -ItemType Directory -Path $pluginsDir | Out-Null
}

# List of plugins to download with their CDN URLs
$plugins = @{
    "docsify-sidebar-collapse.js" = "https://cdn.jsdelivr.net/npm/docsify-sidebar-collapse@1.0.0/dist/docsify-sidebar-collapse.min.js"
    "docsify-copy-code.js" = "https://cdn.jsdelivr.net/npm/docsify-copy-code@2.1.1/dist/docsify-copy-code.min.js"
    "docsify-zoom-image.js" = "https://cdn.jsdelivr.net/npm/docsify-zoom-image@1.0.7/dist/docsify-zoom-image.min.js"
    "docsify-pagination.js" = "https://cdn.jsdelivr.net/npm/docsify-pagination@2.11.0/dist/docsify-pagination.min.js"
    "prism.js" = "https://cdn.jsdelivr.net/npm/prismjs@1.29.0/prism.min.js"
    "prism-css.min.css" = "https://cdn.jsdelivr.net/npm/prismjs@1.29.0/themes/prism-tomorrow.min.css"
    "prism-javascript.min.js" = "https://cdn.jsdelivr.net/npm/prismjs@1.29.0/components/prism-javascript.min.js"
    "prism-python.min.js" = "https://cdn.jsdelivr.net/npm/prismjs@1.29.0/components/prism-python.min.js"
    "prism-bash.min.js" = "https://cdn.jsdelivr.net/npm/prismjs@1.29.0/components/prism-bash.min.js"
    "prism-json.min.js" = "https://cdn.jsdelivr.net/npm/prismjs@1.29.0/components/prism-json.min.js"
    "prism-yaml.min.js" = "https://cdn.jsdelivr.net/npm/prismjs@1.29.0/components/prism-yaml.min.js"
    "prism-powershell.min.js" = "https://cdn.jsdelivr.net/npm/prismjs@1.29.0/components/prism-powershell.min.js"
}

# Download each plugin
foreach ($plugin in $plugins.GetEnumerator()) {
    $outputPath = Join-Path -Path $pluginsDir -ChildPath $plugin.Key
    Write-Host "Downloading $($plugin.Key)..."
    try {
        Invoke-WebRequest -Uri $plugin.Value -OutFile $outputPath -UseBasicParsing
        Write-Host "✓ Downloaded $($plugin.Key)" -ForegroundColor Green
    }
    catch {
        Write-Host "✗ Failed to download $($plugin.Key): $_" -ForegroundColor Red
    }
}

Write-Host "\nAll downloads complete!" -ForegroundColor Green
