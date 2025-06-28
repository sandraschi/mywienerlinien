@echo off
echo Starting Docsify test server...

:: Check if .windsurf\docs exists
if not exist ".windsurf\docs" (
    echo Error: .windsurf\docs directory not found.
    exit /b 1
)

echo Running: npx docsify serve .windsurf\docs -p 3300 --open
echo.

npx docsify serve .windsurf\docs -p 3300 --open

if %ERRORLEVEL% neq 0 (
    echo.
    echo Error: Failed to start Docsify server.
    exit /b 1
)
