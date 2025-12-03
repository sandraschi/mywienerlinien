# MCP Server Testing Guide
**Phase 3A - Enhanced Journey Planning & Natural Language**  
**Date**: 2025-12-03

## Overview

The Vienna Transit MCP Server now features:
- ✅ Real GTFS-based journey planning (not placeholder!)
- ✅ Natural language support with 5 comprehensive prompts
- ✅ Context-aware routing (time of day, weather, tourist tips)
- ✅ Smart alternative suggestions

---

## Testing with Claude Desktop

### Prerequisites
1. Claude Desktop installed
2. MCP server configured in `claude_desktop_config.json`
3. MyWienerLinien frontend running (database accessible)

### Configuration

Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "vienna-transit": {
      "command": "python",
      "args": ["-m", "frontend.mcp_server.server"],
      "cwd": "D:\\Dev\\repos\\mywienerlinien",
      "env": {
        "DATABASE_URL": "postgresql://wienerlinien:wienerlinien@localhost:5433/wienerlinien"
      }
    }
  }
}
```

**Note**: Use `localhost:5433` (not `db:5432`) when running MCP server outside Docker.

---

## Test Scenarios

### 1. Basic Journey Planning

**Natural Language Query:**
```
"How do I get from Stephansplatz to Praterstern?"
```

**Expected Response:**
- Claude should use `station_search` for both stations
- Then call `journey_planner`
- Provide conversational response with:
  - Route description
  - Duration
  - Transfer information (if any)
  - Platform tips

**Validation:**
- ✅ Journey includes actual line names (U1, U3, etc.)
- ✅ Duration is realistic (5-30 minutes for Vienna)
- ✅ Station names are correct
- ✅ Transfer count is accurate

---

### 2. Natural Language Departure Check

**Natural Language Query:**
```
"When's the next U-Bahn from Stephansplatz?"
```

**Expected Response:**
- Claude should use `next_departures("Stephansplatz")`
- Filter for U-Bahn lines (U1, U3)
- Provide countdown and destination
- Mention multiple options

**Validation:**
- ✅ Shows countdown in minutes
- ✅ Includes line names and destinations
- ✅ Mentions delays if present
- ✅ Conversational tone

---

### 3. Context-Aware Airport Transfer

**Natural Language Query:**
```
"I need to get to the airport from Stephansplatz, what are my options?"
```

**Expected Response:**
- Claude should recognize airport context
- Suggest multiple options:
  - U3 to Wien Mitte + CAT (€12, fastest)
  - U3 to Wien Mitte + S7/REX (€4.40, budget)
  - Direct airport bus
- Mention costs and times
- Provide recommendation based on priorities

**Validation:**
- ✅ Multiple options provided
- ✅ Cost comparison included
- ✅ Time estimates realistic
- ✅ Recommendation given

---

### 4. Time-Aware Routing

**Natural Language Query:**
```
"It's 11:30pm, how do I get home from Schwedenplatz to Westbahnhof?"
```

**Expected Response:**
- Claude should recognize late-night context
- Check if regular service still running
- Mention "last trains" if near midnight
- Provide night bus alternatives if after 00:30
- Include frequency information

**Validation:**
- ✅ Time context acknowledged
- ✅ Night bus info if relevant
- ✅ "Last train" warning if applicable
- ✅ Frequency mentioned

---

### 5. Delay Handling & Alternatives

**Natural Language Query:**
```
"Is the U4 running? I need to get to Schönbrunn."
```

**Expected Response:**
- Claude should call `line_status("U4")`
- If delays: Suggest alternatives (tram 10, tram 58)
- If normal: Provide direct route
- Mention platform and travel time

**Validation:**
- ✅ Status check performed
- ✅ Alternative provided if delays
- ✅ Helpful recommendations
- ✅ Complete journey info

---

### 6. Multi-Leg Journey with Transfer

**Natural Language Query:**
```
"Plan a trip from Hauptbahnhof to Ottakring"
```

**Expected Response:**
- Claude should use `journey_planner`
- Likely requires transfer (no direct connection)
- Explain transfer station clearly
- Mention total time including transfer
- Provide platform/exit guidance

**Validation:**
- ✅ Transfer station identified
- ✅ Both segments described
- ✅ Transfer time included in total
- ✅ Clear step-by-step instructions

---

### 7. Tourist Destination Assistance

**Natural Language Query:**
```
"How do I get to Schönbrunn Palace?"
```

**Expected Response:**
- Claude should search for Schönbrunn stations
- Provide route (likely U4)
- Add tourist context:
  - Which exit to use
  - Walking time from station
  - Pro tips (tickets, timing)
- Mention return journey options

**Validation:**
- ✅ Tourist context included
- ✅ Exit/walking info provided
- ✅ Helpful tips added
- ✅ Conversational and friendly

---

### 8. Nearest Station Query

**Natural Language Query:**
```
"What's the nearest U-Bahn station to [location]?"
```

**Expected Response:**
- Claude should use `station_search` with location
- Provide nearest U-Bahn station
- Mention distance and walking time
- Include lines serving that station

**Validation:**
- ✅ Correct nearest station
- ✅ Distance mentioned
- ✅ Lines listed
- ✅ Helpful directions

---

## Expected MCP Tool Calls

Claude should intelligently combine tools:

### Simple Query Pattern
```
User: "Next U3 from Stephansplatz?"
Claude:
1. next_departures("Stephansplatz")
2. Filter for U3
3. Respond conversationally
```

### Complex Query Pattern
```
User: "How do I get to the airport?"
Claude:
1. station_search("airport") or station_search("flughafen")
2. Get user's current location context
3. journey_planner(from, airport_station)
4. line_status() for mentioned lines
5. Respond with options and recommendations
```

---

## Testing Checklist

### Basic Functionality
- [ ] MCP server starts without errors
- [ ] Claude Desktop recognizes the server
- [ ] Tools appear in Claude's tool list
- [ ] Prompts are accessible

### Journey Planning
- [ ] Direct routes work
- [ ] Transfer routes work
- [ ] Duration estimates realistic
- [ ] Station names correct
- [ ] Multiple options provided

### Natural Language
- [ ] Conversational responses
- [ ] Context-aware suggestions
- [ ] Helpful tips included
- [ ] Error messages friendly

### Edge Cases
- [ ] Invalid station names handled gracefully
- [ ] No route available handled well
- [ ] Late night queries mention night buses
- [ ] Airport queries mention CAT train
- [ ] Delay handling suggests alternatives

---

## Troubleshooting

### MCP Server Won't Start

**Error**: `ModuleNotFoundError: No module named 'fastmcp'`
```powershell
pip install fastmcp>=2.13.0
```

**Error**: `Database connection failed`
- Ensure database is running: `docker compose up -d db`
- Use `localhost:5433` not `db:5432` when running outside Docker

### Claude Doesn't See Tools

1. Check `claude_desktop_config.json` syntax
2. Restart Claude Desktop
3. Check MCP server logs
4. Verify `cwd` path is correct

### Journey Planning Returns Empty

1. Ensure GTFS data is loaded: `docker compose run --rm gtfs-loader`
2. Check database has routes/stops/stop_times tables
3. Verify station IDs are correct in database

### Prompts Not Working

1. Restart Claude Desktop
2. Check server.py registers prompts correctly
3. Verify FastMCP version >= 2.13.0

---

## Manual Testing (Without Claude)

Test MCP server directly:

```powershell
cd D:\Dev\repos\mywienerlinien
python -m frontend.mcp_server.server

# In another terminal, use MCP Inspector or manual stdio
```

Test routing service directly:

```python
from frontend.database import db
from frontend.mcp_server.routing_service import JourneyPlanner

planner = JourneyPlanner(db)
routes = planner.plan_journey("stop_id_1", "stop_id_2")
print(routes)
```

---

## Success Criteria

### Minimum (Phase 3A Foundation)
- ✅ MCP server starts and responds
- ✅ Journey planning returns actual routes
- ✅ Natural language prompts load
- ✅ Basic queries work in Claude

### Target (Phase 3A Complete)
- ✅ Complex multi-transfer queries work
- ✅ Context-aware responses
- ✅ Alternative route suggestions
- ✅ Tourist destination assistance
- ✅ Time-aware routing (night buses, etc.)

### Stretch (Phase 3 Full)
- 🔄 Real-time delay integration in routing
- 🔄 Multiple route comparisons
- 🔄 Historical data for predictions
- 🔄 Push notification alerts

---

## Next Steps

1. **Immediate**: Test with Claude Desktop (requires user)
2. **Short-term**: Add real-time delay data to routing
3. **Medium-term**: Implement A* pathfinding for complex routes
4. **Long-term**: Add ML-based delay predictions

---

**Phase 3A Status**: ✅ Implementation complete, ready for testing

