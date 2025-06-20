Write-Host "Starting Wiener Linien Live Map with Docker..." -ForegroundColor Green
Write-Host ""

# Check if Docker is running
try {
    docker info | Out-Null
} catch {
    Write-Host "ERROR: Docker is not running. Please start Docker Desktop first." -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Stop any existing containers
Write-Host "Stopping any existing containers..." -ForegroundColor Yellow
docker-compose down

# Build and start the application
Write-Host "Building and starting the application..." -ForegroundColor Yellow
docker-compose up --build -d

# Wait a moment for the application to start
Write-Host "Waiting for application to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Check if the application is running
Write-Host "Checking application status..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:3080/api/status" -UseBasicParsing -TimeoutSec 5
    if ($response.StatusCode -eq 200) {
        Write-Host ""
        Write-Host "SUCCESS: Wiener Linien Live Map is running!" -ForegroundColor Green
        Write-Host ""
        Write-Host "Access the application at: http://localhost:3080" -ForegroundColor Cyan
        Write-Host "API Status: http://localhost:3080/api/status" -ForegroundColor Cyan
        Write-Host ""
        $openBrowser = Read-Host "Press Enter to open the application in your browser (or 'n' to skip)"
        if ($openBrowser -ne 'n') {
            Start-Process "http://localhost:3080"
        }
    }
} catch {
    Write-Host ""
    Write-Host "WARNING: Application might still be starting up." -ForegroundColor Yellow
    Write-Host "Please wait a moment and try accessing: http://localhost:3080" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "To stop the application, run: docker-compose down" -ForegroundColor Gray
Write-Host "To view logs, run: docker-compose logs -f" -ForegroundColor Gray
Read-Host "Press Enter to exit" 