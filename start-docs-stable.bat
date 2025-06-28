@echo off
setlocal enabledelayedexpansion

:: Stable Documentation Server (Port 3001)
:: This server is meant to run persistently for end-users

:: Configuration
set "DOCS_DIR=%~dp0\.windsurf\docs"
set "PORT=3001"
set "TITLE=Wiener Linien Docs (Stable)"

:: Title and header
echo =========================================
echo  %TITLE%
echo  Running on: http://localhost:%PORT%
echo  Press CTRL+C to stop the server
echo =========================================
echo.

:: Check if Node.js is installed
where node >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Node.js is not installed or not in PATH.
    echo Please install Node.js LTS from: https://nodejs.org/
    pause
    exit /b 1
)

:: Check if docsify is installed
where docsify >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo [INFO] Docsify not found globally. Installing docsify-cli globally...
    npm install -g docsify-cli
    if %ERRORLEVEL% neq 0 (
        echo [ERROR] Failed to install docsify-cli globally.
        pause
        exit /b 1
    )
)

:: Check if the docs directory exists
if not exist "%DOCS_DIR%" (
    echo [ERROR] Documentation directory not found at: %DOCS_DIR%
    pause
    exit /b 1
)

:: Start the server
echo [%TIME%] Starting stable documentation server on port %PORT%...
echo [%TIME%] Documentation will be available at: http://localhost:%PORT%
echo [%TIME%] Press CTRL+C to stop the server
echo.

:restart
cd /d "%DOCS_DIR%"
npx docsify serve -p %PORT% -o
echo.
echo [%TIME%] Server stopped. Restarting in 5 seconds...
timeout /t 5 >nul
goto restart
