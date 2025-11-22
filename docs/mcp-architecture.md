# MCP Server Architecture - Dual Standard Setup

## Overview

We have a **dual-standard architecture** that supports both:
1. **FastMCP Server** (stdio transport) - For Claude Desktop MCP integration
2. **FastAPI Server** (HTTP transport) - For web UI and REST API

Both servers share the same backend code (database, API clients, data loaders).

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────┐
│                    Shared Backend                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │   Database   │  │ API Clients  │  │ Data Loader  │  │
│  │  (PostgreSQL)│  │ (Wiener Lin.)│  │   (GTFS)     │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────┘
           ▲                    ▲
           │                    │
    ┌──────┴──────┐      ┌──────┴──────┐
    │             │      │             │
┌───▼──────┐  ┌───▼──────▼──┐  ┌───▼──────┐
│ FastMCP  │  │   FastAPI   │  │  Web UI  │
│  Server  │  │   Server    │  │  (HTML)  │
│          │  │             │  │          │
│ stdio    │  │    HTTP      │  │  HTTP    │
│ transport│  │   transport  │  │  static  │
└──────────┘  └──────────────┘  └──────────┘
     │                │
     │                │
┌────▼────┐      ┌────▼────┐
│ Claude  │      │ Browser │
│ Desktop │      │  Users  │
└─────────┘      └─────────┘
```

## Transport Standards

### FastMCP Server (stdio)
- **Transport**: stdio (standard input/output)
- **Protocol**: MCP (Model Context Protocol)
- **Clients**: Claude Desktop, MCP Inspector
- **Port**: N/A (uses stdin/stdout)
- **Use Case**: AI assistant integration

### FastAPI Server (HTTP)
- **Transport**: HTTP/WebSocket
- **Protocol**: REST API + WebSocket
- **Clients**: Web browsers, mobile apps, API consumers
- **Port**: 3080 (configurable)
- **Use Case**: Web UI and API access

## Code Sharing Strategy

### Shared Modules
Both servers import from the same modules:

```python
# Shared by both servers
from data_loader import data_loader
from database import db
from vehicle_service import collect_vehicle_data
from disruption_alerts import disruption_monitor
```

### Server-Specific Code

**FastMCP Server** (`mcp_server/`):
- MCP tool implementations
- Pydantic models for MCP responses
- Middleware for MCP protocol
- stdio transport handling

**FastAPI Server** (`app.py`):
- REST API endpoints
- WebSocket handlers
- HTML templates
- Static file serving

## Running Both Servers

### Option 1: Separate Processes (Recommended)
```powershell
# Terminal 1: FastAPI web server
python frontend/app.py

# Terminal 2: MCP server (for development/testing)
python -m frontend.mcp_server.server
```

### Option 2: Single Process (Future)
Could use a process manager to run both, but they're independent:
- FastMCP uses stdio (no port needed)
- FastAPI uses HTTP (port 3080)
- No conflicts

## Claude Desktop Configuration

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

## Benefits of Dual Standard

✅ **Separation of Concerns**
- MCP tools optimized for AI assistants
- Web UI optimized for human users
- Different protocols for different use cases

✅ **Code Reuse**
- Same backend logic
- Same data sources
- Same business logic

✅ **Independent Deployment**
- Can update MCP server without affecting web UI
- Can scale independently
- Different release cycles

✅ **Best of Both Worlds**
- MCP: Natural language AI integration
- FastAPI: Rich web interface with real-time updates

## Is This a Good Idea?

**Yes!** This architecture provides:

1. **Flexibility**: Different transports for different clients
2. **Maintainability**: Clear separation between MCP and web code
3. **Scalability**: Can scale each server independently
4. **Compatibility**: FastMCP 2.13 stdio + FastAPI HTTP don't conflict
5. **Future-proof**: Easy to add more transports (e.g., gRPC) later

## Alternative Approaches Considered

### ❌ Single FastMCP Server with HTTP Transport
- Problem: FastMCP HTTP is for MCP-over-HTTP, not web pages
- Would lose web UI functionality
- Not suitable for serving HTML/JS

### ❌ Convert Everything to FastAPI
- Problem: No stdio transport for Claude Desktop
- Would require MCP proxy/adapter
- More complex than needed

### ✅ Dual Standard (Chosen)
- Best of both worlds
- Clean separation
- No compromises

## Next Steps

1. ✅ MCP server structure created
2. ✅ Add FastMCP dependency (in requirements.txt)
3. ✅ Fix imports and ensure code sharing works
4. ⏳ Test MCP server with Claude Desktop
5. ⏳ Test FastAPI server still works
6. ⏳ Document deployment process

## Status

**Dual Standard Setup: COMPLETE** ✅

- FastMCP server (`frontend/mcp_server/server.py`) - Ready for stdio transport
- FastAPI server (`frontend/app.py`) - Ready for HTTP transport  
- Shared backend imports working correctly
- All tools registered and middleware configured
- Dependencies installed (fastmcp>=2.13.0, pydantic>=2.5.0)

