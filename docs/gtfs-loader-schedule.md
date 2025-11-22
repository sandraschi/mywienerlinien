# GTFS Loader Schedule & Execution

## When It Runs

### 1. **Docker Compose Startup** (Primary Method)
When you run `docker compose up`, the `gtfs-loader` container:
1. Waits for PostgreSQL to be ready
2. Creates database schema
3. Runs `gtfs_scheduled_loader.py`
4. **Checks if data is stale** (default: 7 days old)
5. **Only runs if stale** or forced
6. Exits after completion

**Location**: `docker-compose.yml` → `gtfs-loader` service

### 2. **Manual Execution**
Run directly from command line:

```powershell
# Standard run
python scripts\load_gtfs_to_db.py scripts\gtfs_data\wienerlinien-gtfs.zip

# With custom chunk size
python scripts\load_gtfs_to_db.py scripts\gtfs_data\wienerlinien-gtfs.zip --chunk-size 10000

# Test mode (limited data)
python scripts\load_gtfs_to_db.py scripts\gtfs_data\wienerlinien-gtfs.zip --test-mode

# Scheduled loader (checks staleness)
python scripts\gtfs_scheduled_loader.py

# Force refresh (ignore staleness)
$env:GTFS_FORCE_REFRESH="1"
python scripts\gtfs_scheduled_loader.py
```

### 3. **Staleness Check**
The scheduled loader checks:
- **Marker file**: `logs/gtfs_last_success.txt`
- **Default threshold**: 7 days (configurable via `GTFS_REFRESH_DAYS`)
- **Behavior**: Only runs if data is older than threshold

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `GTFS_REFRESH_DAYS` | `7` | Days before data is considered stale |
| `GTFS_CHUNK_SIZE` | `5000` | Records per batch (larger = faster but more memory) |
| `GTFS_FORCE_REFRESH` | `0` | Force refresh even if not stale (`1`/`true`/`yes`) |
| `GTFS_ZIP_PATH` | Auto-detected | Path to GTFS zip file |
| `GTFS_METADATA_DIR` | Auto-detected | Directory for RBL metadata |
| `GTFS_LOG_DIR` | `logs` | Directory for logs and marker files |

### Docker Compose Example

```yaml
gtfs-loader:
  environment:
    - GTFS_REFRESH_DAYS=7
    - GTFS_CHUNK_SIZE=5000
    - GTFS_FORCE_REFRESH=0
```

## Current Behavior

- **Runs once** on container startup
- **Checks staleness** before running
- **Skips if up-to-date** (saves time)
- **Uses optimized settings** (chunk_size=5000, indexes disabled, etc.)

## Scheduling Options

### Option 1: Cron Job (Recommended for Production)
Add to host crontab or use a cron container:

```bash
# Run weekly on Sunday at 2 AM
0 2 * * 0 docker compose exec gtfs-loader python /app/scripts/gtfs_scheduled_loader.py
```

### Option 2: Docker Restart Policy
Set container to restart periodically:

```yaml
gtfs-loader:
  restart: "on-failure:5"
  # Container restarts on failure, runs loader again
```

### Option 3: External Scheduler
Use Kubernetes CronJob, systemd timer, or cloud scheduler to trigger the container.

## Monitoring

### Check Last Run
```powershell
# View marker file
Get-Content frontend\logs\gtfs_last_success.txt

# Check heartbeat
Get-Content frontend\data\gtfs_loader_heartbeat.json
```

### Check Logs
```powershell
# View loader logs
Get-Content frontend\logs\gtfs_loader.log -Tail 50
```

### Grafana Dashboard
The loader emits heartbeats that can be monitored in Grafana (if configured).

## Notes

- The loader is **not continuously running** - it's a one-shot process
- For regular updates, use cron or external scheduler
- The scheduled loader **exits after completion** (container stops)
- Manual runs bypass staleness checks

