@echo off
setlocal enabledelayedexpansion

echo [INFO] Rebuilding documentation sidebar...

:: Change to the script directory
pushd "%~dp0"

:: Run the sidebar generation script
node ".windsurf\docs\build-sidebar.js"

if %ERRORLEVEL% EQU 0 (
    echo [SUCCESS] Sidebar generated successfully!
) else (
    echo [ERROR] Failed to generate sidebar. Check for errors above.
    exit /b 1
)

popd
