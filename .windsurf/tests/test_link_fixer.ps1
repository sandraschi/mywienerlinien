# Test script for the link fixer

# Configuration
$testDir = Join-Path -Path $PSScriptRoot -ChildPath 'link_fixer_test'
$testOutputDir = Join-Path -Path $testDir -ChildPath 'output'
$scriptPath = Join-Path -Path $PSScriptRoot -ChildPath '..\scripts\fix_broken_links.ps1'

# Ensure the source script exists
if (-not (Test-Path -Path $scriptPath)) {
    Write-Error "Source script not found: $scriptPath"
    exit 1
}

# Create test output directory
if (Test-Path -Path $testOutputDir) {
    Remove-Item -Path $testOutputDir -Recurse -Force
}
New-Item -ItemType Directory -Path $testOutputDir -Force | Out-Null

# Create nested directory for test files
$nestedDir = Join-Path -Path $testOutputDir -ChildPath 'nested'
New-Item -ItemType Directory -Path $nestedDir -Force | Out-Null

# Copy test files to output directory
Copy-Item -Path "$testDir\*.md" -Destination $testOutputDir -Force
Copy-Item -Path "$testDir\nested\*.md" -Destination $nestedDir -Force

# Create a simple test script that uses the original script with test parameters
$testScriptContent = @"
# Test wrapper for fix_broken_links.ps1

# Import the script as a module
. "$($scriptPath -replace '\\', '\\')"

# Override configuration for testing
`$script:config = @{
    RootDir = '$($testOutputDir -replace '\\', '\\')'
    LogsDir = '$($testOutputDir -replace '\\', '\\')'
    SorryPage = '/sorry.html'
    LogFile = 'link_fix_test.log'
}

# Run the main function
Start-LinkFix
"@

# Save test script
$testScriptPath = Join-Path -Path $testOutputDir -ChildPath 'test_fix_links.ps1'
$testScriptContent | Out-File -FilePath $testScriptPath -Encoding UTF8

# Run the test script
Write-Host "Running link fixer test..." -ForegroundColor Cyan
& "C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe" -ExecutionPolicy Bypass -File $testScriptPath -Verbose

# Show results
Write-Host "`nTest Results:" -ForegroundColor Green
Write-Host "=============" -ForegroundColor Green

# Show modified files
Write-Host "`nModified Files:" -ForegroundColor Yellow
Get-ChildItem -Path $testOutputDir -Filter "*.md" -Recurse | 
    Where-Object { $_.LastWriteTime -gt (Get-Date).AddMinutes(-5) } |
    ForEach-Object { 
        Write-Host "- $($_.FullName)" -ForegroundColor Yellow
        Write-Host "  Changed: $($_.LastWriteTime)" -ForegroundColor Gray
    }

# Show log file
$logFile = Get-ChildItem -Path $testOutputDir -Filter "*.log" | Sort-Object LastWriteTime -Descending | Select-Object -First 1
if ($logFile) {
    Write-Host "`nLog File ($($logFile.Name)):" -ForegroundColor Cyan
    Write-Host "========================================"
    Get-Content -Path $logFile.FullName -Tail 20 | ForEach-Object { 
        if ($_ -match '\[ERROR\]') { 
            Write-Host $_ -ForegroundColor Red 
        } elseif ($_ -match '\[WARNING\]') { 
            Write-Host $_ -ForegroundColor Yellow 
        } else { 
            Write-Host $_ 
        }
    }
}

# Show test files
Write-Host "`nTest Files Created:" -ForegroundColor Green
Get-ChildItem -Path $testOutputDir -Filter "*.md" -Recurse | ForEach-Object {
    Write-Host "- $($_.FullName)" -ForegroundColor Green
}

Write-Host "`nTest completed. Check the output above for results." -ForegroundColor Cyan
