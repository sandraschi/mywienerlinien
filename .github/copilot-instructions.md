# mywienerlinien — Copilot instructions

Vienna Transit MCP server + web dashboard. Before starting work: call MCP tools
`next_departures` / `traffic_alerts` for live data (never invent departures).
Backend: `web_sota/backend/server.py` (port 11170, `GET /api/health`).
MCP entry: `src/wienerlinien_mcp/server.py` (stdio). Validate with
`uv run ruff check src/` and `uv run pytest tests/ -q`.
