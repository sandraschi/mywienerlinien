@echo off
REM Wiener Linien Live Map Startup Script
REM This script starts the Flask application with proper error handling and logging

echo ========================================
echo Wiener Linien Live Map Startup Script
echo ========================================
echo.

REM Set error handling
setlocal enabledelayedexpansion

REM Check if Python is installed
echo [INFO] Checking Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH
    echo [ERROR] Please install Python 3.7+ and try again
    pause
    exit /b 1
)

REM Display Python version
python --version
echo.

REM Check if we're in the correct directory
echo [INFO] Checking current directory...
if not exist "frontend\app.py" (
    echo [ERROR] app.py not found in frontend directory
    echo [ERROR] Please run this script from the project root directory
    echo [ERROR] Current directory: %CD%
    pause
    exit /b 1
)

REM Check if requirements are installed
echo [INFO] Checking Python dependencies...
if not exist "frontend\venv" (
    echo [WARNING] Virtual environment not found
    echo [INFO] Creating virtual environment...
    python -m venv frontend\venv
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to create virtual environment
        pause
        exit /b 1
    )
)

REM Activate virtual environment
echo [INFO] Activating virtual environment...
call frontend\venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo [ERROR] Failed to activate virtual environment
    pause
    exit /b 1
)

REM Install/upgrade pip
echo [INFO] Upgrading pip...
python -m pip install --upgrade pip >nul 2>&1

REM Install requirements
echo [INFO] Installing Python dependencies...
if exist "frontend\requirements.txt" (
    pip install -r frontend\requirements.txt
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to install requirements
        echo [ERROR] Please check requirements.txt and try again
        pause
        exit /b 1
    )
) else (
    echo [WARNING] requirements.txt not found, installing basic dependencies...
    pip install Flask requests python-dotenv Flask-Caching
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to install basic dependencies
        pause
        exit /b 1
    )
)

REM Create logs directory if it doesn't exist
echo [INFO] Setting up logging directory...
if not exist "frontend\logs" (
    mkdir frontend\logs
)

REM Test API connectivity
echo [INFO] Testing Wiener Linien API connectivity...
cd frontend
python test_wl_api.py >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARNING] API test failed - app will start with fallback data
) else (
    echo [INFO] API connectivity test passed
)

REM Start the Flask application
echo.
echo ========================================
echo Starting Wiener Linien Live Map...
echo ========================================
echo [INFO] Application will be available at: http://localhost:5000
echo [INFO] Press Ctrl+C to stop the application
echo.

REM Set Flask environment variables
set FLASK_APP=app.py
set FLASK_ENV=development
set FLASK_DEBUG=1

REM Start Flask with error handling
python app.py
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Application failed to start
    echo [ERROR] Check the logs above for details
    echo [ERROR] Common issues:
    echo [ERROR] - Port 5000 is already in use
    echo [ERROR] - Missing dependencies
    echo [ERROR] - API connectivity issues
    pause
    exit /b 1
)

REM If we get here, the app stopped normally
echo.
echo [INFO] Application stopped
pause 