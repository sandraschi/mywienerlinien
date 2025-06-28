# Windsurf Log Viewer

## Overview
The Windsurf Log Viewer uses Grafana and Loki to provide a web-based interface for viewing and searching logs across the Windsurf environment. It's accessible to all team members on the Tailscale VPN.

## Accessing the Log Viewer

1. Ensure you're connected to the Tailscale VPN
2. Open a web browser and navigate to:
   ```
   http://<server-ip>:3140
   ```
3. Login with:
   - Username: `admin`
   - Password: `windsurf123` (change this in production)

## Managing the Log Viewer

### Start/Stop Service
Use the management script:
```powershell
# Start the log viewer
.\start_logs.bat

# Select option 1 to start
# Select option 2 to stop
```

### Viewing Logs
1. Open Grafana in your browser
2. Navigate to "Explore" in the left sidebar
3. Select "Loki" as the data source
4. Use LogQL to query logs:
   ```
   {filename="/logs/*.log"}
   ```

### Log Retention
Logs are stored in `.windsurf/logs` and rotated by the logging system.

## Security
- Access is restricted to Tailscale VPN
- Change the default admin password in production
- Review and adjust permissions as needed

## Troubleshooting

### Common Issues
- **Can't access Grafana**:
  - Verify Docker is running
  - Check if port 3140 is available
  - Ensure Tailscale is connected

- **No logs appearing**:
  - Check if Loki is running: `docker-compose -f docker-compose.logs.yml ps`
  - Verify log files exist in `.windsurf/logs`
  - Check container logs: `docker-compose -f docker-compose.logs.yml logs`

## Backup and Maintenance

### Backing Up Logs
Logs are stored in `.windsurf/logs`. To back up:
```powershell
# Create backup directory
$backupDir = "logs_backup_$(Get-Date -Format 'yyyyMMdd_HHmmss')
mkdir $backupDir

# Copy log files
Copy-Item -Path ".windsurf\logs\*" -Destination $backupDir -Recurse
```

### Updating Containers
```powershell
# Pull latest images
docker-compose -f docker-compose.logs.yml pull

# Recreate containers
docker-compose -f docker-compose.logs.yml up -d
```

## Advanced Configuration

### Changing Ports
Edit `docker-compose.logs.yml` and update:
```yaml
services:
  grafana:
    ports:
      - "NEW_PORT:3000"
```

### Environment Variables
Set in `.env` file or directly in the compose file:
```env
GRAFANA_PASSWORD=your_secure_password
```

## Support
For issues, contact your system administrator or refer to the [Grafana documentation](https://grafana.com/docs/).
