"""Unit tests for the line_status tool."""

from __future__ import annotations

from datetime import datetime
from unittest.mock import Mock, patch

import pytest
from fastmcp import Client, FastMCP
from fastmcp.exceptions import ToolError


@pytest.mark.asyncio
async def test_line_status_system_wide():
    """Test system-wide status check."""
    # Mock disruption monitor
    mock_disruptions = []

    with patch("mcp_server.tools.status.disruption_monitor") as mock_monitor:
        mock_monitor.get_active_disruptions = Mock(return_value=mock_disruptions)

        from mcp_server.tools.status import register_status_tool

        test_mcp = FastMCP(name="test", version="1.0.0")
        register_status_tool(test_mcp)

        async with Client(test_mcp) as client:
            result = await client.call_tool("line_status", {})
            data = result.structured_content

            assert data["line_filter"] is None
            assert len(data["statuses"]) > 0
            assert data["statuses"][0]["status"] == "operational"


@pytest.mark.asyncio
async def test_line_status_specific_line():
    """Test status check for specific line."""
    # Mock disruption monitor
    mock_disruptions = []

    with patch("mcp_server.tools.status.disruption_monitor") as mock_monitor:
        mock_monitor.get_disruptions_by_line = Mock(return_value=mock_disruptions)

        from mcp_server.tools.status import register_status_tool

        test_mcp = FastMCP(name="test", version="1.0.0")
        register_status_tool(test_mcp)

        async with Client(test_mcp) as client:
            result = await client.call_tool("line_status", {"line_name": "U1"})
            data = result.structured_content

            assert data["line_filter"] == "U1"
            assert len(data["statuses"]) > 0


@pytest.mark.asyncio
async def test_line_status_operational():
    """Test status when all lines are operational."""
    mock_disruptions = []

    with patch("mcp_server.tools.status.disruption_monitor") as mock_monitor:
        mock_monitor.get_active_disruptions = Mock(return_value=mock_disruptions)

        from mcp_server.tools.status import register_status_tool

        test_mcp = FastMCP(name="test", version="1.0.0")
        register_status_tool(test_mcp)

        async with Client(test_mcp) as client:
            result = await client.call_tool("line_status", {})
            data = result.structured_content

            assert any(status["status"] == "operational" for status in data["statuses"])


@pytest.mark.asyncio
async def test_line_status_with_disruptions():
    """Test status when disruptions are present."""
    # Create mock disruption object
    mock_disruption = Mock()
    mock_disruption.line = "U1"
    mock_disruption.status.value = "disrupted"
    mock_disruption.severity.value = "high"
    mock_disruption.title = "U1 Service Disruption"
    mock_disruption.description = "U1 line is experiencing delays"
    mock_disruption.affected_stations = ["Stephansplatz", "Schwedenplatz"]
    mock_disruption.start_time = datetime.utcnow()
    mock_disruption.end_time = None

    mock_disruptions = [mock_disruption]

    with patch("mcp_server.tools.status.disruption_monitor") as mock_monitor:
        mock_monitor.get_active_disruptions = Mock(return_value=mock_disruptions)

        from mcp_server.tools.status import register_status_tool

        test_mcp = FastMCP(name="test", version="1.0.0")
        register_status_tool(test_mcp)

        async with Client(test_mcp) as client:
            result = await client.call_tool("line_status", {})
            data = result.structured_content

            assert len(data["statuses"]) > 0
            assert any(status["status"] == "disrupted" for status in data["statuses"])
            disrupted_status = next(s for s in data["statuses"] if s["status"] == "disrupted")
            assert disrupted_status["line"] == "U1"
            assert disrupted_status["severity"] == "high"
            assert len(disrupted_status["affected_stations"]) == 2


@pytest.mark.asyncio
async def test_line_status_error_handling():
    """Test error handling when disruption monitor fails."""
    with patch("mcp_server.tools.status.disruption_monitor") as mock_monitor:
        mock_monitor.get_active_disruptions = Mock(side_effect=Exception("Monitor error"))

        from mcp_server.tools.status import register_status_tool

        test_mcp = FastMCP(name="test", version="1.0.0")
        register_status_tool(test_mcp)

        async with Client(test_mcp) as client:
            with pytest.raises(ToolError, match="Failed to fetch"):
                await client.call_tool("line_status", {})
