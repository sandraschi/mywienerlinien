# Vienna Transit MCP Server

FastMCP 2.13 compliant MCP server for Vienna public transport information.

**Phase 3A Enhancement (2025-12-03)**: AI-powered natural language routing with real GTFS-based journey planning.

## Features

- ✅ FastMCP 2.13 conformance
- ✅ stdio transport (for Claude Desktop)
- ✅ 4 core tools: departures, station search, **enhanced journey planning**, service status
- ✅ **5 AI prompts** for natural language assistance
- ✅ **Real GTFS-based routing** with multi-leg journey support
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

### 4. `journey_planner` ⭐ ENHANCED
Plan optimal journey between Vienna stations with real GTFS routing.

**Phase 3A Enhancement**: Now uses actual GTFS data for route calculation!

**Parameters:**
- `from_station` (str): Origin station (partial match supported)
- `to_station` (str): Destination station (partial match supported)
- `departure_time` (str, optional): ISO format timestamp (defaults to now)

**Returns:** Journey plan with:
- Complete route segments (line, stops, times)
- Number of transfers required
- Total duration in minutes
- Estimated cost (€2.40 for Vienna)
- Multiple route options (direct vs. with transfers)

**Routing Algorithm:**
- Direct routes prioritized
- Single-transfer routes if no direct connection
- Considers actual GTFS schedule data
- Calculates realistic travel times based on vehicle type
- Includes 5-minute transfer buffer

## AI Prompts

The server provides 5 comprehensive prompts to guide Claude:

### 1. `vienna_transit_guide`
Overview of Vienna's transit system, station naming, and tool usage.

### 2. `departure_checking_prompt`
Best practices for checking departures and interpreting results.

### 3. `journey_planning_prompt`
Guidance for journey planning with transfers and timing.

### 4. `natural_language_transit_assistant` ⭐ NEW
Natural language patterns for conversational transit assistance:
- Common user phrases and responses
- Response style guidelines
- Context-aware suggestions
- Error handling templates
- Vienna-specific facts

### 5. `ai_smart_routing_helper` ⭐ NEW
Context-aware smart routing assistance:
- Time-of-day considerations (rush hour, late night)
- Journey type optimization (tourist, airport, shopping)
- Weather/seasonal recommendations
- Smart alternative suggestions
- Proactive travel tips

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



