# Changelog

All notable changes to mywienerlinien are documented here.

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
