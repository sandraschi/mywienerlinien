# *********************************************************************************
# * SOTA Fleet Orchestration - Standardized Start System (v1.19.0)                *
# * Generated/Repaired by Antigravity on 2026-03-03                  *
# *********************************************************************************

# MyWienerLinien Application Manager - PowerShell Version
# Comprehensive script to manage both Wiener Linien app and Docsify documentation

param(
    [Parameter(Position=0)]
    [ValidateSet("start", "stop", "status", "logs", "build", "menu")]
    [string]$Action = "menu"
)

function Write-Header {
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "   MyWienerLinien Application Manager" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
}

function Write-Status {
    param([string]$Message, [string]$Color = "White")
    Write-Host "[$(Get-Date -Format 'HH:mm:ss')] $Message" -ForegroundColor $Color
}

function Show-Menu {
    Clear-Host
    Write-Header
    
    Write-Host "Available Applications:" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "[1] Start Wiener Linien App (Port 10722)" -ForegroundColor Green
    Write-Host "[2] Start Docsify Documentation (Port 3301)" -ForegroundColor Green
    Write-Host "[3] Start Both Applications" -ForegroundColor Green
    Write-Host "[4] Stop Wiener Linien App" -ForegroundColor Red
    Write-Host "[5] Stop Docsify Documentation" -ForegroundColor Red
    Write-Host "[6] Stop All Applications" -ForegroundColor Red
    Write-Host "[7] Show Status" -ForegroundColor Cyan
    Write-Host "[8] Show Logs" -ForegroundColor Cyan
    Write-Host "[9] Build/Rebuild Applications" -ForegroundColor Yellow
    Write-Host "[0] Exit" -ForegroundColor Gray
    Write-Host ""
}

function Start-WienerLinien {
    Write-Status "Starting Wiener Linien application..." "Green"
    Push-Location "frontend"
    try {
        & ".\start_wiener_linien.ps1" "start"
        Write-Status "Wiener Linien app should be available at: http://localhost:10722" "Cyan"
    }
    finally {
        Pop-Location
    }
}

function Start-Docsify {
    Write-Status "Starting Docsify documentation..." "Green"
    Push-Location ".windsurf\docs"
    try {
        docker-compose up -d
        Write-Status "Docsify documentation should be available at: http://localhost:3301" "Cyan"
    }
    finally {
        Pop-Location
    }
}

function Start-Both {
    Write-Status "Starting both applications..." "Green"
    Write-Host ""
    
    Write-Status "Starting Wiener Linien app..." "Yellow"
    Start-WienerLinien
    
    Write-Host ""
    Write-Status "Starting Docsify documentation..." "Yellow"
    Start-Docsify
    
    Write-Host ""
    Write-Status "Both applications started!" "Green"
    Write-Status "Wiener Linien app: http://localhost:10722" "Cyan"
    Write-Status "Docsify documentation: http://localhost:3301" "Cyan"
}

function Stop-WienerLinien {
    Write-Status "Stopping Wiener Linien application..." "Yellow"
    Push-Location "frontend"
    try {
        & ".\start_wiener_linien.ps1" "stop"
    }
    finally {
        Pop-Location
    }
}

function Stop-Docsify {
    Write-Status "Stopping Docsify documentation..." "Yellow"
    Push-Location ".windsurf\docs"
    try {
        docker-compose down
    }
    finally {
        Pop-Location
    }
}

function Stop-All {
    Write-Status "Stopping all applications..." "Yellow"
    Write-Host ""
    
    Write-Status "Stopping Wiener Linien app..." "Yellow"
    Stop-WienerLinien
    
    Write-Host ""
    Write-Status "Stopping Docsify documentation..." "Yellow"
    Stop-Docsify
    
    Write-Host ""
    Write-Status "All applications stopped!" "Green"
}

function Show-Status {
    Write-Status "Application Status:" "Cyan"
    Write-Host ""
    
    Write-Host "Wiener Linien App:" -ForegroundColor Yellow
    Push-Location "frontend"
    try {
        & ".\start_wiener_linien.ps1" "status"
    }
    finally {
        Pop-Location
    }
    
    Write-Host ""
    Write-Host "Docsify Documentation:" -ForegroundColor Yellow
    Push-Location ".windsurf\docs"
    try {
        docker-compose ps
    }
    finally {
        Pop-Location
    }
}

function Show-Logs {
    Write-Status "Select application for logs:" "Cyan"
    Write-Host ""
    Write-Host "[1] Wiener Linien App logs" -ForegroundColor Green
    Write-Host "[2] Docsify Documentation logs" -ForegroundColor Green
    Write-Host "[3] Back to main menu" -ForegroundColor Gray
    Write-Host ""
    
    $logChoice = Read-Host "Enter your choice (1-3)"
    
    switch ($logChoice) {
        "1" {
            Write-Status "Wiener Linien App logs (Press Ctrl+C to exit):" "Cyan"
            Push-Location "frontend"
            try {
                & ".\start_wiener_linien.ps1" "logs"
            }
            finally {
                Pop-Location
            }
        }
        "2" {
            Write-Status "Docsify Documentation logs (Press Ctrl+C to exit):" "Cyan"
            Push-Location ".windsurf\docs"
            try {
                docker-compose logs -f
            }
            finally {
                Pop-Location
            }
        }
        "3" { return }
        default { Write-Status "Invalid choice. Please try again." "Red" }
    }
}

function Build-Apps {
    Write-Status "Build/Rebuild Applications:" "Yellow"
    Write-Host ""
    Write-Host "[1] Build Wiener Linien App" -ForegroundColor Green
    Write-Host "[2] Build Docsify Documentation" -ForegroundColor Green
    Write-Host "[3] Build Both Applications" -ForegroundColor Green
    Write-Host "[4] Back to main menu" -ForegroundColor Gray
    Write-Host ""
    
    $buildChoice = Read-Host "Enter your choice (1-4)"
    
    switch ($buildChoice) {
        "1" {
            Write-Status "Building Wiener Linien application..." "Yellow"
            Push-Location "frontend"
            try {
                & ".\start_wiener_linien.ps1" "build"
            }
            finally {
                Pop-Location
            }
        }
        "2" {
            Write-Status "Building Docsify documentation..." "Yellow"
            Push-Location ".windsurf\docs"
            try {
                docker-compose build --no-cache
            }
            finally {
                Pop-Location
            }
        }
        "3" {
            Write-Status "Building both applications..." "Yellow"
            Write-Host ""
            
            Write-Status "Building Wiener Linien app..." "Yellow"
            Push-Location "frontend"
            try {
                & ".\start_wiener_linien.ps1" "build"
            }
            finally {
                Pop-Location
            }
            
            Write-Host ""
            Write-Status "Building Docsify documentation..." "Yellow"
            Push-Location ".windsurf\docs"
            try {
                docker-compose build --no-cache
            }
            finally {
                Pop-Location
            }
            
            Write-Host ""
            Write-Status "Both applications built successfully!" "Green"
        }
        "4" { return }
        default { Write-Status "Invalid choice. Please try again." "Red" }
    }
}

function Show-InteractiveMenu {
    do {
        Show-Menu
        $choice = Read-Host "Enter your choice (0-9)"
        
        switch ($choice) {
            "1" { Start-WienerLinien; Read-Host "Press Enter to continue..." }
            "2" { Start-Docsify; Read-Host "Press Enter to continue..." }
            "3" { Start-Both; Read-Host "Press Enter to continue..." }
            "4" { Stop-WienerLinien; Read-Host "Press Enter to continue..." }
            "5" { Stop-Docsify; Read-Host "Press Enter to continue..." }
            "6" { Stop-All; Read-Host "Press Enter to continue..." }
            "7" { Show-Status; Read-Host "Press Enter to continue..." }
            "8" { Show-Logs }
            "9" { Build-Apps; Read-Host "Press Enter to continue..." }
            "0" { 
                Write-Status "Thank you for using MyWienerLinien Application Manager!" "Green"
                return 
            }
            default { 
                Write-Status "Invalid choice. Please try again." "Red"
                Start-Sleep -Seconds 2
            }
        }
    } while ($true)
}

# Main execution
switch ($Action) {
    "start" { Start-Both }
    "stop" { Stop-All }
    "status" { Show-Status }
    "logs" { Show-Logs }
    "build" { Build-Apps }
    "menu" { Show-InteractiveMenu }
    default {
        Write-Status "Usage: .\start.ps1 [start|stop|status|logs|build|menu]" "Yellow"
        Write-Status "Default action: menu" "Gray"
    }
} 
