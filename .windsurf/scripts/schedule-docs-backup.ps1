<#
.SYNOPSIS
    Schedules automatic backups of the documentation
.DESCRIPTION
    Creates a Windows Scheduled Task to back up the documentation daily
.NOTES
    Version: 1.0
    Author: Windsurf AI Team
#>

param (
    [Parameter(Mandatory=$false)]
    [string]$BackupDir = "D:\\Backups\\Docs",
    
    [Parameter(Mandatory=$false)]
    [string]$TaskName = "Windsurf Docs Backup",
    
    [Parameter(Mandatory=$false)]
    [switch]$Remove
)

# Requires elevation
$currentPrincipal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
if (-not $currentPrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Error "This script requires administrator privileges to create scheduled tasks."
    Write-Host "Please run PowerShell as Administrator and try again." -ForegroundColor Red
    exit 1
}

$scriptPath = Join-Path $PSScriptRoot "backup-docs.ps1"
$action = New-ScheduledTaskAction -Execute "PowerShell.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$scriptPath`" -BackupDir `"$BackupDir`""
$trigger = New-ScheduledTaskTrigger -Daily -At 2am
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -DontStopOnIdleEnd -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries

if ($Remove) {
    # Remove existing task if it exists
    if (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) {
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
        Write-Host "Scheduled task '$TaskName' has been removed." -ForegroundColor Green
    } else {
        Write-Host "Scheduled task '$TaskName' not found." -ForegroundColor Yellow
    }
} else {
    # Create or update the task
    $taskExists = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    
    if ($taskExists) {
        $task = Set-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Settings $settings -Force
        Write-Host "Scheduled task '$TaskName' has been updated." -ForegroundColor Green
    } else {
        $task = Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Settings $settings -Description "Automated backup of Windsurf documentation" -Force
        Write-Host "Scheduled task '$TaskName' has been created." -ForegroundColor Green
    }
    
    # Output task information
    $task | Select-Object TaskName, State, @{Name='NextRunTime'; Expression={$_.NextRunTime.ToString()}}
    
    Write-Host "`nBackup will run daily at 2 AM" -ForegroundColor Cyan
    Write-Host "Backup location: $BackupDir" -ForegroundColor Cyan
    Write-Host "`nTo remove the scheduled task, run:" -ForegroundColor Yellow
    Write-Host ".\schedule-docs-backup.ps1 -Remove" -ForegroundColor White
}

Write-Host "`nTo run a manual backup:" -ForegroundColor Yellow
Write-Host ".\backup-docs.ps1 -BackupDir `"$BackupDir`"" -ForegroundColor White
