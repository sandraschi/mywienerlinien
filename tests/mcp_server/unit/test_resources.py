"""Unit tests for MCP resources."""

from __future__ import annotations

import pytest
from mcp_server.resources import register_resources


@pytest.mark.asyncio
async def test_resources_registration(mock_mcp_server):
    """Test that resources are registered correctly."""
    resource_refs = register_resources(mock_mcp_server)

    assert len(resource_refs) == 5


@pytest.mark.asyncio
async def test_network_overview_resource(mock_mcp_server):
    """Test network_overview resource."""
    register_resources(mock_mcp_server)

    # Get the resource function
    resource_func = None
    for uri, func in mock_mcp_server._resources.items():
        if "network/overview" in uri:
            resource_func = func
            break

    assert resource_func is not None

    # Execute
    result = await resource_func()

    # Assert
    assert isinstance(result, str)
    assert "Vienna" in result
    assert "U-Bahn" in result or "Metro" in result


@pytest.mark.asyncio
async def test_major_stations_resource(mock_mcp_server, mock_data_loader):
    """Test major_stations resource."""
    register_resources(mock_mcp_server)

    # Get the resource function
    resource_func = None
    for uri, func in mock_mcp_server._resources.items():
        if "stations/major" in uri:
            resource_func = func
            break

    assert resource_func is not None

    # Mock data_loader
    from unittest.mock import patch

    with patch("mcp_server.resources.data_loader", mock_data_loader):
        # Execute
        result = await resource_func()

    # Assert
    assert isinstance(result, str)
    assert "Station" in result


@pytest.mark.asyncio
async def test_metro_lines_resource(mock_mcp_server):
    """Test metro_lines resource."""
    register_resources(mock_mcp_server)

    # Get the resource function
    resource_func = None
    for uri, func in mock_mcp_server._resources.items():
        if "lines/metro" in uri:
            resource_func = func
            break

    assert resource_func is not None

    # Execute
    result = await resource_func()

    # Assert
    assert isinstance(result, str)
    assert "U1" in result or "U-Bahn" in result


@pytest.mark.asyncio
async def test_operating_hours_resource(mock_mcp_server):
    """Test operating_hours resource."""
    register_resources(mock_mcp_server)

    # Get the resource function
    resource_func = None
    for uri, func in mock_mcp_server._resources.items():
        if "operating-hours" in uri:
            resource_func = func
            break

    assert resource_func is not None

    # Execute
    result = await resource_func()

    # Assert
    assert isinstance(result, str)
    assert "hours" in result.lower() or "operating" in result.lower()


@pytest.mark.asyncio
async def test_fare_information_resource(mock_mcp_server):
    """Test fare_information resource."""
    register_resources(mock_mcp_server)

    # Get the resource function
    resource_func = None
    for uri, func in mock_mcp_server._resources.items():
        if "fares" in uri:
            resource_func = func
            break

    assert resource_func is not None

    # Execute
    result = await resource_func()

    # Assert
    assert isinstance(result, str)
    assert "€" in result or "fare" in result.lower() or "ticket" in result.lower()
