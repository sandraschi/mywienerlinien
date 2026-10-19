param([switch]$Headless, [switch]$NoBrowser)
$ErrorActionPreference = "Stop"
$ScriptRoot = Split-Path -Parent $PSCommandPath
# Fleet port: 10722 = publictransport-mcp Frontend (native Leaflet map, no Docker)
$MapPort = 10722

$env:PYTHONPATH = $ScriptRoot
$env:PORT = "$MapPort"

Write-Host 'Starting publictransport-mcp map (native, no Docker)...' -ForegroundColor Cyan
Set-Location $ScriptRoot

# Port zombie clearing before bind (fleet standard)
Get-NetTCPConnection -LocalPort $MapPort -ErrorAction SilentlyContinue |
    ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }

# Schedule data must exist: gtfs-mcp snapshot file (no database server).
$snapPath = if ($env:GTFS_SNAPSHOT_PATH) { $env:GTFS_SNAPSHOT_PATH } else { Join-Path $ScriptRoot '..' 'gtfs-mcp' 'data' 'snapshots' 'vienna.db' }
if (-not (Test-Path $snapPath)) {
    throw "GTFS snapshot not found at $snapPath. Add the Vienna feed in gtfs-mcp or set GTFS_SNAPSHOT_PATH."
}

$childStyle = if ($Headless) { 'Hidden' } else { 'Normal' }

# frontend/app.py serves the Leaflet map + sidebar + city selector from
# frontend/templates + frontend/static (all in-repo, no container).
Start-Process pwsh -ArgumentList '-NoProfile', '-Command', "uv run uvicorn app:app --host 127.0.0.1 --port $MapPort" -WorkingDirectory (Join-Path $ScriptRoot 'frontend') -WindowStyle $childStyle

# Readiness: TCP poll for /api/health (not a fixed sleep)
$ready = $false
for ($i = 0; $i -lt 90; $i++) {
    try {
        $r = Invoke-WebRequest -Uri "http://127.0.0.1:$MapPort/api/health" -TimeoutSec 2 -UseBasicParsing
        if ($r.StatusCode -eq 200) { $ready = $true; break }
    } catch {
        Start-Sleep -Seconds 1
    }
}
if (-not $ready) { throw "Map did not become ready on port $MapPort within 90s" }
Write-Host "Map ready: http://localhost:$MapPort/" -ForegroundColor Green

if (-not $NoBrowser -and -not $Headless) {
    Start-Process "http://localhost:$MapPort/"
}
