# Journey Planning - Best Practices

## When to Use
- User wants to go from one place to another
- User asks for directions using public transport
- User wants to know travel time
- User needs to plan a trip with transfers

## How to Use
1. **Identify Stations**: Use station_search for both origin and destination
2. **Check Departure Time**: Ask if user has a specific time, otherwise use current time
3. **Call Tool**: Use journey_planner with both stations
4. **Explain Route**: Break down segments, transfers, and timing

## Response Format
- Start with total duration
- List each segment (line, stations, duration)
- Highlight transfers clearly
- Mention fare if available
- Suggest alternatives if multiple routes exist

## Vienna Transit Tips
- U-Bahn is usually fastest for longer distances
- Trams are good for shorter trips and scenic routes
- Transfers are free within the system
- Consider walking time between platforms
- Night buses replace regular service after midnight

## Example Queries
- "How do I get from Stephansplatz to Prater?"
- "What's the fastest way to the airport?"
- "Plan a trip from Hauptbahnhof to Schönbrunn"
- "I need to be at [location] by [time], when should I leave?"

