# Fix Docker Context - Try all contexts
$output = "D:\Dev\repos\mywienerlinien\context_fix_output.txt"

"=====================================" | Out-File $output
"Docker Context Fix - $(Get-Date)" | Out-File $output -Append
"=====================================" | Out-File $output -Append
"" | Out-File $output -Append

# List contexts
"Available contexts:" | Out-File $output -Append
docker context ls 2>&1 | Out-File $output -Append
"" | Out-File $output -Append

# Try desktop-linux
"Trying desktop-linux context..." | Out-File $output -Append
docker context use desktop-linux 2>&1 | Out-File $output -Append
docker ps -a --filter "name=wienerlinien" --format "table {{.Names}}\t{{.Status}}" 2>&1 | Out-File $output -Append
"" | Out-File $output -Append

# If that failed, try default
if ($LASTEXITCODE -ne 0) {
    "Trying default context..." | Out-File $output -Append
    docker context use default 2>&1 | Out-File $output -Append
    docker ps -a --filter "name=wienerlinien" --format "table {{.Names}}\t{{.Status}}" 2>&1 | Out-File $output -Append
}

"" | Out-File $output -Append
"=====================================" | Out-File $output -Append

Write-Host "✅ Context fix attempt complete! Read: context_fix_output.txt" -ForegroundColor Green

