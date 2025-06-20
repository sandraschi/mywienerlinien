@echo off
echo Starting Wiener Linien Live Map with Docker...
echo.

REM Check if Docker is running
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Docker is not running. Please start Docker Desktop first.
    pause
    exit /b 1
)

REM Stop any existing containers
echo Stopping any existing containers...
docker-compose down

REM Build and start the application
echo Building and starting the application...
docker-compose up --build -d

REM Wait a moment for the application to start
echo Waiting for application to start...
timeout /t 10 /nobreak >nul

REM Check if the application is running
echo Checking application status...
curl -f http://localhost:3080/api/status >nul 2>&1
if %errorlevel% equ 0 (
    echo.
    echo SUCCESS: Wiener Linien Live Map is running!
    echo.
    echo Access the application at: http://localhost:3080
    echo API Status: http://localhost:3080/api/status
    echo.
    echo Press any key to open the application in your browser...
    pause >nul
    start http://localhost:3080
) else (
    echo.
    echo WARNING: Application might still be starting up.
    echo Please wait a moment and try accessing: http://localhost:3080
)

echo.
echo To stop the application, run: docker-compose down
echo To view logs, run: docker-compose logs -f
pause 