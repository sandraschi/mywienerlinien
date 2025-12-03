"""Help tool for Vienna Transit MCP."""

from fastmcp import FastMCP


def register_help_tool(mcp: FastMCP) -> None:
    """Register the help tool with the MCP server."""

    @mcp.tool()
    async def help(topic: str = "overview") -> str:
        """Get help on using Vienna Transit MCP.

        Provides documentation, usage examples, educational content about
        Vienna's public transport system, and technical details about the
        underlying data systems.

        Args:
            topic: Help topic to display. Available topics:

                **Tool Usage:**
                - overview: Available tools and getting started (default)
                - departures: How to check real-time departures
                - stations: Finding and searching for stations
                - journey: Trip planning between locations
                - timetable: Stop timetable and schedule info
                - alerts: Traffic disruptions and service changes
                - status: Server health and data freshness
                - examples: Common usage examples

                **Vienna Transit Info:**
                - vienna: Vienna's public transport network overview
                - wienerlinien: About Wiener Linien (the company)
                - history: History of Vienna public transport

                **Technical Deep Dives:**
                - gtfs: The GTFS data standard explained
                - data: Why millions of data points are necessary
                - displays: The miracle of real-time station displays
                - architecture: How this MCP server works

        Returns:
            Formatted help text for the requested topic.

        Example:
            >>> await help("history")
            # Vienna Public Transport History...
        """
        topics = {
            # Tool usage
            "overview": _help_overview,
            "departures": _help_departures,
            "stations": _help_stations,
            "journey": _help_journey,
            "timetable": _help_timetable,
            "alerts": _help_alerts,
            "status": _help_status,
            "examples": _help_examples,
            # Vienna transit info
            "vienna": _help_vienna,
            "wienerlinien": _help_wienerlinien,
            "history": _help_history,
            # Technical deep dives
            "gtfs": _help_gtfs,
            "data": _help_data,
            "displays": _help_displays,
            "architecture": _help_architecture,
        }

        topic_lower = topic.lower().strip()
        if topic_lower not in topics:
            return _help_topics_list(topics)

        return topics[topic_lower]()


def _help_topics_list(topics: dict) -> str:
    """Return formatted list of all help topics."""
    return """# Vienna Transit MCP - Help Topics

## Tool Usage
- **overview** - Getting started and available tools
- **departures** - Real-time departure information
- **stations** - Finding and searching stations
- **journey** - Trip planning between locations
- **timetable** - Stop timetables and schedules
- **alerts** - Traffic disruptions and service changes
- **status** - Server health and data freshness
- **examples** - Common usage examples

## Vienna Transit Information
- **vienna** - Vienna's public transport network
- **wienerlinien** - About Wiener Linien (the company)
- **history** - 150+ years of Vienna transit history

## Technical Deep Dives
- **gtfs** - The GTFS data standard explained
- **data** - Why millions of data points matter
- **displays** - The miracle of real-time displays
- **architecture** - How this MCP server works

Use `help("topic_name")` to learn more about any topic.
"""


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


def _help_timetable() -> str:
    return """# Stop Timetable

## Getting a Full Day's Schedule

```python
stop_timetable(
    stop="Karlsplatz",
    line="U4",           # optional: filter by line
    day_type="weekday",  # weekday | saturday | sunday
    include_html=True    # generate HTML timetable
)
```

## Parameters

- **stop** (required): Stop name (fuzzy matching supported)
- **line** (optional): Filter to specific line
- **day_type** (optional): Schedule type
  - `weekday`: Monday-Friday (default)
  - `saturday`: Saturday schedule
  - `sunday`: Sunday/holiday schedule
- **include_html** (optional): Generate HTML output (default True)

## Response Fields

- **stop_name**: Resolved stop name
- **hours**: List of 24 hours, each with departures
- **total_departures**: Count for the day
- **first_departure/last_departure**: Service span
- **lines_serving**: All lines at this stop
- **html**: Formatted HTML timetable

## Understanding Day Types

Vienna transit runs **different schedules** by day:

| Day Type | Typical Pattern |
|----------|-----------------|
| Weekday | Rush hour peaks at 7-9 and 16-18 |
| Saturday | Reduced service, no rush peaks |
| Sunday | Least frequent, later start |

## Example: U4 at Karlsplatz

```
Weekday:  860 departures, first 05:00, last 00:30
Saturday: 758 departures, first 05:30, last 00:30
Sunday:   755 departures, first 06:00, last 00:30
```

## HTML Export

The generated HTML includes:
- Dark Vienna-themed styling
- Hour-by-hour timetable rows
- Color-coded line badges
- Summary statistics
- Mobile-responsive design
"""


# =============================================================================
# VIENNA TRANSIT INFORMATION
# =============================================================================


def _help_vienna() -> str:
    return """# Vienna's Public Transport Network

## Overview

Vienna operates one of the **world's most efficient** public transport systems,
consistently ranked in the top 5 globally for urban mobility. The network
carries over **900 million passengers annually**.

## Network Components

### U-Bahn (Metro) 🚇
- **5 lines**: U1, U2, U3, U4, U6 (U5 under construction)
- **109 stations**
- **83 km** of track
- Runs 05:00-00:30 (24h on weekends)
- ~2.5 minute frequency during peaks

### Straßenbahn (Trams) 🚊
- **28 lines** (Europe's 6th largest network)
- **1,000+ stops**
- **220 km** of track
- Historic Ring trams + modern low-floor vehicles
- Vienna never removed its trams (unlike most cities!)

### Autobus (Buses) 🚌
- **127 lines** (day service)
- **24 night lines** (Nachtbus N25-N86)
- Includes express lines and local connections

### S-Bahn (Commuter Rail) 🚈
- **9 lines** serving greater Vienna
- Operated by ÖBB (Austrian Federal Railways)
- Connects to surrounding regions

## Key Statistics

| Metric | Value |
|--------|-------|
| Annual passengers | 962 million (2023) |
| Daily passengers | ~2.6 million |
| Network length | 1,200+ km |
| Vehicles | 4,500+ |
| Employees | 8,500+ |
| Stops/Stations | 4,700+ |

## Fare System

Vienna uses a **zone-based** fare system:
- **Core Zone 100**: All of Vienna (single fare)
- **Annual Pass**: €365 (€1/day!)
- **24h/48h/72h tickets** for tourists
- **Climate Ticket**: All of Austria for €1,095/year

## Why Vienna Transit is Special

1. **Integrated Network**: One ticket for everything
2. **High Frequency**: Never wait more than 5 minutes
3. **24/7 Weekend Service**: U-Bahn runs all night Fri-Sun
4. **Accessibility**: 100% low-floor trams and buses
5. **Real-time Info**: Every stop has live displays
6. **Affordable**: €365 annual pass since 2012

Use `help("history")` to learn about the fascinating 150+ year history!
"""


def _help_wienerlinien() -> str:
    return """# Wiener Linien - Vienna's Transit Authority

## Company Overview

**Wiener Linien GmbH & Co KG** is the public transport operator of Vienna,
a subsidiary of **Wiener Stadtwerke** (Vienna City Works). It's one of
Europe's largest urban transport companies.

## History & Identity

- **Founded**: 1865 (as horse-drawn tramway)
- **Current form**: 1999 (merger of various operators)
- **Ownership**: 100% City of Vienna
- **Headquarters**: Erdbergstraße 202, 1030 Wien
- **Brand colors**: Red and white (Vienna's colors)

## Operations

### Fleet
- **500+ trams** (including historic and modern)
- **450+ buses** (diesel, hybrid, electric)
- **140+ metro trains** (V-Wagen, newest generation)
- All vehicles equipped with real-time tracking

### Staff
- 8,500+ employees
- Drivers, technicians, planners, customer service
- Major apprenticeship program
- One of Vienna's largest employers

### Infrastructure
- 5 metro lines + 1 under construction (U5)
- 28 tram lines
- 4 maintenance depots
- Control center in Erdberg

## Innovation & Technology

### Open Data Pioneer
Wiener Linien was one of Europe's **first transit agencies** to provide:
- Real-time API (OGD - Open Government Data)
- GTFS feeds (schedule data)
- Live vehicle positions
- Disruption feeds

### Digital Services
- **WienMobil App**: Official journey planner
- **Real-time displays**: At every stop
- **WiFi on vehicles**: Free internet
- **USB charging**: In newer vehicles

## Awards & Recognition

- **UITP Award** for innovation (multiple)
- **European Mobility Week** awards
- Consistently rated best public transport globally
- Model for other cities worldwide

## Contact & Support

- **Website**: wienerlinien.at
- **Service hotline**: +43 1 7909-100
- **Lost & found**: +43 1 7909-43850
- **Twitter/X**: @wiaborak (official mascot!)

## The Wiener Linien Mascot

**Wiaborak** - a purple creature combining Vienna's Lipizzaner horses
with public transport - is the beloved mascot appearing in campaigns
and on social media!
"""


def _help_history() -> str:
    return """# Vienna Public Transport History

## 150+ Years of Urban Mobility

Vienna's public transport history is a remarkable journey from horse power
to one of the world's most advanced systems.

---

## 🐴 The Horse Era (1865-1903)

### 1865: It Begins
- **First horse-drawn tramway** opens: Schottentor → Hernals
- Operated by "Wiener Tramway-Gesellschaft"
- Horses pulled wooden carriages on iron rails
- Revolutionary: faster and smoother than cobblestones!

### Growth
- By 1873: 23 lines operating
- Peak: 3,000 horses employed!
- Horses worked 4-hour shifts
- Stables throughout the city

---

## ⚡ Electrification (1897-1903)

### 1897: Electric Revolution
- First **electric tram** on the Ring
- Siemens & Halske technology
- Public amazed by "horseless carriages"

### 1903: Full Electric
- Last horse tram retired
- Vienna fully electrified
- One of first major cities to achieve this

---

## 🚃 The Stellwagen Era (Early 1900s)

### The Famous "Stellwagen"
- Horse-drawn omnibus predecessor to trams
- Name from "stellen" (to place/position)
- Used where rails couldn't go
- Beloved part of old Vienna culture

### Kulturgeschichte
- Featured in Viennese operettas
- Symbol of "Gemütlichkeit"
- Drivers called "Fiaker" later drove taxis

---

## 🚇 The U-Bahn Dream (1898-1978)

### Early Plans
- **1898**: First subway plans proposed
- **1912**: WWI interrupts planning
- **1937**: Nazi-era plans drawn up
- **1966**: Serious planning begins

### 1969: Construction Starts
- After decades of planning
- Massive infrastructure project
- Built under and around historic buildings

### 1978: U1 Opens! 🎉
- **February 25, 1978**: Reumannplatz → Karlsplatz
- Vienna finally has its metro
- Massive celebration

---

## 📈 Modern Expansion (1978-Present)

### U-Bahn Growth
| Year | Event |
|------|-------|
| 1978 | U1 opens |
| 1980 | U4 opens (follows the Wien River) |
| 1981 | U2 opens (later extended to Seestadt) |
| 1991 | U3 opens (longest line) |
| 1995 | U6 opens (light metro, former suburban) |

### U5: The Future (2026+)
- **First fully automated metro** in Austria
- Rathaus → Wienerberg
- Driverless operation
- Pink line color!

---

## 🕐 Real-Time Revolution (1990s-2000s)

### The Display Era
- **1990s**: First electronic displays appear
- GPS tracking introduced
- Countdown timers at stops

### 2000s: Open Data
- **2010**: Real-time API launched
- GTFS data made public
- Third-party apps flourish

---

## 🚊 Tram Renaissance

### Unlike Other Cities...
Vienna **never removed** its tram network!
- Paris: removed trams in 1937
- London: removed trams in 1952
- Most US cities: gone by 1960s
- Vienna: kept and modernized!

### Modern Trams
- **ULF (Ultra Low Floor)**: 1998, revolutionary design
- **Flexity**: 2018, newest generation
- 100% low-floor fleet planned

---

## Timeline Summary

```
1865 ─── Horse trams begin
    │
1897 ─── Electric trams arrive
    │
1903 ─── Full electrification
    │
1968 ─── U-Bahn construction starts
    │
1978 ─── U1 opens
    │
1995 ─── U6 completes basic network
    │
2010 ─── Real-time open data
    │
2024 ─── U2/U5 construction ongoing
    │
2026 ─── U5 opens (automated!)
```

Use `help("displays")` to learn about the real-time display miracle!
"""


# =============================================================================
# TECHNICAL DEEP DIVES
# =============================================================================


def _help_gtfs() -> str:
    return """# GTFS: The Global Transit Data Standard

## What is GTFS?

**GTFS** (General Transit Feed Specification) is a standardized format for
public transport schedules and geographic information. Created by Google
and TriMet (Portland) in 2005, it's now the **global standard**.

## The Two GTFS Types

### GTFS Static (Schedule Data)
Fixed schedules, stops, and routes:

| File | Contains |
|------|----------|
| `agency.txt` | Transit agency info |
| `routes.txt` | Transit lines |
| `trips.txt` | Individual vehicle trips |
| `stops.txt` | Station/stop locations |
| `stop_times.txt` | When each trip arrives at each stop |
| `calendar.txt` | Service patterns by day |
| `shapes.txt` | Route geometry |

### GTFS Realtime
Live updates via Protocol Buffers:
- **Vehicle Positions**: Where is the U4 right now?
- **Trip Updates**: Delays, cancellations
- **Service Alerts**: Disruptions, closures

## Vienna's GTFS Data

### Scale (approximate)
| Table | Rows |
|-------|------|
| `stops` | 4,700+ |
| `routes` | 150+ |
| `trips` | 100,000+ |
| `stop_times` | **3.7 million+** |
| `shapes` | 500,000+ points |

### Why So Much Data?

Each `stop_time` row represents:
> "Trip 12345 arrives at stop 678 at 08:23:00"

For **one day** on **one line**:
- U1 runs ~400 trips/day
- U1 has 24 stations
- = 9,600 stop_times just for U1 weekday!

Multiply by all lines, all days, all service variations...

## The Calendar Problem

Schedules vary by:
- **Day of week**: Weekday vs Saturday vs Sunday
- **Season**: Summer vs school year
- **Holidays**: Christmas, Easter different
- **Special events**: Ball season, Donauinselfest

GTFS handles this with `service_id`:
```
service_id: "WD_SCHOOL"  # Weekday during school
service_id: "WD_SUMMER"  # Weekday in summer
service_id: "SAT_NORMAL" # Regular Saturday
```

## How This MCP Server Uses GTFS

1. **Database**: GTFS loaded into PostgreSQL
2. **stop_timetable**: Queries stop_times + calendar
3. **journey_planner**: Uses trips + stop_times
4. **station_search**: Uses stops table

## GTFS Quality Matters

Good GTFS enables:
- ✅ Accurate journey planning
- ✅ Real-time prediction
- ✅ Multi-modal routing
- ✅ Accessibility information

Vienna's GTFS is **high quality**:
- Updated weekly
- Accurate coordinates
- Complete accessibility data
- Real-time feed synchronization
"""


def _help_data() -> str:
    return """# Why Millions of Data Points?

## The Scale Challenge

To display "U4 in 3 minutes" at Karlsplatz requires:

### Data That Must Exist:
1. Every stop Karlsplatz serves (6+ platforms)
2. Every trip that passes through
3. The scheduled time for each trip at each stop
4. Which trips run today (calendar)
5. Real-time position of actual vehicles
6. Delay calculations

## Let's Do The Math

### For One Station (Karlsplatz)

```
Lines serving: U1, U2, U4 + 5 trams + 3 buses
Trips per line per day: ~400
Stops per line at Karlsplatz: 2 (each direction)
Days in schedule: 365
Service variations: ~10

Total stop_times just for Karlsplatz:
  11 lines × 400 trips × 2 directions × 10 variations
  = 88,000 stop_time records
```

### For The Entire Network

```
4,700 stops × average 20 trips/hour × 20 hours × 365 days
= 686,200,000 potential data points per year!
```

Reality: ~3.7 million unique stop_times (compressed via patterns)

## Why Can't We Simplify?

### "Just store frequency!"
**Problem**: Frequency varies:
- Rush hour: every 2-3 minutes
- Midday: every 5 minutes
- Evening: every 7-10 minutes
- Night: every 15-30 minutes

### "Just calculate on the fly!"
**Problem**: Exceptions everywhere:
- Short turns (train doesn't go full route)
- Express services (skips stops)
- Diversions (construction)
- Special events

### "One schedule fits all!"
**Problem**: Day variations:
- Weekday rush ≠ Weekday off-peak
- Saturday ≠ Sunday
- Holiday ≠ Normal day
- Summer ≠ School year

## The Real-Time Layer

On top of static schedules, we need:

### Vehicle Tracking
- GPS position every 10-30 seconds
- 4,500 vehicles × 86,400 seconds/day
- = 388 million position updates/day!

### Prediction Updates
When a tram is late:
- Recalculate ALL downstream arrival times
- Update ALL connecting services
- Notify ALL affected displays

## Why This Matters

This massive data enables:

| Feature | Requires |
|---------|----------|
| "U4 in 3 min" | Scheduled times + real-time position |
| Journey planner | All stop_times + transfers |
| Disruption alerts | Real-time + schedule comparison |
| Accessibility | Stop metadata + vehicle info |

## Appreciation Time

Next time you see "3 min" on a display, remember:
- Terabytes of planning data
- Millions of scheduled times
- Thousands of real-time updates
- Decades of engineering

All so you can catch your train. 🚇
"""


def _help_displays() -> str:
    return """# The Miracle of Real-Time Displays

## An Underappreciated Wonder

Those countdown displays at every stop? They're actually
**engineering marvels** that we completely take for granted.

## What Seems Simple

You see: `U4 Hütteldorf — 3 min`

Behind that display:
1. Satellite talking to tram
2. Tram reporting position
3. Server calculating ETA
4. Prediction algorithm running
5. Display receiving update
6. All in real-time, 24/7

## History of Passenger Information

### Pre-Electronic Era (Until 1990s)

**Paper schedules only!**
- Posted at stops (got dirty, torn)
- Pocket timetables
- "The tram comes when it comes"
- No idea if service was disrupted

### First Electronic Displays (1990s)

**Vienna pioneers**:
- Dot-matrix LED displays
- Initially just scheduled times
- "But what if tram is late?"

### GPS Revolution (2000s)

**Real-time becomes real:**
- GPS installed in all vehicles
- Position updates every 30 seconds
- Actual countdown, not schedule!
- Vienna one of first European cities

### Modern Era (2010s-Now)

**Smartphone + everything:**
- Displays at every single stop
- App shows same data
- Open API for developers
- Integration with Google Maps

## How The System Works

### Vehicle Side
```
[GPS Receiver] → [Onboard Computer] → [Radio/4G] → [Control Center]

Every 10-30 seconds:
- Vehicle ID: 4523
- Line: U4
- Position: 48.2011, 16.3645
- Next stop: approaching Karlsplatz
- Door status: closed
- Passenger count: 127
```

### Server Side
```
Position data + Schedule → Prediction Algorithm

Factors considered:
- Current position
- Historical travel times
- Current traffic
- Dwell time patterns
- Weather (yes, really!)
```

### Display Side
```
[Control Center] → [Data Network] → [Display Controller] → [LED/LCD Panel]

Updates every 30-60 seconds
Handles 10+ lines per display
Multi-language support
Accessibility audio
```

## The Engineering Challenge

### Accuracy Problem
```
Scenario: U4 is at Längenfeldgasse
Display at Karlsplatz shows "4 min"

But:
- Signal timing varies
- Passenger boarding varies
- Weather affects speed
- Previous delay propagates
```

### The Prediction
```
Base travel time: 3:30
+ Buffer for variability: 0:15
+ Current delay: 0:20
= Predicted arrival: 4:05 → Display: "4 min"
```

### Cascade Updates
When U4 delays 2 minutes:
- Update Karlsplatz display ✓
- Update Kettenbrückengasse display ✓
- Update Pilgramgasse display ✓
- Update ALL downstream displays ✓
- Update ALL connecting lines displays ✓
- Update journey planner results ✓

**All within 30 seconds!**

## Vienna's Display Network

| Statistic | Value |
|-----------|-------|
| Displays installed | 4,000+ |
| Updates per second | 100,000+ |
| Data transmitted/day | 50+ GB |
| Accuracy target | 90% within 1 min |

## Why We Don't Notice

The **mark of good engineering**: it's invisible.

We notice:
- When display is wrong ❌
- When display is broken ❌

We don't notice:
- 4,000 displays working perfectly ✓
- Millions of accurate predictions ✓
- Decades of iteration ✓

## The Human Impact

Before real-time displays:
- "Is the tram coming?"
- "Should I wait or walk?"
- "Am I at the right stop?"
- Stress, uncertainty, wasted time

After real-time displays:
- "3 minutes, perfect"
- "Delayed, I'll take U3 instead"
- "Peace of mind"

**This is why public transport works.**

Next time: say a quiet thank you to the display. 🙏
"""


def _help_architecture() -> str:
    return """# MCP Server Architecture

## System Overview

This Vienna Transit MCP server bridges **AI assistants** with
**Vienna's public transport data**, making transit info conversational.

```
┌─────────────────────────────────────────────────────────────┐
│                     Claude / AI Assistant                    │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ MCP Protocol (stdio)
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                  Vienna Transit MCP Server                   │
│                                                              │
│   ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│   │  Tools   │  │Resources │  │ Prompts  │  │  Help    │   │
│   └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
│                                                              │
│   ┌─────────────────────────────────────────────────────┐   │
│   │              Business Logic Layer                    │   │
│   │    vehicle_service.py  │  data_loader.py            │   │
│   └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
           │                              │
           │ REST API                     │ SQL
           ▼                              ▼
┌─────────────────────┐      ┌─────────────────────┐
│   Wiener Linien     │      │     PostgreSQL      │
│   Real-time API     │      │    (GTFS Data)      │
└─────────────────────┘      └─────────────────────┘
```

## Data Sources

### 1. Wiener Linien Real-time API
- Vehicle positions
- Live departures
- Traffic alerts
- Disruption info

### 2. PostgreSQL + GTFS
- Static schedules
- Stop locations
- Route information
- Calendar/service patterns

### 3. Calendar.txt (File)
- Day-type mappings
- Service validity dates

## Tool Architecture

Each tool follows this pattern:

```python
@mcp.tool()
async def tool_name(params) -> ResponseModel:
    \"\"\"Detailed docstring for AI understanding.\"\"\"

    # 1. Validate input
    # 2. Query data sources
    # 3. Transform/filter results
    # 4. Return structured response
```

## Current Tools (9)

| Tool | Data Source | Purpose |
|------|-------------|---------|
| `help` | Static text | Documentation |
| `server_status` | All sources | Health monitoring |
| `station_search` | PostgreSQL | Find stops |
| `nearby_stops` | PostgreSQL | Geolocation |
| `next_departures` | Real-time API | Live arrivals |
| `traffic_alerts` | Real-time API | Disruptions |
| `line_status` | Real-time API | Service status |
| `stop_timetable` | PostgreSQL + calendar.txt | Schedules |
| `journey_planner` | PostgreSQL | Route planning |

## Response Models

All responses use **Pydantic models**:

```python
class DepartureResponse(BaseModel):
    station_name: str
    departures: List[Departure]
    timestamp: datetime
```

Benefits:
- Type safety
- Automatic validation
- JSON schema for AI understanding
- Self-documenting

## Caching Strategy

```
Request → Check Cache → [Hit] → Return cached
                     ↓ [Miss]
              Query Source → Cache Result → Return
```

Cache durations:
- Station data: 24 hours
- Real-time departures: 30 seconds
- Traffic alerts: 5 minutes
- Timetables: 1 hour

## Error Handling

```python
try:
    result = await query_data()
except APIError:
    return degraded_response()  # Cached/partial data
except DatabaseError:
    return api_only_response()  # Real-time only
except Exception:
    log_error()
    raise user_friendly_error()
```

## FastMCP Framework

Built on **FastMCP 2.13**:
- Async tool execution
- Resource discovery
- Prompt templates
- Stdio transport for Claude Desktop

## Future Improvements

1. **WebSocket real-time updates**
2. **SSE transport option**
3. **Trip caching/optimization**
4. **Multi-language support**
5. **Offline GTFS mode**
"""
