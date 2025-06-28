# Configuration
$port = 3300  # Using port 3300 to avoid conflicts with Open WebUI/docker
$root = $PSScriptRoot
$root = "D:\Dev\repos\mywienerlinien\.windsurf\docs"
$url = "http://localhost:$port/index.theme-v2.html"

# Kill any processes using port 3300
$processId = (Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue).OwningProcess
if ($processId) {
    Get-Process -Id $processId -ErrorAction SilentlyContinue | Stop-Process -Force
    Write-Host "[*] Stopped process using port $port"
}

# Kill any Python processes that might be running the server
Get-Process python -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like "*http.server*" } | Stop-Process -Force

# Create log directory if it doesn't exist
$logDir = "$root\logs"
if (-not (Test-Path $logDir)) {
    New-Item -ItemType Directory -Path $logDir | Out-Null
}

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$logFile = "$logDir\server_${timestamp}.log"
$errorLogFile = "$logDir\error_${timestamp}.log"

# Start the server with detailed logging
Write-Host "[*] Starting server on port $port..."
$server = Start-Process -FilePath "python" `
    -ArgumentList "-m", "http.server", "$port", "--directory", "$root", "--bind", "127.0.0.1" `
    -PassThru -NoNewWindow `
    -RedirectStandardOutput $logFile `
    -RedirectStandardError $errorLogFile

# Wait for server to start and verify
$maxRetries = 5
$retryCount = 0
$serverStarted = $false

while ($retryCount -lt $maxRetries -and -not $serverStarted) {
    Start-Sleep -Milliseconds 500
    $retryCount++
    
    # Check if port is in use by our process
    $portInUse = Test-NetConnection -ComputerName 127.0.0.1 -Port $port -InformationLevel Quiet
    if ($portInUse) {
        $serverStarted = $true
        Write-Host "[+] Server started successfully on port $port"
    }
}

if (-not $serverStarted) {
    Write-Host "[!] Failed to start server on port $port after $maxRetries attempts"
    Write-Host "[!] Check $errorLogFile for details"
    exit 1
}

# Open the browser
Start-Process $url

Write-Host "[+] Server running at $url"
Write-Host "[+] Logs: $logFile"
Write-Host "[+] Errors: $errorLogFile"
Write-Host "[!] Press any key to stop the server..."

# Wait for a key press
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

# Stop the server
Stop-Process -Id $server.Id -Force -ErrorAction SilentlyContinue
Write-Host "[!] Server stopped"
Write-Host "[!] Logs are available in: $logDir"
