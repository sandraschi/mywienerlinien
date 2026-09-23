# Checking Departures - Best Practices

## When to Use
- User asks "when is the next [train/bus/tram]"
- User wants to know departure times from a station
- User is planning to catch a specific line
- User asks about delays or wait times

## How to Use
1. **Identify Station**: Use station_search if name is unclear
2. **Call Tool**: Use next_departures with station name
3. **Interpret Results**: 
   - Check countdown_minutes for urgency
   - Note delays (delay_minutes)
   - Consider vehicle_type (metro is usually fastest)
   - Show multiple options when available

## Response Format
- Start with the most immediate departure
- Include line, destination, and countdown
- Mention delays prominently if present
- Suggest alternatives if delays are significant
- Include platform info if available

## Example Queries
- "When's the next U-Bahn from Stephansplatz?"
- "Show me departures from Hauptbahnhof"
- "Is there a tram coming soon to Schwedenplatz?"
- "What buses leave from [station] in the next 10 minutes?"

