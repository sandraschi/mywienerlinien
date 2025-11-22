# Vienna Transit MCP Server - Enhanced Product Requirements Document

**Project**: MyWienerLinien → Vienna Transit MCP Server  
**Version**: 2.0 (MCP-First Architecture)  
**Date**: August 10, 2025  
**Status**: Strategic Pivot Recommendation

## Executive Summary

### Vision Statement
Transform MyWienerLinien from a complex web application into the **definitive AI-accessible interface for Vienna public transport** - a focused MCP server that enables natural language transit queries through Claude and other AI assistants.

### Strategic Pivot Rationale
- **Market Gap**: No Vienna-specific transit MCP server exists despite growing MCP ecosystem
- **Overengineering**: Current PostgreSQL+Docker+Grafana stack is overkill for transit visualization
- **AI-First Opportunity**: MCP integration enables "Ask Claude about Vienna trams" conversations
- **Austrian Efficiency**: Simpler architecture with greater real-world utility

## Product Definition

### Core Value Proposition
```
"Ask Claude: 'When's the next U-Bahn to Stephansplatz?'
Get real Wiener Linien data instantly without opening apps."
```

### Target Users
1. **Vienna Residents** using Claude Desktop for daily transit planning
2. **AI Developers** building Vienna-specific applications  
3. **European Transit Enthusiasts** wanting local MCP servers
4. **Sandra's Ecosystem** as core component of Austrian digital services

## Technical Specification

### MCP Server Architecture

#### Essential Tools (MVP)
```python
@mcp.tool()
def next_departures(station: str, max_results: int = 5) -> List[Departure]:
    """Get next departures from Vienna transit station
    
    Args:
        station: Station name (supports German/English, partial matching)
        max_results: Maximum departures to return (1-10)
    
    Returns:
        List of departures with line, destination, time, delay, platform
    """

@mcp.tool() 
def journey_planner(from_station: str, to_station: str, 
                   departure_time: Optional[str] = None) -> JourneyPlan:
    """Plan optimal journey between Vienna stations"""

@mcp.tool()
def line_status(line_name: Optional[str] = None) -> List[ServiceStatus]:
    """Check Vienna transit service status and disruptions"""

@mcp.tool()
def station_search(query: str) -> List[Station]:
    """Find Vienna transit stations by name or location"""
```

### Technology Stack (Simplified)
```python
# Minimal, focused dependencies
fastmcp>=2.10.0          # Official MCP SDK
sqlite3                  # GTFS static data (built-in)
requests>=2.31.0         # Wiener Linien API client
apscheduler>=3.10.0      # Background cache updates
pydantic>=2.5.0          # Data validation
```

## Implementation Roadmap

### Phase 1: MCP Core (2-3 weeks)
**Deliverables**:
- Convert existing Flask app to FastMCP server
- Implement 4 essential MCP tools
- SQLite-based GTFS integration
- Robust Wiener Linien API client with caching

**Success Criteria**:
- MCP server responds to all 4 tools
- Station search handles common Vienna names
- Real-time departures work for major stations
- <2 second response times

### Phase 2: AI Experience (1-2 weeks)
**Deliverables**:
- Smart station name matching (fuzzy search, aliases)
- German/English language support
- Context-aware suggestions
- Claude Desktop optimization

**Success Criteria**:
- Handles "Stephansdom" → "Stephansplatz" mapping
- Works with partial names like "Schwedenpl"
- Understands "Ring tram" and "airport connection"
- Natural conversation flow in Claude

### Phase 3: Advanced Features (2-3 weeks)
**Deliverables**:
- Multi-modal journey planning
- Accessibility information
- Real-time service alerts
- Performance optimization

**Success Criteria**:
- Complex route planning with transfers
- Barrier-free route options
- Proactive disruption notifications
- Sub-second response times

## Distribution Strategy

### Installation Method
```bash
# PyPI package for easy distribution
pip install vienna-transit-mcp

# Or with uvx (recommended)
uvx vienna-transit-mcp
```

### Claude Desktop Configuration
```json
{
  "mcpServers": {
    "vienna-transit": {
      "command": "uvx",
      "args": ["vienna-transit-mcp"]
    }
  }
}
```

### Documentation Requirements
- **Quick Start Guide**: 5-minute setup for Claude Desktop
- **Tool Reference**: Complete API documentation with examples
- **Vienna Context Guide**: Local knowledge for international users
- **AI Prompting Guide**: Optimized queries for best results

## Success Metrics

### Technical KPIs
- **Response Time**: <2 seconds for 95% of tool calls
- **API Reliability**: >98% successful Wiener Linien API calls
- **Tool Accuracy**: >95% correct station matching
- **Uptime**: >99.5% availability

### User Experience KPIs
- **Claude Integration**: Seamless operation in Claude Desktop
- **Natural Language**: Handles common Vienna transit phrases
- **Coverage**: Supports all U-Bahn, major tram/bus lines
- **Daily Usage**: Adoption by Vienna-based Claude users

## Competitive Analysis

### VS. Existing Transit Apps
- **AI-First Interface**: Natural language vs. tap-heavy UIs
- **Workflow Integration**: Part of broader AI assistance, not standalone
- **Zero Learning Curve**: Uses existing Claude conversation skills

### VS. International MCP Servers
- **Vienna Expertise**: Local knowledge, German language support
- **Real-Time Focus**: Live data vs. static schedules only
- **European Privacy**: GDPR-compliant, local data processing

## Risk Mitigation

### Technical Risks
- **API Changes**: Monitor Wiener Linien API, implement fallbacks
- **Rate Limiting**: Respect fair use, implement smart caching
- **Data Quality**: Validate responses, handle edge cases gracefully

### Market Risks
- **MCP Adoption**: Protocol is growing rapidly, low risk
- **Competition**: First-mover advantage, high Vienna specialization barrier
- **Maintenance**: Simple architecture reduces long-term costs

## Strategic Recommendation

**IMMEDIATE ACTION**: Begin Phase 1 implementation using existing MyWienerLinien API integration knowledge.

**Why This Pivot Succeeds**:
1. **Leverages Existing Work**: Vienna API expertise and data processing
2. **Simpler Architecture**: Remove complexity, focus on core value
3. **Growing Market**: MCP ecosystem expanding rapidly in 2025
4. **Austrian Advantage**: Local expertise difficult to replicate
5. **Sandra's Ecosystem**: Perfect fit for Ednaficator integration

**Next Steps**:
1. Study caltrain-mcp implementation patterns
2. Create minimal FastMCP server with one working tool
3. Test integration with Claude Desktop
4. Iterate based on real usage patterns

This transformation positions Sandra at the forefront of the European MCP ecosystem while creating genuinely useful infrastructure for Vienna's AI-assisted residents.

---

**Document Version**: 2.0  
**Last Updated**: August 10, 2025  
**Next Review**: September 10, 2025
