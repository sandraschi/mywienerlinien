# Wiener Linien Docker Management Script
# PowerShell script to manage the Wiener Linien app Docker container

param(
    [Parameter(Position=0)]
    [ValidateSet("start", "stop", "restart", "logs", "status", "build", "clean")]
    [string]$Action = "start"
)

$ContainerName = "wiener-linien-app"
$ComposeFile = "docker-compose.yml"

function Write-Status {
    param([string]$Message, [string]$Color = "White")
    Write-Host "[$(Get-Date -Format 'HH:mm:ss')] $Message" -ForegroundColor $Color
}

function Start-WienerLinien {
    Write-Status "Starting Wiener Linien application..." "Green"
    
    if (Test-Path $ComposeFile) {
        docker-compose up -d
        if ($LASTEXITCODE -eq 0) {
            Write-Status "Wiener Linien app started successfully!" "Green"
            Write-Status "Access the app at: http://localhost:10722" "Cyan"
            Write-Status "API status: http://localhost:10722/api/status" "Cyan"
        } else {
            Write-Status "Failed to start Wiener Linien app" "Red"
        }
    } else {
        Write-Status "docker-compose.yml not found in current directory" "Red"
    }
}

function Stop-WienerLinien {
    Write-Status "Stopping Wiener Linien application..." "Yellow"
    docker-compose down
    if ($LASTEXITCODE -eq 0) {
        Write-Status "Wiener Linien app stopped successfully!" "Green"
    } else {
        Write-Status "Failed to stop Wiener Linien app" "Red"
    }
}

function Restart-WienerLinien {
    Write-Status "Restarting Wiener Linien application..." "Yellow"
    docker-compose restart
    if ($LASTEXITCODE -eq 0) {
        Write-Status "Wiener Linien app restarted successfully!" "Green"
        Write-Status "Access the app at: http://localhost:3080" "Cyan"
    } else {
        Write-Status "Failed to restart Wiener Linien app" "Red"
    }
}

function Show-Logs {
    Write-Status "Showing Wiener Linien app logs..." "Cyan"
    docker-compose logs -f
}

function Show-Status {
    Write-Status "Wiener Linien app status:" "Cyan"
    docker-compose ps
    
    Write-Status "`nContainer health:" "Cyan"
    docker ps --filter "name=$ContainerName" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    
    Write-Status "`nRecent logs:" "Cyan"
    docker-compose logs --tail=10
}

function Build-WienerLinien {
    Write-Status "Building Wiener Linien Docker image..." "Yellow"
    docker-compose build --no-cache
    if ($LASTEXITCODE -eq 0) {
        Write-Status "Wiener Linien image built successfully!" "Green"
    } else {
        Write-Status "Failed to build Wiener Linien image" "Red"
    }
}

function Clean-WienerLinien {
    Write-Status "Cleaning up Wiener Linien containers and images..." "Yellow"
    docker-compose down --rmi all --volumes --remove-orphans
    if ($LASTEXITCODE -eq 0) {
        Write-Status "Cleanup completed successfully!" "Green"
    } else {
        Write-Status "Failed to cleanup Wiener Linien resources" "Red"
    }
}

# Main execution
switch ($Action) {
    "start" { Start-WienerLinien }
    "stop" { Stop-WienerLinien }
    "restart" { Restart-WienerLinien }
    "logs" { Show-Logs }
    "status" { Show-Status }
    "build" { Build-WienerLinien }
    "clean" { Clean-WienerLinien }
    default {
        Write-Status "Usage: .\start_wiener_linien.ps1 [start|stop|restart|logs|status|build|clean]" "Yellow"
        Write-Status "Default action: start" "Gray"
    }
} 
