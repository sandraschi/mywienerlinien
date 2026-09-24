# Development - mywienerlinien

How to run, iterate, lint, and test. For install steps see `INSTALL.md`.
For first-timer wrappee setup see `docs/ONBOARDING.md`.

## Onboarding status

Onboarding N/A is NOT applicable to this repo. A wrappee exists (Wiener Linien
OGD API plus Docker Desktop for PostGIS), so `docs/ONBOARDING.md` is mandatory
per the fleet onboarding standard. Do not mark this repo exempt.

## Two workflows

### Option A - Native dev (fastest iteration)

Best for Python and dashboard code changes. The MCP server also runs this way.

```powershell
# 1. Start PostGIS + observability in Docker (needed for the DB)
docker compose up -d db

# 2. Install deps once
uv sync --extra dev

# 3. Run the web backend with hot-reload
.\run_dev.ps1
# Dashboard: http://localhost:3080, backend: http://127.0.0.1:11170

# 4. Or run the fleet-standard backend directly
just serve
```

Native processes connect to the Docker DB via
`DATABASE_URL=postgresql://wienerlinien:wienerlinien@localhost:5433/wienerlinien`.

### Option B - Full Docker stack (closest to production)

Best for verifying compose wiring, Grafana, Loki, and the GTFS loader.

```powershell
# Start everything: db + frontend map + grafana + loki + promtail
docker compose up -d

# Map: http://localhost:3079, Grafana: http://localhost:3140
# Follow logs
docker compose logs -f frontend

# Fast restart after code changes (uses layer cache, about 10 s)
docker compose restart frontend

# Load or refresh GTFS data into PostGIS
docker compose run --rm -e GTFS_FORCE_REFRESH=1 gtfs-loader
```

Full rebuilds (`docker compose build frontend`) are only needed when
dependencies change. Never use `--no-cache` for plain code edits.

### MCP server (always native, never in Docker)

stdio transport needs direct process communication, so the MCP server runs on
the host even when everything else is in Docker:

```powershell
$env:DATABASE_URL = "postgresql://wienerlinien:wienerlinien@localhost:5433/wienerlinien"
uv run vienna-transit-mcp
# or: uv run python -m wienerlinien_mcp.server  (from src/ layout)
```

Claude Desktop config uses `python -m frontend.mcp_server.server` with
`PYTHONPATH=D:/Dev/repos/mywienerlinien` in older setups and
`wienerlinien_mcp.server:mcp` (`uv run vienna-transit-mcp`) in the current
`pyproject.toml` entry point. Both need the same `DATABASE_URL`.

## justfile recipes

Run `just` with no args to list recipes. The ones that matter daily:

| Recipe | Command | What it does |
|---|---|---|
| `just bootstrap` | `uv sync --extra dev` + `pre-commit install` | First-time setup |
| `just serve` | `uv run uvicorn server:app --host 127.0.0.1 --port 11170 --app-dir web_sota/backend` | Fleet backend on 11170 |
| `just run` | `uv run mywienerlinien` | Run the MCP/package entry point |
| `just test` | `uv run pytest tests/ -q` | Full test suite, quiet |
| `just lint` | `uv run ruff check .` | Repo-wide lint |
| `just fmt` | `uv run ruff check src/ --fix` + `uv run ruff format src/` | Auto-fix + format `src/` |
| `just fix` | `uv run ruff check . --fix --unsafe-fixes` + `format .` | Aggressive repo-wide fix |
| `just check-sec` | `uv run bandit -r src/` | Security audit |
| `just audit-deps` | `uv run safety check` | Dependency audit |
| `just mcpb-pack` | `mcpb/pack.ps1` | Wipe + fresh-copy `src/` to `mcpb/src/`, then pack the Claude Desktop bundle |
| `just clean` | remove `__pycache__` | Clear bytecode caches |

## Lint and test commands

```powershell
# Lint (scoped first for speed, then repo-wide)
uv run ruff check src/
uv run ruff check .

# Format check
uv run ruff format --check src/

# Type check (lenient config in pyproject.toml)
uv run mypy frontend/mcp_server/ --ignore-missing-imports

# Tests
uv run pytest tests/ -q
uv run pytest tests/test_departures.py -q   # single file while iterating
```

`pyproject.toml` sets pytest `testpaths = ["tests"]`, `asyncio_mode = "auto"`,
and ruff line-length 120. Pre-commit runs ruff before each commit; run
`just lint` before pushing so the hook has nothing to complain about.

## GTFS data note for developers

The first GTFS import takes 15-30 minutes and writes millions of rows
(stops, routes, trips, stop_times) into PostGIS. Later runs are incremental
unless `GTFS_FORCE_REFRESH=1`. Do not interrupt the loader mid-import; if you
must, drop and re-run rather than debugging a half-loaded schema. See
`docs/TROUBLESHOOTING.md` for staleness and schema symptoms.

## Repo layout cheat sheet

- `src/wienerlinien_mcp/server.py` - MCP entry (`vienna-transit-mcp`)
- `src/wienerlinien_mcp/tools/`, `prompts.py`, `resources.py` - MCP surface
- `web_sota/backend/server.py` - FastAPI backend (`server:app`, port 11170)
- `web_sota/src/` - Vite dashboard (port 10896)
- `frontend/app.py` - legacy Docker frontend (port 3079/3080)
- `docker-compose.yml` - db, frontend, loader, grafana, loki, promtail
- `tests/` - pytest suite
