# MCP Server Implementation Plan - FastMCP 2.13 Conformance

## Current Status

### Existing Codebase
- ✅ FastAPI web application with Wiener Linien API integration
- ✅ GTFS data loading and processing
- ✅ Database layer (PostgreSQL) with routes, stops, vehicles
- ✅ WebSocket support for real-time updates
- ❌ **No MCP server implementation yet**
- ❌ **No FastMCP dependency**

### Documentation
- ✅ PRD exists (`docs/ENHANCED-PRD-2025-08-10.md`) targeting FastMCP 2.10.0
- ⚠️ Needs update for FastMCP 2.13 conformance

## FastMCP 2.13 Compatibility Requirements

### Core Requirements

1. **MCP Specification 2025-06-18 Compliance**
   - Elicitation support for dynamic server-client communication
   - Output schemas for structured tool responses
   - Proper tool registration and validation

2. **Middleware Support** (introduced in 2.9.0, enhanced in 2.13)
   - Cross-cutting concerns: authentication, logging, error handling
   - Tool call middleware
   - Resource read middleware
   - Prompt request middleware

3. **Authentication** (enhanced in 2.11.0)
   - Automatic discovery
   - Programmatic OAuth flows
   - Session management

4. **Transport Mechanisms**
   - Support for StreamableHTTP transport (recommended for scalable deployments)
   - Standard stdio transport (for Claude Desktop)

5. **Tool Registration & Validation**
   - Proper tool decorators with type hints
   - Pydantic models for request/response validation
   - Contract testing support

## Implementation Plan

### Phase 1: Foundation Setup (Week 1)

**Dependencies:**
```python
fastmcp>=2.13.0          # Latest FastMCP with 2.13 features
pydantic>=2.5.0          # Data validation (required by FastMCP)
requests>=2.31.0         # Wiener Linien API client
```

**Tasks:**
1. Create new `mcp_server/` directory structure
2. Add FastMCP 2.13 to requirements
3. Create minimal MCP server with one tool (proof of concept)
4. Test with Claude Desktop

**Structure:**
```
mcp_server/
├── __init__.py
├── server.py              # Main FastMCP server
├── tools/
│   ├── __init__.py
│   ├── departures.py     # next_departures tool
│   ├── journey.py        # journey_planner tool
│   ├── status.py         # line_status tool
│   └── stations.py       # station_search tool
├── models/
│   ├── __init__.py
│   ├── departures.py     # Pydantic models
│   └── stations.py
├── middleware/
│   ├── __init__.py
│   ├── logging.py        # Request/response logging
│   └── error_handler.py  # Error handling middleware
└── config.py             # Server configuration
```

### Phase 2: Core Tools Implementation (Week 2-3)

**Tool 1: `next_departures`**
```python
@mcp.tool()
async def next_departures(
    station: str,
    max_results: int = 5
) -> List[Departure]:
    """Get next departures from Vienna transit station.
    
    Args:
        station: Station name (supports German/English, partial matching)
        max_results: Maximum departures to return (1-10, default: 5)
    
    Returns:
        List of departures with line, destination, time, delay, platform
    """
```

**Tool 2: `station_search`**
```python
@mcp.tool()
async def station_search(
    query: str,
    limit: int = 10
) -> List[Station]:
    """Find Vienna transit stations by name or location.
    
    Args:
        query: Search query (station name, partial match supported)
        limit: Maximum results to return (1-20, default: 10)
    
    Returns:
        List of matching stations with name, RBL, coordinates, type
    """
```

**Tool 3: `line_status`**
```python
@mcp.tool()
async def line_status(
    line_name: Optional[str] = None
) -> List[ServiceStatus]:
    """Check Vienna transit service status and disruptions.
    
    Args:
        line_name: Optional line name filter (e.g., "U1", "D")
    
    Returns:
        List of service status entries with line, status, disruptions
    """
```

**Tool 4: `journey_planner`**
```python
@mcp.tool()
async def journey_planner(
    from_station: str,
    to_station: str,
    departure_time: Optional[str] = None
) -> JourneyPlan:
    """Plan optimal journey between Vienna stations.
    
    Args:
        from_station: Origin station name
        to_station: Destination station name
        departure_time: Optional departure time (ISO format)
    
    Returns:
        Journey plan with routes, transfers, duration, cost
    """
```

### Phase 3: FastMCP 2.13 Features (Week 3-4)

**Middleware Implementation:**
```python
from fastmcp import FastMCP
from fastmcp.middleware import Middleware

# Logging middleware
@mcp.middleware()
async def logging_middleware(request, call_next):
    logger.info(f"Tool call: {request.tool_name}")
    response = await call_next(request)
    logger.info(f"Tool response: {response.status}")
    return response

# Error handling middleware
@mcp.middleware()
async def error_handler_middleware(request, call_next):
    try:
        return await call_next(request)
    except Exception as e:
        logger.error(f"Tool error: {e}", exc_info=True)
        return ErrorResponse(
            code=-32603,
            message="Internal error",
            data={"error": str(e)}
        )
```

**Output Schemas:**
```python
from pydantic import BaseModel, Field

class Departure(BaseModel):
    """Departure information with structured schema."""
    line: str = Field(..., description="Line name (e.g., U1, D, 13A)")
    destination: str = Field(..., description="Destination station")
    departure_time: datetime = Field(..., description="Scheduled departure time")
    countdown_minutes: int = Field(..., description="Minutes until departure")
    delay_minutes: Optional[int] = Field(None, description="Delay in minutes")
    platform: Optional[str] = Field(None, description="Platform number")
    
    class Config:
        json_schema_extra = {
            "example": {
                "line": "U1",
                "destination": "Leopoldau",
                "departure_time": "2025-01-15T14:30:00Z",
                "countdown_minutes": 3,
                "delay_minutes": 0,
                "platform": "1"
            }
        }
```

**Elicitation Support:**
```python
@mcp.tool()
async def next_departures(
    station: str,
    max_results: int = 5
) -> List[Departure]:
    # If station not found, use elicitation to ask for clarification
    if not station_exists(station):
        suggestions = fuzzy_search_stations(station)
        raise ElicitationRequired(
            message=f"Station '{station}' not found. Did you mean:",
            suggestions=suggestions[:5]
        )
    # ... rest of implementation
```

### Phase 4: Testing & Validation (Week 4-5)

**Contract Testing:**
- Validate all tools against MCP specification
- Test tool registration
- Verify output schemas
- Test error handling

**Integration Testing:**
- Test with Claude Desktop
- Test with MCP Inspector
- Verify middleware execution
- Test elicitation flows

**Performance Testing:**
- Response time targets: <2 seconds for 95% of calls
- API reliability: >98% success rate
- Tool accuracy: >95% station matching

## Migration Strategy

### Option 1: Parallel Implementation (Recommended)
- Keep existing FastAPI web app running
- Build MCP server as separate module
- Share data access layer (database, API clients)
- Gradual migration of functionality

### Option 2: Full Conversion
- Convert FastAPI app to FastMCP server
- Remove web UI components
- Focus entirely on MCP tools
- **Risk**: Loses web interface functionality

## Compatibility Checklist

- [ ] FastMCP 2.13.0+ installed
- [ ] MCP 2025-06-18 specification compliance
- [ ] Middleware implemented for logging/error handling
- [ ] Output schemas defined for all tools
- [ ] Elicitation support for ambiguous inputs
- [ ] Proper tool registration with type hints
- [ ] Pydantic models for all request/response types
- [ ] Session management (if needed)
- [ ] Contract tests passing
- [ ] Claude Desktop integration tested

## Next Steps

1. **Immediate**: Update PRD to reference FastMCP 2.13
2. **Week 1**: Set up MCP server structure, add FastMCP dependency
3. **Week 2**: Implement first tool (`next_departures`) with full 2.13 features
4. **Week 3**: Add remaining tools with middleware and schemas
5. **Week 4**: Testing and validation
6. **Week 5**: Documentation and deployment

## Resources

- [FastMCP Documentation](https://fastmcp.wiki/)
- [FastMCP Changelog](https://fastmcp.wiki/en/changelog)
- [MCP Specification](https://modelcontextprotocol.io/)
- [FastMCP Middleware Guide](https://fastmcp.wiki/en/servers/middleware)
- [FastMCP Authentication](https://fastmcp.wiki/en/servers/auth/authentication)

