# Create plugins directory if it doesn't exist
$pluginsDir = Join-Path -Path $PSScriptRoot -ChildPath "plugins"
if (-not (Test-Path -Path $pluginsDir)) {
    New-Item -ItemType Directory -Path $pluginsDir -Force | Out-Null
}

# Download sidebar-collapse CSS
$cssUrl = "https://cdn.jsdelivr.net/npm/docsify-sidebar-collapse/dist/sidebar.min.css"
$outputPath = Join-Path -Path $pluginsDir -ChildPath "sidebar-collapse.min.css"

Write-Host "Downloading sidebar-collapse CSS..."
try {
    Invoke-WebRequest -Uri $cssUrl -OutFile $outputPath -UseBasicParsing
    Write-Host "Successfully downloaded sidebar-collapse CSS to $outputPath"
} catch {
    Write-Error "Failed to download sidebar-collapse CSS: $_"
    exit 1
}

# Verify the file was downloaded
if (Test-Path -Path $outputPath) {
    Write-Host "Verification: File exists at $outputPath"
} else {
    Write-Error "Failed to verify the downloaded file. Please check the path and try again."
    exit 1
}
