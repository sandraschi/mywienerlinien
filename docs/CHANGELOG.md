# Changelog

## 2025-11-22

- Code quality improvements:
  - Fixed all ruff linting warnings across the codebase.
  - Removed unused imports (`time`, `os`, `create_engine`) from `scripts/gtfs_scheduled_loader.py` and `scripts/test_gtfs_loader_performance.py`.
  - Removed unused variable `metadata_dir` from `scripts/gtfs_scheduled_loader.py`.
  - All code now passes ruff checks with zero warnings.

## 2025-11-16

- Commuter status board:
  - Added `/status` page (tiles, delays, disruptions) backed by `/api/status/summary`.
  - Vehicle summary aggregates and line metadata exposed via `get_vehicle_summary()`.
- Vehicle markers:
  - Larger, high-contrast divIcons; markers update in place across refreshes.
- Observability:
  - Loader heartbeats persisted to `/logs/gtfs_loader.log` and shipped to Loki.
  - Grafana dashboard gained heartbeat stat + feed; Promtail simplified to tail `/logs/*.log`.
- Ports:
  - Avoid :00 collisions. Loki published on 3193 (internal 3100). Frontend published on 3079.
- GTFS loader robustness:
  - Coerce numpy ints to native ints when inserting trips; continuous heartbeats during long runs.
- GTFS loader performance:
  - Major performance optimizations implemented: **25-50x speedup** (from ~13 hours to ~15-30 minutes).
  - Phase 1: Disabled materialized view refresh triggers during bulk load, refreshing once at end (~6-13x speedup).
  - Phase 2: Disabled indexes during load, switched to `bulk_insert_mappings()`, increased chunk size to 5000 (additional 2-5x speedup).
  - See `docs/gtfs-loader-fix.md` for detailed technical documentation.

## 2025-11-12

- Wired the realtime vehicle pipeline end-to-end:
  - `scripts/load_gtfs_to_db.py` now enriches stops with RBL/DIVA metadata from the Wiener Linien OGD CSVs.
  - `scripts/process_gtfs.py` regenerates markdown with RBL + zone information, allowing the frontend to parse RBLs for fallback display.
  - `frontend/vehicle_service.py` throttles monitor calls, honours line filters, and de-duplicates RBLs so `/api/vehicles` reliably returns live positions (e.g. `line=U3`).
- Updated the frontend socket client (`frontend/static/js/map.js`) to use the `/ws/socket.io` namespace, restoring live updates without 404s.
- Documented the new workflow in `README.md` and `docs/gtfs/README.md` (how to run the loader, regenerate markdown, and verify realtime results).

