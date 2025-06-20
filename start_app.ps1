# Wiener Linien Live Map Startup Script (PowerShell)
# This script starts the Flask application with proper error handling and logging

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Wiener Linien Live Map Startup Script" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Function to log messages with timestamps
function Write-Log {
    param(
        [string]$Message,
        [string]$Level = "INFO"
    )
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $color = switch ($Level) {
        "ERROR" { "Red" }
        "WARNING" { "Yellow" }
        "SUCCESS" { "Green" }
        default { "White" }
    }
    Write-Host "[$timestamp] [$Level] $Message" -ForegroundColor $color
}

# Function to check if command exists
function Test-Command {
    param([string]$Command)
    try {
        Get-Command $Command -ErrorAction Stop | Out-Null
        return $true
    } catch {
        return $false
    }
}

# Check if Python is installed
Write-Log "Checking Python installation..."
if (-not (Test-Command "python")) {
    Write-Log "Python is not installed or not in PATH" "ERROR"
    Write-Log "Please install Python 3.7+ and try again" "ERROR"
    Read-Host "Press Enter to exit"
    exit 1
}

# Display Python version
$pythonVersion = python --version 2>&1
Write-Log "Found: $pythonVersion" "SUCCESS"
Write-Host ""

# Check if we're in the correct directory
Write-Log "Checking current directory..."
if (-not (Test-Path "frontend\app.py")) {
    Write-Log "app.py not found in frontend directory" "ERROR"
    Write-Log "Please run this script from the project root directory" "ERROR"
    Write-Log "Current directory: $PWD" "ERROR"
    Read-Host "Press Enter to exit"
    exit 1
}

# Check if virtual environment exists
Write-Log "Checking Python dependencies..."
if (-not (Test-Path "frontend\venv")) {
    Write-Log "Virtual environment not found" "WARNING"
    Write-Log "Creating virtual environment..."
    
    try {
        python -m venv frontend\venv
        if ($LASTEXITCODE -ne 0) {
            throw "Failed to create virtual environment"
        }
        Write-Log "Virtual environment created successfully" "SUCCESS"
    } catch {
        Write-Log "Failed to create virtual environment: $_" "ERROR"
        Read-Host "Press Enter to exit"
        exit 1
    }
}

# Activate virtual environment
Write-Log "Activating virtual environment..."
try {
    & "frontend\venv\Scripts\Activate.ps1"
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to activate virtual environment"
    }
    Write-Log "Virtual environment activated" "SUCCESS"
} catch {
    Write-Log "Failed to activate virtual environment: $_" "ERROR"
    Read-Host "Press Enter to exit"
    exit 1
}

# Install/upgrade pip
Write-Log "Upgrading pip..."
try {
    python -m pip install --upgrade pip | Out-Null
    Write-Log "Pip upgraded successfully" "SUCCESS"
} catch {
    Write-Log "Failed to upgrade pip: $_" "WARNING"
}

# Install requirements
Write-Log "Installing Python dependencies..."
if (Test-Path "frontend\requirements.txt") {
    try {
        pip install -r frontend\requirements.txt
        if ($LASTEXITCODE -ne 0) {
            throw "Failed to install requirements"
        }
        Write-Log "Dependencies installed successfully" "SUCCESS"
    } catch {
        Write-Log "Failed to install requirements: $_" "ERROR"
        Write-Log "Please check requirements.txt and try again" "ERROR"
        Read-Host "Press Enter to exit"
        exit 1
    }
} else {
    Write-Log "requirements.txt not found, installing basic dependencies..." "WARNING"
    try {
        pip install Flask requests python-dotenv Flask-Caching
        if ($LASTEXITCODE -ne 0) {
            throw "Failed to install basic dependencies"
        }
        Write-Log "Basic dependencies installed successfully" "SUCCESS"
    } catch {
        Write-Log "Failed to install basic dependencies: $_" "ERROR"
        Read-Host "Press Enter to exit"
        exit 1
    }
}

# Create logs directory if it doesn't exist
Write-Log "Setting up logging directory..."
if (-not (Test-Path "frontend\logs")) {
    New-Item -ItemType Directory -Path "frontend\logs" -Force | Out-Null
    Write-Log "Logs directory created" "SUCCESS"
}

# Test API connectivity
Write-Log "Testing Wiener Linien API connectivity..."
Set-Location frontend
try {
    python test_wl_api.py | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Log "API connectivity test passed" "SUCCESS"
    } else {
        Write-Log "API test failed - app will start with fallback data" "WARNING"
    }
} catch {
    Write-Log "API test failed - app will start with fallback data" "WARNING"
}

# Start the Flask application
Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "Starting Wiener Linien Live Map..." -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Log "Application will be available at: http://localhost:5000" "INFO"
Write-Log "Press Ctrl+C to stop the application" "INFO"
Write-Host ""

# Set Flask environment variables
$env:FLASK_APP = "app.py"
$env:FLASK_ENV = "development"
$env:FLASK_DEBUG = "1"

# Start Flask with error handling
try {
    python app.py
    if ($LASTEXITCODE -ne 0) {
        throw "Application failed to start"
    }
} catch {
    Write-Host ""
    Write-Log "Application failed to start" "ERROR"
    Write-Log "Check the logs above for details" "ERROR"
    Write-Log "Common issues:" "ERROR"
    Write-Log "- Port 5000 is already in use" "ERROR"
    Write-Log "- Missing dependencies" "ERROR"
    Write-Log "- API connectivity issues" "ERROR"
    Read-Host "Press Enter to exit"
    exit 1
}

# If we get here, the app stopped normally
Write-Host ""
Write-Log "Application stopped" "INFO"
Read-Host "Press Enter to exit" 