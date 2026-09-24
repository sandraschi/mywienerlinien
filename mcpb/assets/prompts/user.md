# Vienna Transit User Guide

## Getting Started

1. **Configure Settings**: Adjust timeout and cache settings as needed
2. **Find Stations**: Use station_search to locate stops by name
3. **Check Departures**: Get real-time departure information
4. **Plan Journeys**: Use journey_planner for route optimization

This guide covers everything the Vienna Transit MCP assistant can do: live departures, station search, trip planning, timetables, disruptions, nearby stops, multi-city support, and server health. Work through it in order the first time, then use the FAQ and troubleshooting sections as a reference.

## Installation and Setup

### Claude Desktop bundle (MCPB)

1. Install the `.mcpb` bundle for vienna-transit-mcp in Claude Desktop.
2. The server starts with stdio transport; no manual port handling is needed on desktop.
3. Two settings are exposed in the bundle manifest:
   - `timeout`: operation timeout in seconds, default 30. Raise it to 60 on slow connections.
   - `cache_duration`: how long API responses are cached, default 15 seconds. Lower it for fresher live data, raise it to reduce API load.

### Web and backend setup (optional)

The full app also ships a Vite dashboard and a FastAPI backend plus an optional Docker stack with map, PostGIS, and Grafana. Those are not required for the MCP assistant features in this guide. If you run the backend, the health endpoints `GET /health` and `GET /api/health` confirm liveness, and `GET /api/status` reports uptime and version.

### Environment notes

- `DATABASE_URL` points at Postgres when persistence is enabled; the assistant works without it for live queries.
- `GTFS_FORCE_REFRESH` and `GTFS_REFRESH_DAYS` control static schedule refreshes.
- Times from the assistant are quoted in Europe/Vienna local 24-hour format; raw API times are UTC under the hood.

## Core Features

### Finding Stations
```
Search by name: station_search("Karlsplatz")
Search with context: station_search("Central Station")
Fuzzy matching: station_search("stephansdom")
```

### Departure Information
```
Next departures: next_departures("Westbahnhof", limit=5)
Specific lines: next_departures("Karlsplatz", lines=["U1", "U2", "U4"])
Time window: next_departures("Schottentor", minutes=30)
```

Note: the canonical parameters are `station` (station name, fuzzy accepted) and `max_results` (1 to 10, default 5). The shorthand above shows intent; the assistant normalizes line filters and time windows before calling the tool.

### Journey Planning
```
Simple route: journey_planner("from: Westbahnhof", "to: Karlsplatz")
With preferences: journey_planner("from: Airport", "to: City Center", mode="fastest")
Avoid transfers: journey_planner("from: A", "to: B", max_transfers=0)
```

### Service Status
```
Check disruptions: line_status("U1")
All services: line_status()
Elevator status: line_status("elevator")
```

## Complete Tool Reference

Twelve tools plus routes reference info. Each entry lists what it does, its parameters, and Vienna-specific examples.

### 1. help - built-in documentation

Parameter: `topic` (optional, default "overview"). Tool-usage topics: overview, departures, stations, journey, timetable, alerts, status, examples. Vienna knowledge topics: vienna, wienerlinien, history. Technical topics: gtfs, data, displays, architecture.

Vienna examples:
- `help()` - first-run orientation and full tool list.
- `help("departures")` - how live departure boards work.
- `help("history")` - history of Vienna public transport for school projects or curious tourists.
- `help("wienerlinien")` - about Wiener Linien, the operator.
- `help("gtfs")` - what the GTFS schedule standard is and why the app needs millions of data points.

Use help whenever you want to learn rather than travel: company background, data standards, architecture, and usage examples.

### 2. server_status - health and freshness

No required parameters. Returns uptime, version, database connectivity, last GTFS refresh, and live feed reachability.

Vienna examples:
- "Is the system working? The times look wrong." - the assistant calls server_status first.
- Before a high-stakes answer (airport run, last train home), the assistant verifies freshness.
- "How fresh is your data?" - answered with the last-updated timestamp from server_status.

If data is stale, the assistant says so openly and labels subsequent times as scheduled-only.

### 3. list_cities - supported cities

No required parameters. Returns every configured city with city_code, city_name, country, timezone, language, enabled flag, data_loaded flag, and map center.

Vienna examples:
- "Which cities do you support?" - full list with status.
- A search for a non-Vienna place fails - the assistant checks list_cities to see whether another city context fits.
- "Compare Vienna with your other cities." - city_transit_stats per city after listing.

Vienna is the default city. Only cities reported as enabled with loaded data are usable.

### 4. switch_to_city - change active city

Parameter: `city_code` (lowercase identifier, for example "vienna").

Vienna examples:
- `switch_to_city("vienna")` - return home after exploring another city.
- "Now show me departures in the other city." - the assistant lists cities, switches, confirms, and re-runs the query.
- After switching, station names are re-resolved because the same name can exist in two cities.

The assistant always confirms the switch and states what changed: search, departures, timetables, and planning now resolve against the new city.

### 5. city_transit_stats - network statistics

Parameter: `city_code` (optional, defaults to the active city). Returns total stops, total routes, total scheduled trips, currently active vehicles, and last update timestamp.

Vienna examples:
- "How big is the Vienna network?" - 1,000+ stops, full U-Bahn, tram, bus, S-Bahn, and night coverage with counts.
- "How many vehicles are running right now?" - active vehicle count with timestamp.
- "Does the data look complete?" - stop, route, and trip totals plus last_updated.

Always read the last_updated value when freshness matters.

### 6. station_search - fuzzy station lookup

Parameter: `query` (station name fragment, German or English, abbreviations accepted).

Vienna examples:
- `station_search("Stephansplatz")` - exact cathedral square interchange (U1, U3).
- `station_search("Stefans")` or `station_search("stephansdom")` - partial and fuzzy forms that still resolve.
- `station_search("HBF")` - common abbreviation resolving to Hauptbahnhof (verify before use).
- `station_search("Westbahnhof")` - western rail station (U3, U6).
- `station_search("Hauptbahnhof")` - main station (U1, long-distance rail, S-Bahn).
- `station_search("Schwedenplatz")` - Danube canal interchange (U1, U4).
- `station_search("Karlsplatz")` - opera district mega-interchange (U1, U2, U4).
- `station_search("Schottentor")` - university tram hub (U2).
- `station_search("Praterstern")` - Prater access (U1, U2, S-Bahn).
- `station_search("Floridsdorf")` - northern U6 terminus with S-Bahn.
- `station_search("Siebenhirten")` - southern U6 terminus.
- `station_search("Flughafen Wien")` - airport rail station for flight days.
- `station_search("Central Station")` - English form resolving to Hauptbahnhof.

Results include official names and RBL stop codes. When several candidates match, the assistant lists them with RBL codes and asks you to pick one.

### 7. nearby_stops - stops around a point

Parameters: latitude, longitude, and an optional search radius in meters. A coordinates variant (`nearby_stops_by_coordinates`) is also available.

Vienna examples:
- "What is the closest station to my hotel near Naschmarkt?" - anchor with station_search("Naschmarkt"), then nearby_stops with your coordinates.
- Standing at Stephansdom with GPS: nearby stops within a few hundred meters, sorted by distance.
- "Which tram stops are near Belvedere palace?" - nearby_stops around the palace coordinates plus the D and O tram context.

Always note the radius used. Coordinates outside the active city get a clear message plus a city-switch offer.

### 8. next_departures - live boards

Parameters: `station` (fuzzy name accepted) and `max_results` (1 to 10, default 5). Returns line, destination, scheduled time, countdown minutes, delay minutes when known, platform when published, and vehicle_type (metro, tram, bus, nightbus).

Vienna examples:
- `next_departures("Stephansplatz", max_results=3)` - quick glance at the cathedral interchange.
- `next_departures("Westbahnhof", max_results=8)` - wide board at a major rail station.
- `next_departures("Karlsplatz", max_results=10)` then filter to U4 - all U4 departures toward Huetteldorf and Heiligenstadt.
- `next_departures("Hauptbahnhof", max_results=8)` - before a long-distance connection.
- `next_departures("Schwedenplatz", max_results=5)` - canal interchange evening check.
- `next_departures("Praterstern", max_results=5)` - Prater evening or Ferris wheel visit.
- `next_departures("Floridsdorf", max_results=5)` - northern commute start.
- Night check: late-night board showing nightbus N-lines with countdowns.

The assistant always names the matched official station and its RBL code so you can verify the right stop.

### 9. traffic_alerts - disruptions and news

Optional filters per implementation. Sources: Wiener Linien trafficInfoList (structured disruption records) plus newsList (editorial service news): construction, closures, detours, event service changes, and notices published as news.

Vienna examples:
- "Is the U1 running normally?" - traffic_alerts plus line_status("U1") in the same turn.
- "Weekend works on the U4?" - alerts narrate the closure, line_status gives the verdict.
- "Elevator outage at Karlsplatz?" - checked via status and alerts; outages published as news are relayed with wording and scope.
- "Marathon day detours?" - event-related changes with workaround routes.
- Pre-airport reliability check alongside journey_planner.

No published alert means "no alerts currently published", not a guarantee of perfection.

### 10. line_status - per-line verdict

Parameter: `line` (optional; for example "U1", "U4", "D", "13A"). No argument summarizes the whole network.

Vienna examples:
- `line_status("U1")` - red line Oberlaa to Leopoldau status.
- `line_status("U6")` - brown line Floridsdorf to Siebenhirten status.
- `line_status("D")` - ring tram corridor status.
- `line_status("N60")` - night bus status before a late trip.
- `line_status()` - full-network morning briefing for commuters.

Combine with traffic_alerts for the complete picture: narrative plus verdict.

### 11. stop_timetable - schedules and frequencies

Parameters: `station` plus optional line and schedule scope per implementation. Answers regular-schedule questions: first and last services, Sunday frequency, night boundaries.

Vienna examples:
- "When is the first U1 from Leopoldau on Sunday?" - scheduled timetable, labeled as scheduled.
- "How often does tram D run here evenings?" - frequency from the timetable.
- "Last train from Heiligenstadt tonight?" - last-service lookup.
- "Does the N66 stop here after 00:30?" - night boundary check (regular service about 05:00 to 00:30, night network 00:30 to 05:00).
- Airport early flight: first S-Bahn and CAT-corridor options from the timetable, then live confirmation via next_departures on the day.

Scheduled times are labeled scheduled; live times are labeled live. Never mix them silently.

### 12. journey_planner - door-to-door routing

Parameters: origin station, destination station, plus preference hints (fastest mode, transfer limits) per implementation. A-star multi-transfer routing over GTFS data across U-Bahn, tram, bus, S-Bahn, and night lines.

Vienna examples:
- Westbahnhof to Stephansplatz: U3 to Stephansplatz direct, or U3 plus one change depending on works.
- Hauptbahnhof to Flughafen Wien Bahnhof: S-Bahn airport corridor itinerary with live cross-check.
- Schoenbrunn (resolve via station_search, e.g. Schoenbrunn ULF stop area) to Praterstern: multi-leg with explicit transfer station.
- Floridsdorf to Siebenhirten: direct U6 brown line, no transfer needed.
- Ottakring to Simmering: direct U3 orange line end to end.
- Schwedenplatz home at 02:00: nightbus-filtered itinerary with sparse-frequency warning.
- Karlsplatz to Grinzing via Heiligenstadt: U4 north plus connecting tram or bus leg.

Both endpoints are resolved with station_search first when ambiguous. Every itinerary lists legs with line, boarding station, direction or destination, alighting station, and transfer notes with a 5 to 10 minute buffer assumption.

### 13. routes info - learn the network

Backed by the `routes` tool and static resources (network overview, metro lines, major stations, operating hours, fares). No live data; reference only.

Vienna examples:
- "Where does the U2 go?" - purple line Karlsplatz to Seestadt corridor with termini check.
- "What does tram D serve?" - Nußdorfer Strasse to Oper corridor highlights.
- "Which night buses exist?" - N-prefix lines such as N25, N38, N60, N66.
- "What do A-suffix buses mean?" - city bus numbering logic (13A, 59A).
- "How do S-Bahn airport connections work?" - corridor explanation, then journey_planner for your trip.

## Vienna Transit Lines

### U-Bahn (Metro)
- **U1**: Red line - Oberlaa ↔ Leopoldau
- **U2**: Purple line - Karlsplatz ↔ Seestadt
- **U3**: Orange line - Ottakring ↔ Simmering
- **U4**: Green line - Hütteldorf ↔ Heiligenstadt
- **U6**: Brown line - Floridsdorf ↔ Siebenhirten

There is no U5 in regular service. If you ask for U5, the assistant explains this and plans with operating lines instead.

### Key Tram Lines
- **1**: Schottentor ↔ Stefan Fadinger Platz
- **2**: Dornbach ↔ Friedrich-Engels-Platz
- **D**: Nußdorfer Straße ↔ Oper
- **O**: Raxstraße ↔ Ring

Full tram coverage includes lines 1, 2, 6, 18, 31, 38, 43, 44, 46, 49, 52, 60, 62, 65 through 68, 71, 74, 80, 82, 84, D, E2, and O. Ask routes info for any corridor.

### Night Lines (N prefix)

N6, N8, N25, N31, N35, N38, N41, N43, N46, N49, N54, N60, N62, N66, N68, N71, N75, N81, N82, N84, N85, N87, N88, N89, N90, N91, N95, N96, N97, N98, N99. Night network runs roughly 00:30 to 05:00 when regular service sleeps.

### Major Stations
- **Westbahnhof**: Main western train station
- **Südbahnhof**: Southern train connections
- **Franz-Josefs-Bahnhof**: City center station
- **Karlsplatz**: Major interchange
- **Schottentor**: University district
- **Stephansdom**: City center cathedral

Extended interchange guide: Stephansplatz (U1, U3), Karlsplatz (U1, U2, U4), Westbahnhof (U3, U6), Hauptbahnhof (U1, rail, S-Bahn), Praterstern (U1, U2, S-Bahn), Schwedenplatz (U1, U4), Schottentor (U2, trams), Floridsdorf (U6, S-Bahn), Siebenhirten (U6 south), Oberlaa (U1 south), Leopoldau (U1 north), Heiligenstadt (U4 north), Huetteldorf (U4 west).

## RBL Stop Codes

RBL codes are Vienna stop identifiers that disambiguate bays and directions sharing one name. The assistant surfaces them on first mention each turn (for example Stephansplatz RBL 101). When two RBLs share a name and the bay changes your answer, the assistant asks you to confirm direction. For journey planning, confirming the right RBL avoids boarding on the wrong side of an interchange.

## Tourist Playbook

Day-one orientation: ask for `help("overview")`, then locate your hotel with nearby_stops, then save three anchors: Stephansplatz, Karlsplatz, and your home station. Day-trip pattern: journey_planner from your home station to Schoenbrunn in the morning, live next_departures before each hop, traffic_alerts at lunch for afternoon works, night timetable check before dinner. Attraction pairings that work well: Stephansdom plus Karlsplatz opera quarter (U1 one stop), Belvedere plus Hauptbahnhof corridor, Schoenbrunn plus Westbahnhof (U4 and U3 combinations), Prater plus Praterstern (walk-up access), Naschmarkt plus Karlsplatz (short walk or one U stop). For groups, request max_results 8 to 10 so everyone sees options. For strollers and wheelchairs, ask about elevators via line_status and alerts before committing to an interchange.

## Commuter Playbook

Morning briefing pattern: line_status() for the network, next_departures for your home stop with max_results 5, traffic_alerts for your corridor. Evening pattern: departures before leaving the office, timetable check if leaving after 23:30. Disruption pattern: when your line is closed, ask for journey_planner alternatives immediately and pin the transfer station. Buffer rules: 5 to 10 minutes per transfer, more during works and events. Friday and event nights around stadiums (Huetteldorf corridor) and the city center deserve an alerts check.

## Night Travel Guide

Regular service runs about 05:00 to 00:30. The N-line night network covers about 00:30 to 05:00 with sparse frequencies. Weekend U-Bahn may run through the night in published windows - verify with stop_timetable, never assume. Night planning steps: resolve your boarding stop with station_search, check stop_timetable for the night boundary, run journey_planner for the full route, confirm with next_departures shortly before leaving, and keep a taxi fallback for missed connections. Key night corridors include N25, N38, N60, and N66 among the full N list above. After midnight, over-fetch departures (max_results 8 to 10) because the next usable option may be far out.

## Accessibility Guide

Many stations have elevators; coverage varies by line and construction phase. Ask the assistant to check line_status and traffic_alerts for elevator outages before interchanges with stairs-only risk. Wheelchair-accessible routing is available on request - say so explicitly and the planner preference is applied where implemented. Audio announcements run at major stations. If step-free access is essential, name your origin, destination, and the requirement in one message so the assistant checks status, alerts, and the itinerary together. Report outdated elevator data via server_status freshness plus the operator hotline below.

## Multi-City Guide

Vienna is home. To travel elsewhere: ask list_cities, pick an enabled city with loaded data, and confirm switch_to_city with the lowercase code. Re-enter station names after switching. Compare networks with city_transit_stats (stops, routes, trips, active vehicles, last update). Switch back to "vienna" when done. Cross-city trip planning in one itinerary is not supported; plan each city leg separately.

## Data Honesty: What the Assistant Cannot Do

Wiener Linien exposes no live GPS vehicle positions through this server. Map markers for vehicles are schedule-interpolated estimates, not sightings. "Where is my bus right now" is answered with next scheduled departures plus reported delays, never a fabricated position. Incidents come from trafficInfoList and newsList feeds; unpublished issues are invisible, so "no alerts published" is not a guarantee. Platforms are shown only when published. Prices and fares are reference info, not live data. The assistant states these limits plainly instead of guessing.

## Best Practices

### Accurate Station Names
- Use official station names when possible
- Include district numbers for clarity (e.g., "Karlsplatz U1/U2/U4")
- Check spelling for international users

Fuzzy search forgives a lot (Stephans, HBF, Central Station), but the assistant always confirms the matched official name and RBL. Confirm direction bays at big interchanges.

### Time Management
- Allow buffer time for transfers (5-10 minutes)
- Check service frequency during off-peak hours
- Plan for weekend service changes

Cross-check live departures with alerts on tight connections, and re-check boards a few minutes before boarding.

### Accessibility
- Many stations have elevators (check line_status)
- Wheelchair-accessible routes available
- Audio announcements at major stations

## Troubleshooting

### No Departures Found
- Verify station name spelling
- Check if station is in service
- Try nearby alternative stations

Extended: confirm the RBL bay and direction, check the night-service boundary (00:30 to 05:00 limited network), look at traffic_alerts for closures, verify feed health with server_status, and try the nearest interchange (Karlsplatz, Praterstern, Westbahnhof, Hauptbahnhof).

### Journey Planning Issues
- Ensure both origin and destination are valid
- Check for service disruptions
- Try different routing preferences

Extended: resolve each endpoint separately with station_search, relax transfer limits, check alerts for a severed corridor, and accept a partial answer (origin departures plus corridor guidance) when the full route cannot compute.

### Service Status Problems
- Check for planned maintenance
- Verify internet connectivity
- Contact Wiener Linien directly for urgent issues

Extended: compare line_status against traffic_alerts, check server_status for stale data, fall back to stop_timetable scheduled times labeled as scheduled-only, and add buffer time.

### Unknown or Ambiguous Station
- Strip generic words and retry the core name (for example "Stephansdome" to "Stephans").
- Try German and English variants (Hauptbahnhof versus Central Station, Donau versus Danube).
- Pick from the suggestion list with RBL codes instead of retyping blindly.
- Share coordinates or a landmark for a nearby_stops query.

### Wrong City Results
- Ask for list_cities and state which city you mean.
- Confirm switch_to_city with the lowercase code.
- Re-enter station names after switching.

### Stale or Suspicious Data
- Ask for server_status and read the last-updated timestamp.
- Compare live departures against stop_timetable scheduled times.
- Check station on-site displays as ground truth and allow extra buffer.

## Service Hours

- **Regular Service**: 5:00 AM - 12:30 AM
- **Night Service**: 12:30 AM - 5:00 AM (limited routes)
- **Weekend Adjustments**: Reduced frequency on Sundays
- **Holiday Changes**: Special schedules for holidays

Verify holiday and weekend specifics with stop_timetable; never rely on memory for exceptions.

## Emergency Contacts

- **Wiener Linien**: +43 1 7909 100 (24/7)
- **Emergency**: 112 (police, fire, ambulance)
- **Traffic Information**: ÖAMTC or ARBÖ for road conditions

## FAQ

**How do I find the right station name?** Use station_search with any fragment; confirm the official name and RBL code the assistant reports.

**What do countdown minutes mean?** Minutes until departure from now, computed live from schedule plus reported delay.

**What does delay_minutes mean?** Reported lateness; absent means on time or unreported, not a guarantee.

**Why is there no platform listed?** Platforms are published only for some stops; the assistant says "platform not published" rather than guessing.

**Can the assistant show my bus on a map?** Only as a schedule-interpolated estimate, never live GPS. Ask for next departures instead.

**How do I plan an airport trip?** Resolve Flughafen Wien Bahnhof with station_search, run journey_planner from your origin, cross-check traffic_alerts, and confirm with next_departures before leaving.

**How do I travel at 2am?** Ask for the night itinerary explicitly; the assistant uses stop_timetable plus journey_planner filtered to N-lines and warns about sparse frequency.

**How do I avoid transfers?** Say so; the planner applies a fewest-transfer preference where implemented, for example Floridsdorf to Siebenhirten direct on U6.

**What if my line is closed?** Ask for status plus alerts, then request a journey_planner workaround in the same conversation.

**Which lines serve Karlsplatz?** U1, U2, U4 plus trams and buses; confirm live details with next_departures at max_results 10.

**Where does the U1 run?** Oberlaa to Leopoldau (red line); check routes info for corridor detail.

**Is there a U5?** No U5 in regular service; the assistant routes you on operating lines.

**How do A-buses and N-buses differ?** A-suffix lines are daytime city buses (13A); N-prefix lines are night buses (N60).

**Can I get elevator status?** Yes via line_status and traffic_alerts; outages published as news are relayed with scope.

**What are RBL codes?** Vienna stop identifiers for bays and directions; they disambiguate interchanges.

**Which cities are supported?** Ask list_cities; Vienna is default and others depend on enabled, loaded data.

**How do I switch cities?** Confirm switch_to_city with the lowercase code, then re-enter station names.

**Why do results look like the wrong city?** Stale city context; list, switch, and re-resolve.

**How fresh is the data?** Ask server_status for the last-updated timestamp; stale data is labeled openly.

**What if times look wrong?** Report it; the assistant checks server_status, alerts, and falls back to scheduled timetable data.

**Can I plan for Sunday or holidays?** Yes with stop_timetable; frequencies differ, so verify rather than assuming weekday service.

**How much buffer should I allow?** 5 to 10 minutes per transfer, more during works, events, and late nights.

**Does the assistant handle S-Bahn and regional trains?** Yes within the GTFS network, including the airport corridor and suburban connections.

**Who do I call in an emergency?** 112 for emergencies, Wiener Linien +43 1 7909 100 for urgent operator issues.

**How do I learn the whole network?** Start with help("overview"), then routes info topics and the help vienna and wienerlinien chapters.

## Quick Command Cheat Sheet

Copy-paste starters for common situations. The assistant normalizes parameters before calling tools.

- Morning commute: "Next departures from Floridsdorf, and is the U6 running normally?" (next_departures plus line_status plus traffic_alerts.)
- Tourist hop: "How do I get from Stephansplatz to Schoenbrunn?" (station_search both ends, then journey_planner.)
- Airport run: "Fastest route from Westbahnhof to Flughafen Wien Bahnhof, check disruptions too." (journey_planner plus alerts plus status.)
- Night out: "Night buses from Schwedenplatz after 1am?" (stop_timetable boundary plus planner plus live board.)
- Weekend works: "Any closures on the U4 this weekend?" (line_status("U4") plus traffic_alerts.)
- New arrival: "Which cities do you support, and how big is the Vienna network?" (list_cities plus city_transit_stats.)
- Doubt: "These times look stale, check server health." (server_status, then scheduled fallback.)
- Learning: "Where does tram D go, and what is GTFS?" (routes info plus help("gtfs").)

## Glossary

- **RBL code**: Vienna stop identifier for bays and directions; confirms the exact boarding point.
- **countdown_minutes**: live minutes until departure, computed from schedule plus delay.
- **delay_minutes**: reported lateness; missing means on time or unreported.
- **vehicle_type**: metro (U-Bahn), tram, bus, or nightbus (N-line).
- **trafficInfoList**: structured Wiener Linien disruption records feeding traffic_alerts.
- **newsList**: editorial Wiener Linien service news feeding traffic_alerts.
- **GTFS**: General Transit Feed Specification, the schedule standard behind planning and timetables.
- **Schedule-interpolated**: estimated vehicle positions derived from timetables, not live GPS.
- **Interchange**: a station serving multiple lines, for example Karlsplatz (U1, U2, U4).
- **Night network**: N-prefix bus lines plus published overnight corridors running about 00:30 to 05:00.
