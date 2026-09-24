"""CI/local smoke check: the live MCP server imports and lists its tools."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from fastmcp import Client

from wienerlinien_mcp.server import mcp


async def main() -> None:
    async with Client(mcp) as client:
        tools = await client.list_tools()
        prompts = await client.list_prompts()
        resources = await client.list_resources()
    print(f"tools={len(tools)} prompts={len(prompts)} resources={len(resources)}")
    assert len(tools) >= 12, f"expected >=12 tools, got {len(tools)}"


if __name__ == "__main__":
    asyncio.run(main())
