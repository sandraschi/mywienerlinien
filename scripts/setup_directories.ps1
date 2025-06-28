# Create required directories if they don't exist
$directories = @(
    "D:\Dev\repos\mywienerlinien\.windsurf\logs",
    "D:\Dev\repos\mywienerlinien\docs\gtfs"
)

foreach ($dir in $directories) {
    if (-not (Test-Path -Path $dir)) {
        try {
            New-Item -ItemType Directory -Path $dir -Force | Out-Null
            Write-Host "Created directory: $dir" -ForegroundColor Green
        } catch {
            Write-Error "Failed to create directory $dir : $_"
            exit 1
        }
    } else {
        Write-Host "Directory already exists: $dir" -ForegroundColor Yellow
    }
}

# Verify write permissions to the logs directory
$testFile = Join-Path "D:\Dev\repos\mywienerlinien\.windsurf\logs" "test_permissions.tmp"
try {
    [System.IO.File]::WriteAllText($testFile, "test")
    Remove-Item -Path $testFile -Force
    Write-Host "Verified write permissions to logs directory" -ForegroundColor Green
} catch {
    Write-Error "No write permissions to logs directory: $_"
    exit 1
}

Write-Host "All directories are ready" -ForegroundColor Green
