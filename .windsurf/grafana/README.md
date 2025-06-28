# Grafana Dashboard Management

This directory contains tools and configurations for managing Grafana dashboards in the Windsurf project.

## Directory Structure

```
.windsurf/grafana/
├── dashboards/               # Directory containing dashboard JSON files
│   └── windsurf-logs-dashboard.json  # Main logs dashboard
├── import_dashboard.ps1      # PowerShell script for importing dashboards
└── README.md                 # This file
```

## Dashboard Import Script

The `import_dashboard.ps1` script automates the process of importing Grafana dashboards from JSON files into a running Grafana instance.

### Prerequisites

- PowerShell 5.1 or later
- Access to a running Grafana instance
- Valid Grafana credentials (default: admin/windsurf123)

### Usage

```powershell
# Import a single dashboard
.\import_dashboard.ps1 -DashboardPath ".\dashboards\windsurf-logs-dashboard.json"

# Import all dashboards from a directory
.\import_dashboard.ps1 -DashboardPath ".\dashboards"

# Specify custom Grafana URL and credentials
.\import_dashboard.ps1 -GrafanaUrl "http://localhost:3000" -Username admin -Password yourpassword
```

### Parameters

- `-GrafanaUrl`: Base URL of the Grafana instance (default: http://localhost:3140)
- `-Username`: Grafana username (default: admin)
- `-Password`: Grafana password (default: windsurf123)
- `-DashboardPath`: Path to a single dashboard JSON file or directory containing dashboards (default: .\dashboards)

### Examples

1. **Basic Usage** (uses all defaults):
   ```powershell
   .\import_dashboard.ps1
   ```

2. **Custom Grafana Instance**:
   ```powershell
   .\import_dashboard.ps1 -GrafanaUrl "http://grafana:3000" -Username admin -Password yourpassword
   ```

3. **Specific Dashboard**:
   ```powershell
   .\import_dashboard.ps1 -DashboardPath ".\custom-dashboards\my-dashboard.json"
   ```

## Available Dashboards

### Windsurf Logs Dashboard

**File**: `dashboards/windsurf-logs-dashboard.json`

A comprehensive dashboard for monitoring Windsurf application logs with the following features:

- Log volume by level over time
- Recent log entries table
- Log level distribution
- Error rate monitoring

#### How to Import

```powershell
# From the .windsurf/grafana directory
.\import_dashboard.ps1 -DashboardPath ".\dashboards\windsurf-logs-dashboard.json"
```

## Troubleshooting

### Authentication Failures

1. Verify the Grafana URL is correct
2. Check that the username and password are correct
3. Ensure the Grafana instance is running and accessible

### Import Errors

1. Check that the dashboard JSON is valid
2. Verify you have sufficient permissions in Grafana
3. Check the script's output for detailed error messages

### Performance Issues

If importing large dashboards is slow, try increasing the timeout:

```powershell
# In import_dashboard.ps1, modify the Invoke-RestMethod call to add:
-TimeoutSec 300  # Increase timeout to 5 minutes
```

## Best Practices

1. **Version Control**: Always keep your dashboard JSON files under version control
2. **Backup**: Regularly back up your Grafana dashboards
3. **Documentation**: Document any custom variables or data sources used in your dashboards
4. **Testing**: Test dashboard imports in a non-production environment first

## Related Documentation

- [Grafana Dashboard API](https://grafana.com/docs/grafana/latest/http_api/dashboard/)
- [Importing Dashboards via API](https://grafana.com/docs/grafana/latest/http_api/dashboard/#create--update-dashboard)
- [Dashboard JSON Model](https://grafana.com/docs/grafana/latest/dashboards/json-model/)

## License

This project is licensed under the MIT License - see the [LICENSE](../LICENSE) file for details.
