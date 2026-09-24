param([switch]$Headless, [switch]$BackendOnly, [switch]$NoBrowser)
$ErrorActionPreference = "Stop"
$ScriptRoot = Split-Path -Parent $PSCommandPath
# Ports mirror fleet-start.config.ps1 (BackendPort 11170, FrontendPort 10896)
$BackendPort = 11170
$FrontendPort = 10896

$env:WEB_PORT = "$BackendPort"
$env:FASTMCP_LOG_LEVEL = 'WARNING'

Write-Host 'Starting mywienerlinien...' -ForegroundColor Cyan
Set-Location $ScriptRoot

# Port zombie clearing before bind (fleet standard)
Get-NetTCPConnection -LocalPort $BackendPort -ErrorAction SilentlyContinue |
    ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }
if (-not $BackendOnly) {
    Get-NetTCPConnection -LocalPort $FrontendPort -ErrorAction SilentlyContinue |
        ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }
}

$childStyle = if ($Headless) { 'Hidden' } else { 'Normal' }

# Start backend: web_sota FastAPI (UvicornTarget server:app) with repo-root
# working directory so web_sota/backend/major_stops.json + lines.json resolve.
Start-Process pwsh -ArgumentList '-NoProfile', '-Command', "uv run uvicorn server:app --host 127.0.0.1 --port $BackendPort --app-dir web_sota/backend" -WorkingDirectory $ScriptRoot -WindowStyle $childStyle

# Backend readiness: TCP poll for /api/health (not a fixed sleep)
$ready = $false
for ($i = 0; $i -lt 60; $i++) {
    try {
        $r = Invoke-WebRequest -Uri "http://127.0.0.1:$BackendPort/api/health" -TimeoutSec 2 -UseBasicParsing
        if ($r.StatusCode -eq 200) { $ready = $true; break }
    } catch {
        Start-Sleep -Seconds 1
    }
}
if (-not $ready) { throw "Backend did not become ready on port $BackendPort within 60s" }
Write-Host "Backend ready: http://127.0.0.1:$BackendPort/api/health" -ForegroundColor Green

if ($BackendOnly) { return }

# Start frontend (Vite dev on 10896, proxies /api to the backend)
Start-Process pwsh -ArgumentList '-NoProfile', '-Command', 'npm run dev' -WorkingDirectory (Join-Path $ScriptRoot 'web_sota') -WindowStyle $childStyle

if (-not $NoBrowser -and -not $Headless) {
    Start-Sleep -Seconds 3
    Start-Process "http://localhost:$FrontendPort"
}
Write-Host "Dashboard: http://localhost:$FrontendPort" -ForegroundColor Green
