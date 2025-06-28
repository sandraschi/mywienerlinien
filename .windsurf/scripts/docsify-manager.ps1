<#
.DESCRIPTION
    Manages the Docsify documentation server with graceful process handling.
    Ensures only one instance runs per port and handles clean shutdown.
#>

param (
    [int]$Port = 3000,
    [switch]$Tailscale,
    [switch]$Stop
)

$ErrorActionPreference = 'Stop'
$script:process = $null

function Get-ProcessByPort {
    param([int]$port)
    
    try {
        # First try with Get-NetTCPConnection if available
        if (Get-Command Get-NetTCPConnection -ErrorAction SilentlyContinue) {
            $connection = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
            if ($connection) {
                return Get-Process -Id $connection.OwningProcess -ErrorAction SilentlyContinue
            }
        }
        
        # Fallback method using netstat
        $netstatOutput = netstat -ano | findstr ":$port.*LISTENING"
        if ($netstatOutput) {
            $parts = $netstatOutput -split '\s+'
            $processId = $parts[-1]
            return Get-Process -Id $processId -ErrorAction SilentlyContinue
        }
        
        # Last resort - find by command line
        $processes = Get-Process -Name "node" -ErrorAction SilentlyContinue | 
            Where-Object { $_.CommandLine -like "*docsify*serve*$port*" }
        if ($processes) { return $processes[0] }
        
    } catch {
        Write-Warning "Error finding process by port: $_"
    }
    
    return $null
}

function Stop-DocsifyServer {
    param([int]$port)
    
    $process = Get-ProcessByPort -port $port
    if ($process) {
        Write-Host "Stopping Docsify server (PID: $($process.Id))..." -ForegroundColor Yellow
        
        try {
            # Try graceful shutdown first
            if (-not $process.HasExited) {
                $process.CloseMainWindow() | Out-Null
                
                # Wait for process to exit
                $process.WaitForExit(2000) | Out-Null
                
                if (-not $process.HasExited) {
                    Write-Host "Force stopping process..." -ForegroundColor Yellow
                    Stop-Process -Id $process.Id -Force -ErrorAction SilentlyContinue
                    $process.WaitForExit(1000) | Out-Null
                }
                
                # Double check
                if (-not $process.HasExited) {
                    Write-Warning "Failed to stop process $($process.Id)"
                    return $false
                }
            }
            
            Write-Host "Server stopped" -ForegroundColor Green
            return $true
            
        } catch {
            Write-Warning "Error stopping process: $_"
            return $false
        }
    }
    
    Write-Host "No Docsify server found on port $port" -ForegroundColor Yellow
    return $true
}

function Start-DocsifyServer {
    param([int]$port, [switch]$tailscale)
    
    # Check if already running
    $existingProcess = Get-ProcessByPort -port $port
    if ($existingProcess) {
        Write-Host "Docsify server already running (PID: $($existingProcess.Id))" -ForegroundColor Green
        return $existingProcess
    }
    
    # Ensure we're in the right directory
    $rootDir = Split-Path -Parent $PSScriptRoot
    $docsDirectory = Join-Path $rootDir "docs"
    
    if (-not (Test-Path $docsDirectory)) {
        Write-Error "Docs directory not found at: $docsDirectory"
        return $null
    }
    
    # Check for Node.js
    if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
        Write-Host "Node.js not found. Installing via winget..." -ForegroundColor Yellow
        winget install --id OpenJS.NodeJS.LTS -e --accept-package-agreements --accept-source-agreements
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
    }
    
    # Check for docsify-cli
    if (-not (npm list -g docsify-cli --depth=0 2>$null)) {
        Write-Host "Installing docsify-cli globally..." -ForegroundColor Yellow
        npm install -g docsify-cli
    }
    
    $ip = if ($tailscale) { '0.0.0.0' } else { 'localhost' }
    
    Write-Host "Starting Docsify server on http://$($ip):$port" -ForegroundColor Green
    
    $processInfo = New-Object System.Diagnostics.ProcessStartInfo
    $processInfo.FileName = 'cmd.exe'
    $processInfo.Arguments = "/c `"docsify serve docs -p $port -l $ip --open""
    $processInfo.WorkingDirectory = (Get-Item $PSScriptRoot/..).FullName
    $processInfo.UseShellExecute = $false
    $processInfo.CreateNoWindow = $true
    
    $process = New-Object System.Diagnostics.Process
    $process.StartInfo = $processInfo
    $process.Start() | Out-Null
    
    # Wait a bit for the process to start
    Start-Sleep -Seconds 2
    
    # Verify it's running
    $runningProcess = Get-ProcessByPort -port $port
    if (-not $runningProcess) {
        Write-Error "Failed to start Docsify server"
        return $null
    }
    
    Write-Host "Docsify server started (PID: $($runningProcess.Id))" -ForegroundColor Green
    return $runningProcess
}

# Main execution
try {
    if ($Stop) {
        Stop-DocsifyServer -port $Port
    } else {
        $script:process = Start-DocsifyServer -port $Port -tailscale:$Tailscale
        
        if ($script:process) {
            # Handle Ctrl+C
            [console]::TreatControlCAsInput = $false
            [Console]::CancelKeyPress.Add({
                Write-Host "`nStopping server..." -ForegroundColor Yellow
                Stop-DocsifyServer -port $Port | Out-Null
            })
            
            # Keep the script running
            $script:process.WaitForExit()
        }
    }
} catch {
    Write-Error "Error: $_"
    exit 1
}

<#
.SYNOPSIS
    Manages the Docsify documentation server.

.DESCRIPTION
    This script provides a robust way to start and stop the Docsify documentation server
    with proper process management and cleanup.

.PARAMETER Port
    The port number to run the Docsify server on (default: 3000).

.PARAMETER Tailscale
    If specified, binds to all network interfaces (0.0.0.0) for Tailscale access.

.PARAMETER Stop
    Stops the running Docsify server on the specified port.

.EXAMPLE
    .\docsify-manager.ps1 -Port 3000
    Starts the Docsify server on port 3000.

.EXAMPLE
    .\docsify-manager.ps1 -Port 3000 -Tailscale
    Starts the server accessible via Tailscale.

.EXAMPLE
    .\docsify-manager.ps1 -Port 3000 -Stop
    Stops the server on port 3000.
#>
