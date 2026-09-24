@echo off
setlocal
REM mywienerlinien launcher: delegates to start.ps1 (fleet standard).
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0start.ps1" %*
endlocal
