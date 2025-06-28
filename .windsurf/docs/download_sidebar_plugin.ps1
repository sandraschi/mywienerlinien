# Create plugins directory if it doesn't exist
$pluginsDir = Join-Path -Path $PSScriptRoot -ChildPath "plugins"
if (-not (Test-Path -Path $pluginsDir)) {
    New-Item -ItemType Directory -Path $pluginsDir -Force | Out-Null
}

# Download docsify-sidebar plugin
$sidebarJsUrl = "https://cdn.jsdelivr.net/npm/docsify-sidebar@1.0.0/dist/docsify-sidebar.min.js"
$outputJsPath = Join-Path -Path $pluginsDir -ChildPath "docsify-sidebar.min.js"

Write-Host "Downloading docsify-sidebar plugin..."
try {
    Invoke-WebRequest -Uri $sidebarJsUrl -OutFile $outputJsPath -UseBasicParsing
    Write-Host "Successfully downloaded docsify-sidebar plugin to $outputJsPath"
} catch {
    Write-Error "Failed to download docsify-sidebar plugin: $_"
    exit 1
}

# Verify the file was downloaded
if (Test-Path -Path $outputJsPath) {
    Write-Host "Verification: File exists at $outputJsPath"
} else {
    Write-Error "Failed to verify the downloaded file. Please check the path and try again."
    exit 1
}
