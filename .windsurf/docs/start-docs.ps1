# Windsurf Documentation Server - PowerShell Version
param(
    [int]$Port = 3300,
    [switch]$Debug,
    [switch]$NoBrowser
)

# Configuration
$RootDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$HtmlFile = "index.html"
$Url = "http://localhost:$Port/$HtmlFile"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   Windsurf Documentation Server" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Function to test if a port is in use
function Test-Port {
    param([int]$Port)
    try {
        $connection = New-Object System.Net.Sockets.TcpClient
        $connection.Connect("localhost", $Port)
        $connection.Close()
        return $true
    }
    catch {
        return $false
    }
}

# Kill any existing processes on the port
if (Test-Port -Port $Port) {
    Write-Host "[*] Found existing process on port $Port, attempting to stop..." -ForegroundColor Yellow
    $processes = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess
    foreach ($pid in $processes) {
        try {
            Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
            Write-Host "[*] Stopped process PID $pid" -ForegroundColor Green
        }
        catch {
            Write-Host "[WARNING] Could not stop process PID $pid" -ForegroundColor Yellow
        }
    }
    Start-Sleep -Seconds 2
}

# Try Node.js first (preferred for Docsify)
Write-Host "[*] Checking for Node.js..." -ForegroundColor Blue
$nodePath = Get-Command node -ErrorAction SilentlyContinue
if ($nodePath) {
    Write-Host "[*] Node.js found at: $($nodePath.Source)" -ForegroundColor Green
    
    # Check if docsify-cli is available
    try {
        node -e "try { require('docsify-cli'); console.log('docsify-cli found'); } catch(e) { process.exit(1); }" 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "[*] Starting Docsify server with Node.js..." -ForegroundColor Green
            $serverProcess = Start-Process -FilePath "node" -ArgumentList "node_modules/.bin/docsify", "serve", ".", "--port", $Port -PassThru -WindowStyle Hidden
            $ServerType = "docsify"
        }
        else {
            Write-Host "[*] Installing docsify-cli globally..." -ForegroundColor Yellow
            npm install -g docsify-cli
            if ($LASTEXITCODE -eq 0) {
                Write-Host "[*] Starting Docsify server..." -ForegroundColor Green
                $serverProcess = Start-Process -FilePath "docsify" -ArgumentList "serve", ".", "--port", $Port -PassThru -WindowStyle Hidden
                $ServerType = "docsify"
            }
            else {
                Write-Host "[WARNING] Failed to install docsify-cli, falling back to Python..." -ForegroundColor Yellow
                $nodePath = $null
            }
        }
    }
    catch {
        Write-Host "[WARNING] Error checking docsify-cli, falling back to Python..." -ForegroundColor Yellow
        $nodePath = $null
    }
}

# Python fallback
if (-not $nodePath) {
    Write-Host "[*] Looking for Python..." -ForegroundColor Blue
    $pythonPath = Get-Command python -ErrorAction SilentlyContinue
    if (-not $pythonPath) {
        $pythonPath = Get-Command python3 -ErrorAction SilentlyContinue
    }
    
    if ($pythonPath) {
        Write-Host "[*] Python found at: $($pythonPath.Source)" -ForegroundColor Green
        Write-Host "[*] Starting Python HTTP server..." -ForegroundColor Green
        $serverProcess = Start-Process -FilePath $pythonPath.Source -ArgumentList "-m", "http.server", $Port, "--bind", "0.0.0.0", "--directory", $RootDir -PassThru -WindowStyle Hidden
        $ServerType = "python"
    }
    else {
        Write-Host "[ERROR] Neither Node.js nor Python found." -ForegroundColor Red
        Write-Host "[ERROR] Please install either:" -ForegroundColor Red
        Write-Host "[ERROR]   - Node.js (recommended for Docsify)" -ForegroundColor Red
        Write-Host "[ERROR]   - Python (fallback option)" -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
}

# Wait for server to start
Write-Host "[*] Waiting for server to start..." -ForegroundColor Blue
Start-Sleep -Seconds 3

# Test if server is running
$retries = 0
$maxRetries = 10
do {
    if (Test-Port -Port $Port) {
        Write-Host "[*] Server is running successfully!" -ForegroundColor Green
        break
    }
    else {
        $retries++
        if ($retries -lt $maxRetries) {
            Write-Host "[*] Waiting for server... (attempt $retries/$maxRetries)" -ForegroundColor Yellow
            Start-Sleep -Seconds 1
        }
        else {
            Write-Host "[WARNING] Server might not be ready yet, but continuing..." -ForegroundColor Yellow
        }
    }
} while ($retries -lt $maxRetries)

# Display information
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   Server Information" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "[*] Server type: $ServerType" -ForegroundColor White
Write-Host "[*] Root directory: $RootDir" -ForegroundColor White
Write-Host "[*] Local URL: $Url" -ForegroundColor White
Write-Host "[*] Network URL: http://$env:COMPUTERNAME`:$Port/" -ForegroundColor White
Write-Host ""

# Debug information
if ($Debug) {
    Write-Host "=== Debug Information ===" -ForegroundColor Magenta
    Write-Host "Current directory: $(Get-Location)" -ForegroundColor Gray
    Write-Host "Files in root directory:" -ForegroundColor Gray
    Get-ChildItem $RootDir -Name | ForEach-Object { Write-Host "  $_" -ForegroundColor Gray }
    
    # Check for key files
    $keyFiles = @("index.html", "_sidebar.md", "_coverpage.md")
    foreach ($file in $keyFiles) {
        $filePath = Join-Path $RootDir $file
        if (Test-Path $filePath) {
            Write-Host "[✓] $file found" -ForegroundColor Green
        }
        else {
            Write-Host "[✗] $file missing" -ForegroundColor Red
        }
    }
    Write-Host ""
}

# Open the browser
if (-not $NoBrowser) {
    Write-Host "[*] Opening browser..." -ForegroundColor Blue
    Start-Process $Url
}

Write-Host "[*] Server is running..." -ForegroundColor Green
Write-Host "[*] Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""

# Keep the script running and handle cleanup
try {
    while ($true) {
        Start-Sleep -Seconds 1
        
        # Check if server process is still running
        if ($serverProcess -and $serverProcess.HasExited) {
            Write-Host "[WARNING] Server process has stopped unexpectedly" -ForegroundColor Yellow
            break
        }
    }
}
catch {
    Write-Host ""
    Write-Host "[*] Stopping server..." -ForegroundColor Blue
    
    if ($serverProcess -and -not $serverProcess.HasExited) {
        $serverProcess.Kill()
    }
    
    # Also kill any remaining processes on the port
    $processes = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess
    foreach ($pid in $processes) {
        try {
            Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
        }
        catch {
            # Ignore errors
        }
    }
    
    Write-Host "[*] Server stopped" -ForegroundColor Green
} 