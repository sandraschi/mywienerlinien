# Pre-commit Biome gate for web_sota/. Fails the commit when
# `npm run biome:ci` reports errors inside web_sota/.
$ErrorActionPreference = "Stop"
$root = Join-Path $PSScriptRoot ".."
$web = Join-Path $root "web_sota"
if (-not (Test-Path $web)) { exit 0 }
Push-Location $web
try {
    npm run biome:ci --silent
    if ($LASTEXITCODE -ne 0) {
        Write-Host "biome:ci failed - run 'npx biome check --write src' in web_sota/" -ForegroundColor Red
        exit 1
    }
} finally {
    Pop-Location
}
