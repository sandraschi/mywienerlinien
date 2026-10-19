# Troubleshooting - mywienerlinien

Symptom-first fixes. For setup from zero see `docs/ONBOARDING.md`; for env
reference see `docs/CONFIGURATION.md`.

## 1. pytest collection errors mentioning `frontend.*` paths

Symptom: `pytest` fails at collection with `ModuleNotFoundError: No module
named 'frontend...'` or imports resolving to the wrong tree.

Cause: two import roots coexist (`src/` layout for `wienerlinien_mcp` and the
legacy `frontend/` package). Running pytest from the wrong directory or with a
stale `PYTHONPATH` picks up the wrong one.

Fix:

```powershell
# Run from the repo root, always
cd D:\Dev\repos\mywienerlinien
$env:PYTHONPATH = "D:\Dev\repos\mywienerlinien;D:\Dev\repos\mywienerlinien\src"
uv run pytest tests/ -q
```

If a single test file pins `sys.path` to `frontend/`, run the suite (not the
file in isolation) so `pyproject.toml` `testpaths = ["tests"]` applies. Clear
stale bytecode with `just clean` after moving files.

## 2. FastAPI / dependency version notes

Symptom: `uv sync` resolves but `uvicorn` or `fastmcp` import fails, or
`pydantic` validation errors appear after an upgrade.

Facts: `pyproject.toml` pins `fastapi>=0.110.2`, `SQLAlchemy==2.0.23`,
`fastmcp>=3.4.4,<4`, `pydantic>=2.5.0`. FastMCP 3.x middleware APIs moved;
this repo deliberately leaves middleware registration commented out in
`src/wienerlinien_mcp/server.py` until the 2.13+ API is confirmed.

Fix:

```powershell
uv sync --all-extras
uv run python -c "import fastmcp, fastapi, pydantic; print(fastmcp.__version__)"
```

Do not downgrade FastMCP to silence an import error; fix the import. Never
mix pydantic v1 and v2 in the same server.

## 3. GTFS snapshot staleness or missing file

Symptom: departures work but `journey_planner` returns nothing; the map is
empty while `/api/health` is ok.

Cause: schedule data comes from the gtfs-mcp snapshot file
(`GTFS_SNAPSHOT_PATH`, sibling default). A missing file or a stale snapshot
(Vienna feed moves; check `_meta.written_at` inside the file) starves every
schedule read at once.

Fix:

```powershell
# Where does the app look?
# (empty = sibling ../gtfs-mcp/data/snapshots/vienna.db if that file exists)
$env:GTFS_SNAPSHOT_PATH
# Refresh: add the feed again in gtfs-mcp (snapshot rewrites atomically)
```

## 4. CORS errors in the dashboard

Symptom: browser console shows `Access-Control-Allow-Origin` failures; direct
`curl` to the backend works fine.

Cause: the dashboard origin is not in `FRONTEND_PORTS`. The backend builds
explicit origins plus a loopback/LAN/Tauri regex from that var.

Fix: add the dashboard port to `.env` and restart the backend:

```powershell
# .env
FRONTEND_PORTS=10896,3079,3080
```

Then restart (`just serve` or `docker compose restart frontend`). The regex
already covers `localhost`, `127.0.0.1`, `10.x`, `192.168.x`, Tailscale
`100.x`, and `tauri.localhost`, so a failure after this step means the port
itself is wrong, not the pattern.

## 5. Port conflicts (11170, 10896, 3079, 3140, 3193)

Symptom: `start.ps1` reports the port in use, or the backend binds but the
dashboard shows stale data from another repo.

Fix: find the owner before killing anything; several fleet repos share the
10700-11000 reservoir.

```powershell
netstat -ano | Select-String "11170|10896|3079"
# then either stop the owning compose stack or, for fleet ports:
just kill-all   # only if INSTALL.md documents it for this repo state
```

`start.ps1` clears `BackendPort`/`FrontendPort` before binding; a conflict
that survives a launcher restart means a non-fleet process owns the port.

## 6. Empty data: snapshot or app.db missing

Symptom: backend healthy (`/api/health` ok) but map/stations/journeys empty,
or tools report DB-unreachable.

Checklist in order:

1. Does the snapshot file exist? Check `GTFS_SNAPSHOT_PATH`, else the
   sibling default `../gtfs-mcp/data/snapshots/vienna.db`.
2. Does `data/app.db` exist? It is auto-created on first boot; a custom
   `APP_DB_PATH` must point at a writable directory.
3. Is the MCP server exporting the same paths? Claude Desktop and Cursor each
   need them in their own config/env; setting them in one terminal does not
   propagate to the launched client.

Quick probe:

```powershell
Test-Path $env:GTFS_SNAPSHOT_PATH
Test-Path ./data/app.db
curl http://127.0.0.1:11170/api/health
```

If the last line returns `{"status":"ok"}` but data is empty, the backend
is up and the snapshot file is the problem; go back to section 3.
