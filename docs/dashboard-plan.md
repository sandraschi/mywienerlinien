# Dashboard Strategy — Wiener Linien Observability

## Goals
- Deliver two complementary dashboards:
  - **Operations Control** (Grafana): deep technical state for engineering/SRE.
  - **Commuter Status Board** (frontend page or Grafana kiosk mode): passenger-friendly summary of live service conditions.
- Surface real-time issues quickly (loader stalls, API failures, line disruptions).
- Keep data sources unified (Loki logs, loader heartbeat, vehicle snapshots, Wiener Linien traffic info).

## Operations Dashboard Enhancements (Grafana)
- **Heartbeat Stat**: parse `HEARTBEAT stage=...` log lines to show last loader stage + age. Alert if stale beyond 15 minutes.
- **Loader Duration Panel**: logfmt `duration_seconds` fields and chart per-stage run times.
- **Vehicle Snapshot Metrics**: count vehicles per line/type (expose via structured logs or Prometheus endpoint).
- **Error Spotlight**: table panel highlighting recent ERROR/WARN entries.
- **Alerting**: Grafana rules for heartbeat lapse, spike in API 5xx, vehicle count dropping below threshold.

## Commuter Status Board
- **Headline Cards**:
  - Global status (Good Service / Minor Delays / Major Disruption).
  - Active alerts count (from trafficInfo).
  - Vehicles online (metro/tram/bus/night).
- **Line Health Grid**:
  - One tile per major line with color-coded delay state, next arrival countdown, disruption snippet.
- **Map Overlay (optional)**:
  - Leaflet map showing delayed vehicles highlighted, fallback list view for kiosk mode.
- **Alert Ticker**:
  - Rolling feed of disruptions (“Line 5 stalled at Westbahnhof”).
- **Favorites Shortcut**:
  - Show user-selected stops (requires simple local storage).

## Data & Implementation Notes
- **Heartbeat Source**: `scripts/load_gtfs_to_db.py` emits logfmt heartbeat entries; Promtail ships them to Loki.
- **Vehicle Telemetry**: `frontend/vehicle_service.py` already aggregates snapshots—extend logs with per-refresh counts.
- **Traffic Alerts**: integrate `/ogd_realtime/trafficInfo` fetcher, cache for UI + logs.
- **Frontend Page**: add route `/status` backed by new template/component; reuse Socket.IO stream for live updates.
- **Grafana Provisioning**: extend `grafana/provisioning/dashboards/wiener_linien_dashboard.json` with new stat/panel definitions.

## Next Steps
1. Finish heartbeat ingestion (Grafana stat, alert rule).
2. Instrument vehicle snapshot logger with summary metrics.
3. Build commuter dashboard UI scaffold (cards + alert ticker).
4. Hook up trafficInfo polling & persistence.
5. Polish visuals, add kiosk mode instructions.


