# Changelog

All notable changes to mywienerlinien are documented here.

## [Unreleased] - 2026-09-24 (assfix deferred)

### Fixed

- **Tests green (86/86)**: pytest collection fixed (`pythonpath`, declared
  psycopg2/socketio doubles); `tests/mcp_server` retargeted from the legacy
  `frontend/mcp_server` tree to live `src/wienerlinien_mcp`; tool tests use the
  public `Client` API (the old `_tools` introspection passed vacuously).
- **Real bugs found by the new tests**: prompts returned `list[dict]` (FastMCP 3.4
  rejects it - now `str`); naive/aware datetime crash in departures; journey
  planner `KeyError 'id'` (RBL-to-GTFS stop-id resolver added); cities stats
  always-zero (`fetch_one` kwarg never existed); server_status always
  "disconnected" (raw SQL string); routes used SQLite `?`/`GROUP_CONCAT` on
  Postgres (named params + `STRING_AGG`); cities manager API mismatch
  (`list_cities()` never existed); legacy server import crash.
- **Pyright clean (62 -> 0)**: canonical `mcp.types.ToolAnnotations` import,
  FastMCP 3.4 middleware classes (enabled in server), dead beyond-top-level
  imports removed, service type hardening; abandoned tree excluded.
- **Webapp**: 12 pages (dashboard hero, departures, disruptions, lines, inbox,
  chat, tools, skills, apps, logs, settings, help) on live OGD data
  (departures/disruptions/news) + GTFS reference snapshots; Zustand LLM store;
  Tauri listen + HTTP fallback; biome + tsc green; production build verified.
- **CI**: windows runners, uv, strict pytest, frontend gates, pyright gate,
  actionlint clean; pre-commit with Biome + pyright local hooks (hook installed).
- **Plus**: `glama.json`, Prefab cards, shutdown tool/endpoint, skills dir,
  session injection (cursor/windsurf/copilot/opencode/antigravity),
  webhook receiver (fail-closed), `start.ps1` rewrite + delegating `start.bat`,
  renovate, `.gitattributes`, `llms.txt`/`llms-full.txt`, `docs/` stack,
  MCPB 3-4-100 prompts (system 4068w, user 4059w, 109 examples).

## [Unreleased] - 2026-09-23 (assfix)

### Fixed

- **CORS wide-open**: `allow_origins=["*"]` replaced with explicit origins + unconditional
  Tailscale/LAN/Tauri regex in `frontend/app.py` and `web_sota/backend/server.py`.
- **Deps**: FastMCP `>=3.1.0` bumped to `>=3.4.4,<4` (fleet floor); `fastapi` unpinned
  (`==0.110.2` blocked starlette 1.x); `uv.lock` regenerated (fastmcp 3.4.7, fastapi 0.141.1).
- **Ruff**: removed `S110`/`S112` from ignore (3 silent `except: pass` now log via
  `logger.exception`); added `T20` print-ban + per-file-ignores for scripts/tests/mcpb.
- **web_sota backend**: listens on registry port 11170 (was hardcoded 8000); added
  `/api/health`, `/api/status`, `/api/skills`, `/api/capabilities`, `/api/v1/diagnostics`,
  `/api/llm/discover|models|onboarding`, `POST /api/shutdown`; fixed 2 bare `except:`.
- **justfile**: added `serve`, `test`, `fmt`, `bootstrap`, `mcpb-pack` recipes.
- **CI**: `node-version` 20 -> 22.
- **Docs/context**: new `llms.txt`, `llms-full.txt`, `.env.example`, `.mcpbignore` (root),
  `.claude-plugin/plugin.json` + `hooks/hooks.json`, `.windsurfrules`, copilot instructions,
  `## Session Context` in `.cursorrules`; `reports/` + `*.mcpb` gitignored.
- **Dashboard**: hardcoded departures now badged SAMPLE DATA until wired to `/api`.

## [2.0.1] - 2026-08-04 (incidents pipeline)

### Fixed

- **Disruption monitor was dead**: it fetched the wrong OGD endpoints
  (`/trafficInfo` and `/news` - both 404; correct: `/trafficInfoList`,
  `/newsList`) and was never started (`start_monitoring()` had no call site).
  Now started in `initialize_app()`.
- **V1.4 payload mapping**: trafficInfos identify items by `name` (not `id`)
  and carry `references.lines` / `time.start|end` / German-date strings -
  previously every poll created duplicate alerts with timestamp ids and
  `fromisoformat` crashed on `DD.MM.YYYY HH:MM` (tz-aware vs naive datetime
  comparison). Rewritten mapping + tolerant datetime parser.
- Verified: monitor creates/updates real alerts (lift outages, S16/S48 line
  notices), `/api/traffic-info` returns 238 alerts, `/api/disruptions`
  serves active incidents. The OGD live API is used for incidents exactly as
  intended - vehicle positions remain schedule-interpolated.

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
