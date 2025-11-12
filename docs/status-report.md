# Status Report — 2025-11-12

## Highlights

- PostgreSQL loader (`scripts/load_gtfs_to_db.py`) imports the latest feed (with optional `--test-mode`) and writes comma-separated RBL codes plus DIVA metadata into the `stops` table.
- Markdown regeneration (`scripts/process_gtfs.py`) mirrors the new data. `frontend/data/*.md` now carries RBL lists and zones per stop, which the UI can parse if the DB is offline.
- Realtime vehicle API is functional:
  - `/api/vehicles?line=U3` returns ~25 live trains in Vienna.
  - Default `/api/vehicles` uses curated RBLs for each mode and returns mixed metro/bus coverage.
  - `frontend/vehicle_service.py` caches snapshots for 30s, rate-limits monitor requests (0.2s pause), and stops querying once three successful monitors are accrued for a specific line.
- Socket.IO client reconnects successfully via `/ws/socket.io`, so the map autorefresh works without polling.
- The Wiener Linien control stack contrasts GTFS “plan” data with live telemetry from every vehicle and surfaces discrepancies through the `/monitor` feed—no manual entry required. We simply consume the same automated predictions.

## Next Steps / Known Gaps

- Route polylines currently render from the static `frontend/data/gtfs/routes` bundle. Run the loader without `--test-mode` to refresh them with the latest GTFS shapes instead of the bundled snapshot.
- Consider persisting station coordinates/RBLs inside the DB-backed `stations` table for quicker lookup (the UI currently reparses markdown on startup if the DB is absent).
- Add automated smoke tests that hit `/api/vehicles` and assert a minimum vehicle count for a few lines to catch upstream Wiener Linien failures.

## Verification Checklist

- [x] `docker compose up -d db frontend`
- [x] `python scripts\load_gtfs_to_db.py scripts\gtfs_data\wienerlinien-gtfs.zip --metadata-dir scripts\gtfs_data --test-mode`
- [x] `python scripts\process_gtfs.py`
- [x] `curl http://localhost:3080/api/vehicles?line=U3`
- [x] UI map displays moving vehicles once the Socket.IO connection opens.

