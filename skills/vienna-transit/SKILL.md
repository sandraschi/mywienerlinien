---
name: vienna-transit
description: Query Vienna public-transport departures, journeys, and disruptions via the mywienerlinien MCP server.
---

# Vienna Transit skill

Use when the user asks about Vienna transit: departures, lines, disruptions, timetables, nearby stops, journey planning.

1. Resolve the stop first: `station_search` (fuzzy) or `nearby_stops` for coordinates.
2. Departures: `next_departures(station, max_results)`. Never invent times.
3. Disruptions: `traffic_alerts()` + `line_status(line)` before promising a route.
4. Planning: `journey_planner(from, to)` (A* multi-transfer, schedule-based).
5. Status/health: `server_status()`; cards: `show_departures_card`, `show_server_status_card`.
6. Wiener Linien publishes no live GPS: say "schedule-interpolated" when showing map markers.
