# Changelog

## 2025-11-12

- Wired the realtime vehicle pipeline end-to-end:
  - `scripts/load_gtfs_to_db.py` now enriches stops with RBL/DIVA metadata from the Wiener Linien OGD CSVs.
  - `scripts/process_gtfs.py` regenerates markdown with RBL + zone information, allowing the frontend to parse RBLs for fallback display.
  - `frontend/vehicle_service.py` throttles monitor calls, honours line filters, and de-duplicates RBLs so `/api/vehicles` reliably returns live positions (e.g. `line=U3`).
- Updated the frontend socket client (`frontend/static/js/map.js`) to use the `/ws/socket.io` namespace, restoring live updates without 404s.
- Documented the new workflow in `README.md` and `docs/gtfs/README.md` (how to run the loader, regenerate markdown, and verify realtime results).

