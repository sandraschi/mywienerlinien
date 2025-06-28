<#
.SYNOPSIS
    Imports Grafana dashboards from JSON files into a Grafana instance.
.DESCRIPTION
    This script automates the process of importing Grafana dashboards from JSON files
    into a running Grafana instance. It handles authentication and provides feedback
    on the import process.
.PARAMETER GrafanaUrl
    The base URL of the Grafana instance (default: http://localhost:3140)
.PARAMETER Username
    Grafana username (default: admin)
.PARAMETER Password
    Grafana password (default: windsurf123)
.PARAMETER DashboardPath
    Path to the dashboard JSON file or directory containing dashboard JSON files
    (default: $PSScriptRoot/dashboards)
.EXAMPLE
    .\import_dashboard.ps1 -DashboardPath ".\dashboards\windsurf-logs-dashboard.json"
.EXAMPLE
    .\import_dashboard.ps1 -GrafanaUrl "http://grafana:3000" -Username admin -Password secret -DashboardPath ".\dashboards"
#>

param (
    [string]$GrafanaUrl = "http://localhost:3140",
    [string]$Username = "admin",
    [string]$Password = "windsurf123",
    [string]$DashboardPath = "$PSScriptRoot\dashboards"
)

# Set TLS 1.2 for secure connections
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

# Function to get auth token
function Get-GrafanaAuthToken {
    param (
        [string]$GrafanaUrl,
        [string]$Username,
        [string]$Password
    )

    $authUrl = "${GrafanaUrl}/login"
    $body = @{
        user = $Username
        password = $Password
    } | ConvertTo-Json

    try {
        $response = Invoke-RestMethod -Uri "${GrafanaUrl}/api/login" -Method Post -Body $body -ContentType "application/json" -SessionVariable session
        return $session
    }
    catch {
        Write-Error "Failed to authenticate with Grafana: $_"
        exit 1
    }
}

# Function to import dashboard
function Import-GrafanaDashboard {
    param (
        [System.Object]$Session,
        [string]$GrafanaUrl,
        [string]$DashboardPath
    )

    $dashboardName = [System.IO.Path]::GetFileNameWithoutExtension($DashboardPath)
    Write-Host "Importing dashboard: $dashboardName" -ForegroundColor Cyan

    try {
        $dashboardJson = Get-Content -Path $DashboardPath -Raw
        $dashboardData = @{
            dashboard = ($dashboardJson | ConvertFrom-Json -AsHashtable)
            overwrite = $true
        } | ConvertTo-Json -Depth 20

        $importUrl = "${GrafanaUrl}/api/dashboards/import"
        $headers = @{
            "Content-Type" = "application/json"
            "Accept" = "application/json"
        }

        $response = Invoke-RestMethod -WebSession $Session -Uri $importUrl -Method Post -Body $dashboardData -Headers $headers
        Write-Host "Successfully imported dashboard: $($response.slug)" -ForegroundColor Green
    }
    catch {
        Write-Error "Failed to import dashboard $dashboardName : $_"
    }
}

# Main script execution
Write-Host "=== Grafana Dashboard Importer ===" -ForegroundColor Yellow
Write-Host "Connecting to Grafana at: $GrafanaUrl"

# Get authentication token
$session = Get-GrafanaAuthToken -GrafanaUrl $GrafanaUrl -Username $Username -Password $Password

# Process dashboard path
if (Test-Path -Path $DashboardPath -PathType Leaf) {
    # Single file
    Import-GrafanaDashboard -Session $session -GrafanaUrl $GrafanaUrl -DashboardPath $DashboardPath
}
elseif (Test-Path -Path $DashboardPath -PathType Container) {
    # Directory - process all JSON files
    $dashboardFiles = Get-ChildItem -Path $DashboardPath -Filter "*.json" -File
    
    if ($dashboardFiles.Count -eq 0) {
        Write-Warning "No JSON dashboard files found in $DashboardPath"
        exit 1
    }

    foreach ($file in $dashboardFiles) {
        Import-GrafanaDashboard -Session $session -GrafanaUrl $GrafanaUrl -DashboardPath $file.FullName
    }
}
else {
    Write-Error "Dashboard path not found: $DashboardPath"
    exit 1
}

Write-Host "`nDashboard import process completed." -ForegroundColor Green
