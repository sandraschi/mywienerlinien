# Vienna Public Transport Guide

## Overview
Vienna has an extensive public transport network operated by Wiener Linien:
- **U-Bahn (Metro)**: 5 lines (U1-U6) serving the city center and suburbs
- **Tram**: Extensive tram network with over 30 lines
- **Bus**: City buses and regional buses
- **Night Bus**: Night service (N-prefixed lines) operating after midnight

## Station Naming
- Stations often have multiple names or abbreviations
- "Hauptbahnhof" = "HBF" = Vienna's main train station
- "Stephansplatz" is the central square (not "Stephansdom" which is the cathedral)
- Partial names work: "Stephans" matches "Stephansplatz"
- German names are standard, but English works too

## Common Use Cases

### Checking Departures
When users ask "when is the next train/bus/tram", use `next_departures`:
- Ask for the station name if not provided
- Suggest checking multiple lines if user is flexible
- Mention delays if present
- Include vehicle type (metro/tram/bus) in response

### Finding Stations
Use `station_search` when:
- User mentions a location but not exact station name
- User asks "where is the station for X"
- Need to verify station spelling
- Finding nearby stations

### Journey Planning
Use `journey_planner` for:
- Route planning between stations
- Finding connections and transfers
- Checking travel time
- Planning trips with specific departure times

### Service Status
Use `line_status` to:
- Check for disruptions or delays
- Verify if a line is operating normally
- Get information about service changes
- Check system-wide status

## Best Practices
1. **Station Names**: Always use `station_search` first if station name is uncertain
2. **Real-time Data**: Departure times are live - mention this to users
3. **Delays**: Always check and report delays when present
4. **Multiple Options**: For departures, show 3-5 options when possible
5. **Context**: Consider time of day (night buses only run after midnight)
6. **Language**: Support both German and English queries

## Vienna-Specific Tips
- U-Bahn lines are color-coded (U1=red, U2=purple, U3=orange, U4=green, U6=brown)
- Ring tram (Line D) circles the historic center
- Airport connection: U3 to Wien Mitte, then CAT train
- Most stations have multiple platforms - check platform info when available
- Zone 100 covers most of Vienna - fare is typically €2.40 for single trip

