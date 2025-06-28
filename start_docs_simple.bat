@echo off
setlocal enabledelayedexpansion

echo Starting documentation server...
echo.

:: Set the directory and port
set "DOCS_DIR=%~dp0\.windsurf\docs"
set "PORT=3300"
set "URL=http://localhost:%PORT%"

:: Check if Python is available
where python >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo Error: Python is not found in PATH.
    echo Please install Python or add it to your system PATH.
    pause
    exit /b 1
)

:: Kill any existing Python server on this port
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":%PORT%" ^| findstr "LISTENING"') do (
    echo Stopping process using port %PORT%...
    taskkill /F /PID %%a >nul 2>&1
)

:: Change to docs directory
cd /d "%DOCS_DIR%"
if %ERRORLEVEL% neq 0 (
    echo Error: Could not change to directory: %DOCS_DIR%
    pause
    exit /b 1
)

:: Start the server
echo Starting Python HTTP server on port %PORT%...
start "" "%URL%"
start "Python HTTP Server" cmd /k "python -m http.server %PORT%"

echo.
echo Server started at %URL%
echo Press any key to stop the server...
pause >nul

echo Stopping server...
taskkill /F /FI "WINDOWTITLE eq Python HTTP Server*" >nul 2>&1
echo Server stopped.
pause
