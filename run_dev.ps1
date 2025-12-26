# Quick Development Runner
# Run frontend outside Docker for instant hot-reload

Write-Host "`n🚀 MyWienerLinien Dev Mode" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Check if database is running
Write-Host "📊 Checking database..." -ForegroundColor Yellow
$dbRunning = docker ps --filter "name=wienerlinien-db" --filter "status=running" --format "{{.Names}}"
if (-not $dbRunning) {
    Write-Host "❌ Database not running. Starting..." -ForegroundColor Red
    docker compose up -d db
    Write-Host "⏳ Waiting for database..." -ForegroundColor Yellow
    Start-Sleep -Seconds 10
}
Write-Host "✅ Database running" -ForegroundColor Green

# Set environment variables
$env:DATABASE_URL = "postgresql://wienerlinien:wienerlinien@localhost:5433/wienerlinien"
$env:APP_ENV = "development"

# Check if venv exists
if (-not (Test-Path "frontend\.venv")) {
    Write-Host "`n📦 Creating virtual environment..." -ForegroundColor Yellow
    cd frontend
    python -m venv .venv
    & .\.venv\Scripts\Activate.ps1
    Write-Host "📦 Installing dependencies..." -ForegroundColor Yellow
    pip install -r requirements.txt
    cd ..
} else {
    Write-Host "✅ Virtual environment exists" -ForegroundColor Green
}

# Activate venv and run
Write-Host "`n🔥 Starting hot-reload server..." -ForegroundColor Cyan
Write-Host "   Changes to .py files will auto-reload!" -ForegroundColor White
Write-Host "   URL: http://localhost:3080`n" -ForegroundColor Green

cd frontend
& .\.venv\Scripts\Activate.ps1
uvicorn app:app --host 0.0.0.0 --port 3080 --reload

