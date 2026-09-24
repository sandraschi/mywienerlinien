# Configuration - mywienerlinien

Reference for every environment variable, port, and fleet-start field.
Copy `.env.example` to `.env` and fill in values before running.

## Environment variables

| Variable | Meaning | Default / example |
|---|---|---|
| `DATABASE_URL` | SQLAlchemy / asyncpg connection string for PostGIS. Used by web backend, GTFS loader, and native MCP server. | `postgresql://wienerlinien:wienerlinien@localhost:5433/wienerlinien` |
| `APP_ENV` | Runtime profile. `development` enables verbose logging and hot-reload; `production` tightens logging. | `development` |
| `WEB_PORT` | Port for the `web_sota` FastAPI backend (`server:app`). Read by `server.py` and `fleet-start.config.ps1`. | `11170` |
| `FRONTEND_PORTS` | Comma-separated list of allowed frontend origins for CORS. Backend builds `allow_origins` from this. | `10896,3079,3080` |
| `OPENWEATHER_API_KEY` | Optional key for Phase 5 weather integration. Empty means weather features return a not-configured notice. | empty |
| `GTFS_FORCE_REFRESH` | Set to `1` to force the GTFS loader to re-download and re-import on next run, even if feed is fresh. | `0` |
| `GTFS_REFRESH_DAYS` | Staleness threshold in days. Loader runs automatically when cached feed metadata is older than this. | `365` |
| `GTFS_ZIP_PATH` | Path to the Wiener Linien GTFS zip inside the loader context. In Docker this is a volume path. | `/app/scripts/gtfs_data/wienerlinien-gtfs.zip` |
| `GTFS_METADATA_DIR` | Directory holding GTFS metadata (feed date, hash, import marker). Loader checks this for staleness. | `/app/scripts/gtfs_data` |
| `GRAFANA_PASSWORD` | Admin password for the Grafana container. Empty falls back to the compose default; set it in real deployments. | empty (compose default) |
| `WIENER_LINIEN_TEST_MODE` | When set (e.g. `1`), realtime OGD calls are stubbed for offline tests. Leave empty for live API calls. | empty (live) |

Notes:

- No Wiener Linien API key is needed. The OGD monitor, trafficInfoList, and newsList endpoints are keyless since 2024.
- `DATABASE_URL` must point at port `5433` (Docker PostGIS), not the default `5432`, when running natively.
- The MCP server (`src/wienerlinien_mcp/server.py`) reads `DATABASE_URL` at import time. Set it before launching Claude Desktop or `uv run vienna-transit-mcp`.

## Ports

| Service | Port | URL / use |
|---|---|---|
| FastAPI backend (`web_sota`) | 11170 | `http://127.0.0.1:11170/api/health` |
| Vite dashboard (native `run_dev.ps1` / fleet frontend) | 10896 | `http://localhost:10896` |
| Docker map frontend | 3079 (host) | `http://localhost:3079` |
| Docker frontend container internal | 3080 | container-internal; native dev also uses 3080 for hot-reload |
| PostgreSQL + PostGIS (Docker) | 5433 | `localhost:5433`, db `wienerlinien`, user `wienerlinien` |
| Loki (logs) | 3193 | `http://localhost:3193` |
| Grafana (dashboards) | 3140 | `http://localhost:3140` |
| Ollama (optional LLM proxy target) | 11434 | `http://127.0.0.1:11434/v1` |
| LM Studio (optional LLM proxy target) | 1234 | `http://127.0.0.1:1234/v1` |

Port registry: `mcp-central-docs/operations/WEBAPP_PORTS.md`. Backend 11170 and dashboard 10896 are the fleet-claimed pair. Do not hardcode other ports; read `WEB_PORT` / `FRONTEND_PORTS` from the environment.

## fleet-start.config.ps1 fields

File: `fleet-start.config.ps1` at the repo root. `start.ps1` is fleet-standard and reads this hashtable.

| Field | Value in this repo | Meaning |
|---|---|---|
| `Name` | `mywienerlinien` | Fleet repo key. Must match the repo directory name. |
| `BackendPort` | `11170` | Port the launcher probes and clears before binding the backend. |
| `FrontendPort` | `10896` | Port the launcher probes for the Vite dashboard. |
| `HealthPath` | `/health` | Liveness probe path. Backend `server.py` serves both `/health` and `/api/health` with `{"status": "ok"}`. |
| `WebRoot` | `web_sota` | Directory holding the web stack (`backend/server.py` + `src/` dashboard). |
| `Backend.Kind` | `uvicorn` | Launcher starts a Uvicorn process. |
| `Backend.UvicornTarget` | `server:app` | ASGI target inside `web_sota/backend/`. Full invoke: `uv run uvicorn server:app --host 127.0.0.1 --port 11170 --app-dir web_sota/backend`. |
| `Backend.SyncExtras` | `@('dev')` | `uv sync` extras installed before launch (pytest, ruff, mypy, pre-commit). |
| `Backend.Env` | `@{ WEB_PORT = '11170' }` | Extra env injected at launch. Mirrors `.env.example`. |
| `Frontend.Kind` | `vite-npm` | Launcher treats the dashboard as a Vite app started with npm. |
| `Frontend.PackageManager` | `npm` | Package manager for the dashboard. |
| `Frontend.PortEnvVar` | `VITE_PORT` | Env var carrying the dashboard port to Vite. |
| `Frontend.ApiTargetEnv` | `VITE_API_TARGET` | Env var carrying the backend URL so the dashboard calls `127.0.0.1:11170` and not a hardcoded host. |

If you change `BackendPort`, update `WEB_PORT` in `.env`, `Backend.Env` in this file, and the ports table in this doc together. A mismatch shows up as a health-probe timeout.

## Setup order

1. Copy the template: `Copy-Item .env.example .env`.
2. Keep `DATABASE_URL` on port 5433 unless you moved PostGIS deliberately.
3. Set `WEB_PORT=11170` so `server.py`, `just serve`, and `fleet-start.config.ps1` agree.
4. Fill `GRAFANA_PASSWORD` on shared machines; leave it empty only for local throwaway stacks.
5. Add `OPENWEATHER_API_KEY` only if you need weather cards; transit tools do not read it.
6. Leave `GTFS_FORCE_REFRESH=0` for normal runs; set `=1` for one loader run, then set it back.

## Docker compose mapping

- `db` service publishes `5433->5432` so the host sees PostGIS on 5433 while the container listens on its default 5432. `DATABASE_URL` uses the host-side port.
- `frontend` (Docker map) publishes host 3079. The legacy app inside still thinks in terms of 3080; both appear in `FRONTEND_PORTS` so CORS accepts either.
- Grafana publishes 3140, Loki listens on 3193. Neither needs env vars in `.env.example` because their ports are fixed in `docker-compose.yml`.
- The `gtfs-loader` profile reads `GTFS_ZIP_PATH`, `GTFS_METADATA_DIR`, `GTFS_FORCE_REFRESH`, and `GTFS_REFRESH_DAYS` from the environment. It writes the zip and metadata into the `gtfs_data` named volume, not into the repo tree.
- Named volumes (`postgres_data`, `wienerlinien_data`, `gtfs_data`) survive `docker compose down`. This is deliberate: it preserves the 15-30 min GTFS import across restarts. Use `docker compose down -v` only when you intend to re-import from scratch.

## Per-client notes

- PowerShell terminal: `$env:DATABASE_URL = "postgresql://wienerlinien:wienerlinien@localhost:5433/wienerlinien"` lasts for that session only. Persist it in `.env` for repeat runs.
- Claude Desktop: the `env` block of the `vienna-transit` server entry needs the same `DATABASE_URL`. The Desktop client does not read your terminal env.
- Cursor IDE: uses the system Python env; install the package there (`python -m pip install -e .`) and set `DATABASE_URL` in the MCP server config, not just the shell.
- CI: `WIENER_LINIEN_TEST_MODE=1` plus a test Postgres URL keeps network-dependent tests hermetic. Never point CI at the dev volume with production GTFS data.

## See also

- `docs/ONBOARDING.md` - first-timer setup that consumes these vars.
- `docs/DEVELOPMENT.md` - native vs Docker runs that set them.
- `docs/TROUBLESHOOTING.md` - what breaks when they are wrong.
- `.env.example` - canonical template; this file explains it, the template defines it.

## Changing a port safely

1. Claim the new port via `mcp-central-docs/fleet-gate/claim_ports.py` so no other fleet repo collides.
2. Update `.env` (`WEB_PORT` / `FRONTEND_PORTS`), `fleet-start.config.ps1` (`BackendPort` / `FrontendPort` / `Backend.Env`), and `justfile` (`serve` recipe port).
3. Restart the backend and re-run the sanity check: `curl http://127.0.0.1:<port>/api/health` must return `{"status": "ok"}`.
4. Update the ports table at the top of this file so the next reader sees the truth.
