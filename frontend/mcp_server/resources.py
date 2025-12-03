"""MCP resources for Vienna Transit MCP Server.

Resources provide static or semi-static data that AI assistants can reference
to better understand Vienna's transit system, common stations, lines, and
operational information.

MCP resources are URI-addressable data that AI assistants can read to gain
context about the transit system. They complement tools by providing reference
information that helps assistants provide more accurate and helpful responses.

This module registers several resources:
- vienna-transit://network/overview: High-level network structure
- vienna-transit://stations/major: List of major stations
- vienna-transit://lines/metro: Metro line information
- vienna-transit://operating-hours: Service hours and schedules
- vienna-transit://fares: Fare and ticket information

Resources are registered with the FastMCP server and can be accessed by
AI assistants through the MCP protocol using their URIs.
"""

from fastmcp import FastMCP

try:
    from ...data_loader import data_loader
except ImportError:
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from data_loader import data_loader


def register_resources(mcp: FastMCP) -> list:
    """Register MCP resources with the server.

    Resources provide reference data that helps AI assistants:
    - Understand Vienna's transit network structure
    - Reference common stations and lines
    - Access operational information
    - Provide context-aware responses

    Following FastMCP 2.12+ standards: resources are async functions that return
    strings (usually JSON). References are stored to prevent garbage collection.

    Args:
        mcp (FastMCP): FastMCP server instance to register resources with

    Returns:
        list: List of resource function references to prevent garbage collection
    """
    resource_refs = []

    @mcp.resource("vienna-transit://network/overview")
    async def network_overview() -> str:
        """Overview of Vienna's public transport network.

        Provides high-level information about Vienna's transit system including
        line types, coverage, and operational characteristics.

        Returns:
            Network overview text
        """
        return """# Vienna Public Transport Network Overview

## Network Structure
Vienna's public transport is operated by Wiener Linien and consists of:

### Metro (U-Bahn)
- **5 Lines**: U1, U2, U3, U4, U6 (U5 is under construction)
- **Color Coding**:
  - U1: Red
  - U2: Purple
  - U3: Orange
  - U4: Green
  - U6: Brown
- **Frequency**: 2-5 minutes during peak hours
- **Operating Hours**: ~5:00 AM - 12:30 AM (varies by line)
- **Coverage**: Serves city center and major suburbs

### Tram
- **30+ Lines**: Including historic Ring tram (Line D)
- **Frequency**: 5-10 minutes typically
- **Operating Hours**: ~5:00 AM - 12:30 AM
- **Coverage**: Extensive city-wide network, good for shorter trips

### Bus
- **City Buses**: Numbered routes (1A, 13A, etc.)
- **Regional Buses**: Connect suburbs and outer districts
- **Frequency**: 5-15 minutes typically
- **Operating Hours**: ~5:00 AM - 12:30 AM

### Night Bus
- **N-Prefixed Lines**: N25, N38, N43, etc.
- **Operating Hours**: After midnight until ~5:00 AM
- **Frequency**: 15-30 minutes
- **Coverage**: Limited but covers major routes

## Fare Zones
- **Zone 100**: Most of Vienna (single ticket €2.40)
- **Zone 200**: Outer suburbs
- **Zone 300+**: Regional connections

## Key Stations
- **Stephansplatz**: Central square, U1/U3 hub
- **Hauptbahnhof (HBF)**: Main train station, U1
- **Schwedenplatz**: U1/U4 hub, near city center
- **Praterstern**: U1/U2 hub, near Prater park
- **Karlsplatz**: U1/U2/U4 hub, major transfer point
"""

    resource_refs.append(network_overview)

    @mcp.resource("vienna-transit://stations/major")
    async def major_stations() -> str:
        """List of major Vienna transit stations.

        Provides information about important stations that serve as hubs or
        landmarks, helping AI assistants understand the network structure.

        Returns:
            Major stations information
        """
        try:
            stations = data_loader.load_stations()
            # Filter for major stations (those with multiple lines or important locations)
            major_station_names = [
                "Stephansplatz",
                "Hauptbahnhof",
                "Schwedenplatz",
                "Karlsplatz",
                "Praterstern",
                "Westbahnhof",
                "Landstraße",
                "Meidling",
                "Spittelau",
                "Ottakring",
                "Floridsdorf",
                "Leopoldau",
            ]

            major_stations = [s for s in stations if s.name in major_station_names]

            result = "# Major Vienna Transit Stations\n\n"
            result += "These stations serve as important hubs or landmarks:\n\n"

            for station in sorted(major_stations, key=lambda x: x.name):
                result += f"## {station.name}\n"
                result += f"- **Type**: {station.type}\n"
                if station.zone:
                    result += f"- **Zone**: {station.zone}\n"
                result += "\n"

            return result
        except Exception:
            return """# Major Vienna Transit Stations

## Key Hubs
- **Stephansplatz**: Central square, U1/U3 hub
- **Hauptbahnhof**: Main train station, U1
- **Schwedenplatz**: U1/U4 hub
- **Karlsplatz**: U1/U2/U4 hub
- **Praterstern**: U1/U2 hub
- **Westbahnhof**: West train station
- **Landstraße**: U3/U4 hub
- **Meidling**: South train station, U6

## Important Locations
- **Spittelau**: U4/U6 hub, waste incineration plant
- **Ottakring**: U3 terminus
- **Floridsdorf**: U6 terminus
- **Leopoldau**: U1 terminus
"""

    resource_refs.append(major_stations)

    @mcp.resource("vienna-transit://lines/metro")
    async def metro_lines() -> str:
        """Information about Vienna's metro (U-Bahn) lines.

        Provides details about each U-Bahn line including routes, frequencies,
        and key stations.

        Returns:
            Metro lines information
        """
        return """# Vienna Metro (U-Bahn) Lines

## U1 (Red Line)
- **Route**: Reumannplatz ↔ Leopoldau
- **Key Stations**: Stephansplatz, Praterstern, Hauptbahnhof
- **Frequency**: 2-5 minutes peak, 5-7 minutes off-peak
- **Notes**: Main north-south line, serves city center

## U2 (Purple Line)
- **Route**: Seestadt ↔ Karlsplatz
- **Key Stations**: Praterstern, Schottenring, Karlsplatz
- **Frequency**: 3-5 minutes peak, 5-8 minutes off-peak
- **Notes**: Serves eastern districts and city center

## U3 (Orange Line)
- **Route**: Ottakring ↔ Simmering
- **Key Stations**: Stephansplatz, Landstraße, Erdberg
- **Frequency**: 3-5 minutes peak, 5-8 minutes off-peak
- **Notes**: East-west line through city center

## U4 (Green Line)
- **Route**: Hütteldorf ↔ Heiligenstadt
- **Key Stations**: Schwedenplatz, Karlsplatz, Schönbrunn
- **Frequency**: 3-5 minutes peak, 5-8 minutes off-peak
- **Notes**: Serves western districts, connects to Schönbrunn

## U6 (Brown Line)
- **Route**: Siebenhirten ↔ Floridsdorf
- **Key Stations**: Meidling, Spittelau, Floridsdorf
- **Frequency**: 3-5 minutes peak, 5-8 minutes off-peak
- **Notes**: North-south line, serves western and northern districts

## U5 (Under Construction)
- **Status**: Currently being built
- **Planned Route**: Will connect to U2
- **Expected Completion**: 2026-2028
"""

    resource_refs.append(metro_lines)

    @mcp.resource("vienna-transit://operating-hours")
    async def operating_hours() -> str:
        """Operating hours for Vienna public transport.

        Provides information about when different services operate, including
        regular hours and night service.

        Returns:
            Operating hours information
        """
        return """# Vienna Transit Operating Hours

## Regular Service
- **Metro (U-Bahn)**:
  - First train: ~5:00 AM (varies by line)
  - Last train: ~12:30 AM (varies by line)
  - Frequency: 2-5 minutes peak, 5-8 minutes off-peak

- **Tram**:
  - First tram: ~5:00 AM
  - Last tram: ~12:30 AM
  - Frequency: 5-10 minutes typically

- **Bus**:
  - First bus: ~5:00 AM
  - Last bus: ~12:30 AM
  - Frequency: 5-15 minutes typically

## Night Service
- **Night Buses**: Operate after regular service ends
- **Hours**: ~12:30 AM - ~5:00 AM
- **Frequency**: 15-30 minutes
- **Lines**: N-prefixed (N25, N38, N43, etc.)
- **Coverage**: Limited but covers major routes

## Special Services
- **Ring Tram (Line D)**: Tourist-oriented, operates during daytime
- **Airport Connection**: U3 to Wien Mitte, then CAT train
- **Weekend Service**: Similar hours, may have reduced frequency

## Peak Hours
- **Morning**: 7:00 AM - 9:00 AM
- **Evening**: 4:00 PM - 6:00 PM
- **Frequency**: Increased during peak hours
"""

    resource_refs.append(operating_hours)

    @mcp.resource("vienna-transit://fares")
    async def fare_information() -> str:
        """Fare information for Vienna public transport.

        Provides pricing information and ticket types available.

        Returns:
            Fare information text
        """
        return """# Vienna Transit Fares

## Single Tickets
- **Zone 100** (Most of Vienna): €2.40
- **Zone 200**: €2.80
- **Zone 300+**: Varies by distance

## Passes
- **24-Hour Ticket**: €8.00 (unlimited travel)
- **48-Hour Ticket**: €14.10
- **72-Hour Ticket**: €17.10
- **Weekly Ticket**: €17.10
- **Monthly Ticket**: €51.00

## Discounts
- **Children** (under 15): Free with adult
- **Students**: Reduced rates available
- **Seniors**: Discounted monthly passes

## Payment Methods
- **Cash**: At ticket machines and some stations
- **Card**: Contactless payment accepted
- **Mobile**: Wiener Linien app
- **Vienna Card**: Tourist card includes transit

## Validation
- Tickets must be validated before first use
- Validation machines at stations and on vehicles
- Fines apply for unvalidated tickets
"""

    resource_refs.append(fare_information)

    return resource_refs
