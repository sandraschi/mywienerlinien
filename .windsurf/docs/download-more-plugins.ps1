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

# List of additional plugins to download
$plugins = @(
    @{ 
        Name = "docsify-tabs.js"; 
        Url = "https://cdn.jsdelivr.net/npm/docsify-tabs@1" 
    },
    @{ 
        Name = "docsify-pagination.js"; 
        Url = "https://cdn.jsdelivr.net/npm/docsify-pagination/dist/docsify-pagination.min.js" 
    },
    @{ 
        Name = "docsify-edit-link.js"; 
        Url = "https://cdn.jsdelivr.net/npm/docsify/lib/plugins/edit-link.min.js" 
    },
    @{ 
        Name = "docsify-mermaid.js"; 
        Url = "https://cdn.jsdelivr.net/npm/docsify-mermaid@latest/dist/docsify-mermaid.min.js" 
    },
    @{ 
        Name = "mermaid.min.js"; 
        Url = "https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js" 
    },
    @{ 
        Name = "docsify-katex.js"; 
        Url = "https://cdn.jsdelivr.net/npm/docsify-katex@latest/dist/docsify-katex.js" 
    },
    @{ 
        Name = "katex.min.css"; 
        Url = "https://cdn.jsdelivr.net/npm/katex@latest/dist/katex.min.css" 
    },
    @{ 
        Name = "katex.min.js"; 
        Url = "https://cdn.jsdelivr.net/npm/katex@latest/dist/katex.min.js" 
    },
    @{ 
        Name = "docsify-footnote.js"; 
        Url = "https://cdn.jsdelivr.net/npm/docsify-footnote/dist/docsify-footnote.min.js" 
    },
    @{ 
        Name = "docsify-pdf-embed.js"; 
        Url = "https://cdn.jsdelivr.net/npm/docsify-pdf-embed@latest/dist/pdf-embed.min.js" 
    },
    @{ 
        Name = "pdfjs-dist-viewer-min.js"; 
        Url = "https://cdn.jsdelivr.net/npm/pdfjs-dist@3.11.174/build/pdf.min.js" 
    },
    @{ 
        Name = "pdfjs-dist-viewer-min.css"; 
        Url = "https://cdn.jsdelivr.net/npm/pdfjs-dist@3.11.174/web/pdf_viewer.min.css" 
    },
    @{ 
        Name = "docsify-toc.js"; 
        Url = "https://cdn.jsdelivr.net/npm/docsify-toc@1" 
    },
    @{ 
        Name = "docsify-chart.js"; 
        Url = "https://cdn.jsdelivr.net/npm/docsify-chart@1" 
    },
    @{ 
        Name = "chart.js"; 
        Url = "https://cdn.jsdelivr.net/npm/chart.js@3.9.1/dist/chart.min.js" 
    }
)

# Download only missing plugins
foreach ($plugin in $plugins) {
    $outputPath = Join-Path -Path $pluginsDir -ChildPath $plugin.Name
    if (-not (Test-Path -Path $outputPath)) {
        Get-WebFile -url $plugin.Url -outputFile $outputPath
    } else {
        Write-Host "Skipping $($plugin.Name) - already exists" -ForegroundColor Yellow
    }
}

Write-Host "`nPlugin download complete!" -ForegroundColor Green
