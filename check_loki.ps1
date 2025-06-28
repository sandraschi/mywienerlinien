# Simple Loki Stack Checker
Write-Host "=== Loki Stack Checker ===" -ForegroundColor Cyan

# Check Docker services
Write-Host "`n[1/4] Checking Docker services..." -ForegroundColor Yellow
$services = @("loki", "promtail", "grafana")

foreach ($service in $services) {
    $status = docker ps --filter "name=^${service}$" --format "{{.Status}}" 2>&1
    if ($LASTEXITCODE -eq 0 -and $status) {
        Write-Host "[OK]   $service is running" -ForegroundColor Green
    } else {
        Write-Host "[ERROR] $service is NOT running" -ForegroundColor Red
    }
}

# Check Loki endpoints
Write-Host "`n[2/4] Checking Loki endpoints..." -ForegroundColor Yellow
$lokiEndpoints = @(
    @{Name="Loki Health"; Path="/ready"},
    @{Name="Loki Metrics"; Path="/metrics"},
    @{Name="Loki Ring"; Path="/ring"}
)

foreach ($endpoint in $lokiEndpoints) {
    $url = "http://localhost:3100$($endpoint.Path)"
    try {
        $response = Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 5 -ErrorAction Stop
        Write-Host "[OK]   $($endpoint.Name) ($url) - Status: $($response.StatusCode)" -ForegroundColor Green
    } catch {
        Write-Host "[ERROR] $($endpoint.Name) ($url) - $($_.Exception.Message)" -ForegroundColor Red
    }
}

# Check Promtail
Write-Host "`n[3/4] Checking Promtail..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:9080/metrics" -UseBasicParsing -TimeoutSec 5 -ErrorAction Stop
    Write-Host "[OK]   Promtail metrics endpoint is accessible" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Promtail metrics endpoint is not accessible: $($_.Exception.Message)" -ForegroundColor Red
}

# Check Grafana
Write-Host "`n[4/4] Checking Grafana..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:3140/api/health" -UseBasicParsing -TimeoutSec 5 -ErrorAction Stop
    $health = $response.Content | ConvertFrom-Json
    Write-Host "[OK]   Grafana is running" -ForegroundColor Green
    Write-Host "       Version: $($health.version)"
    Write-Host "       Database: $($health.database)"
} catch {
    Write-Host "[ERROR] Grafana is not accessible: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`n=== Check complete ===" -ForegroundColor Cyan
