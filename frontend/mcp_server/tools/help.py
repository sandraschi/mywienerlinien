"""Help tool for Vienna Transit MCP."""

from fastmcp import FastMCP


def register_help_tool(mcp: FastMCP) -> None:
    """Register the help tool with the MCP server."""

    @mcp.tool()
    async def help(topic: str = "overview") -> str:
        """Get help on using Vienna Transit MCP.

        Provides documentation, usage examples, and guidance for all available
        tools. Use this when you're unsure how to accomplish a task or want
        to discover available functionality.

        Args:
            topic: Help topic to display. Available topics:
                - overview: Available tools and getting started (default)
                - departures: How to check real-time departures
                - stations: Finding and searching for stations
                - journey: Trip planning between locations
                - alerts: Traffic disruptions and service changes
                - status: Server health and data freshness
                - examples: Common usage examples

        Returns:
            Formatted help text for the requested topic.

        Example:
            >>> await help("departures")
            # Checking Departures...
        """
        topics = {
            "overview": _help_overview,
            "departures": _help_departures,
            "stations": _help_stations,
            "journey": _help_journey,
            "alerts": _help_alerts,
            "status": _help_status,
            "examples": _help_examples,
        }

        topic_lower = topic.lower().strip()
        if topic_lower not in topics:
            available = ", ".join(sorted(topics.keys()))
            return f"Unknown topic: '{topic}'. Available topics: {available}"

        return topics[topic_lower]()


def _help_overview() -> str:
    return """# Vienna Transit MCP - Help Overview

## Available Tools

### Real-time Information
- **next_departures** - Get upcoming departures from any station
- **line_status** - Check for disruptions on specific lines
- **traffic_alerts** - View current service disruptions city-wide

### Search & Discovery
- **station_search** - Find stations by name (fuzzy matching)
- **nearby_stops** - Find stops near coordinates
- **help** - This help system

### Trip Planning
- **journey_planner** - Plan routes between stations

### Server Information
- **server_status** - Check API health and data freshness

## Quick Start

1. **Find a station**: `station_search("Stephans")` → finds Stephansplatz
2. **Check departures**: `next_departures("Stephansplatz")`
3. **Plan a trip**: `journey_planner("Stephansplatz", "Praterstern")`

## Tips

- Station names support partial matching: "HBF" finds "Hauptbahnhof"
- Departures show countdown in minutes
- Use `help("topic")` for detailed help on any topic

## Data Sources

- Real-time data: Wiener Linien Open Data API
- Static data: GTFS (General Transit Feed Specification)
- Updates: Real-time data refreshes every request, GTFS weekly
"""


def _help_departures() -> str:
    return """# Checking Departures

## Basic Usage

```
next_departures(station="Stephansplatz", max_results=5)
```

## Parameters

- **station** (required): Station name
  - Full name: "Stephansplatz", "Hauptbahnhof"
  - Partial: "Stephans", "HBF", "Schweden"
  - Common abbreviations supported

- **max_results** (optional): 1-10, default 5

## Response Fields

Each departure includes:
- **line**: Line identifier (U1, D, 13A, N25)
- **direction**: Final destination
- **countdown**: Minutes until departure
- **delay**: Delay in minutes (if any)
- **vehicle_type**: metro, tram, bus, nightbus
- **platform**: Platform/track number (if available)

## Vehicle Types

- **metro**: U1-U6 lines (underground)
- **tram**: Streetcar lines (1-71, D, O)
- **bus**: Regular bus lines (1A-98A)
- **nightbus**: Night services (N25-N75)

## Examples

```python
# Next 5 departures from Stephansplatz
next_departures("Stephansplatz")

# Next 10 departures from main station
next_departures("Hauptbahnhof", max_results=10)

# Partial name matching
next_departures("Schweden")  # finds Schwedenplatz
```
"""


def _help_stations() -> str:
    return """# Finding Stations

## Station Search

```
station_search(query="Stephans", limit=5)
```

## Parameters

- **query** (required): Search term
  - Full or partial station name
  - Case insensitive
  - Fuzzy matching enabled

- **limit** (optional): Max results, default 10

## Response Fields

Each station includes:
- **name**: Full station name
- **rbl**: RBL code (Wiener Linien identifier)
- **type**: Station type (metro, tram, bus, stop)
- **zone**: Fare zone (usually "100" for Vienna)
- **lat/lng**: Coordinates (if available)

## Station Types

- **metro**: U-Bahn stations
- **tram**: Tram stops
- **bus**: Bus stops
- **stop**: Generic stops (multiple types)

## Search Tips

- Use partial names for faster typing
- Common abbreviations: HBF (Hauptbahnhof), WBF (Westbahnhof)
- Search is case-insensitive
- Results sorted by relevance

## Examples

```python
# Find Stephansplatz
station_search("Stephansplatz")

# Fuzzy search
station_search("stephan")  # finds Stephansplatz, Stephansdom

# Find all stations containing "platz"
station_search("platz", limit=20)
```
"""


def _help_journey() -> str:
    return """# Trip Planning

## Basic Usage

```
journey_planner(
    from_station="Stephansplatz",
    to_station="Praterstern",
    departure_time="2025-01-15T14:30:00Z"  # optional
)
```

## Parameters

- **from_station** (required): Starting station name
- **to_station** (required): Destination station name
- **departure_time** (optional): ISO 8601 format, defaults to now

## Response Fields

- **from_station/to_station**: Resolved station names
- **total_duration_minutes**: Total journey time
- **transfers**: Number of line changes
- **segments**: Individual journey legs
- **estimated_cost**: Approximate fare

## Journey Segments

Each segment includes:
- **line**: Line to take
- **from_station/to_station**: Segment endpoints
- **departure_time/arrival_time**: Timing
- **duration_minutes**: Segment duration
- **vehicle_type**: Type of transport

## Tips

- Station names support partial matching
- If multiple routes exist, fastest is shown
- Transfers include walking time between platforms
- Night service routes shown when applicable

## Example

```python
journey_planner("Stephansplatz", "Schönbrunn")
# Returns: U1 to Karlsplatz, U4 to Schönbrunn
# Duration: ~15 minutes, 1 transfer
```

## Note

Journey planning uses GTFS schedule data. Real-time delays
are not currently factored into route suggestions.
"""


def _help_alerts() -> str:
    return """# Traffic Alerts & Disruptions

## Checking Line Status

```
line_status(line_name="U1")  # specific line
line_status()  # all lines
```

## Parameters

- **line_name** (optional): Filter by specific line
  - If omitted, returns system-wide status

## Status Levels

- **operational**: Normal service
- **disrupted**: Service affected (detours, delays)
- **suspended**: Service not running

## Severity Levels

- **low**: Minor delays, info only
- **medium**: Significant impact
- **high**: Major disruption

## Response Fields

- **line**: Affected line (if line-specific)
- **status**: Current status
- **severity**: Impact level
- **title**: Brief description
- **description**: Full details
- **affected_stations**: List of impacted stops
- **start_time/end_time**: Duration (if known)

## Common Disruptions

- Construction work
- Technical issues
- Events (concerts, matches)
- Weather conditions
- Accidents

## Examples

```python
# Check all disruptions
line_status()

# Check specific line
line_status("U6")

# Check tram line
line_status("D")
```
"""


def _help_status() -> str:
    return """# Server Status

## Checking Health

```
server_status()
```

## Response Fields

- **status**: Overall health (healthy, degraded, unhealthy)
- **api_status**: Wiener Linien API reachable
- **database_status**: PostgreSQL connected
- **data_freshness**: Age of GTFS data
- **cache_stats**: Cache performance
- **version**: Server version
- **uptime**: Time since last restart

## Status Meanings

### Overall Status
- **healthy**: All systems operational
- **degraded**: Some features limited
- **unhealthy**: Major issues

### API Status
- **connected**: Real-time data available
- **timeout**: Slow responses
- **unavailable**: API down

### Database Status
- **connected**: Full functionality
- **disconnected**: Limited to API-only features

## When to Check Status

- Before relying on real-time data
- If you get unexpected errors
- To verify data freshness

## Example Response

```json
{
  "status": "healthy",
  "api_status": "connected",
  "database_status": "connected",
  "gtfs_last_updated": "2025-01-10",
  "cache_hit_rate": "85%",
  "version": "1.0.0"
}
```
"""


def _help_examples() -> str:
    return """# Common Usage Examples

## Morning Commute Check

```python
# Find departures from your home station
next_departures("Währinger Straße", max_results=5)

# Check for any disruptions on your line
line_status("40")
```

## Planning a Trip

```python
# Step 1: Find the destination station
station_search("Rathausplatz")

# Step 2: Plan the journey
journey_planner("Stephansplatz", "Rathaus")

# Step 3: Check real-time departures
next_departures("Stephansplatz")
```

## Finding Nearby Options

```python
# Search for stations in an area
station_search("Mariahilf")

# Or use nearby_stops with coordinates
nearby_stops(lat=48.1985, lng=16.3471, radius=500)
```

## Checking for Problems

```python
# System-wide status
line_status()

# Server health
server_status()

# Specific line
line_status("U2")
```

## Night Service

```python
# Night bus departures
next_departures("Schwedenplatz")
# Look for lines starting with "N"

# Check night service status
line_status("N25")
```

## Quick Reference

| Task | Command |
|------|---------|
| Find station | `station_search("name")` |
| Get departures | `next_departures("station")` |
| Plan trip | `journey_planner("from", "to")` |
| Check disruptions | `line_status()` |
| Server health | `server_status()` |
| Get help | `help("topic")` |
"""

