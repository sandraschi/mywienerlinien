@echo off
REM Wiener Linien Docker Management Script
REM Windows batch script to manage the Wiener Linien app Docker container

setlocal enabledelayedexpansion

set CONTAINER_NAME=wiener-linien-app
set COMPOSE_FILE=docker-compose.yml

if "%1"=="" (
    set ACTION=start
) else (
    set ACTION=%1
)

echo [%time%] Wiener Linien Docker Management Script
echo.

if /i "%ACTION%"=="start" goto :start
if /i "%ACTION%"=="stop" goto :stop
if /i "%ACTION%"=="restart" goto :restart
if /i "%ACTION%"=="logs" goto :logs
if /i "%ACTION%"=="status" goto :status
if /i "%ACTION%"=="build" goto :build
if /i "%ACTION%"=="clean" goto :clean
goto :usage

:start
echo [%time%] Starting Wiener Linien application...
if exist %COMPOSE_FILE% (
    docker-compose up -d
    if !errorlevel! equ 0 (
        echo [%time%] Wiener Linien app started successfully!
        echo [%time%] Access the app at: http://localhost:3080
        echo [%time%] API status: http://localhost:3080/api/status
    ) else (
        echo [%time%] Failed to start Wiener Linien app
    )
) else (
    echo [%time%] docker-compose.yml not found in current directory
)
goto :end

:stop
echo [%time%] Stopping Wiener Linien application...
docker-compose down
if !errorlevel! equ 0 (
    echo [%time%] Wiener Linien app stopped successfully!
) else (
    echo [%time%] Failed to stop Wiener Linien app
)
goto :end

:restart
echo [%time%] Restarting Wiener Linien application...
docker-compose restart
if !errorlevel! equ 0 (
    echo [%time%] Wiener Linien app restarted successfully!
    echo [%time%] Access the app at: http://localhost:3080
) else (
    echo [%time%] Failed to restart Wiener Linien app
)
goto :end

:logs
echo [%time%] Showing Wiener Linien app logs...
docker-compose logs -f
goto :end

:status
echo [%time%] Wiener Linien app status:
docker-compose ps
echo.
echo [%time%] Container health:
docker ps --filter "name=%CONTAINER_NAME%" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
echo.
echo [%time%] Recent logs:
docker-compose logs --tail=10
goto :end

:build
echo [%time%] Building Wiener Linien Docker image...
docker-compose build --no-cache
if !errorlevel! equ 0 (
    echo [%time%] Wiener Linien image built successfully!
) else (
    echo [%time%] Failed to build Wiener Linien image
)
goto :end

:clean
echo [%time%] Cleaning up Wiener Linien containers and images...
docker-compose down --rmi all --volumes --remove-orphans
if !errorlevel! equ 0 (
    echo [%time%] Cleanup completed successfully!
) else (
    echo [%time%] Failed to cleanup Wiener Linien resources
)
goto :end

:usage
echo Usage: start_wiener_linien.bat [start^|stop^|restart^|logs^|status^|build^|clean]
echo Default action: start
echo.
echo Available actions:
echo   start   - Start the Wiener Linien application
echo   stop    - Stop the Wiener Linien application
echo   restart - Restart the Wiener Linien application
echo   logs    - Show application logs
echo   status  - Show application status
echo   build   - Build the Docker image
echo   clean   - Clean up containers and images
goto :end

:end
echo.
pause 
