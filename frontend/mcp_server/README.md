# Vienna Transit MCP Server

**Last Updated:** 2025-12-05  
**Status:** 🏆 SOTA Compliant (9.5/10)  
**Version:** 2.0.0  
**FastMCP:** 2.13.0+

FastMCP 2.13 compliant MCP server for Vienna public transport information with AI-powered natural language assistance.

---

## 🏆 SOTA Compliance

✅ **FastMCP 2.13** - Latest protocol support  
✅ **9 Tools** - All production-ready with real features  
✅ **5 Prompts** - Comprehensive AI guidance  
✅ **5 Resources** - Transit system reference data  
✅ **Real GTFS Routing** - A* pathfinding with multi-transfer support  
✅ **ML Predictions** - Random Forest delay forecasting  
✅ **Production Error Handling** - Graceful degradation  
✅ **Comprehensive Documentation** - Google-style docstrings

See `../../SOTA_CHECKLIST.md` for detailed compliance report.

---

## 🚀 Features

### Core Capabilities
- ✅ FastMCP 2.13 conformance
- ✅ stdio transport (for Claude Desktop)
- ✅ 9 production-ready tools
- ✅ 5 AI prompts for natural language assistance
- ✅ 5 resources for transit reference
- ✅ Real GTFS-based routing with A* algorithm
- ✅ ML delay predictions (Phase 3C)
- ✅ Multi-city support framework (Phase 4)
- ✅ Pydantic models for type safety
- ✅ Shared backend with FastAPI web app

### What Makes It SOTA
- **Real Features**: Actual GTFS routing, not mocks
- **ML Integration**: Delay predictions with Random Forest
- **Production Ready**: Comprehensive error handling
- **Database Integration**: PostgreSQL/PostGIS with graceful fallback
- **Graph Algorithms**: A* pathfinding for optimal routes
- **Real-time Data**: Live delays integrated into routing

---

## 📦 Installation

### Requirements
- Python 3.9+
- FastMCP 2.13.0+
- Pydantic 2.5.0+
- PostgreSQL 16+ (for full features)

### Install Dependencies

```powershell
# Install all dependencies
pip install -r ../requirements.txt

# Or install as package
cd ../..
pip install -e .
```

---

## 🎮 Usage

### ⚠️ Important: MCP Server Does NOT Run in Docker

**The MCP server runs natively (not containerized) because:**
- MCP uses stdio transport (not HTTP)
- Claude Desktop connects directly to Python process
- Docker would require complex stdio plumbing
- Native execution is simpler and more reliable

**What DOES run in Docker:**
- ✅ PostgreSQL database (port 5433)
- ✅ FastAPI web application (port 3079)
- ✅ Grafana (port 3140)

**What runs natively:**
- ✅ MCP server (stdio for Claude Desktop)

---

### 1. Run MCP Server (Native)

```powershell
# From project root
python -m frontend.wienerlinien_mcp.server

# Or with FastMCP CLI
fastmcp dev frontend.wienerlinien_mcp.server:mcp
```

### 2. Claude Desktop Configuration (Native Execution)

**Important:** 
- Entry point is `:mcp` (NOT `:main`)
- MCP server runs natively (not in Docker)
- Connects to Docker database on `localhost:5433`

Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "vienna-transit": {
      "command": "python",
      "args": ["-m", "frontend.wienerlinien_mcp.server"],
      "cwd": "D:\\Dev\\repos\\mywienerlinien",
      "env": {
        "DATABASE_URL": "postgresql://wienerlinien:wienerlinien@localhost:5433/wienerlinien"
      }
    }
  }
}
```

### 3. Test Installation

```powershell
# Test import
cd ../..
python test_mcp.py

# Test with database
$env:DATABASE_URL = "postgresql://wienerlinien:wienerlinien@localhost:5433/wienerlinien"
python -m frontend.wienerlinien_mcp.server
```

---

## 🛠️ Available Tools (9 Total)

### Essential Tools

#### 1. `help`
Get help with MCP tools and Vienna transit system.

**Parameters:**
- `topic` (str, optional): Help topic ("tools", "transit", "vienna")

**Returns:** Formatted help text

---

#### 2. `server_status`
Check MCP server health and configuration.

**Returns:** Server status, database connection, tool counts

---

### Search & Discovery Tools

#### 3. `station_search`
Find Vienna transit stations by name with fuzzy matching.

**Parameters:**
- `query` (str): Search query (partial match supported)
- `limit` (int, optional): Maximum results (1-20, default: 10)

**Returns:** List of matching stations with:
- Station name and ID
- Location (coordinates)
- Available lines
- Zone information

**Example:**
```
query: "stephans"
→ Returns: Stephansplatz (U1, U3)
```

---

#### 4. `nearby_stops`
Find stations near a geographic location.

**Parameters:**
- `latitude` (float): Latitude coordinate
- `longitude` (float): Longitude coordinate
- `radius_meters` (int, optional): Search radius (default: 500m)
- `limit` (int, optional): Maximum results (default: 10)

**Returns:** List of nearby stations with distances

---

### Real-time Information Tools

#### 5. `next_departures`
Get real-time departures from any Vienna station.

**Parameters:**
- `station` (str): Station name (partial match supported)
- `max_results` (int, optional): Maximum departures (1-10, default: 5)

**Returns:** List of departures with:
- Line and destination
- Planned and real-time departure
- Countdown in minutes
- Delays (if any)
- Platform/track information

**Example:**
```
station: "Stephansplatz"
→ Returns: U1 towards Leopoldau in 3 minutes
```

---

#### 6. `traffic_alerts`
Check Vienna transit service disruptions and alerts.

**Parameters:**
- `line_name` (str, optional): Filter by line (e.g., "U1")
- `severity` (str, optional): Filter by severity ("high", "medium", "low")

**Returns:** List of active alerts with:
- Affected lines and stations
- Disruption description
- Severity level
- Start and end times

---

#### 7. `line_status`
Get status of specific Vienna transit lines.

**Parameters:**
- `line_name` (str, optional): Line filter (e.g., "U1", "D", "13A")

**Returns:** Status information for lines:
- Operational status
- Current disruptions
- Service frequency
- Coverage information

---

### Schedule & Planning Tools

#### 8. `stop_timetable`
Get full schedule for a Vienna station.

**Parameters:**
- `station` (str): Station name
- `line` (str, optional): Filter by line
- `direction` (str, optional): Filter by direction
- `time_window_minutes` (int, optional): Time window (default: 60)

**Returns:** Complete timetable with:
- All departures in time window
- Scheduled times
- Directions and destinations
- Service type (weekday/weekend)

---

#### 9. `journey_planner` ⭐ Enhanced with A* Routing
Plan optimal journey between Vienna stations with real GTFS routing.

**Features:**
- Real A* pathfinding algorithm
- Multi-transfer support
- Real-time delay integration
- Direct route prioritization
- Realistic travel time calculations

**Parameters:**
- `from_station` (str): Origin station (partial match supported)
- `to_station` (str): Destination station (partial match supported)
- `departure_time` (str, optional): ISO format timestamp (defaults to now)

**Returns:** Journey plan with:
- Complete route segments (line, stops, times)
- Number of transfers required
- Total duration in minutes
- Estimated cost (€2.40 for Vienna zone)
- Multiple route options if available

**Routing Algorithm:**
- Direct routes prioritized (0 transfers)
- Single-transfer routes calculated
- A* algorithm for optimal path
- 5-minute transfer buffer included
- Real-time delays considered
- Realistic travel times by vehicle type

**Example:**
```
from: "Stephansplatz"
to: "Schönbrunn"
→ Returns: U1 to Karlsplatz, transfer to U4, 15 minutes total
```

---

## 🎯 AI Prompts (5 Total)

### 1. `vienna_transit_guide`
Comprehensive guide to Vienna's transit system:
- Network overview (U-Bahn, tram, bus)
- Station naming conventions
- Tool usage best practices
- Common use cases

### 2. `departure_checking_prompt`
Best practices for checking departures:
- How to interpret results
- Handling delays
- Multiple station queries
- Real-time vs. scheduled times

### 3. `journey_planning_prompt`
Guidance for journey planning:
- Transfer considerations
- Timing and buffers
- Direct vs. transfer routes
- Accessibility options

### 4. `station_search_prompt`
Tips for finding stations:
- Partial name matching
- German vs. English names
- Common abbreviations
- Disambiguation strategies

### 5. `real_time_prompt`
Real-time data handling:
- Interpreting delays
- Service disruptions
- Alternative routes
- Peak hour considerations

---

## 📚 Resources (5 Total)

1. **Network Overview** - Vienna transit system structure
2. **Major Stations** - Key interchange stations
3. **Metro Lines** - U-Bahn line details (U1-U6)
4. **Operating Hours** - Service times and schedules
5. **Fares** - Ticket prices and zones

---

## 🏗️ Architecture

### Dual Standard Design

This MCP server runs alongside the FastAPI web server:
- **FastMCP**: stdio transport for Claude Desktop (runs natively, NOT in Docker)
- **FastAPI**: HTTP transport for web UI (runs in Docker container)
- **Shared Backend**: Both use same PostgreSQL database (in Docker)

**Why MCP runs natively:**
- stdio transport requires direct process communication
- Docker stdio plumbing is complex and fragile
- Claude Desktop expects local Python process
- Native execution is simpler and more reliable

**Architecture:**
```
┌─────────────────┐      ┌──────────────────┐
│  Claude Desktop │─stdio─▶│  MCP Server    │
│   (UI)          │      │  (Native Python) │
└─────────────────┘      └──────────────────┘
                                   │ TCP
                                   ▼
                         ┌──────────────────┐
                         │  PostgreSQL      │
                         │  (Docker :5433)  │
                         └──────────────────┘
                                   ▲ TCP
                                   │
                         ┌──────────────────┐
                         │  FastAPI Web     │
                         │  (Docker :3079)  │
                         └──────────────────┘
                                   ▲ HTTP
                                   │
                         ┌──────────────────┐
                         │  Web Browser     │
                         └──────────────────┘
```

### Core Components

```
wienerlinien_mcp/
├── server.py                  # FastMCP server initialization
├── tools/                     # Tool implementations (9 tools)
│   ├── help.py               # Help tool
│   ├── server_status.py      # Status tool
│   ├── stations.py           # Station search
│   ├── nearby.py             # Nearby stops
│   ├── departures.py         # Real-time departures
│   ├── alerts.py             # Traffic alerts
│   ├── status.py             # Line status
│   ├── timetable.py          # Schedule lookup
│   └── journey.py            # Journey planning (A* routing)
├── prompts.py                # AI prompts (5 prompts)
├── resources.py              # Resources (5 resources)
├── models/                   # Pydantic models
│   ├── departure.py
│   ├── station.py
│   ├── journey.py
│   └── alert.py
├── routing_service.py        # A* pathfinding
├── graph_service.py          # Transit graph
├── realtime_service.py       # Real-time delays
└── utils.py                  # Shared utilities
```

### Shared Backend Modules

- `data_loader.py` - GTFS data loading
- `database.py` - PostgreSQL/PostGIS
- `vehicle_service.py` - Real-time tracking
- `disruption_alerts.py` - Service disruptions
- `prediction_service.py` - ML predictions (Phase 3C)
- `city_manager.py` - Multi-city support (Phase 4)

---

## 🧪 Testing

### MCP Inspector (Recommended)

```powershell
# Test with MCP Inspector
mcp-inspector python -m frontend.wienerlinien_mcp.server
```

### Manual Testing

```powershell
# Test import
python test_mcp.py

# Test with Claude Desktop
# Add to config and restart Claude
```

### Test Scenarios

See `../../docs/MCP_TESTING_GUIDE.md` for comprehensive test scenarios:
- Tool functionality tests
- Error handling tests
- Real-time data tests
- Journey planning tests
- Multi-city tests

---

## 🔧 Development

### Adding New Tools

1. Create tool file in `tools/` directory
2. Implement with `@mcp.tool()` decorator
3. Add Pydantic models in `models/` if needed
4. Register in `server.py`
5. Add prompt guidance in `prompts.py`
6. Update this README

### Code Quality

```powershell
# Linting
ruff check wienerlinien_mcp/

# Formatting
ruff format wienerlinien_mcp/

# Type checking
mypy wienerlinien_mcp/ --ignore-missing-imports
```

### Debugging

```powershell
# Enable debug logging
$env:LOG_LEVEL = "DEBUG"
python -m frontend.wienerlinien_mcp.server
```

---

## 📊 Performance

### Metrics
- **Tool Response Time**: < 100ms (database queries)
- **Journey Planning**: < 500ms (A* algorithm)
- **Real-time Updates**: 15-second cache
- **Database Queries**: Optimized indexes

### Caching
- Station lookups: 5 minutes
- Real-time data: 15 seconds
- GTFS data: On startup
- Graph construction: On demand

---

## 🐛 Troubleshooting

### Common Issues

#### 1. Database Connection Failed
```
Error: Could not connect to database
```
**Solution:** Ensure PostgreSQL is running on port 5433

#### 2. Import Errors
```
NameError: name 'List' is not defined
```
**Solution:** Fixed in latest version (use `list` or import `List`)

#### 3. Entry Point Error
```
AttributeError: module has no attribute 'main'
```
**Solution:** Use `:mcp` not `:main` in config

#### 4. No Results Returned
```
Journey planning returns empty
```
**Solution:** Ensure GTFS data is loaded and graph is built

---

## 📝 Version History

### 2.0.0 (2025-12-05) - SOTA Compliant
- ✅ 9 tools (was 4)
- ✅ FastMCP 2.13 compliance
- ✅ Fixed entry point (`:mcp`)
- ✅ Fixed type hints
- ✅ ML predictions (Phase 3C)
- ✅ Multi-city support (Phase 4)

### 1.5.0 (2025-12-03) - Phase 3A
- A* pathfinding implementation
- Real GTFS routing
- Multi-transfer support

### 1.0.0 (2025-01-15) - Initial Release
- 4 core tools
- Basic prompts
- FastMCP 2.12

---

## 📚 Additional Documentation

- `../../README.md` - Main project README
- `../../SOTA_CHECKLIST.md` - SOTA compliance details
- `../../docs/MCP_TESTING_GUIDE.md` - Comprehensive testing guide
- `../../docs/mcp-architecture.md` - Architecture details
- `../../DOCKER_DEV_GUIDE.md` - Development workflow

---

## 🤝 Contributing

1. Follow code quality standards (ruff, mypy)
2. Add comprehensive docstrings
3. Include Pydantic models for type safety
4. Add tests for new tools
5. Update this README

---

## 📄 License

Part of the Annoyinator Barnacle Projects collection.

**Data Source:** Wiener Linien - https://www.wienerlinien.at/open-data  
**License:** Creative Commons Attribution 4.0 International (CC BY 4.0)

---

**Vienna Transit MCP Server is SOTA compliant and production-ready!** 🏆✨
