@echo off
echo Killing processes on port 3080...

REM Check if running as administrator
net session >nul 2>&1
if %errorLevel% == 0 (
    echo Running with elevated privileges...
) else (
    echo Requesting elevated privileges...
    powershell -Command "Start-Process '%~dpnx0' -Verb RunAs"
    exit /b
)

REM Find and kill processes using port 3080
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :3080') do (
    echo Found process ID: %%a
    taskkill /PID %%a /F
    if !errorLevel! == 0 (
        echo Successfully killed process %%a
    ) else (
        echo Failed to kill process %%a
    )
)

echo Port 3080 should now be free.
pause 