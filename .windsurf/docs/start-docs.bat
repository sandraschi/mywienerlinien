@echo off
setlocal enabledelayedexpansion

:: Configuration
set PORT=3300
set ROOT_DIR=%~dp0
set HTML_FILE=index.theme-v2.html
set URL=http://localhost:%PORT%/%HTML_FILE%

:: Kill any existing Python processes
echo [*] Stopping any existing Python servers...
tasklist /FI "IMAGENAME eq python.exe" 2>nul | find /I "python.exe" >nul
if %ERRORLEVEL% EQU 0 (
    taskkill /F /IM python.exe >nul 2>&1
    if %ERRORLEVEL% EQU 0 (
        echo [*] Stopped existing Python processes
    ) else (
        echo [*] No Python processes found
    )
)

:: Find Python executable
echo [*] Looking for Python...
where python >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    set PYTHON_CMD=python
) else (
    where python3 >nul 2>&1
    if %ERRORLEVEL% EQU 0 (
        set PYTHON_CMD=python3
    ) else (
        echo [ERROR] Python not found. Please install Python and try again.
        pause
        exit /b 1
    )
)

echo [*] Starting documentation server...
echo [*] Root directory: %ROOT_DIR%
echo [*] URL: %URL%
echo [*] Network access: http://%COMPUTERNAME%:%PORT%/
echo [*] Local access: http://localhost:%PORT%/

:: Start Python HTTP server (bind to all interfaces for network access)
start "" "%PYTHON_CMD%" -m http.server %PORT% --bind 0.0.0.0 --directory "%ROOT_DIR%"

:: Wait for server to start
timeout /t 2 /nobreak >nul

:: Open the browser
start "" "%URL%"

echo [*] Server is running...
echo [*] Press any key to stop the server
pause >nul

:: Stop the server
taskkill /F /IM python.exe >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [*] Server stopped
) else (
    echo [*] No server process found
)

exit /b 0
