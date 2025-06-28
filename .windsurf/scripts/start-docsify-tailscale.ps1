<#
.SYNOPSIS
    Starts a Docsify documentation server accessible via Tailscale
.DESCRIPTION
    This script starts a Docsify server that's accessible via your Tailscale IP address.
    It automatically detects your Tailscale IP and serves the documentation.
.NOTES
    Version: 1.0
    Author: Windsurf AI Team
    Requires: Node.js, npm, and Tailscale
#>

# Set error action preference
$ErrorActionPreference = 'Stop'

# Configuration
$docsPath = "$PSScriptRoot\..\docs"
$port = 3000

# Check for Node.js
if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
    Write-Host "Node.js not found. Installing via winget..." -ForegroundColor Yellow
    try {
        winget install --id OpenJS.NodeJS.LTS -e --accept-package-agreements --accept-source-agreements
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
    } catch {
        Write-Error "Failed to install Node.js. Please install it manually from https://nodejs.org/"
        exit 1
    }
}

# Install Docsify if not installed
try {
    $null = npm list -g docsify-cli --depth=0 2>$null
} catch {
    Write-Host "Installing Docsify globally..." -ForegroundColor Cyan
    npm install -g docsify-cli
}

# Get Tailscale IP
$tailscaleIP = (Get-NetIPAddress -AddressFamily IPv4 -InterfaceAlias "Tailscale*" | 
               Where-Object { $_.IPAddress -ne '100.64.0.1' }).IPAddress

if (-not $tailscaleIP) {
    Write-Error "Tailscale interface not found. Make sure Tailscale is running."
    exit 1
}

# Start Docsify
Write-Host "Starting Docsify server..." -ForegroundColor Green
Write-Host "Local:      http://localhost:$port" -ForegroundColor Cyan
Write-Host "Tailscale:  http://$($tailscaleIP):$port" -ForegroundColor Cyan
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow

# Start the server
try {
    Push-Location $docsPath
    docsify serve . -p $port -l $tailscaleIP --open
} finally {
    Pop-Location
}
