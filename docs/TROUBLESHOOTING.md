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

## 3. GTFS loader staleness or half-loaded schema

Symptoms: departures work but `journey_planner` returns nothing; stop counts
look wrong; loader exits instantly saying feed is fresh when it is not.

Cause: the loader compares feed metadata in `GTFS_METADATA_DIR` against
`GTFS_REFRESH_DAYS` (default 365). A stale marker or an interrupted first
import (15-30 min for ~10M stop_times) leaves a partial schema.

Fix:

```powershell
# Force a full refresh
docker compose run --rm -e GTFS_FORCE_REFRESH=1 gtfs-loader
docker compose logs -f gtfs-loader
```

Check row counts after import (expect ~4.6k stops, ~1.1k routes, ~560k
trips). If the schema itself mismatches (e.g. old `cities(name, country)`
vs new `cities(city_code, city_name, ...)`), re-run migrations before the
loader; the backend health check does not catch this.

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

## 5. Port conflicts (11170, 10896, 3079, 5433, 3140, 3193)

Symptom: `start.ps1` reports the port in use, or the backend binds but the
dashboard shows stale data from another repo.

Fix: find the owner before killing anything; several fleet repos share the
10700-11000 reservoir.

```powershell
netstat -ano | Select-String "11170|10896|3079|5433"
# then either stop the owning compose stack or, for fleet ports:
just kill-all   # only if INSTALL.md documents it for this repo state
```

`start.ps1` clears `BackendPort`/`FrontendPort` before binding; a conflict
that survives a launcher restart means a non-fleet process (often a second
Postgres on 5432 vs this repo's 5433) owns the port.

## 6. DB connection refused on 5433

Symptom: backend or MCP server logs `connection refused` or `timeout` for
`localhost:5433`; dashboard loads but shows no data.

Checklist in order:

1. Is Docker Desktop running and the `db` service up?
   `docker compose ps` should show `db` healthy with port `5433->5432`.
2. Is `DATABASE_URL` pointing at 5433? Native default is
   `postgresql://wienerlinien:wienerlinien@localhost:5433/wienerlinien`.
   Port 5432 is a different (often local) Postgres.
3. Did the DB finish initializing? PostGIS init plus GTFS import can take
   15-30 min on first run; `docker compose logs db` shows progress.
4. Is the MCP server exporting the same URL? Claude Desktop and Cursor each
   need it in their own config/env; setting it in one terminal does not
   propagate to the launched client.

Quick probe:

```powershell
docker compose ps db
Test-NetConnection 127.0.0.1 -Port 5433
curl http://127.0.0.1:11170/api/health
```

If the last line returns `{"status":"ok"}` but data is empty, the DB is up
and the GTFS import is the problem; go back to section 3.
