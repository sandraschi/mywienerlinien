Write-Host "This is a test script" -ForegroundColor Green
Write-Host "Current directory: $PWD" -ForegroundColor Cyan
Write-Host "Script directory: $PSScriptRoot" -ForegroundColor Cyan

# Test file operations
$testFile = Join-Path -Path $PSScriptRoot -ChildPath "test_output.txt"
"Test content" | Out-File -FilePath $testFile -Force

if (Test-Path $testFile) {
    Write-Host "Successfully created test file: $testFile" -ForegroundColor Green
} else {
    Write-Host "Failed to create test file" -ForegroundColor Red
}
