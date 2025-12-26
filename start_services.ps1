# Start MyWienerLinien Services - Redirects to file
$output = "D:\Dev\repos\mywienerlinien\start_output.txt"

"=====================================" | Out-File $output
"Starting MyWienerLinien - $(Get-Date)" | Out-File $output -Append
"=====================================" | Out-File $output -Append
"" | Out-File $output -Append

"[1] Stopping old containers..." | Out-File $output -Append
docker compose down 2>&1 | Out-File $output -Append
"" | Out-File $output -Append

"[2] Starting all services..." | Out-File $output -Append
docker compose up -d 2>&1 | Out-File $output -Append
"" | Out-File $output -Append

"[3] Waiting 30 seconds for initialization..." | Out-File $output -Append
Start-Sleep -Seconds 30
"" | Out-File $output -Append

"[4] Container Status:" | Out-File $output -Append
docker compose ps 2>&1 | Out-File $output -Append
"" | Out-File $output -Append

"[5] Testing endpoints..." | Out-File $output -Append
Start-Sleep -Seconds 5

try {
    $home = Invoke-WebRequest -Uri "http://localhost:3079/" -UseBasicParsing -TimeoutSec 5
    "✅ Home: $($home.StatusCode)" | Out-File $output -Append
} catch {
    "❌ Home: Failed" | Out-File $output -Append
}

"" | Out-File $output -Append
"=====================================" | Out-File $output -Append
"Startup complete! Check http://localhost:3079" | Out-File $output -Append
"=====================================" | Out-File $output -Append

Write-Host "✅ Startup script complete! Read: start_output.txt" -ForegroundColor Green

