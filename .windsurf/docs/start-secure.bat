@echo off
setlocal enabledelayedexpansion

:: SECURE LOCAL DEVELOPMENT SERVER
:: Binds to 127.0.0.1 only - not accessible over Tailscale/network

:: Configuration - Using port 3310 for secure local testing
set PORT=3310
set BIND_ADDR=127.0.0.1
set ROOT_DIR=%~dp0
set URL=http://%BIND_ADDR%:%PORT%/index.theme-v2.html

:: Check if Python is available
where python >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Python is not found in PATH. Please install Python or add it to your PATH.
    pause
    exit /b 1
)

:: Check if port is in use (basic check)
netstat -ano | find ":%PORT%" | find "LISTENING" >nul
if %ERRORLEVEL% EQU 0 (
    echo Port %PORT% is already in use. Another process may be using it.
    echo Please close the other process or choose a different port.
    pause
    exit /b 1
)

echo Starting secure local server on port %PORT% (not accessible via Tailscale)...
echo Server will be available at: %URL%
echo This server is ONLY accessible from this computer (localhost/127.0.0.1)
echo It is NOT accessible via Tailscale or any other network interface
echo Port: %PORT% (secure localhost only)
echo.
echo Press Ctrl+C to stop the server...
echo.

:: Start the server (bound to localhost only)
python -m http.server %PORT% --bind %BIND_ADDR% --directory "%ROOT_DIR%"

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Failed to start server. Error code: %ERRORLEVEL%
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo Server stopped.
pause
