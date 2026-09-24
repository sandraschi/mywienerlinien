# Tools - mywienerlinien

MCP surface (`src/wienerlinien_mcp/server.py`, transport stdio, server name
`vienna-transit`) plus the `web_sota` REST API (`web_sota/backend/server.py`).

## MCP tools (12)

Registered in `server.py` via `register_*` helpers. All return structured
dicts with `success` plus domain fields.

| # | Tool | Module | Purpose | Key params |
|---|---|---|---|---|
| 1 | `help` | `tools/help.py` | Explain available tools and Vienna transit basics | `topic` (optional tool or area name) |
| 2 | `server_status` | `tools/server_status.py` | Health of the MCP server: version, DB reachability, config | none |
| 3 | `list_cities` | `tools/cities.py` | List all configured transit cities and their status | none |
| 4 | `switch_to_city` | `tools/cities.py` | Switch the active city for subsequent queries | `city_code` (e.g. `VIE`) |
| 5 | `city_transit_stats` | `tools/cities.py` | Stop / route / trip counts and coverage for one city | `city_code` (optional, defaults to active) |
| 6 | `station_search` | `tools/stations.py` | Fuzzy station lookup by name fragment, German or English | `query`, `limit` (default 5) |
| 7 | `nearby_stops` | `tools/nearby.py` | Stops near a place name or coordinate pair (includes `nearby_stops_by_coordinates` variant) | `location` or `lat` + `lon`, `radius_m` |
| 8 | `next_departures` | `tools/departures.py` | Real-time departures for a stop from the OGD monitor API | `station`, `line` (optional), `count` (optional) |
| 9 | `traffic_alerts` | `tools/alerts.py` | Active disruptions from `/trafficInfoList` + `/newsList` | `line` (optional filter) |
| 10 | `line_status` | `tools/status.py` | Status of one line or the whole network (plus status variants) | `line` (optional; empty = system-wide) |
| 11 | `stop_timetable` | `tools/timetable.py` | Full schedule for a stop (plus per-line timetable variant) | `station`, `date` (optional), `line` (optional) |
| 12 | `journey_planner` | `tools/journey.py` | A* route with transfers over the GTFS graph | `origin`, `destination`, `departure_time` (optional) |

Related helper surface in `tools/routes.py` (`routes` info) feeds the
journey planner and line status tools; it is not a separate 13th tool.

Typical call chains: `station_search` then `next_departures`; `station_search`
both ends then `journey_planner`; `line_status` / `traffic_alerts` when a
route looks delayed.

## MCP prompts (5)

Registered in `prompts.py` via `register_prompts`. Each returns
`list[dict]` messages in `[{"role": "user", "content": "..."}]` form.

| Prompt | Helps with |
|---|---|
| `vienna_transit_guide` | System overview: U-Bahn / tram / bus / night bus, naming, fares, when to use each tool |
| `departure_checking_prompt` | Departure flow: identify station, call `next_departures`, format countdowns and delays |
| `journey_planning_prompt` | Journey flow: resolve both stations, call `journey_planner`, explain segments and transfers |
| `natural_language_transit_assistant` | Conversational templates ("how do I get to...", "when is the next...") with response style rules |
| `ai_smart_routing_helper` | Context-aware routing: time of day, tourist vs commuter, weather, proactive alternatives |

## MCP resources (5)

Registered in `resources.py` via `register_resources`. All are async and
return text (markdown or JSON-ready strings).

| URI | Content |
|---|---|
| `vienna-transit://network/overview` | Network structure: 5 U-Bahn lines, 30+ tram lines, buses, night buses, Zone 100 |
| `vienna-transit://stations/major` | Major hubs: Stephansplatz, Hauptbahnhof, Schwedenplatz, Karlsplatz, Praterstern, Westbahnhof, others |
| `vienna-transit://lines/metro` | Per-line routes, colors, frequencies, key stations; U5 under construction |
| `vienna-transit://operating-hours` | Regular hours (~05:00-00:30), night buses, peak windows |
| `vienna-transit://fares` | Single EUR 2.40, 24h EUR 8.00, weekly EUR 17.10, validation rules |

## REST endpoints (`web_sota/backend/server.py`)

Base: `http://127.0.0.1:11170`. Fleet-standard plus LLM proxy plus log buffer.

| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | Liveness probe (fleet-start `HealthPath`), returns `{"status": "ok"}` |
| GET | `/api/health` | Same liveness under the `/api` prefix |
| GET | `/api/status` | Service name, version `2.0.1`, uptime seconds |
| GET | `/api/skills` | Chat skill list: `vienna-departures`, `vienna-journey`, `vienna-disruptions` |
| GET | `/api/capabilities` | Name, version, backend port, route list, feature flags |
| GET | `/api/v1/diagnostics` | CUA-NSIS smoke surface: routes + python/platform info + errors array |
| GET | `/api/llm/discover` | Alias for providers ( chat UI calls this on mount) |
| GET | `/api/llm/providers` | Live probe of Ollama `:11434` and LM Studio `:1234`, with model lists |
| GET | `/api/llm/models` | Model map per provider derived from the probe above |
| GET | `/api/llm/onboarding` | Starter facts (no live vehicle positions, OGD per-stop departures) + recommended path |
| POST | `/api/llm/chat` | Backend LLM proxy; body `{"provider", "model", "prompt"}`; keys never leave the server |
| GET | `/api/logs` | Activity ring buffer entries (via `routes/logging.py` router) |
| GET | `/api/logs/stats` | Log counts by level/source |
| GET | `/api/logs/export` | Download logs |
| DELETE | `/api/logs` | Clear the buffer |
| POST | `/api/shutdown` | Orderly exit: returns 200 now, process exits after 500 ms (fleet launcher restarts) |

Legacy Docker frontend (`frontend/app.py`) additionally serves
`/api/status/summary`, `/api/traffic-info`, `/api/disruptions`,
`/api/v1/journey`, and a realtime WebSocket. Use the `web_sota` table above
for new dashboard work.

## Example call chains

Departures for an uncertain station name:

1. `station_search(query="Stephans")` resolves to `Stephansplatz` (plus RBLs).
2. `next_departures(station="Stephansplatz", count=5)` returns live countdowns.
3. If a line shows a delay, `line_status(line="U1")` explains it.

Trip between two places:

1. `station_search` for the origin and again for the destination.
2. `journey_planner(origin=..., destination=...)` returns segments, transfers, and total time.
3. `traffic_alerts(line=...)` for each leg if timing looks off.

City-level overview (multi-city Phase 4/6 surface):

1. `list_cities` shows configured cities and which one is active.
2. `city_transit_stats(city_code="VIE")` gives stop / route / trip totals.
3. `switch_to_city(city_code=...)` changes the active city for later calls.

Nearby discovery:

1. `nearby_stops(location="Schloss Schoenbrunn", radius_m=500)` for a place name.
2. `nearby_stops` with `lat` + `lon` when the caller already has coordinates.
3. Feed the best hit into `next_departures` or `stop_timetable`.

## Transport and error contract

- MCP transport is stdio: the server speaks JSON-RPC over stdout, so it must run as a plain host process (`uv run vienna-transit-mcp`), never inside `docker compose`.
- Every tool returns a dict with at least `success` (bool) and `message` (str). Failures carry the reason in `message` (e.g. unknown station, DB unreachable) rather than raising through the transport.
- Tools that need the DB (`station_search`, `journey_planner`, `stop_timetable`, city tools) report DB-unreachable explicitly when PostGIS on 5433 is down. They never synthesize transit data.
- Tools that need the live OGD API (`next_departures`, `traffic_alerts`, `line_status`) honor `WIENER_LINIEN_TEST_MODE`: when set, they return labeled test doubles for offline runs.
- REST follows the same honesty rule: `/api/health` and `/api/status` reflect the backend process only; they do not imply the DB or GTFS import is healthy. Use `server_status` (MCP) or row-count checks for that.
