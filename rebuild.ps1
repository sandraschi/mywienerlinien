# MyWienerLinien Rebuild Script
# Output redirected to rebuild_output.txt

$ErrorActionPreference = "Continue"
$output = "D:\Dev\repos\mywienerlinien\rebuild_output.txt"

"=====================================" | Out-File $output
"MyWienerLinien Rebuild - $(Get-Date)" | Out-File $output -Append
"=====================================" | Out-File $output -Append
"" | Out-File $output -Append

# Test 1: Docker connectivity
"[1/5] Testing Docker connection..." | Out-File $output -Append
docker --version 2>&1 | Out-File $output -Append
"" | Out-File $output -Append

# Test 2: List existing containers
"[2/5] Listing existing containers..." | Out-File $output -Append
docker ps -a --filter "name=mywienerlinien" 2>&1 | Out-File $output -Append
"" | Out-File $output -Append

# Test 3: Stop old containers
"[3/5] Stopping old mywienerlinien containers..." | Out-File $output -Append
docker compose down 2>&1 | Out-File $output -Append
"" | Out-File $output -Append

# Test 4: Build frontend (no cache for clean build)
"[4/5] Building frontend container (this may take 5-10 minutes)..." | Out-File $output -Append
docker compose build frontend 2>&1 | Out-File $output -Append
"" | Out-File $output -Append

# Test 5: Start all services
"[5/5] Starting all services..." | Out-File $output -Append
docker compose up -d 2>&1 | Out-File $output -Append
"" | Out-File $output -Append

# Wait and check status
"Waiting 30 seconds for services to initialize..." | Out-File $output -Append
Start-Sleep -Seconds 30
"" | Out-File $output -Append

"Final Status:" | Out-File $output -Append
docker compose ps 2>&1 | Out-File $output -Append
"" | Out-File $output -Append

"=====================================" | Out-File $output -Append
"Rebuild complete! Check http://localhost:3079" | Out-File $output -Append
"=====================================" | Out-File $output -Append

Write-Host "`n✅ Script complete! Output saved to: $output" -ForegroundColor Green

