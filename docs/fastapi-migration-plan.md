# FastAPI Migration Plan

## Phase 1 – Foundations
- Replace Flask dependencies with FastAPI, Uvicorn, and python-socketio (ASGI).
- Restructure `frontend/app.py` to expose a FastAPI application and ASGI Socket.IO wrapper.
- Provide equivalent Jinja2 templating and static asset mounting.

## Phase 2 – Endpoint & Lifecycle Parity
- Port all REST endpoints (`/`, `/api/*`, `/data/*`, `/routes`) to FastAPI handlers.
- Integrate the existing GTFS bootstrap (`gtfs_manager.ensure_data_ready`) into the new startup path.
- Reimplement caching concerns (e.g., routes cache) in a framework-agnostic way.

## Phase 3 – Realtime & Background Services
- Migrate `websocket_manager` to the python-socketio ASGI model with async event handlers.
- Ensure live disruption broadcasts and update requests continue to function.
- Preserve background GTFS refresh scheduling post-migration.

## Phase 4 – Tooling & Tests
- Update Dockerfiles, compose files, and start scripts to launch Uvicorn instead of Flask.
- Refresh dependency lists and documentation.
- Adapt the test suite to FastAPI’s `TestClient` and extend coverage for new startup behaviour.

## Phase 5 – UI & Data Enhancements
- Deliver interactive line selection UI with search, type tabs, and multi-select support.
- Fetch GTFS-derived route geometry and stops via `/api/lines/{line}/route` for live map rendering.
- Provide `/api/lines/{line}` and `/api/lines/{line}/stations` endpoints for rich client metadata.
- Extend vehicle APIs and WebSocket updates to honour multi-line and vehicle-type filters.

## Observability & Operations
- Added structured logging for GTFS lookups, RBL derivation, and per-client vehicle streaming.
- Vehicle service exposes total vs filtered counts via `/api/vehicles` and WebSocket payloads.
- `/api/status` surfaces `vehicle_total` and aggregated filter metrics for Grafana dashboards.
- Documentation updated to cover the line selection UI and new GTFS-driven endpoints.

