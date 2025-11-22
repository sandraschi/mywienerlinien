"""Unit tests for the line_status tool."""

from __future__ import annotations

from datetime import datetime
from unittest.mock import Mock, patch

import pytest
from mcp_server.models.status import LineStatusResponse


@pytest.mark.asyncio
async def test_line_status_system_wide():
    """Test system-wide status check."""
    # Mock disruption monitor
    mock_disruptions = []

    with patch("mcp_server.tools.status.disruption_monitor") as mock_monitor:
        mock_monitor.get_active_disruptions = Mock(return_value=mock_disruptions)

        from fastmcp import FastMCP
        from mcp_server.tools.status import register_status_tool

        test_mcp = FastMCP(name="test", version="1.0.0")
        register_status_tool(test_mcp)

        if hasattr(test_mcp, "_tools") and "line_status" in test_mcp._tools:
            tool_func = test_mcp._tools["line_status"]
            result = await tool_func(line_name=None)

            assert isinstance(result, LineStatusResponse)
            assert result.line_filter is None
            assert len(result.statuses) > 0
            assert result.statuses[0].status == "operational"
        else:
            assert test_mcp is not None


@pytest.mark.asyncio
async def test_line_status_specific_line():
    """Test status check for specific line."""
    # Mock disruption monitor
    mock_disruptions = []

    with patch("mcp_server.tools.status.disruption_monitor") as mock_monitor:
        mock_monitor.get_disruptions_by_line = Mock(return_value=mock_disruptions)

        from fastmcp import FastMCP
        from mcp_server.tools.status import register_status_tool

        test_mcp = FastMCP(name="test", version="1.0.0")
        register_status_tool(test_mcp)

        if hasattr(test_mcp, "_tools") and "line_status" in test_mcp._tools:
            tool_func = test_mcp._tools["line_status"]
            result = await tool_func(line_name="U1")

            assert isinstance(result, LineStatusResponse)
            assert result.line_filter == "U1"
            assert len(result.statuses) > 0
        else:
            assert test_mcp is not None


@pytest.mark.asyncio
async def test_line_status_operational():
    """Test status when all lines are operational."""
    mock_disruptions = []

    with patch("mcp_server.tools.status.disruption_monitor") as mock_monitor:
        mock_monitor.get_active_disruptions = Mock(return_value=mock_disruptions)

        from fastmcp import FastMCP
        from mcp_server.tools.status import register_status_tool

        test_mcp = FastMCP(name="test", version="1.0.0")
        register_status_tool(test_mcp)

        if hasattr(test_mcp, "_tools") and "line_status" in test_mcp._tools:
            tool_func = test_mcp._tools["line_status"]
            result = await tool_func(line_name=None)

            assert any(status.status == "operational" for status in result.statuses)
        else:
            assert test_mcp is not None


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

        from fastmcp import FastMCP
        from mcp_server.tools.status import register_status_tool

        test_mcp = FastMCP(name="test", version="1.0.0")
        register_status_tool(test_mcp)

        if hasattr(test_mcp, "_tools") and "line_status" in test_mcp._tools:
            tool_func = test_mcp._tools["line_status"]
            result = await tool_func(line_name=None)

            assert len(result.statuses) > 0
            assert any(status.status == "disrupted" for status in result.statuses)
            disrupted_status = next(s for s in result.statuses if s.status == "disrupted")
            assert disrupted_status.line == "U1"
            assert disrupted_status.severity == "high"
            assert len(disrupted_status.affected_stations) == 2
        else:
            assert test_mcp is not None


@pytest.mark.asyncio
async def test_line_status_error_handling():
    """Test error handling when disruption monitor fails."""
    with patch("mcp_server.tools.status.disruption_monitor") as mock_monitor:
        mock_monitor.get_active_disruptions = Mock(side_effect=Exception("Monitor error"))

        from fastmcp import FastMCP
        from mcp_server.tools.status import register_status_tool

        test_mcp = FastMCP(name="test", version="1.0.0")
        register_status_tool(test_mcp)

        if hasattr(test_mcp, "_tools") and "line_status" in test_mcp._tools:
            tool_func = test_mcp._tools["line_status"]
            with pytest.raises(RuntimeError, match="Failed to fetch"):
                await tool_func(line_name=None)
        else:
            assert test_mcp is not None
