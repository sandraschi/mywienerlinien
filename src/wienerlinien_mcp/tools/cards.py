"""Prefab App cards for the Vienna Transit MCP server.

List/status-class outputs ship a Prefab UI surface alongside the mandatory
plain-text summary (SOTA_REQUIREMENTS.md 2.2). Registration is skipped when
``WIENERLINEN_PREFAB_APPS=0`` (CI / headless); the ``prefab_ui`` import itself
always succeeds.
"""

import logging
import os
import time
from typing import Annotated

from fastmcp import FastMCP
from fastmcp.tools import ToolResult
from fastmcp.tools.tool import ToolAnnotations
from prefab_ui.app import PrefabApp
from prefab_ui.components import Card, CardContent, CardHeader, Text
from pydantic import Field

from wienerlinien_mcp.tools.departures import get_next_departures_internal

logger = logging.getLogger(__name__)

_server_start_time = time.time()


def _status_lines() -> list[str]:
    uptime = int(time.time() - _server_start_time)
    return [
        "Vienna Transit MCP",
        f"status: healthy (uptime {uptime // 3600}h {(uptime % 3600) // 60}m)",
        "backend: http://127.0.0.1:11170/api/health",
    ]


def register_cards(mcp: FastMCP) -> None:
    """Register Prefab App card tools (env-gated)."""
    if os.getenv("WIENERLINEN_PREFAB_APPS", "1") != "1":
        logger.info("Prefab App cards disabled via WIENERLINEN_PREFAB_APPS=0")
        return

    @mcp.tool(
        app=True,
        annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True),
    )
    async def show_server_status_card() -> ToolResult:
        """Show the Vienna Transit server status as a UI card.

        ## Return Format
        ToolResult with plain-text `content` summary plus a
        `structured_content` PrefabApp card for MCP App hosts.

        ## Examples
        ```python
        result = await show_server_status_card()
        ```
        """
        lines = _status_lines()
        with Card(css_class="max-w-lg") as view:
            with CardHeader():
                Text(lines[0])
            with CardContent():
                for line in lines[1:]:
                    Text(line)
        summary = " | ".join(lines)
        return ToolResult(
            content=summary,
            structured_content=PrefabApp(title="Vienna Transit status", view=view),
        )

    @mcp.tool(
        app=True,
        annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True),
    )
    async def show_departures_card(
        station: Annotated[str, Field(description="Station name (fuzzy match supported).")],
        max_results: Annotated[int, Field(description="Max departures.", ge=1, le=10)] = 5,
    ) -> ToolResult:
        """Show next departures for a station as a UI card.

        ## Return Format
        ToolResult with plain-text `content` summary plus a
        `structured_content` PrefabApp card for MCP App hosts.

        ## Examples
        ```python
        result = await show_departures_card("Stephansplatz", max_results=3)
        ```
        """
        vehicles = await get_next_departures_internal(station, max_results)
        lines = [f"Departures for {station}:"]
        for v in (vehicles or [])[:max_results]:
            lines.append(f"{v.get('line', '?')} -> {v.get('next_station', '?')}")
        if len(lines) == 1:
            lines.append("No departures found.")
        with Card(css_class="max-w-lg") as view:
            with CardHeader():
                Text(lines[0])
            with CardContent():
                for line in lines[1:]:
                    Text(line)
        return ToolResult(
            content=" | ".join(lines),
            structured_content=PrefabApp(title=f"Departures: {station}", view=view),
        )
