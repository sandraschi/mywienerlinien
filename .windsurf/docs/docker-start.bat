@echo off
setlocal enabledelayedexpansion

REM Configuration
set CONTAINER_NAME=windsurf-docs
set PORT=3301

echo ========================================
echo    Windsurf Docs Docker Manager
echo ========================================
echo.

REM Check if Docker is running
docker version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker is not running or not installed.
    echo [ERROR] Please start Docker Desktop and try again.
    pause
    exit /b 1
)

REM Check command line arguments
if "%1"=="-build" goto :build
if "%1"=="-stop" goto :stop
if "%1"=="-restart" goto :restart
if "%1"=="-logs" goto :logs
if "%1"=="-shell" goto :shell
if "%1"=="-clean" goto :clean

REM Default: Start the container
goto :start

:build
echo [*] Building Docker image...
docker-compose build
if errorlevel 1 (
    echo [✗] Failed to build image
    pause
    exit /b 1
)
echo [✓] Image built successfully
goto :start

:stop
echo [*] Stopping container...
docker-compose down
echo [✓] Container stopped
pause
exit /b 0

:restart
echo [*] Restarting container...
docker-compose down
docker-compose up -d
echo [✓] Container restarted
pause
exit /b 0

:logs
echo [*] Showing container logs...
docker-compose logs -f
pause
exit /b 0

:shell
echo [*] Opening shell in container...
docker-compose exec docsify sh
pause
exit /b 0

:clean
echo [*] Cleaning up Docker resources...
docker-compose down --rmi all --volumes --remove-orphans
echo [✓] Cleanup complete
pause
exit /b 0

:start
echo [*] Starting Docsify documentation server...

REM Check if container is already running
docker ps --filter "name=%CONTAINER_NAME%" --format "table {{.Names}}" | findstr "%CONTAINER_NAME%" >nul
if not errorlevel 1 (
    echo [*] Container is already running
    echo [*] Access your docs at: http://localhost:%PORT%
    echo [*] Use -logs to view logs, -stop to stop the container
    pause
    exit /b 0
)

REM Start the container
docker-compose up -d

if errorlevel 1 (
    echo [✗] Failed to start container
    pause
    exit /b 1
)

echo.
echo ========================================
echo    Server Information
echo ========================================
echo [*] Container: %CONTAINER_NAME%
echo [*] Local URL: http://localhost:%PORT%
echo [*] Status: Running
echo.
echo [*] Available commands:
echo   -build   : Build the image
echo   -stop    : Stop the container
echo   -restart : Restart the container
echo   -logs    : View container logs
echo   -shell   : Open shell in container
echo   -clean   : Clean up all Docker resources
echo.

REM Wait a moment for the server to start
timeout /t 3 /nobreak >nul

REM Open browser
echo [*] Opening browser...
start http://localhost:%PORT%

echo [*] Server is running...
echo [*] Press any key to exit (container will continue running)
pause >nul 