# Continuous App Monitor - Updates file every 5 seconds
$output = "D:\Dev\repos\mywienerlinien\monitor_output.txt"

Write-Host "🔄 Monitoring MyWienerLinien... (Ctrl+C to stop)" -ForegroundColor Cyan
Write-Host "Output: monitor_output.txt" -ForegroundColor Yellow

while ($true) {
    "=====================================" | Out-File $output
    "Monitor Update - $(Get-Date -Format 'HH:mm:ss')" | Out-File $output -Append
    "=====================================" | Out-File $output -Append
    "" | Out-File $output -Append
    
    # Quick endpoint test
    "Endpoint Status:" | Out-File $output -Append
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:3079/" -UseBasicParsing -TimeoutSec 2
        "✅ App responding: $($response.StatusCode)" | Out-File $output -Append
        "   Content size: $(($response.Content.Length / 1KB).ToString('F1')) KB" | Out-File $output -Append
    } catch {
        "❌ App not responding: $($_.Exception.Message)" | Out-File $output -Append
    }
    "" | Out-File $output -Append
    
    # Frontend logs (last 5 lines)
    "Latest Frontend Logs:" | Out-File $output -Append
    docker logs wienerlinien-frontend --tail 5 2>&1 | Out-File $output -Append
    
    Start-Sleep -Seconds 5
}

