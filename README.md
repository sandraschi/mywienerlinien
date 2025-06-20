# Wiener Linien Live Map

A real-time map display for Vienna's public transport system, showing moving vehicle markers for U-Bahn, trams, and buses.

## Features

- Interactive map of Vienna with real-time vehicle positions
- Color-coded markers for different transport types (U-Bahn, tram, bus)
- Filter vehicles by type or line number
- Auto-refresh every 15 seconds
- Responsive design for desktop and mobile
- No API key required (as of 2024)

## Table of Contents

- [Features](#features)
- [Setup](#setup)
- [Wiener Linien API Documentation](#wiener-linien-api-documentation)
  - [API Endpoints](#api-endpoints)
  - [Data Structure](#data-structure)
  - [Fair Use Policy](#fair-use-policy)
  - [Static Data](#static-data)
- [Implementation Details](#implementation-details)
  - [Architecture](#architecture)
  - [Caching Strategy](#caching-strategy)
  - [Frontend Components](#frontend-components)
- [Development Guidelines](#development-guidelines)
- [Troubleshooting](#troubleshooting)
- [License](#license)

## Setup

1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
2. Run the application:
   ```
   python app.py
   ```
3. Open http://localhost:5000 in your browser

## Wiener Linien API Documentation

### API Endpoints

The Wiener Linien Open Data API provides several endpoints for accessing real-time public transport data. As of 2024, **no API key is required** to access these endpoints.

#### Main Endpoints

| Endpoint | Description | Parameters |
|----------|-------------|------------|
| `/monitor` | Real-time departure information with vehicle positions | `rbl` (optional): RBL number of the stop<br>`line` (optional): Line name<br>`diva` (optional): DIVA number of the stop |
| `/trafficInfoList` | Traffic information (disruptions, etc.) | `name` (optional): Filter by name<br>`relatedLine` (optional): Filter by line<br>`relatedStop` (optional): Filter by stop |
| `/newsList` | News and announcements | `name` (optional): Filter by name |

#### Example Requests

```
# Get all monitors (stops with real-time data)
https://www.wienerlinien.at/ogd_realtime/monitor

# Get specific stop by RBL number
https://www.wienerlinien.at/ogd_realtime/monitor?rbl=1234

# Get specific line
https://www.wienerlinien.at/ogd_realtime/monitor?line=U1
```

### Data Structure

The API returns data in JSON format. Here's a simplified overview of the response structure for the `/monitor` endpoint:

```json
{
  "data": {
    "monitors": [
      {
        "locationStop": {
          "properties": {
            "name": "Stop Name",
            "title": "Stop Title",
            "municipality": "Wien",
            "coordinates": {
              "lat": 48.12345,
              "lon": 16.12345
            }
          }
        },
        "lines": [
          {
            "name": "U1",
            "towards": "Destination",
            "direction": "H",
            "platform": "1",
            "richtungsId": "1",
            "barrierFree": true,
            "realtimeSupported": true,
            "trafficjam": false,
            "departures": {
              "departure": [
                {
                  "departureId": 12345,
                  "departureTime": {
                    "timePlanned": "2025-05-04T22:15:00.000+0200",
                    "timeReal": "2025-05-04T22:16:30.000+0200",
                    "countdown": 5
                  },
                  "vehicle": {
                    "name": "U1",
                    "towards": "Destination",
                    "direction": "H",
                    "richtungsId": "1",
                    "barrierFree": true,
                    "foldingRamp": false,
                    "realtimeSupported": true,
                    "trafficjam": false,
                    "type": "ptMetro",
                    "attributes": {},
                    "linienId": 301,
                    "id": "U1-301-12345",
                    "latitude": 48.12345,
                    "longitude": 16.12345,
                    "direction": 45
                  }
                }
              ]
            }
          }
        ]
      }
    ]
  },
  "message": {
    "value": "OK",
    "messageCode": 1,
    "serverTime": "2025-05-04T22:15:00.000+0200"
  }
}
```

### Fair Use Policy

The Wiener Linien API has a fair use policy that must be respected:

1. **Query only necessary stops**: Only request data for stops that are needed for personal use.
2. **Minimum interval between requests**: Do not make requests more frequently than every 15 seconds.
3. **IP blocking**: Wiener Linien reserves the right to block IP addresses that violate these rules.

Our application respects these limits by implementing appropriate caching strategies.

### Static Data

In addition to real-time data, Wiener Linien provides static data in CSV format:

| File | Description |
|------|-------------|
| `wienerlinien-ogd-linien.csv` | List of all lines with their attributes |
| `wienerlinien-ogd-haltestellen.csv` | List of all stops with their attributes |
| `wienerlinien-ogd-steige.csv` | List of all platforms with their attributes |
| `wienerlinien-ogd-fahrwegverlaeufe.csv` | Route geometries |
| `wienerlinien-ogd-haltepunkte.csv` | Detailed stop points |

These files are available at: `https://www.wienerlinien.at/ogd_realtime/doku/ogd/`

## Implementation Details

### Architecture

This application follows a simple client-server architecture:

1. **Backend (Flask)**:
   - Proxies requests to the Wiener Linien API
   - Caches responses to respect fair use policy
   - Transforms data for frontend consumption
   - Serves static files and HTML templates

2. **Frontend (JavaScript/Leaflet)**:
   - Displays an interactive map using Leaflet.js
   - Periodically fetches vehicle positions from the backend
   - Updates vehicle markers on the map
   - Provides filtering and UI controls

### Caching Strategy

To comply with the fair use policy, the application implements a multi-level caching strategy:

1. **Server-side caching**: Flask-Caching is used to cache API responses for 15 seconds.
2. **Static data caching**: Line information and other static data are loaded once at startup.
3. **Client-side polling**: The frontend requests updates every 15 seconds.

### Frontend Components

The frontend consists of several key components:

1. **Map**: Leaflet.js map centered on Vienna
2. **Vehicle markers**: Color-coded markers for different vehicle types
3. **Control panel**: Filters for vehicle types and lines
4. **Auto-refresh**: Automatic updates every 15 seconds

## Development Guidelines

This project follows strict development guidelines to ensure code quality, reliability, and maintainability. All contributors must follow the **Project Rulebook** located in `docs/RULEBOOK.md`.

### Key Development Rules:
- **Error Handling**: All functions must have comprehensive error handling to prevent crashes
- **Logging**: Proper logging must be implemented for all critical operations
- **API Integration**: Respect rate limits and implement proper fallback mechanisms
- **Code Quality**: Follow PEP 8 standards and maintain readable, self-documenting code
- **Testing**: All new functionality must include appropriate tests

### Before Contributing:
1. Read the complete [Rulebook](docs/RULEBOOK.md)
2. Ensure your code follows all established patterns
3. Test your changes thoroughly
4. Update documentation as needed

## Troubleshooting

### Common Issues

1. **No vehicles appearing on the map**:
   - Check if the Wiener Linien API is accessible
   - Verify that your system time is correct
   - Try different filters (some lines may not have real-time data)

2. **Slow performance**:
   - Reduce the number of visible vehicles by using filters
   - Check your network connection

3. **Error messages**:
   - "Failed to fetch": Check your internet connection
   - "API Error": The Wiener Linien API may be experiencing issues

## License

This project is part of the Annoyinator Barnacle Projects collection.

Data source: Wiener Linien - https://www.wienerlinien.at/open-data
License: Creative Commons Attribution 4.0 International (CC BY 4.0)
