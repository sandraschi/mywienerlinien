@echo off
setlocal enabledelayedexpansion

:: Configuration
set "COMPOSE_FILE=docker-compose.logs.yml"
set "GRAFANA_PORT=3140"
set "DEFAULT_PASSWORD=windsurf123"

:: Check if Docker is running
docker info >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Docker is not running. Please start Docker Desktop and try again.
    pause
    exit /b 1
)

:menu
cls
echo ==============================
echo   Windsurf Log Viewer Manager
echo ==============================
echo 1. Start Log Viewer
echo 2. Stop Log Viewer
echo 3. View Logs
echo 4. Check Status
echo 5. Open in Browser
echo 6. Exit
echo.
set /p choice=Enter your choice (1-6): 

if "%choice%"=="1" goto start
if "%choice%"=="2" goto stop
if "%choice%"=="3" goto logs
if "%choice%"=="4" goto status
if "%choice%"=="5" goto open
if "%choice%"=="6" exit /b
echo Invalid choice. Please try again.
timeout /t 2 >nul
goto menu

:start
echo Starting Log Viewer...
set "GRAFANA_PASSWORD=%DEFAULT_PASSWORD%"
docker-compose -f "%COMPOSE_FILE%" up -d
goto status

:stop
echo Stopping Log Viewer...
docker-compose -f "%COMPOSE_FILE%" down
goto status

:logs
docker-compose -f "%COMPOSE_FILE%" logs -f --tail=100
pause
goto menu

:status
docker-compose -f "%COMPOSE_FILE%" ps
echo.
echo Grafana URL: http://localhost:%GRAFANA_PORT%
echo Username: admin
echo Password: %DEFAULT_PASSWORD%
pause
goto menu

:open
start http://localhost:%GRAFANA_PORT%
goto menu
