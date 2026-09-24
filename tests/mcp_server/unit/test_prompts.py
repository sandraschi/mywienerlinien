"""Unit tests for MCP prompts."""

from __future__ import annotations

from fastmcp import Client

from mcp_server.prompts import register_prompts


def test_prompts_registration(mock_mcp_server):
    """Test that prompts are registered correctly."""
    prompt_refs = register_prompts(mock_mcp_server)

    assert len(prompt_refs) == 5
    assert "vienna_transit_guide" in [p.__name__ for p in prompt_refs]
    assert "departure_checking_prompt" in [p.__name__ for p in prompt_refs]
    assert "journey_planning_prompt" in [p.__name__ for p in prompt_refs]


async def _prompt_blob(client: Client, needle: str) -> str:
    """Fetch the first prompt whose name contains needle; return messages as text."""
    prompts = await client.list_prompts()
    names = [p.name for p in prompts]
    match = next((n for n in names if needle in n), None)
    assert match is not None, f"no prompt matching {needle!r} in {names}"
    result = await client.get_prompt(match)
    assert result.messages
    return str(result.messages)


async def test_vienna_transit_guide_prompt(mock_mcp_server):
    """Test vienna_transit_guide prompt content."""
    register_prompts(mock_mcp_server)

    async with Client(mock_mcp_server) as client:
        blob = await _prompt_blob(client, "vienna_transit_guide")

    assert "Vienna" in blob


async def test_departure_checking_prompt(mock_mcp_server):
    """Test departure_checking_prompt content."""
    register_prompts(mock_mcp_server)

    async with Client(mock_mcp_server) as client:
        blob = await _prompt_blob(client, "departure_checking")

    assert "departure" in blob.lower()


async def test_journey_planning_prompt(mock_mcp_server):
    """Test journey_planning_prompt content."""
    register_prompts(mock_mcp_server)

    async with Client(mock_mcp_server) as client:
        blob = await _prompt_blob(client, "journey_planning")

    assert "journey" in blob.lower() or "planning" in blob.lower()
