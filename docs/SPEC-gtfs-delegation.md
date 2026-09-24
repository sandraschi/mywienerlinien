# SPEC: GTFS delegation to gtfs-mcp + SQLite + rename to publictransport-mcp

- Status: draft (2026-09-24)
- Owner: Sandra Schipal
- Scope: `mywienerlinien` + `gtfs-mcp` (read-only changes to gtfs-mcp in Phase 1)
- Out of scope for tonight: Phase 0 (map verification on the current stack) is
  already in flight and is NOT blocked by this SPEC.

## 1. Problem

`mywienerlinien` (a pre-standards 2025 project) carries ~20 GTFS scripts plus a
bespoke Postgres schema that duplicates `gtfs-mcp`, which is newer, SOTA-shaped
(FastMCP 3.4, annotated tools, windows CI), and already SQLite-based. Fleet rule:
one capability lives in exactly one repo. GTFS feed infrastructure belongs to
`gtfs-mcp`; Vienna application logic (OGD realtime, RBL mapping, Leaflet map,
journey UX, Claude integration) belongs here.

## 2. Evidence (measured 2026-09-24, not assumed)

`gtfs-mcp` tool inventory (`services/gtfs_service.py`, 14 tools): `add_feed`,
`list_feeds`, `get_departures`, `get_stop_info`, `find_stops`, `get_stop_routes`,
`list_routes`, `web_search`, `status`, `list_presets`, `remove_feed`,
`depot_stats`, `export_feed`, `shutdown`. Transports: stdio + HTTP Streamable
(`/mcp`, default port 10913). Vienna is the verified default preset.
Storage: per-feed SQLite (`gtfs_mcp.db`, aiosqlite) + registry DB.

Critical schema finding (`core/persistence.py`): gtfs-mcp stores feed rows in a
generic `feed_rows` snapshot table — there is NO normalized transit schema (no
indexed stops/routes/trips/stop_times/shapes tables) and zero hits for
`shapes`, `journey`, `transfer`, `headway`, `RBL`, or `stop_code` anywhere in
`src/gtfs_mcp`. Consequences for delegation:

- ✅ Covered today: feed download/refresh, presets (Vienna verified),
  `find_stops`, `get_stop_info`, `get_stop_routes`, `list_routes`,
  static `get_departures`, feed CRUD/export.
- ❌ Missing for our consumers: shapes polylines (the map draws them),
  stop_times range serving, journey-planning inputs, RBL mapping
  (correctly absent — Wiener-Linien-specific, stays here as an adapter),
  realtime OGD (stays here — agency-specific by design).

## 3. Toolset completeness verdict (direct answer)

For a **GTFS feed manager**: complete and well-shaped. Discovery, presets,
CRUD, export, departures, stops, routes, depot stats — with proper annotations
and `## Return Format` / `## Examples` docstrings throughout. Better shaped
than our 13 hand-rolled tools were a day ago.

For a **transit application backend**: incomplete — no shapes, no journeys, no
realtime, no RBL. That is the correct split, not a deficiency: infrastructure
there, application here. Delegation therefore requires Phase 1 extensions, not
just a client rewrite.

## 4. Target architecture

```text
gtfs-mcp (sole writer)                publictransport-mcp (reader + Vienna layer)
─────────────────────                ────────────────────────────────────────────
OGD feed ──► download/parse ──► normalized SQLite snapshot
              refresh policy          (WAL, indexed stops/routes/trips/
              (Vienna = default)       stop_times/shapes/calendar)
                        │                         ▲
                        └──── shared file ────────┘
                                      │
                    map (Leaflet) + tools read snapshot (SQLAlchemy, same
                    dialect both sides); OGD realtime + RBL adapter + A*
                    journey planner stay here (agency-specific).
```

Why a shared SQLite snapshot instead of MCP-over-HTTP for everything: the map
renders thousands of stops/shapes per view — JSON-RPC per tile is the wrong
shape. MCP-over-HTTP (gtfs-mcp `/mcp`) stays the admin path (refresh triggers,
feed CRUD, depot stats); bulk reads go to the shared file. Single writer
(gtfs-mcp pipeline) avoids lock contention; readers are lock-free under WAL.

## 5. Phases

### Phase 0 — verify map on current stack (IN FLIGHT, not blocked)

Fresh feed load running; verify map/sidebar/cities on :10722; dashboard links
already re-pointed. Postgres container stays until Phase 3.

### Phase 1 — extend gtfs-mcp (shared benefit, upstream first)

1. Normalized snapshot writer: indexed `stops/routes/trips/stop_times/shapes/
   calendar/calendar_dates` tables in the shared SQLite file (bulk insert, not
   per-row ORM — the module's own docs warn 6M+ rows stall per-row ORM).
2. Serve shapes + stop_times ranges (new tools or snapshot columns — gtfs-mcp
   maintainer's call; our map needs polylines + per-stop departures).
3. Contract: snapshot path layout, WAL mode, refresh atomicity (write-temp +
   atomic replace so readers never see half a feed), version marker table.
4. Acceptance: our map renders from a gtfs-mcp-written snapshot with zero
   local GTFS code in the read path.

### Phase 2 — migrate our read layer to the snapshot

1. Point map + tools + services at the shared SQLite file (SQLAlchemy URL swap).
2. Dialect port (all Postgres-isms, catalogued 2026-09-24): `STRING_AGG` →
   `group_concat`, `INTERVAL '…'` → datetime arithmetic, `NOW()` →
   `datetime('now')`, `EXTRACT(DOW/HOUR…)` → `strftime`, `SELECT COUNT(*) AS
   count` fine, `:named` params fine in both, `text()` fine in both.
3. RBL adapter stays: `stop_code` lives in the snapshot (it is a stock GTFS
   column); the RBL→monitor-ID mapping logic stays here (agency-specific).
4. Keep A* journey planner here (needs graph build over snapshot — no gtfs-mcp
   change needed).
5. Acceptance: `pytest`, pyright, map + dashboard fully green on SQLite with
   postgres container stopped and removed.

### Phase 3 — drop our pipeline + Postgres

1. Delete `scripts/gtfs_*.py`, `load_gtfs_to_db.py`, `rbl_mapper.py`,
   `gtfs_manager.py` (frontend), `db/` Dockerfile + init scripts, compose
   `db`/`gtfs-loader` services (keep loki/grafana entries only if still wanted).
2. Remove `psycopg2-binary`, `asyncpg` (if unused elsewhere — verify), GTFS env
   vars; update `docs/`, `llms-full.txt`, ONBOARDING, fleet-start config.
3. Acceptance: `grep -ri postgres|psycopg|gtfs_manager` returns only historical
   docs/CHANGELOG hits; `docker compose config` has no db.

### Phase 4 — rename to publictransport-mcp

Explicit checklist (rename PR, not drive-by): GitHub repo rename (+ redirect),
local dir, `pyproject` name + package `wienerlinien_mcp` → `publictransport_mcp`
(+ all imports), MCP server name `vienna-transit` → keep per-city instances or
`public-transport`, fleet-start config, WEBAPP_PORTS.md, all docs + llms files,
Claude Desktop + `.mcpb` manifest + glama.json, CI paths, start scripts.
Multi-city support is already real code, so the name is honest. Do this LAST,
on a quiet tree, with the full gate suite green before and after.

## 6. Risks

- Mid-load DB (Sept 2026 refresh running): let it finish; it verifies Phase 0
  and seeds migration testing. Never interrupt a feed load — half a schema
  looks healthy and returns empty.
- Schema drift between our snapshot expectations and gtfs-mcp's writer:
  pinned by the Phase 1 contract + a snapshot self-test (`verify_server.py`
  extended with shape/stop_times probes).
- Realtime stays agency-specific forever: OGD monitor/disruptions/newsList +
  RBL adapter are Vienna code and must NOT migrate upstream.
- Rename churn: freeze feature work during Phase 4 week.

## 7. Open questions

1. gtfs-mcp maintainer: snapshot-table DDL — who authors it (us as PR, or them)?
2. Snapshot location: gtfs-mcp data dir with read path convention, or a fleet
   data dir? (Proposal: gtfs-mcp owns the file; we read via env path.)
3. Refresh cadence ownership: gtfs-mcp scheduler drives; our `GTFS_REFRESH_DAYS`
   env retires in Phase 3.
4. Port 10913 (gtfs-mcp HTTP): register/keep for the admin path in Phase 1.
