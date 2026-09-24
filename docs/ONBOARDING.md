# Onboarding - mywienerlinien

## What this is for

Vienna public transport in two places: a live map + departures dashboard and
a Claude Desktop MCP server (`vienna-transit`, 12 tools) that answers
natural-language transit questions. It plans GTFS-based journeys with A*
pathfinding, shows real-time departures per stop, and surfaces Wiener Linien
disruptions. It does not show live GPS vehicle positions, because Wiener
Linien publishes none; map markers are schedule-interpolated between stops.

## Cost and accounts (money / CC)

| Question | Answer |
|----------|--------|
| Do I need an account? | No for transit data. Wiener Linien OGD API (monitor, trafficInfoList, newsList) needs no key since 2024. Optional: OpenWeatherMap key only if you want Phase 5 weather features. |
| Free tier? | Yes. Transit data is free and unlimited under fair use (query needed stops only, 15 s minimum interval). OpenWeatherMap has its own free tier if you add a key. |
| Credit card required? | No. Neither Wiener Linien nor the local stack (Docker, PostGIS, Grafana) needs a card. |
| Ongoing cost? | Free. Local Docker resource usage only (disk for the GTFS import, RAM for Postgres). |
| Who bills? | Nobody for the default setup. OpenWeatherMap bills only if you exceed their free tier on a key you added yourself. |

## Prerequisites outside this repo

- Docker Desktop (Windows) - hosts PostGIS on 5433, Grafana, Loki, and the
  GTFS loader. Required even for native dev because the DB lives in Docker.
- Python 3.12+ and `uv` - for the native backend, dashboard dev, and the MCP server.
- Node + npm - for the Vite dashboard (`web_sota/src/`).
- `just` (via `winget install Casey.Just`) - runs the repo recipes (`just bootstrap`, `just serve`).
- A local LLM (Ollama on :11434 or LM Studio on :1234) - optional, only for
  the dashboard chat proxy. Transit tools work without it.
- No Wiener Linien account, no API token, no signup.

## First-timer setup steps

1. Clone and enter the repo:

   ```powershell
   git clone https://github.com/sandraschi/mywienerlinien
   cd mywienerlinien
   ```

2. Copy the env template and check the ports:

   ```powershell
   Copy-Item .env.example .env
   # Confirm WEB_PORT=11170 and DATABASE_URL points at localhost:5433
   ```

3. Start the database and install deps:

   ```powershell
   docker compose up -d db
   just bootstrap
   ```

4. Load GTFS data (first run takes 15-30 min, leave it alone):

   ```powershell
   docker compose run --rm -e GTFS_FORCE_REFRESH=1 gtfs-loader
   ```

5. Start the backend + dashboard:

   ```powershell
   just serve
   # Backend: http://127.0.0.1:11170/api/health
   ```

6. Optional native hot-reload dashboard: `.\run_dev.ps1` (port 3080).
7. Optional MCP in Claude Desktop: add server `vienna-transit` with command
   `uv`, args `--directory D:/Dev/repos/mywienerlinien run vienna-transit-mcp`,
   env `DATABASE_URL=postgresql://wienerlinien:wienerlinien@localhost:5433/wienerlinien`.
   See `INSTALL.md` for the JSON snippet.

## Pitfalls

- Docker Desktop D: bind-mount bug: on some machines Docker Desktop fails to
  create new D: bind mounts (`mkdir /run/desktop/mnt/host/d: file exists`).
  This repo avoids host bind mounts; state lives in named volumes
  (`postgres_data`, `wienerlinien_data`, `gtfs_data`). Do not add your own
  `volumes: ./...` entries to fix a path problem; you will re-trigger the bug.
- MCP server runs natively, not in Docker: stdio transport needs direct
  process communication. Do not `dockerize` the MCP entry; run
  `uv run vienna-transit-mcp` on the host with `DATABASE_URL` pointed at the
  Docker DB on 5433.
- GTFS first import takes 15-30 min: ~10M stop_times rows. An interrupted
  import leaves a half-loaded schema that looks healthy but returns empty
  journeys. Re-run with `GTFS_FORCE_REFRESH=1` rather than debugging partial
  data. See `docs/TROUBLESHOOTING.md` section 3.
- Port confusion 5432 vs 5433: local Postgres defaults to 5432; this repo's
  Docker PostGIS is on 5433. A `connection refused` almost always means the
  URL points at the wrong one or Docker Desktop is not running.
- No live vehicle GPS exists: if you expected moving-bus dots from real
  telemetry, reset expectations. The map interpolates scheduled positions;
  only departures and incidents are live.
- Rate limits: the OGD API is fair-use (15 s intervals, query needed stops).
  The code caches accordingly; hammering it from a script gets you throttled.

## Sanity check

- Backend liveness:

  ```powershell
  curl http://127.0.0.1:11170/api/health
  # expect: {"status":"ok"}
  ```

- Status with version and uptime: `GET 127.0.0.1:11170/api/status` returns
  `service: mywienerlinien-webapi`, `version: 2.0.1`.
- Map loads natively at `http://localhost:10722/` (`just map` or
  `.\start-map.ps1`; needs postgres on 5433 via `docker compose up -d db`)
  with departures visible for a known stop (e.g. Stephansplatz).
- MCP probe: run `help` (or `server_status`) in Claude Desktop; a live DB
  reports success, a missing DB reports it explicitly instead of fake data.

## Declared doubles

- Without Docker running (no DB on 5433), departures, journeys, timetables,
  and station search return explicit not-configured / DB-unreachable errors.
  Nothing fabricates transit data.
- `WIENER_LINIEN_TEST_MODE=1` stubs realtime OGD calls for offline tests;
  outputs under this flag are labeled test doubles, never live data.
- The dashboard before GTFS import shows honestly empty lists, not sample
  departures. No MOCK-until-onboarded layer is shipped in this repo; when the
  DB is empty the UI says so.
