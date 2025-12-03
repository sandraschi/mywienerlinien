"""MCP prompts for Vienna Transit MCP Server.

Prompts provide guidance to AI assistants on how to effectively use the Vienna
transit tools. They help Claude and other AI assistants understand context,
best practices, and common use cases.

MCP prompts are special resources that help AI assistants:
- Understand when to use each tool
- Interpret tool results correctly
- Provide helpful responses to users
- Follow best practices for transit queries

This module registers several prompts:
- vienna_transit_guide: Comprehensive guide to Vienna's transit system
- departure_checking_prompt: Best practices for checking departures
- journey_planning_prompt: Guidance for journey planning assistance

All prompts are registered with the FastMCP server and made available to
AI assistants through the MCP protocol.

Following FastMCP 2.12+ standards: prompts return list[dict[str, Any]] with
message format [{"role": "user", "content": "..."}].
"""

from typing import Any

from fastmcp import FastMCP


def register_prompts(mcp: FastMCP) -> list:
    """Register MCP prompts with the server.
    
    Prompts help AI assistants understand:
    - When to use each tool
    - How to interpret results
    - Common Vienna transit terminology
    - Best practices for queries
    
    Args:
        mcp (FastMCP): FastMCP server instance to register prompts with
    
    Returns:
        list: List of prompt function references to prevent garbage collection
    """
    prompt_refs = []
    
    @mcp.prompt()
    def vienna_transit_guide() -> list[dict[str, Any]]:
        """Guide for using Vienna public transport tools.
        
        This prompt helps AI assistants understand Vienna's transit system and
        how to effectively use the available tools to help users plan journeys,
        check departures, and find stations.
        
        Returns:
            list[dict[str, Any]]: Message format for MCP protocol
        """
        content = """# Vienna Public Transport Guide

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
"""
        return [{"role": "user", "content": content}]
    
    prompt_refs.append(vienna_transit_guide)

    @mcp.prompt()
    def departure_checking_prompt() -> list[dict[str, Any]]:
        """Prompt for checking departures effectively.
        
        Helps AI assistants understand how to check departures and interpret
        the results to provide helpful information to users.
        
        Returns:
            list[dict[str, Any]]: Message format for MCP protocol
        """
        content = """# Checking Departures - Best Practices

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
"""
        return [{"role": "user", "content": content}]
    
    prompt_refs.append(departure_checking_prompt)

    @mcp.prompt()
    def journey_planning_prompt() -> list[dict[str, Any]]:
        """Prompt for journey planning assistance.
        
        Guides AI assistants on helping users plan trips between stations,
        including transfers, timing, and route optimization.
        
        Returns:
            list[dict[str, Any]]: Message format for MCP protocol
        """
        content = """# Journey Planning - Best Practices

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
"""
        return [{"role": "user", "content": content}]
    
    prompt_refs.append(journey_planning_prompt)
    
    @mcp.prompt()
    def natural_language_transit_assistant() -> list[dict[str, Any]]:
        """Natural language templates for common transit queries.
        
        Phase 3A Enhancement: Helps AI assistants understand and respond to
        natural language transit queries with conversational, helpful responses.
        
        Returns:
            list[dict[str, Any]]: Message format for MCP protocol
        """
        content = """# Natural Language Transit Assistant

## Conversational Patterns

### Common User Phrases and How to Handle Them

**"How do I get to [place]?"**
- Use station_search to find the exact station name
- Then use journey_planner for route
- Respond with: "To get to [place], take the [line] from [current location] to [destination]. It takes about X minutes."

**"When's the next train/tram/bus?"**
- Ask for station name if not provided
- Use next_departures
- Respond with: "The next [vehicle] is in X minutes on [line] towards [destination]."

**"Am I close to a station?"**
- Ask for their location or use context
- Use station_search with location
- Respond with: "The nearest station is [name], about [distance] away."

**"Is there a delay on [line]?"**
- Use line_status
- If delays: "Yes, there are currently delays on [line]: [reason]. I recommend [alternative]."
- If normal: "No, [line] is running normally."

**"What's the fastest way to [place]?"**
- Use journey_planner
- Compare multiple routes if available
- Respond with: "The fastest way is [route description] taking X minutes."

**"Do I need to transfer?"**
- Implied in journey planning
- If transfers: "Yes, you'll need to transfer at [station]. Total journey: X minutes."
- If direct: "No transfers needed! Direct line [X] gets you there in Y minutes."

## Response Style Guidelines

### Be Conversational
- ❌ "Journey duration: 15 minutes. Transfers: 1."
- ✅ "Your trip will take about 15 minutes with one quick transfer at Karlsplatz."

### Provide Context
- ❌ "U3 departs at 14:35."
- ✅ "The next U3 towards Simmering leaves in 5 minutes (14:35) from platform 1."

### Anticipate Needs
- ✅ "The U1 is in 3 minutes, but if you miss it, the next one is in 7 minutes."
- ✅ "There's a slight delay on U4, so I'd recommend taking the tram instead."

### Be Helpful
- ✅ "That's a long walk! The 13A bus stops right near Schönbrunn and runs every 10 minutes."
- ✅ "Pro tip: Stay on the left side for the best view of the Danube!"

## Natural Language Examples

### Example 1: Getting to the Airport
User: "I need to get to the airport"
Assistant:
1. Search for "airport" or "Flughafen" stations
2. Use journey_planner
3. Response: "To get to Vienna Airport, take the U3 to Wien Mitte, then catch the CAT (City Airport Train). Total time: about 25 minutes. The CAT costs €12 but it's the fastest option!"

### Example 2: Checking Next Departure
User: "when's the next train from stephansplatz"
Assistant:
1. Use next_departures("Stephansplatz")
2. Response: "At Stephansplatz, the next U1 towards Leopoldau is in 2 minutes, and the U3 towards Ottakring is in 4 minutes. Where are you heading?"

### Example 3: Explaining Transfers
User: "how do i get from hauptbahnhof to prater"
Assistant:
1. Use journey_planner
2. If transfer needed: "From Hauptbahnhof, take the U1 north towards Leopoldau. After 3 stops (about 5 minutes), get off at Praterstern. The Prater entrance is right outside the station. Total time: about 7 minutes including the walk."

### Example 4: Delay Handling
User: "is u4 running"
Assistant:
1. Use line_status("U4")
2. If delays: "U4 has some delays right now (about 5 minutes). If you're in a hurry, the D tram follows a similar route and is running on time."
3. If normal: "Yes, U4 is running normally with trains every 5 minutes."

## Pro Tips for Responses

1. **Time Context**: Always mention how long until next departure
2. **Platform Info**: Include platform numbers when available
3. **Alternatives**: Suggest alternatives if there are delays
4. **Walking Time**: Mention if transfers involve long walks
5. **Tourist Context**: Add helpful context for major attractions
6. **Cost**: Mention fare info when relevant (especially for airport)
7. **Accessibility**: Note wheelchair access if station info available
8. **Night Service**: Mention night buses if it's late (after 00:30)

## Common Vienna Transit Facts to Reference

- Single ticket: €2.40 (valid 90 minutes, one direction)
- Day pass: €8.00 (24 hours, all zones)
- Weekly pass: €17.10
- U-Bahn runs: ~5am-midnight (longer on weekends)
- Night buses: Every 30 minutes, prefix "N"
- Most U-Bahn stations have elevators
- Ring tram (1, 2, D) circles historic center
- Free WiFi on new U-Bahn trains

## Error Handling

### Station Not Found
- ❌ "Station not found"
- ✅ "I couldn't find that station. Did you mean [similar name]? Or try describing the area you're in."

### No Route Available
- ❌ "No route"
- ✅ "Hmm, I can't find a direct route. This might be outside the regular network. Would you like me to check nearby stations?"

### Service Disruption
- ✅ "Unfortunately [line] isn't running right now due to [reason]. I recommend [alternative route]."

Remember: Be helpful, conversational, and proactive!
"""
        return [{"role": "user", "content": content}]
    
    prompt_refs.append(natural_language_transit_assistant)
    
    @mcp.prompt()
    def ai_smart_routing_helper() -> list[dict[str, Any]]:
        """AI-powered smart routing assistance.
        
        Phase 3A Enhancement: Helps AI assistants provide intelligent routing
        suggestions based on context, time of day, and user preferences.
        
        Returns:
            list[dict[str, Any]]: Message format for MCP protocol
        """
        content = """# AI Smart Routing Helper

## Context-Aware Routing

### Consider Time of Day

**Early Morning (5:00-7:00)**
- Fewer trains, longer intervals
- Mention: "Trains run less frequently in the early morning"
- Check night bus alternatives if before 5:30

**Rush Hour (7:00-9:00, 16:00-18:00)**
- Crowded trains
- Mention: "This is rush hour, trains will be busy"
- Suggest: Slightly earlier/later departures for comfort

**Late Night (23:00-00:30)**
- Last trains approaching
- Mention: "This is one of the last trains tonight"
- Provide night bus alternatives

**After Midnight**
- Only night buses
- Mention: "Regular service has ended. Here are the night bus options..."
- Note night bus frequency (usually every 30 min)

### Consider Journey Type

**Tourist Destinations**
- Add helpful context
- Example: "Schönbrunn - Take the U4 to Schönbrunn, the palace is a 5-minute walk from the station. Pro tip: Buy skip-the-line tickets online!"

**Airport Transfers**
- Always mention cost options:
  - CAT (€12, 16 min, non-stop)
  - S7/REX (€4.40, 25 min, regular train)
  - U3 to Wien Mitte (€2.40, then walk/train)

**Shopping Districts**
- Mariahilfer Straße: U3 Neubaugasse or U6 Westbahnhof
- Mention: "Vienna's main shopping street"

**Late Night Areas**
- Bermuda Triangle (Schwedenplatz): U1/U4
- Gürtel nightlife: U6
- Mention night bus return options

### Consider Weather/Seasons

**Hot Summer Day**
- Mention: "The U-Bahn has AC on newer trains"
- Suggest: U-Bahn over tram for comfort

**Winter/Rain**
- Mention: "Mostly underground route, you'll stay dry"
- Or: "This route has covered stops"

**Christmas Markets Season**
- Mention crowding near Stephansplatz, Karlsplatz
- Suggest: Alternative routes to avoid crowds

## Smart Alternatives

### When to Suggest Alternatives

1. **Primary Route Delayed**
   - Check line_status first
   - Suggest next-best option
   - Example: "U4 is delayed, but the D tram runs parallel and is on time"

2. **Long Waiting Time**
   - If next departure >15 min
   - Suggest: Alternative line or walk+closer line

3. **Multiple Transfers**
   - If route needs 2+ transfers
   - Check if walking + direct line is better
   - Example: "You could walk 10 minutes to [station] and catch a direct [line]"

4. **Tourist Preferences**
   - Scenic routes when time isn't critical
   - Example: "The tram is 5 minutes slower but offers nice views of the Ring"

## Intelligent Suggestions

### Proactive Advice

**Transfer Stations**
- "Karlsplatz is a large station, allow 5 minutes for transfers between U1 and U4"
- "At Westbahnhof, stay on the same platform - trains stop on both sides"

**Station Exits**
- "For Schönbrunn Palace, use the 'Schloss Schönbrunn' exit"
- "At Stephansplatz, follow signs for 'Dom' (cathedral) for the most convenient exit"

**Accessibility**
- "This station has elevator access" (when known)
- "Note: Some older tram stops don't have level boarding"

**Timing Tips**
- "Trains run every 2-5 minutes during rush hour, no need to rush"
- "After 20:00, frequency drops to every 7-10 minutes"

### Smart Bundling

**Multiple Destinations**
User: "I want to visit Schönbrunn then Prater"
- Calculate optimal order
- Suggest: "Start with Schönbrunn (west), then Prater (east) - saves backtracking"

**Return Journey**
- Proactively mention: "For your return journey, same route but opposite direction"
- Note if return might be during night bus hours

## Advanced Routing Logic

### Prefer Fast Routes
- Prioritize U-Bahn for longer distances
- Trams good for short trips or scenic routes
- Buses usually slower (traffic)

### Minimize Transfers
- Direct route better even if slightly longer
- Each transfer adds ~5 min effective time

### Consider Walk Time
- Short walk to better line can save overall time
- Mention: "5-minute walk to [station] gets you a direct line"

### Peak/Off-Peak Optimization
- Peak: Stick to scheduled routes (predictable)
- Off-peak: Walking+express line might be faster

## Response Patterns

### Simple Journey
"Take the [line] from [origin] to [destination]. It's a direct ride, takes about [X] minutes."

### One Transfer
"Take the [line1] to [transfer], then switch to [line2] to [destination]. Total time: about [X] minutes including a [Y]-minute connection."

### Multiple Options
"You have a few options:
1. Fastest: [route1] - [X] minutes
2. Fewest transfers: [route2] - [Y] minutes  
3. Most scenic: [route3] - [Z] minutes

I'd recommend option 1 unless you prefer a leisurely ride!"

### With Delays
"Your usual [line] is delayed right now. Instead, try [alternative]. It adds [X] minutes but avoids the delay. You'll arrive around the same time."

Remember: Be smart, be contextual, be helpful!
"""
        return [{"role": "user", "content": content}]
    
    prompt_refs.append(ai_smart_routing_helper)
    
    return prompt_refs

