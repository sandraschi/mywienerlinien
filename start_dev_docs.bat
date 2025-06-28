@echo off
setlocal enabledelayedexpansion

:: Check for admin rights
net session >nul 2>&1
if %ERRORLEVEL% == 0 (
    set "IS_ADMIN=1"
) else (
    set "IS_ADMIN=0"
)

:: Development Docsify server starter (Port 3001)
echo === Starting Windsurf Development Documentation Server ===
echo.

:: Check if Node.js is installed
where node >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Node.js is not installed or not in PATH.
    echo Please install Node.js LTS from: https://nodejs.org/
    pause
    exit /b 1
)

:: Set paths
set "DOCS_DIR=%~dp0\.windsurf\docs"
set "DEV_PORT=3001"
set "DEV_LABEL=DEV"

:: Kill any process using port 3001
echo [1/3] Stopping any existing development server...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":%DEV_PORT%" ^| findstr "LISTENING"') do (
    echo Found process with PID %%a using port %DEV_PORT%
    if %IS_ADMIN%==1 (
        taskkill /F /PID %%a >nul 2>&1
        if !ERRORLEVEL! EQU 0 (
            echo Successfully terminated process
        ) else (
            echo Failed to terminate process, trying with PowerShell
            powershell -Command "Stop-Process -Id %%a -Force -ErrorAction SilentlyContinue"
        )
    ) else (
        echo Warning: Need admin rights to terminate process
        powershell -Command "Start-Process cmd -Verb RunAs -ArgumentList '/c taskkill /F /PID %%a'"
    )
)

timeout /t 2 /nobreak >nul

:: Change to docs directory
if not exist "%DOCS_DIR%" (
    echo [ERROR] Documentation directory not found at:
    echo %DOCS_DIR%
    pause
    exit /b 1
)

cd /d "%DOCS_DIR%"

:: Install dependencies if needed
if not exist "node_modules" (
    echo [2/3] Installing dependencies...
    call npm install
    if %ERRORLEVEL% neq 0 (
        echo [ERROR] Failed to install dependencies
        pause
        exit /b 1
    )
)

:: Start the development server
echo [3/3] Starting Development Docsify server on http://localhost:%DEV_PORT%...

:: Open browser first
start "" "http://localhost:%DEV_PORT%"

:: Start server in a new window with a different title
start "Docsify DEV Server" cmd /c "cd /d "%DOCS_DIR%" & npx docsify serve -p %DEV_PORT% -o"

echo.
echo Development server started successfully!
echo Access the development documentation at: http://localhost:%DEV_PORT%
echo.
echo Press any key to stop the server...
pause >nul

echo.
echo Stopping development documentation server...

timeout /t 1 /nobreak >nul

:: Try to stop the server
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":%DEV_PORT%" ^| findstr "LISTENING"') do (
    echo Found process using port %DEV_PORT% with PID %%a
    if %IS_ADMIN%==1 (
        taskkill /F /PID %%a >nul 2>&1
        if !ERRORLEVEL! EQU 0 (
            echo Successfully terminated process
        ) else (
            powershell -Command "Stop-Process -Id %%a -Force -ErrorAction SilentlyContinue"
        )
    ) else (
        powershell -Command "Start-Process cmd -Verb RunAs -ArgumentList '/c taskkill /F /PID %%a'"
    )
)

echo Server stopped.
timeout /t 1 /nobreak >nul

echo If the server is still running, please close any command windows
echo titled "Docsify DEV Server" or use Task Manager to end any Node.js processes.
pause
exit /b 0
