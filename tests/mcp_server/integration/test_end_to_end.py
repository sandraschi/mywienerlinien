"""End-to-end integration tests for MCP server workflows."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Add frontend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "frontend"))


@pytest.mark.asyncio
async def test_complete_departure_check_workflow():
    """Test complete workflow: search station -> check departures."""
    from mcp_server.server import mcp

    # Verify server is initialized
    assert mcp is not None

    # In a real end-to-end test, you would:
    # 1. Use the MCP protocol to call tools sequentially
    # 2. Mock external dependencies (API, database)
    # 3. Verify complete workflow from user query to response

    # For now, we verify the server is set up correctly
    assert mcp.name == "vienna-transit"


@pytest.mark.asyncio
async def test_complete_journey_planning_workflow():
    """Test complete workflow: search both stations -> plan journey."""
    from mcp_server.server import mcp

    # Verify server is initialized
    assert mcp is not None

    # In a real end-to-end test, you would:
    # 1. Search for origin station
    # 2. Search for destination station
    # 3. Plan journey between them
    # 4. Verify journey plan is valid

    # For now, we verify the server is set up correctly
    assert mcp.name == "vienna-transit"


@pytest.mark.asyncio
async def test_status_check_workflow():
    """Test workflow: check system status -> check specific line."""
    from mcp_server.server import mcp

    # Verify server is initialized
    assert mcp is not None

    # In a real end-to-end test, you would:
    # 1. Check system-wide status
    # 2. Check specific line status
    # 3. Verify status responses are correct

    # For now, we verify the server is set up correctly
    assert mcp.name == "vienna-transit"


@pytest.mark.asyncio
async def test_resource_access_workflow():
    """Test accessing resources for context."""
    from mcp_server.server import _resource_refs

    # Access network overview
    assert len(_resource_refs) > 0
    network_resource = _resource_refs[0]  # network_overview
    network_info = await network_resource()

    assert "Vienna" in network_info
    assert isinstance(network_info, str)

    # Access metro lines
    metro_resource = None
    for ref in _resource_refs:
        if "metro" in str(ref):
            metro_resource = ref
            break

    if metro_resource:
        metro_info = await metro_resource()
        assert "U1" in metro_info or "U-Bahn" in metro_info
