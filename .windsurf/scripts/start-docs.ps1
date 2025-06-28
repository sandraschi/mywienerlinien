<#
.SYNOPSIS
    Starts the SxS Documentation System with Docker
.DESCRIPTION
    This script provides multiple options to run the documentation system:
    1. Local development with live-reload
    2. Docker container
    3. Docker Compose with Nginx
.NOTES
    Version: 1.0
    Author: Windsurf AI Team
    Requires: Docker, Docker Compose
#>

param (
    [Parameter(Mandatory=$false)]
    [ValidateSet('local', 'docker', 'compose')]
    [string]$Mode = 'local',
    
    [Parameter(Mandatory=$false)]
    [int]$Port = 3000,
    
    [Parameter(Mandatory=$false)]
    [switch]$Tailscale,
    
    [Parameter(Mandatory=$false)]
    [switch]$Help
)

$ErrorActionPreference = 'Stop'

# Display help if requested
if ($Help) {
    Get-Help $PSCommandPath -Detailed
    exit 0
}

function Show-Header {
    Write-Host "=== SxS Documentation System ===" -ForegroundColor Cyan
    Write-Host "Mode: $Mode" -ForegroundColor Yellow
    if ($Tailscale) {
        Write-Host "Tailscale: Enabled" -ForegroundColor Green
    }
    Write-Host "Port: $Port" -ForegroundColor Yellow
    Write-Host "`n"
}

function Stop-ExistingServer {
    param([int]$port)
    
    $pidFile = "$env:TEMP\windsurf-docs-$port.pid"
    
    if (Test-Path $pidFile) {
        $oldPid = Get-Content $pidFile -Raw -ErrorAction SilentlyContinue
        
        if ($oldPid) {
            Write-Host "Found existing server process (PID: $oldPid), sending graceful shutdown..." -ForegroundColor Yellow
            
            # Try graceful shutdown first
            try {
                $process = Get-Process -Id $oldPid -ErrorAction SilentlyContinue
                if ($process) {
                    # Send Ctrl+C equivalent
                    $process.CloseMainWindow() | Out-Null
                    
                    # Wait for process to exit
                    $process.WaitForExit(3000)  # Wait up to 3 seconds
                    
                    if (-not $process.HasExited) {
                        Write-Host "Process did not exit gracefully, forcing termination..." -ForegroundColor Yellow
                        $process | Stop-Process -Force -ErrorAction SilentlyContinue
                    } else {
                        Write-Host "Server stopped gracefully" -ForegroundColor Green
                    }
                }
            } catch {
                Write-Warning "Error stopping process: $_"
            }
            
            # Clean up PID file
            Remove-Item $pidFile -Force -ErrorAction SilentlyContinue
        }
    }
}

# Import the docsify manager
. $PSScriptRoot\docsify-manager.ps1

function Start-Local {
    param([int]$port, [switch]$tailscale)
    
    Write-Host "Starting documentation server..." -ForegroundColor Green
    
    # Check if we're running in a new PowerShell session
    if (-not $PSScriptRoot) {
        Write-Error "This script must be dot-sourced or run from its directory"
        return
    }
    
    # Start the server using the manager
    $process = Start-DocsifyServer -port $port -tailscale:$tailscale
    
    if ($process) {
        Write-Host "Documentation server started successfully!" -ForegroundColor Green
        Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
        
        # Keep the script running until Ctrl+C
        try {
            $process.WaitForExit()
        } finally {
            # Cleanup
            if (-not $process.HasExited) {
                Stop-DocsifyServer -port $port | Out-Null
            }
        }
    } else {
        Write-Error "Failed to start documentation server"
    }
    
    # Install Docsify if needed
    if (-not (Get-Command docsify -ErrorAction SilentlyContinue)) {
        Write-Host "Installing Docsify globally..." -ForegroundColor Cyan
        npm install -g docsify-cli
    }
    
    # Get IP address
    $ip = if ($Tailscale) {
        (Get-NetIPAddress -AddressFamily IPv4 -InterfaceAlias "Tailscale*" | 
         Where-Object { $_.IPAddress -ne '100.64.0.1' }).IPAddress
    } else {
        'localhost'
    }
    
    if (-not $ip) {
        Write-Warning "Tailscale interface not found. Falling back to localhost."
        $ip = 'localhost'
    }
    
    Write-Host "`nDocumentation will be available at:" -ForegroundColor Cyan
    Write-Host "- Local:      http://localhost:$port" -ForegroundColor Green
    if ($Tailscale) {
        Write-Host "- Tailscale:  http://$($ip):$port" -ForegroundColor Green
    }
    Write-Host "`nPress Ctrl+C to stop the server" -ForegroundColor Yellow
    
    # Start the server using the manager
    Start-DocsifyServer -port $port -tailscale:$tailscale
}

function Invoke-DockerCommand {
    param(
        [string]$Command,
        [string]$ContainerName,
        [int]$Port,
        [switch]$Detached
    )
    
    $dockerArgs = @(
        $Command
        if ($Detached) { '-d' }
        '--name', $ContainerName
        '-p', "${Port}:3000"
        '-v', "${PWD}/.windsurf/docs:/app/.windsurf/docs"
        'windsurf-docs'
    )
    
    & docker $dockerArgs
}

function Start-DockerContainer {
    param([int]$port)
    
    Write-Host "Starting Docker container..." -ForegroundColor Green
    
    # Build the image
    Write-Host "Building Docker image..." -ForegroundColor Cyan
    docker build -t windsurf-docs -f docker/Dockerfile.docsify .
    
    # Remove existing container if it exists
    if (docker ps -a --filter "name=windsurf-docs" --format '{{.Names}}' | Select-String -Pattern '^windsurf-docs$') {
        Write-Host "Removing existing container..." -ForegroundColor Yellow
        docker rm -f windsurf-docs
    }
    
    # Start the container
    Write-Host "Starting container..." -ForegroundColor Cyan
    Invoke-DockerCommand -Command 'run' -ContainerName 'windsurf-docs' -Port $port -Detached
    
    # Show logs
    Write-Host "`nContainer logs (Ctrl+C to stop):" -ForegroundColor Cyan
    docker logs -f windsurf-docs
}

function Start-DockerCompose {
    param([int]$port)
    
    Write-Host "Starting Docker Compose stack..." -ForegroundColor Green
    
    # Create required directories
    $nginxDirs = @('nginx/conf.d', 'nginx/ssl', 'nginx/logs')
    foreach ($dir in $nginxDirs) {
        $fullPath = Join-Path $PSScriptRoot "..\$dir"
        if (-not (Test-Path $fullPath)) {
            New-Item -ItemType Directory -Path $fullPath -Force | Out-Null
        }
    }
    
    # Create default Nginx config if it doesn't exist
    $nginxConfPath = Join-Path $PSScriptRoot "..\nginx\conf.d\default.conf"
    if (-not (Test-Path $nginxConfPath)) {
        @'
server {
    listen 80;
    server_name localhost;
    
    location / {
        proxy_pass http://docs:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
'@ | Out-File -FilePath $nginxConfPath -Encoding utf8
    }
    
    # Start the stack
    Write-Host "Starting services..." -ForegroundColor Cyan
    docker-compose -f docker-compose.docs.yml up -d
    
    # Show logs
    Write-Host "`nContainer logs (Ctrl+C to stop):" -ForegroundColor Cyan
    docker-compose -f docker-compose.docs.yml logs -f
}

# Main execution
Show-Header

switch ($Mode.ToLower()) {
    'local' {
        Start-Local -port $Port
    }
    'docker' {
        Start-DockerContainer -port $Port
    }
    'compose' {
        Start-DockerCompose -port $Port
    }
    default {
        Write-Error "Invalid mode: $Mode. Use 'local', 'docker', or 'compose'."
        exit 1
    }
}

# Display final instructions
if ($Mode -eq 'docker' -or $Mode -eq 'compose') {
    Write-Host "`nDocumentation is now running in $Mode mode." -ForegroundColor Green
    Write-Host "Access it at: http://localhost:$Port" -ForegroundColor Cyan
    
    if ($Tailscale) {
        $tailscaleIP = (Get-NetIPAddress -AddressFamily IPv4 -InterfaceAlias "Tailscale*" | 
                       Where-Object { $_.IPAddress -ne '100.64.0.1' }).IPAddress
        if ($tailscaleIP) {
            Write-Host "Tailscale access: http://${tailscaleIP}:$Port" -ForegroundColor Cyan
        }
    }
    
    Write-Host "`nTo stop the containers, run:" -ForegroundColor Yellow
    if ($Mode -eq 'docker') {
        Write-Host "  docker stop windsurf-docs" -ForegroundColor White
        Write-Host "  docker rm windsurf-docs" -ForegroundColor White
    } else {
        Write-Host "  docker-compose -f docker-compose.docs.yml down" -ForegroundColor White
    }
}
