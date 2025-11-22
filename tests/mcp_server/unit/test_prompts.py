"""Unit tests for MCP prompts."""

from __future__ import annotations

from mcp_server.prompts import register_prompts


def test_prompts_registration(mock_mcp_server):
    """Test that prompts are registered correctly."""
    prompt_refs = register_prompts(mock_mcp_server)

    assert len(prompt_refs) == 3
    assert "vienna_transit_guide" in [p.__name__ for p in prompt_refs]
    assert "departure_checking_prompt" in [p.__name__ for p in prompt_refs]
    assert "journey_planning_prompt" in [p.__name__ for p in prompt_refs]


def test_vienna_transit_guide_prompt(mock_mcp_server):
    """Test vienna_transit_guide prompt content."""
    register_prompts(mock_mcp_server)

    # Get the prompt function
    prompt_func = None
    for name, func in mock_mcp_server._prompts.items():
        if "vienna_transit_guide" in name:
            prompt_func = func
            break

    assert prompt_func is not None

    # Execute
    result = prompt_func()

    # Assert
    assert isinstance(result, list)
    assert len(result) > 0
    assert result[0]["role"] == "user"
    assert "Vienna" in result[0]["content"]


def test_departure_checking_prompt(mock_mcp_server):
    """Test departure_checking_prompt content."""
    register_prompts(mock_mcp_server)

    # Get the prompt function
    prompt_func = None
    for name, func in mock_mcp_server._prompts.items():
        if "departure_checking" in name:
            prompt_func = func
            break

    assert prompt_func is not None

    # Execute
    result = prompt_func()

    # Assert
    assert isinstance(result, list)
    assert result[0]["role"] == "user"
    assert "departure" in result[0]["content"].lower()


def test_journey_planning_prompt(mock_mcp_server):
    """Test journey_planning_prompt content."""
    register_prompts(mock_mcp_server)

    # Get the prompt function
    prompt_func = None
    for name, func in mock_mcp_server._prompts.items():
        if "journey_planning" in name:
            prompt_func = func
            break

    assert prompt_func is not None

    # Execute
    result = prompt_func()

    # Assert
    assert isinstance(result, list)
    assert result[0]["role"] == "user"
    assert "journey" in result[0]["content"].lower() or "planning" in result[0]["content"].lower()
