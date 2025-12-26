# Docker Status Checker - Redirects to file
$output = "D:\Dev\repos\mywienerlinien\status_output.txt"

"=====================================" | Out-File $output
"MyWienerLinien Status - $(Get-Date)" | Out-File $output -Append
"=====================================" | Out-File $output -Append
"" | Out-File $output -Append

# Docker version
"[1] Docker Version:" | Out-File $output -Append
docker --version 2>&1 | Out-File $output -Append
"" | Out-File $output -Append

# Container status
"[2] Container Status:" | Out-File $output -Append
docker ps -a --filter "name=wienerlinien" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" 2>&1 | Out-File $output -Append
"" | Out-File $output -Append

# Compose status
"[3] Docker Compose Status:" | Out-File $output -Append
docker compose ps 2>&1 | Out-File $output -Append
"" | Out-File $output -Append

# Frontend logs (last 20 lines)
"[4] Frontend Logs (last 20):" | Out-File $output -Append
docker logs wienerlinien-frontend --tail 20 2>&1 | Out-File $output -Append
"" | Out-File $output -Append

# Test endpoints
"[5] Endpoint Tests:" | Out-File $output -Append
try {
    $home = Invoke-WebRequest -Uri "http://localhost:3079/" -UseBasicParsing -TimeoutSec 5
    "✅ Home page: $($home.StatusCode)" | Out-File $output -Append
} catch {
    "❌ Home page: $($_.Exception.Message)" | Out-File $output -Append
}

try {
    $analytics = Invoke-WebRequest -Uri "http://localhost:3079/analytics" -UseBasicParsing -TimeoutSec 5
    "✅ Analytics: $($analytics.StatusCode)" | Out-File $output -Append
} catch {
    "❌ Analytics: $($_.Exception.Message)" | Out-File $output -Append
}

try {
    $community = Invoke-WebRequest -Uri "http://localhost:3079/community" -UseBasicParsing -TimeoutSec 5
    "✅ Community: $($community.StatusCode)" | Out-File $output -Append
} catch {
    "❌ Community: $($_.Exception.Message)" | Out-File $output -Append
}

"" | Out-File $output -Append
"=====================================" | Out-File $output -Append
"Check complete! Saved to: $output" | Out-File $output -Append
"=====================================" | Out-File $output -Append

Write-Host "✅ Status check complete! Read: status_output.txt" -ForegroundColor Green

