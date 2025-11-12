## GTFS Loader Status (November 2025)

The end-to-end GTFS → DB → realtime pipeline now works in both `--test-mode` (quick smoke) and full mode:

- `scripts/load_gtfs_to_db.py` (Python 3.10 / Windows 10) successfully imports the latest Wiener Linien feed with `gtfs_kit 12.0.0`. In test mode we cap shapes/trips; omit `--test-mode` for the full import (expect ~15 minutes, ~3.4M stop_times).
- Stops are enriched with RBL/DIVA metadata pulled from the OGD *Haltestellen* and *Steige* CSVs via `scripts/rbl_mapper.py`. Primary RBLs are stored in `stops.stop_code` (comma-separated); DIVA numbers are appended to `stops.stop_desc` as `DIVA:...`.
- Loader logging highlights each stage (`Agencies loaded`, `Stops loaded`, `Shapes loaded`, `Trips loaded`). Monitor `logs/gtfs_loader.log` or console output to confirm progress; no more silent hangs observed after chunked processing was added.
- Regenerated markdown (`scripts/process_gtfs.py`) mirrors the DB metadata, including RBLs and zone IDs. These files now live in `frontend/data/` and are referenced by the UI when DB access is unavailable.

### Running the loader

```powershell
python scripts\load_gtfs_to_db.py scripts\gtfs_data\wienerlinien-gtfs.zip --metadata-dir scripts\gtfs_data
# Add --test-mode for a fast run (200 shapes / 500 trips)
```

- Ensure Postgres (docker service `wienerlinien-db`) is up and reachable at `localhost:5433`. The loader truncates and repopulates `stops`, `routes`, `trips`, `stop_times`, and `shapes` in a single transaction.
- Metadata CSVs are cached under `scripts\gtfs_data`. Delete them if you need to force a re-download from `data.wien.gv.at`.

### After importing

1. Run `python scripts\process_gtfs.py` to refresh markdown outputs with the new RBL data.
2. Restart the frontend container (`docker compose restart frontend`). The API will immediately begin returning realtime vehicles for RBL-enabled lines (e.g. `GET /api/vehicles?line=U3`).
3. For full polylines, rerun the loader without `--test-mode` so the `shapes` table is complete; the map then renders route geometry.

