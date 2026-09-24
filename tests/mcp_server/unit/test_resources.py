"""Unit tests for MCP resources."""

from __future__ import annotations

import pytest
from fastmcp import Client

from mcp_server.resources import register_resources


@pytest.mark.asyncio
async def test_resources_registration(mock_mcp_server):
    """Test that resources are registered correctly."""
    resource_refs = register_resources(mock_mcp_server)

    assert len(resource_refs) == 5


async def _resource_text(client: Client, needle: str) -> str:
    """Read the first resource whose URI contains needle; return contents as text."""
    resources = await client.list_resources()
    uris = [str(r.uri) for r in resources]
    match = next((u for u in uris if needle in u), None)
    assert match is not None, f"no resource matching {needle!r} in {uris}"
    contents = await client.read_resource(match)
    assert contents
    return str(contents)


@pytest.mark.asyncio
async def test_network_overview_resource(mock_mcp_server):
    """Test network_overview resource."""
    register_resources(mock_mcp_server)

    async with Client(mock_mcp_server) as client:
        text = await _resource_text(client, "network/overview")

    assert "Vienna" in text
    assert "U-Bahn" in text or "Metro" in text


@pytest.mark.asyncio
async def test_major_stations_resource(mock_mcp_server, mock_data_loader):
    """Test major_stations resource."""
    register_resources(mock_mcp_server)

    # Mock data_loader
    from unittest.mock import patch

    with patch("mcp_server.resources.data_loader", mock_data_loader):
        async with Client(mock_mcp_server) as client:
            text = await _resource_text(client, "stations/major")

    assert "Station" in text


@pytest.mark.asyncio
async def test_metro_lines_resource(mock_mcp_server):
    """Test metro_lines resource."""
    register_resources(mock_mcp_server)

    async with Client(mock_mcp_server) as client:
        text = await _resource_text(client, "lines/metro")

    assert "U1" in text or "U-Bahn" in text


@pytest.mark.asyncio
async def test_operating_hours_resource(mock_mcp_server):
    """Test operating_hours resource."""
    register_resources(mock_mcp_server)

    async with Client(mock_mcp_server) as client:
        text = await _resource_text(client, "operating-hours")

    assert "hours" in text.lower() or "operating" in text.lower()


@pytest.mark.asyncio
async def test_fare_information_resource(mock_mcp_server):
    """Test fare_information resource."""
    register_resources(mock_mcp_server)

    async with Client(mock_mcp_server) as client:
        text = await _resource_text(client, "fares")

    assert "€" in text or "fare" in text.lower() or "ticket" in text.lower()
