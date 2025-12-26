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

    return prompt_refs
