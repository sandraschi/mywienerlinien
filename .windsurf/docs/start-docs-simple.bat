@echo off
setlocal

:: Configuration
set PORT=3300
set ROOT_DIR=%~dp0

echo ========================================
echo    Windsurf Documentation Server
echo ========================================
echo.

:: Check if we're in the right directory
if not exist "index.html" (
    echo [ERROR] index.html not found in current directory
    echo [ERROR] Please run this script from the docs directory
    pause
    exit /b 1
)

:: Kill any existing processes on the port
echo [*] Checking for existing processes on port %PORT%...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":%PORT%" 2^>nul') do (
    echo [*] Stopping process PID %%a
    taskkill /F /PID %%a >nul 2>&1
)

:: Try Python first (most reliable)
echo [*] Looking for Python...
where python >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [*] Starting Python HTTP server...
    echo [*] URL: http://localhost:%PORT%/
    echo [*] Press Ctrl+C to stop the server
    echo.
    python -m http.server %PORT% --bind 0.0.0.0 --directory "%ROOT_DIR%"
    goto :end
)

where python3 >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [*] Starting Python3 HTTP server...
    echo [*] URL: http://localhost:%PORT%/
    echo [*] Press Ctrl+C to stop the server
    echo.
    python3 -m http.server %PORT% --bind 0.0.0.0 --directory "%ROOT_DIR%"
    goto :end
)

:: Try Node.js if Python not available
echo [*] Python not found, trying Node.js...
where node >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [*] Node.js found, checking for docsify...
    node -e "try { require('docsify-cli'); console.log('docsify-cli found'); } catch(e) { process.exit(1); }" >nul 2>&1
    if %ERRORLEVEL% EQU 0 (
        echo [*] Starting Docsify server...
        echo [*] URL: http://localhost:%PORT%/
        echo [*] Press Ctrl+C to stop the server
        echo.
        docsify serve . --port %PORT%
        goto :end
    ) else (
        echo [*] Installing docsify-cli...
        npm install -g docsify-cli
        if %ERRORLEVEL% EQU 0 (
            echo [*] Starting Docsify server...
            echo [*] URL: http://localhost:%PORT%/
            echo [*] Press Ctrl+C to stop the server
            echo.
            docsify serve . --port %PORT%
            goto :end
        )
    )
)

echo [ERROR] Neither Python nor Node.js found.
echo [ERROR] Please install either:
echo [ERROR]   - Python (recommended)
echo [ERROR]   - Node.js with docsify-cli
pause
exit /b 1

:end
echo [*] Server stopped 