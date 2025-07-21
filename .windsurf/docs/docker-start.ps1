param(
    [switch]$Build,
    [switch]$Stop,
    [switch]$Restart,
    [switch]$Logs,
    [switch]$Shell,
    [switch]$Clean
)

# Configuration
$ContainerName = "windsurf-docs"
$ImageName = "windsurf-docs"
$Port = "3301"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   Windsurf Docs Docker Manager" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Function to check if Docker is running
function Test-Docker {
    try {
        docker version | Out-Null
        return $true
    }
    catch {
        return $false
    }
}

# Check if Docker is available
if (-not (Test-Docker)) {
    Write-Host "[ERROR] Docker is not running or not installed." -ForegroundColor Red
    Write-Host "[ERROR] Please start Docker Desktop and try again." -ForegroundColor Red
    exit 1
}

# Build the image
if ($Build) {
    Write-Host "[*] Building Docker image..." -ForegroundColor Blue
    docker-compose build
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[✓] Image built successfully" -ForegroundColor Green
    }
    else {
        Write-Host "[✗] Failed to build image" -ForegroundColor Red
        exit 1
    }
}

# Stop the container
if ($Stop) {
    Write-Host "[*] Stopping container..." -ForegroundColor Blue
    docker-compose down
    Write-Host "[✓] Container stopped" -ForegroundColor Green
    exit 0
}

# Restart the container
if ($Restart) {
    Write-Host "[*] Restarting container..." -ForegroundColor Blue
    docker-compose down
    docker-compose up -d
    Write-Host "[✓] Container restarted" -ForegroundColor Green
    exit 0
}

# Show logs
if ($Logs) {
    Write-Host "[*] Showing container logs..." -ForegroundColor Blue
    docker-compose logs -f
    exit 0
}

# Open shell
if ($Shell) {
    Write-Host "[*] Opening shell in container..." -ForegroundColor Blue
    docker-compose exec docsify sh
    exit 0
}

# Clean up
if ($Clean) {
    Write-Host "[*] Cleaning up Docker resources..." -ForegroundColor Blue
    docker-compose down --rmi all --volumes --remove-orphans
    Write-Host "[✓] Cleanup complete" -ForegroundColor Green
    exit 0
}

# Default: Start the container
Write-Host "[*] Starting Docsify documentation server..." -ForegroundColor Blue

# Check if container is already running
$running = docker ps --filter "name=$ContainerName" --format "table {{.Names}}" | Select-String $ContainerName
if ($running) {
    Write-Host "[*] Container is already running" -ForegroundColor Yellow
    Write-Host "[*] Access your docs at: http://localhost:$Port" -ForegroundColor Green
    Write-Host "[*] Use -Logs to view logs, -Stop to stop the container" -ForegroundColor Cyan
    exit 0
}

# Start the container
docker-compose up -d

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "   Server Information" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "[*] Container: $ContainerName" -ForegroundColor White
    Write-Host "[*] Local URL: http://localhost:$Port" -ForegroundColor White
    Write-Host "[*] Status: Running" -ForegroundColor Green
    Write-Host ""
    Write-Host "[*] Available commands:" -ForegroundColor Cyan
    Write-Host "  -Logs    : View container logs" -ForegroundColor Gray
    Write-Host "  -Stop    : Stop the container" -ForegroundColor Gray
    Write-Host "  -Restart : Restart the container" -ForegroundColor Gray
    Write-Host "  -Shell   : Open shell in container" -ForegroundColor Gray
    Write-Host "  -Clean   : Clean up all Docker resources" -ForegroundColor Gray
    Write-Host ""
    
    # Wait a moment for the server to start
    Start-Sleep -Seconds 3
    
    # Open browser
    Write-Host "[*] Opening browser..." -ForegroundColor Blue
    Start-Process "http://localhost:$Port"
}
else {
    Write-Host "[✗] Failed to start container" -ForegroundColor Red
    exit 1
} 