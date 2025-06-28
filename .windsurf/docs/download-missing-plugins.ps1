# Create plugins directory if it doesn't exist
$pluginsDir = Join-Path -Path $PSScriptRoot -ChildPath "plugins"
if (-not (Test-Path -Path $pluginsDir)) {
    New-Item -ItemType Directory -Path $pluginsDir | Out-Null
}

# Function to download a file
function Get-WebFile {
    param (
        [string]$url,
        [string]$outputFile
    )
    
    Write-Host "Downloading $url to $outputFile"
    try {
        Invoke-WebRequest -Uri $url -OutFile $outputFile -UseBasicParsing
        Write-Host "Downloaded $outputFile" -ForegroundColor Green
    } catch {
        Write-Host "Failed to download $url" -ForegroundColor Red
        Write-Host $_.Exception.Message -ForegroundColor Red
    }
}

# List of missing plugins to download
$missingPlugins = @(
    @{ 
        Name = "docsify-search.min.js"; 
        Url = "https://cdn.jsdelivr.net/npm/docsify@4/lib/plugins/search.min.js" 
    },
    @{ 
        Name = "zoom-image.js"; 
        Url = "https://cdn.jsdelivr.net/npm/docsify@4/lib/plugins/zoom-image.min.js" 
    }
)

# Download only missing plugins
foreach ($plugin in $missingPlugins) {
    $outputPath = Join-Path -Path $pluginsDir -ChildPath $plugin.Name
    if (-not (Test-Path -Path $outputPath)) {
        Get-WebFile -url $plugin.Url -outputFile $outputPath
    } else {
        Write-Host "Skipping $($plugin.Name) - already exists" -ForegroundColor Yellow
    }
}

Write-Host "\nPlugin download complete!" -ForegroundColor Green
