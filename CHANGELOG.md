# Changelog

All notable changes to mywienerlinien are documented here.

## [2.0.1] - 2026-08-04 (pseudo-live vehicle tracking)

### Added

- **Schedule-interpolated pseudo-vehicle tracking**: vehicle markers on the
  map are computed from the GTFS stop_times in PostGIS, not from live GPS
  (Wiener Linien publishes none - the OGD API covers incidents/blockages
  only). For every trip of a line that is between two stops right now, a
  marker is placed linearly between the bracketing stops. One marker per
  active trip - correct at any headway; selectable per line (e.g. trams),
  with a 60-marker cap per line. Timezone-aware (Europe/Vienna).
- **Speed**: the schedule query now pushes a 45min/60min time window into
  SQL (was scanning all 6.1M stop_times; line refresh ~0.8s).
- Cross-reference to the sibling server **gtfs-mcp** in README + About page.

### Fixed

- **Event-loop starvation**: `collect_vehicle_data` (sync, seconds-long) was
  called directly inside async handlers/websocket broadcast - uvicorn stopped
  answering, container went unhealthy. Now runs via `asyncio.to_thread` with
  a per-key refresh lock (concurrent callers share one computation).
- **Container flapping**: `--reload` was watching /app while the app writes
  logs into /app - infinite reload loop. Removed from the compose command.
- **Image bloat (8.26 GB -> 1.6 GB)**: `.dockerignore` patterns now use `**`
  so nested dirs (scripts/gtfs_data, frontend/data, *.sqlite, venvs) are
  excluded; the GTFS zip/extracted data/7.8 GB stale gtfs.sqlite are no
  longer baked into the image. Deleted ~10 GB of stale local artifacts.
- About page 500 (broken `url_for('read_line_info')`) - replaced with a
  literal link.

## [2.0.1] - 2026-08-04

### Fixed

- **Docker images are now self-contained**: the frontend image previously
  failed to boot standalone (`RuntimeError: GTFS manager could not import
  supporting scripts`) because `scripts/`, `models/` and `db/init-scripts`
  were never copied into it - compose bind mounts had masked the gap.
  `frontend/Dockerfile` now builds from the repo root and bakes in the app,
  scripts, models, db init SQL, and both requirements files
  (`requirements.txt` + `requirements-db.txt`).
- **Host bind mounts removed from docker-compose.yml**: Docker Desktop on this
  machine cannot create new D: bind mounts (`mkdir /run/desktop/mnt/host/d:
  file exists`). Replaced with named volumes (`postgres_data`,
  `wienerlinien_data`, `gtfs_data`) and a local postgis image with the init
  SQL baked in.
- **GTFS loader verified end-to-end**: imported the real Wiener Linien feed
  into PostGIS - 4,624 stops, 681 routes, 326,812 trips, 6,114,443 stop_times;
  frontend serves /api/health + /api/status 200 with data.

### Added

- `.dockerignore` for the repo-root build context.
- `db/Dockerfile` (postgis + baked init scripts).

## [2.0.1] - 2025-12-27

Phase 1-5 complete + schema migration (original release).
