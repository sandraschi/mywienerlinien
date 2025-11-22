# Grafana Observability Playbook

## Dashboards Overview

### Operations Command Center (Grafana)
- **Heartbeat Stat**: Monitors GTFS loader log heartbeats; turns amber when no entries seen for 15 minutes.
- **Heartbeat Feed**: Shows the latest loader stages with timestamps.
- **Log Level Trend**: Aggregates Loki log levels to spot spikes in errors.
- **Requests by Route**: Counts route-specific log traffic for hot lines.
- **Average Request Duration**: Highlights API latency regressions.
- **HTTP Status Codes**: Surfaces sudden rises in 4xx/5xx responses.
- **Raw Logs Panel**: Provides filtered Loki stream for ad-hoc debugging.

### Commuter Status Board (Frontend `/status`)
- Headline service state with total vehicles & delays.
- Mode-specific vehicle counts (metro, tram, bus, etc.).
- GTFS loader heartbeat summary (uses shared heartbeat file/logs).
- Line tiles showing live vehicles per line.
- Delay leaderboard and disruption ticker fed by Wiener Linien OGD API.

## Data Pipeline

1. **Promtail**
   - Scrapes application log files (`frontend/logs/*.log`).
   - Scrapes Docker container stdout via Docker service discovery (requires `docker.sock` mount).
   - Parses JSON Docker logs into structured Loki entries with container metadata.

2. **Loki**
   - Stores logfmt-formatted loader heartbeats.
   - Aggregates FastAPI structured logs (level, route, duration, status).

3. **Grafana**
   - Provisioned dashboard (`grafana/provisioning/dashboards/wiener_linien_dashboard.json`).
   - Unified alerting recommended thresholds:
     - Loader heartbeat absent for 15 minutes.
     - Error log rate above baseline (e.g., >20 errors/5 minutes).
     - Vehicle count drops below configurable threshold.

4. **Frontend Dashboard**
   - Calls `/api/status/summary` for vehicle + heartbeat aggregates.
   - Calls `/api/disruptions` for ticker items.

## Alerting Playbook

| Scenario | Signal | Suggested Action |
| --- | --- | --- |
| Loader stalled | `count_over_time(HEARTBEAT[15m]) == 0` | Restart loader container, inspect GTFS feed health |
| API errors spike | `sum by (status)(count_over_time(status>=500[5m])) > 20` | Check external API availability & DB health |
| Vehicle count collapse | `vehicles_total < 10` (payload metric) | Investigate OGD API or network connectivity |
| Disruption surge | `disruptions.active` > threshold | Prepare customer communications |

## Grafana Setup Steps

1. Bring stack up: `docker compose up -d grafana loki promtail`.
2. Log into Grafana (`http://localhost:3140`, default password `windsurf123`).
3. Confirm Loki data source is auto-provisioned (`grafana/provisioning/datasources/loki.yml`).
4. Import dashboard: automatically detected via provisioning; otherwise import JSON manually.
5. Configure alert rules (Grafana Cloud or OSS Unified Alerting):
   - Navigate to **Alerting → Alert rules → New alert rule**.
   - Query expression: `count_over_time({job="wiener-linien-app"} |= "HEARTBEAT" [15m])`.
   - Condition: trigger when result `< 1`.
   - Notifications: email, Slack, Opsgenie as needed.

Ports note: Loki is published at `http://localhost:3193` for convenience, but Grafana and Promtail should continue to use the internal URL `http://loki:3100` within the Docker network.

## Maintenance

- **Heartbeat File**: located at `/app/data/gtfs_loader_heartbeat.json` (inside loader). Ensure Promtail job has access or replicate to shared volume.
- **Log Rotation**: Promtail relies on Docker log rotation; configure Docker daemon for size-based rotation to avoid disk exhaustion.
- **Dashboard Tweaks**: edit JSON and restart Grafana container or re-run provisioning.
- **Testing**: Simulate loader stall by stopping the loader container; verify alert triggers.

## Grafana AI Notes

Grafana Cloud marketing highlights “AI-powered observability” (anomaly detection, contextual root cause, SLO recommendations). Monitor roadmap for exposing those features to OSS; consider integration with Grafana Cloud if advanced AI insights are required.
