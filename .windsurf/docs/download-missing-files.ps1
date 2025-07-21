# Create plugins directory if it doesn't exist
$pluginsDir = "D:\Dev\repos\mywienerlinien\.windsurf\docs\plugins"
if (-not (Test-Path -Path $pluginsDir)) {
    New-Item -ItemType Directory -Path $pluginsDir -Force
}

# Download missing files
$filesToDownload = @{
    "https://cdn.jsdelivr.net/npm/prismjs@1.29.0/themes/prism-tomorrow.min.css" = "prism-tomorrow.css"
    "https://cdn.jsdelivr.net/npm/docsify@4.13.0/lib/themes/vue.css" = "docsify.min.css"
}

foreach ($url in $filesToDownload.Keys) {
    $outputFile = Join-Path -Path $pluginsDir -ChildPath $filesToDownload[$url]
    Write-Host "Downloading $url to $outputFile"
    try {
        Invoke-WebRequest -Uri $url -OutFile $outputFile -UseBasicParsing
        Write-Host "Successfully downloaded $($filesToDownload[$url])" -ForegroundColor Green
    }
    catch {
        Write-Host "Failed to download $($filesToDownload[$url]): $_" -ForegroundColor Red
    }
}

Write-Host "\nDownload complete!" -ForegroundColor Green
