@echo off
setlocal enabledelayedexpansion

title MyWienerLinien - Application Manager
color 0A

echo.
echo ========================================
echo    MyWienerLinien Application Manager
echo ========================================
echo.

:menu
echo Available Applications:
echo.
echo [1] Start Wiener Linien App (Port 3080)
echo [2] Start Docsify Documentation (Port 3301)
echo [3] Start Both Applications
echo [4] Stop Wiener Linien App
echo [5] Stop Docsify Documentation
echo [6] Stop All Applications
echo [7] Show Status
echo [8] Show Logs
echo [9] Build/Rebuild Applications
echo [0] Exit
echo.
set /p choice="Enter your choice (0-9): "

if "%choice%"=="1" goto :start_wiener_linien
if "%choice%"=="2" goto :start_docsify
if "%choice%"=="3" goto :start_both
if "%choice%"=="4" goto :stop_wiener_linien
if "%choice%"=="5" goto :stop_docsify
if "%choice%"=="6" goto :stop_all
if "%choice%"=="7" goto :show_status
if "%choice%"=="8" goto :show_logs
if "%choice%"=="9" goto :build_apps
if "%choice%"=="0" goto :exit
goto :menu

:start_wiener_linien
echo.
echo [%time%] Starting Wiener Linien application...
cd frontend
call start_wiener_linien.bat start
cd ..
echo.
echo [%time%] Wiener Linien app should be available at: http://localhost:3080
echo.
pause
goto :menu

:start_docsify
echo.
echo [%time%] Starting Docsify documentation...
cd .windsurf\docs
docker-compose up -d
cd ..\..
echo.
echo [%time%] Docsify documentation should be available at: http://localhost:3301
echo.
pause
goto :menu

:start_both
echo.
echo [%time%] Starting both applications...
echo.
echo Starting Wiener Linien app...
cd frontend
call start_wiener_linien.bat start
cd ..
echo.
echo Starting Docsify documentation...
cd .windsurf\docs
docker-compose up -d
cd ..\..
echo.
echo [%time%] Both applications started!
echo [%time%] Wiener Linien app: http://localhost:3080
echo [%time%] Docsify documentation: http://localhost:3301
echo.
pause
goto :menu

:stop_wiener_linien
echo.
echo [%time%] Stopping Wiener Linien application...
cd frontend
call start_wiener_linien.bat stop
cd ..
echo.
pause
goto :menu

:stop_docsify
echo.
echo [%time%] Stopping Docsify documentation...
cd .windsurf\docs
docker-compose down
cd ..\..
echo.
pause
goto :menu

:stop_all
echo.
echo [%time%] Stopping all applications...
echo.
echo Stopping Wiener Linien app...
cd frontend
call start_wiener_linien.bat stop
cd ..
echo.
echo Stopping Docsify documentation...
cd .windsurf\docs
docker-compose down
cd ..\..
echo.
echo [%time%] All applications stopped!
echo.
pause
goto :menu

:show_status
echo.
echo [%time%] Application Status:
echo.
echo Wiener Linien App:
cd frontend
call start_wiener_linien.bat status
cd ..
echo.
echo Docsify Documentation:
cd .windsurf\docs
docker-compose ps
cd ..\..
echo.
pause
goto :menu

:show_logs
echo.
echo [%time%] Select application for logs:
echo.
echo [1] Wiener Linien App logs
echo [2] Docsify Documentation logs
echo [3] Back to main menu
echo.
set /p log_choice="Enter your choice (1-3): "

if "%log_choice%"=="1" goto :wiener_linien_logs
if "%log_choice%"=="2" goto :docsify_logs
if "%log_choice%"=="3" goto :menu
goto :show_logs

:wiener_linien_logs
echo.
echo [%time%] Wiener Linien App logs (Press Ctrl+C to exit):
cd frontend
call start_wiener_linien.bat logs
cd ..
goto :menu

:docsify_logs
echo.
echo [%time%] Docsify Documentation logs (Press Ctrl+C to exit):
cd .windsurf\docs
docker-compose logs -f
cd ..\..
goto :menu

:build_apps
echo.
echo [%time%] Build/Rebuild Applications:
echo.
echo [1] Build Wiener Linien App
echo [2] Build Docsify Documentation
echo [3] Build Both Applications
echo [4] Back to main menu
echo.
set /p build_choice="Enter your choice (1-4): "

if "%build_choice%"=="1" goto :build_wiener_linien
if "%build_choice%"=="2" goto :build_docsify
if "%build_choice%"=="3" goto :build_both
if "%build_choice%"=="4" goto :menu
goto :build_apps

:build_wiener_linien
echo.
echo [%time%] Building Wiener Linien application...
cd frontend
call start_wiener_linien.bat build
cd ..
echo.
pause
goto :menu

:build_docsify
echo.
echo [%time%] Building Docsify documentation...
cd .windsurf\docs
docker-compose build --no-cache
cd ..\..
echo.
pause
goto :menu

:build_both
echo.
echo [%time%] Building both applications...
echo.
echo Building Wiener Linien app...
cd frontend
call start_wiener_linien.bat build
cd ..
echo.
echo Building Docsify documentation...
cd .windsurf\docs
docker-compose build --no-cache
cd ..\..
echo.
echo [%time%] Both applications built successfully!
echo.
pause
goto :menu

:exit
echo.
echo [%time%] Thank you for using MyWienerLinien Application Manager!
echo.
pause
exit /b 0 