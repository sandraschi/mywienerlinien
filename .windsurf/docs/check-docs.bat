@echo off
setlocal enabledelayedexpansion

echo ========================================
echo    Windsurf Documentation Checker
echo ========================================
echo.

set ROOT_DIR=%~dp0
set ERRORS=0
set WARNINGS=0

echo [*] Checking documentation structure...
echo [*] Root directory: %ROOT_DIR%
echo.

:: Check for essential files
echo === Essential Files ===
if exist "index.html" (
    echo [✓] index.html found
) else (
    echo [✗] index.html missing
    set /a ERRORS+=1
)

if exist "_sidebar.md" (
    echo [✓] _sidebar.md found
) else (
    echo [✗] _sidebar.md missing
    set /a ERRORS+=1
)

if exist "_coverpage.md" (
    echo [✓] _coverpage.md found
) else (
    echo [⚠] _coverpage.md missing (optional)
    set /a WARNINGS+=1
)

echo.

:: Check for plugins directory
echo === Plugins ===
if exist "plugins\" (
    echo [✓] plugins directory found
    dir /b plugins\ 2>nul | find /c /v "" >nul
    if %ERRORLEVEL% EQU 0 (
        echo [✓] plugins directory contains files
    ) else (
        echo [⚠] plugins directory is empty
        set /a WARNINGS+=1
    )
) else (
    echo [✗] plugins directory missing
    set /a ERRORS+=1
)

echo.

:: Check for CSS directory
echo === CSS ===
if exist "css\" (
    echo [✓] css directory found
    dir /b css\ 2>nul | find /c /v "" >nul
    if %ERRORLEVEL% EQU 0 (
        echo [✓] css directory contains files
    ) else (
        echo [⚠] css directory is empty
        set /a WARNINGS+=1
    )
) else (
    echo [⚠] css directory missing (optional)
    set /a WARNINGS+=1
)

echo.

:: Check sidebar structure
echo === Sidebar Analysis ===
if exist "_sidebar.md" (
    echo [*] Analyzing _sidebar.md...
    
    :: Count total lines
    for /f %%i in ('type "_sidebar.md" ^| find /c /v ""') do set TOTAL_LINES=%%i
    echo [*] Total lines in sidebar: !TOTAL_LINES!
    
    :: Count links
    for /f %%i in ('findstr /c:"[^" /c:"](/" "_sidebar.md" ^| find /c /v ""') do set LINK_COUNT=%%i
    echo [*] Link count: !LINK_COUNT!
    
    :: Check for common issues
    findstr /c:"[^" "_sidebar.md" >nul
    if %ERRORLEVEL% EQU 0 (
        echo [✓] Sidebar contains links
    ) else (
        echo [✗] Sidebar contains no links
        set /a ERRORS+=1
    )
    
    :: Check for broken links (basic check)
    echo [*] Checking for potential broken links...
    for /f "tokens=2 delims=()" %%a in ('findstr /c:"](/" "_sidebar.md"') do (
        set "link=%%a"
        if not exist "!link!" (
            if not exist "!link!.md" (
                echo [⚠] Potential broken link: !link!
                set /a WARNINGS+=1
            )
        )
    )
) else (
    echo [✗] Cannot analyze sidebar - file missing
    set /a ERRORS+=1
)

echo.

:: Check directory structure
echo === Directory Structure ===
set DIRS_CHECKED=0
set DIRS_FOUND=0

for /d %%d in (*) do (
    set /a DIRS_CHECKED+=1
    if exist "%%d\" (
        set /a DIRS_FOUND+=1
        echo [✓] Directory: %%d
    )
)

echo [*] Directories found: !DIRS_FOUND! out of !DIRS_CHECKED!

echo.

:: Check for common issues
echo === Common Issues ===

:: Check if running from correct directory
if not exist "index.html" (
    echo [✗] Not running from docs directory
    set /a ERRORS+=1
)

:: Check for port conflicts
netstat -ano | findstr ":3300" >nul
if %ERRORLEVEL% EQU 0 (
    echo [⚠] Port 3300 is already in use
    set /a WARNINGS+=1
)

:: Check for Python/Node.js
where python >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [✓] Python found
) else (
    where python3 >nul 2>&1
    if %ERRORLEVEL% EQU 0 (
        echo [✓] Python3 found
    ) else (
        where node >nul 2>&1
        if %ERRORLEVEL% EQU 0 (
            echo [✓] Node.js found
        ) else (
            echo [✗] No server runtime found (Python or Node.js)
            set /a ERRORS+=1
        )
    )
)

echo.

:: Summary
echo ========================================
echo    Summary
echo ========================================
echo [*] Errors: %ERRORS%
echo [*] Warnings: %WARNINGS%

if %ERRORS% EQU 0 (
    if %WARNINGS% EQU 0 (
        echo [✓] Documentation structure looks good!
        echo [*] You can run start-docs-simple.bat to start the server
    ) else (
        echo [⚠] Documentation has warnings but should work
        echo [*] You can run start-docs-simple.bat to start the server
    )
) else (
    echo [✗] Documentation has errors that need to be fixed
    echo [*] Please fix the errors above before starting the server
)

echo.
pause 