Param([switch]$Headless)

# --- SOTA Headless Standard ---
if ($Headless -and ($Host.UI.RawUI.WindowTitle -notmatch 'Hidden')) {
    Start-Process pwsh -ArgumentList '-NoProfile', '-File', $PSCommandPath, '-Headless' -WindowStyle Hidden
    exit
}
$WindowStyle = if ($Headless) { 'Hidden' } else { 'Normal' }
# ------------------------------

# Wiener Linien web_sota start script
# Frontend: Vite on port 10896 (proxies /api â†’ localhost:3079)
# No separate backend needed â€” uses the running Docker stack on port 3079

$WebPort = 10896
$PSScriptRoot_ = Split-Path -Parent $MyInvocation.MyCommand.Definition

Write-Host "Checking port $WebPort..." -ForegroundColor Yellow
$pids = Get-NetTCPConnection -LocalPort $WebPort -ErrorAction SilentlyContinue |
    Where-Object { $_.OwningProcess -gt 4 } |
    Select-Object -ExpandProperty OwningProcess -Unique
foreach ($p in $pids) {
    Write-Host "Killing PID $p on port $WebPort" -ForegroundColor Red
    try { Stop-Process -Id $p -Force -ErrorAction Stop } catch {}
}

Set-Location $PSScriptRoot_

if (-not (Test-Path "node_modules")) {
    Write-Host "Installing npm dependencies..." -ForegroundColor Cyan
    npm install
}

Write-Host "Starting Wiener Linien dashboard on http://localhost:$WebPort" -ForegroundColor Green
Write-Host "  Requires: Docker stack running on port 3079" -ForegroundColor Gray

# 4b. Launch background task to open browser once frontend is ready (Auto-opened by Antigravity)
$frontendUrl = "http://127.0.0.1:$WebPort/"
$pollAndOpen = "for (`$i = 0; `$i -lt 60; `$i++) { try { `$null = Invoke-WebRequest -Uri '$frontendUrl' -TimeoutSec 2 -UseBasicParsing -ErrorAction Stop; Start-Process '$frontendUrl'; exit } catch { Start-Sleep -Seconds 1 } }"
Start-Process powershell -ArgumentList "-NoProfile", "-WindowStyle", "Hidden", "-Command", $pollAndOpen

Write-Host "Browser will open automatically when Vite is ready." -ForegroundColor Gray

# 4b. Launch background task to open browser once frontend is ready (Auto-opened by Antigravity)
$frontendUrl = "http://127.0.0.1:$WebPort/"
$pollAndOpen = "for (`$i = 0; `$i -lt 60; `$i++) { try { `$null = Invoke-WebRequest -Uri '$frontendUrl' -TimeoutSec 2 -UseBasicParsing -ErrorAction Stop; Start-Process '$frontendUrl'; exit } catch { Start-Sleep -Seconds 1 } }"
Start-Process powershell -ArgumentList "-NoProfile", "-WindowStyle", "Hidden", "-Command", $pollAndOpen

Write-Host "Browser will open automatically when Vite is ready." -ForegroundColor Gray
npm run dev -- --port $WebPort --host




