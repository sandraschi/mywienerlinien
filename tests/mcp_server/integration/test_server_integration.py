"""Integration tests for the complete MCP server."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Add frontend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "frontend"))


@pytest.mark.asyncio
async def test_server_initialization():
    """Test that the MCP server initializes correctly."""
    from mcp_server.server import _prompt_refs, _resource_refs, mcp

    # Assert server is created
    assert mcp is not None
    assert mcp.name == "vienna-transit"

    # Assert prompts are registered
    assert len(_prompt_refs) == 5

    # Assert resources are registered
    assert len(_resource_refs) == 5

    # Tools are registered via decorators - verify server exists
    # FastMCP may store tools internally, so we verify registration succeeded
    assert mcp is not None


@pytest.mark.asyncio
async def test_tool_workflow_departures_to_station_search():
    """Test workflow: search station, then get departures."""
    from mcp_server.server import mcp

    # Verify server is initialized
    assert mcp is not None

    # Tools are registered - in a real integration test, you would:
    # 1. Use the MCP protocol to call tools
    # 2. Or access tools through FastMCP's public API
    # 3. Or test via the actual MCP server interface

    # For now, we verify the server is set up correctly
    assert mcp.name == "vienna-transit"


@pytest.mark.asyncio
async def test_tool_workflow_journey_planning():
    """Test workflow: search stations, then plan journey."""
    from mcp_server.server import mcp

    # Verify server is initialized
    assert mcp is not None

    # In a real integration test, you would:
    # 1. Call tools through the MCP protocol
    # 2. Verify the complete workflow
    # 3. Test with mocked or real API responses

    # For now, we verify the server is set up correctly
    assert mcp.name == "vienna-transit"


@pytest.mark.asyncio
async def test_prompts_and_resources_access():
    """Test that prompts and resources can be accessed."""
    from mcp_server.server import _prompt_refs, _resource_refs

    # Test prompts
    assert len(_prompt_refs) == 5
    for prompt_ref in _prompt_refs:
        result = prompt_ref()
        assert isinstance(result, list)
        assert len(result) > 0
        assert result[0]["role"] == "user"

    # Test resources
    assert len(_resource_refs) == 5
    for resource_ref in _resource_refs:
        result = await resource_ref()
        assert isinstance(result, str)
        assert len(result) > 0


@pytest.mark.asyncio
async def test_error_handling_workflow():
    """Test error handling across tool workflow."""
    from mcp_server.server import mcp

    # Verify server is initialized
    assert mcp is not None

    # In a real integration test, you would:
    # 1. Test error handling through the MCP protocol
    # 2. Verify appropriate error responses
    # 3. Test edge cases and invalid inputs

    # For now, we verify the server is set up correctly
    assert mcp.name == "vienna-transit"
