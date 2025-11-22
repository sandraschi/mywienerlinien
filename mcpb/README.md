# Vienna Transit MCP - MCPB Package

FastMCP 2.13 compliant MCP server package for Vienna public transport information.

## Package Information

- **Name**: vienna-transit-mcp
- **Version**: 1.0.0
- **Platforms**: Windows, macOS, Linux
- **Python**: >=3.9

## Features

- ✅ 4 core tools for Vienna transit queries
- ✅ 3 prompts for AI assistant guidance
- ✅ 5 resources for transit system reference
- ✅ FastMCP 2.13 compliant
- ✅ Real-time departure information
- ✅ Station search with fuzzy matching
- ✅ Journey planning
- ✅ Service status monitoring

## Installation

### Via Claude Desktop

1. Download the `.mcpb` package file
2. Open Claude Desktop
3. Drag and drop the `.mcpb` file into Claude Desktop
4. Configure settings if needed
5. Start using Vienna transit tools!

### Manual Installation

1. Extract the package to a directory
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Configure in Claude Desktop `claude_desktop_config.json`:
   ```json
   {
     "mcpServers": {
       "vienna-transit": {
         "command": "python",
         "args": ["-m", "frontend.mcp_server.server"],
         "cwd": "/path/to/extracted/package"
       }
     }
   }
   ```

## Configuration

### User Settings

Configure via Claude Desktop settings panel:

- **timeout** (default: 30): Operation timeout in seconds
- **cache_duration** (default: 15): Cache duration for API responses

## Available Tools

### 1. `next_departures`
Get next departures from a Vienna transit station.

**Parameters:**
- `station` (str): Station name (e.g., "Stephansplatz")
- `max_results` (int, optional): Maximum departures (1-10, default: 5)

**Returns:** List of departures with line, destination, time, delay

### 2. `station_search`
Find Vienna transit stations by name.

**Parameters:**
- `query` (str): Search query (partial match supported)
- `limit` (int, optional): Maximum results (1-20, default: 10)

**Returns:** List of matching stations

### 3. `line_status`
Check Vienna transit service status and disruptions.

**Parameters:**
- `line_name` (str, optional): Line filter (e.g., "U1", "D")

**Returns:** List of service status entries

### 4. `journey_planner`
Plan optimal journey between Vienna stations.

**Parameters:**
- `from_station` (str): Origin station
- `to_station` (str): Destination station
- `departure_time` (str, optional): ISO format timestamp

**Returns:** Journey plan with routes, transfers, duration

## Available Prompts

1. **vienna_transit_guide**: Comprehensive guide to Vienna's transit system
2. **departure_checking_prompt**: Best practices for checking departures
3. **journey_planning_prompt**: Guidance for journey planning

## Available Resources

1. **vienna-transit://network/overview**: Network structure overview
2. **vienna-transit://stations/major**: Major stations list
3. **vienna-transit://lines/metro**: Metro line information
4. **vienna-transit://operating-hours**: Operating hours
5. **vienna-transit://fares**: Fare information

## Usage Examples

### Checking Departures

```
User: "When is the next U-Bahn from Stephansplatz?"
Claude: [Uses next_departures tool]
```

### Finding Stations

```
User: "Where is the station for Hauptbahnhof?"
Claude: [Uses station_search tool]
```

### Journey Planning

```
User: "How do I get from Stephansplatz to Prater?"
Claude: [Uses journey_planner tool]
```

### Service Status

```
User: "Is the U1 line running normally?"
Claude: [Uses line_status tool]
```

## Troubleshooting

### Common Issues

1. **Server not starting**: Check Python version (>=3.9) and dependencies
2. **No data returned**: Verify internet connection and Wiener Linien API availability
3. **Import errors**: Ensure all dependencies are installed

### Support

- **Documentation**: See main project README
- **Issues**: Report on GitHub
- **Questions**: Check project documentation

## License

MIT License - See main project LICENSE file

## Data Source

Data provided by Wiener Linien Open Data API:
- https://www.wienerlinien.at/open-data
- License: Creative Commons Attribution 4.0 International (CC BY 4.0)

