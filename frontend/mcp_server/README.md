# Vienna Transit MCP Server

FastMCP 2.13 compliant MCP server for Vienna public transport information.

## Features

- ✅ FastMCP 2.13 conformance
- ✅ stdio transport (for Claude Desktop)
- ✅ 4 core tools: departures, station search, journey planning, service status
- ✅ Middleware for logging and error handling
- ✅ Pydantic models for type safety
- ✅ Shared backend with FastAPI web app

## Installation

```powershell
pip install fastmcp>=2.13.0 pydantic>=2.5.0
```

## Usage

### Run MCP Server

```powershell
# From project root
python -m frontend.mcp_server.server

# Or with FastMCP CLI (if installed)
fastmcp dev frontend.mcp_server.server:mcp
```

### Claude Desktop Configuration

Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "vienna-transit": {
      "command": "python",
      "args": ["-m", "frontend.mcp_server.server"],
      "cwd": "D:\\Dev\\repos\\mywienerlinien"
    }
  }
}
```

## Available Tools

### 1. `next_departures`
Get next departures from a Vienna transit station.

**Parameters:**
- `station` (str): Station name (e.g., "Stephansplatz")
- `max_results` (int, optional): Maximum departures (1-10, default: 5)

**Returns:** List of departures with line, destination, time, delay

### 2. `station_search`
Find Vienna transit stations by name.

**Parameters:**
- `query` (str): Search query (partial match supported)
- `limit` (int, optional): Maximum results (1-20, default: 10)

**Returns:** List of matching stations

### 3. `line_status`
Check Vienna transit service status and disruptions.

**Parameters:**
- `line_name` (str, optional): Line filter (e.g., "U1", "D")

**Returns:** List of service status entries

### 4. `journey_planner`
Plan optimal journey between Vienna stations.

**Parameters:**
- `from_station` (str): Origin station
- `to_station` (str): Destination station
- `departure_time` (str, optional): ISO format timestamp

**Returns:** Journey plan with routes, transfers, duration

## Architecture

This MCP server runs alongside the FastAPI web server:
- **FastMCP**: stdio transport for Claude Desktop
- **FastAPI**: HTTP transport for web UI
- **Shared Backend**: Both use same database and API clients

See `docs/mcp-architecture.md` for details.

## Development

### Testing

```powershell
# Test with MCP Inspector (if available)
mcp-inspector python -m frontend.mcp_server.server

# Or test manually with Claude Desktop
```

### Adding New Tools

1. Create tool function in `tools/` directory
2. Register with `@mcp.tool()` decorator
3. Add Pydantic models in `models/` if needed
4. Register in `server.py`

## Requirements

- Python 3.9+
- FastMCP 2.13.0+
- Pydantic 2.5.0+
- Access to Wiener Linien API (via shared backend)



