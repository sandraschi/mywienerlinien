@echo off
setlocal enabledelayedexpansion

:: Configuration
set PORT=3300
set ROOT_DIR=%~dp0
set HTML_FILE=index.html
set URL=http://localhost:%PORT%/%HTML_FILE%

echo ========================================
echo    Windsurf Documentation Server
echo ========================================
echo.

:: Kill any existing processes on the port
echo [*] Checking for existing processes on port %PORT%...
netstat -ano | findstr ":%PORT%" >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [*] Found existing process on port %PORT%, attempting to stop...
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":%PORT%"') do (
        taskkill /F /PID %%a >nul 2>&1
        if !ERRORLEVEL! EQU 0 (
            echo [*] Stopped process PID %%a
        )
    )
    timeout /t 2 /nobreak >nul
)

:: Try Node.js first (preferred for Docsify)
echo [*] Checking for Node.js...
where node >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [*] Node.js found, checking for docsify-cli...
    node -e "try { require('docsify-cli'); console.log('docsify-cli found'); } catch(e) { console.log('docsify-cli not found'); process.exit(1); }" >nul 2>&1
    if %ERRORLEVEL% EQU 0 (
        echo [*] Starting Docsify server with Node.js...
        start "" "node" "node_modules/.bin/docsify" "serve" "." "--port" "%PORT%"
        set SERVER_TYPE=docsify
    ) else (
        echo [*] Installing docsify-cli globally...
        npm install -g docsify-cli
        if %ERRORLEVEL% EQU 0 (
            echo [*] Starting Docsify server...
            start "" "docsify" "serve" "." "--port" "%PORT%"
            set SERVER_TYPE=docsify
        ) else (
            echo [WARNING] Failed to install docsify-cli, falling back to Python...
            goto :python_server
        )
    )
) else (
    echo [*] Node.js not found, trying Python...
    goto :python_server
)

:: Python fallback
:python_server
echo [*] Looking for Python...
where python >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    set PYTHON_CMD=python
) else (
    where python3 >nul 2>&1
    if %ERRORLEVEL% EQU 0 (
        set PYTHON_CMD=python3
    ) else (
        echo [ERROR] Neither Node.js nor Python found.
        echo [ERROR] Please install either:
        echo [ERROR]   - Node.js (recommended for Docsify)
        echo [ERROR]   - Python (fallback option)
        pause
        exit /b 1
    )
)

echo [*] Starting Python HTTP server...
start "" "%PYTHON_CMD%" -m http.server %PORT% --bind 0.0.0.0 --directory "%ROOT_DIR%"
set SERVER_TYPE=python

:server_started
:: Wait for server to start
echo [*] Waiting for server to start...
timeout /t 3 /nobreak >nul

:: Test if server is running
echo [*] Testing server connection...
curl -s http://localhost:%PORT% >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [*] Server is running successfully!
) else (
    echo [WARNING] Server might not be ready yet, but continuing...
)

:: Display information
echo.
echo ========================================
echo    Server Information
echo ========================================
echo [*] Server type: %SERVER_TYPE%
echo [*] Root directory: %ROOT_DIR%
echo [*] Local URL: %URL%
echo [*] Network URL: http://%COMPUTERNAME%:%PORT%/
echo [*] External URL: http://%COMPUTERNAME%:%PORT%/
echo.

:: Open the browser
echo [*] Opening browser...
start "" "%URL%"

echo [*] Server is running...
echo [*] Press Ctrl+C to stop the server
echo [*] Or close this window to stop the server
echo.

:: Keep the window open and handle cleanup
:loop
timeout /t 1 /nobreak >nul
goto :loop

:: Cleanup function (called on exit)
:cleanup
echo.
echo [*] Stopping server...
if "%SERVER_TYPE%"=="docsify" (
    taskkill /F /IM node.exe >nul 2>&1
) else (
    taskkill /F /IM python.exe >nul 2>&1
)
echo [*] Server stopped
exit /b 0 