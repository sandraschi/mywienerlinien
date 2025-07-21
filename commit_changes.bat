@echo off
setlocal enabledelayedexpansion

REM Change to the repository directory
cd /d "%~dp0"

echo Adding files to git...
git add .

if errorlevel 1 (
    echo Error: Failed to add files to git
    exit /b 1
)

echo Committing changes...
git commit -m "Fix route loading and display issues

- Improved markdown parsing for route data
- Added debug logging for route loading
- Fixed duplicate route handling
- Enhanced route toggle UI in sidebar
- Updated Docker configuration for development"

if errorlevel 1 (
    echo Error: Failed to commit changes
    exit /b 1
)

echo Changes committed successfully!
pause
