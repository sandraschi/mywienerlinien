"""Self-termination tool for the Vienna Transit MCP server."""

from fastmcp import FastMCP
from mcp.types import ToolAnnotations
from pydantic import BaseModel, Field


class ShutdownResponse(BaseModel):
    """Shutdown acknowledgement."""

    status: str = Field(..., description="ok when the request was accepted")
    message: str = Field(..., description="How shutdown proceeds for each transport")


def register_shutdown_tool(mcp: FastMCP) -> None:
    """Register the server_shutdown tool with the MCP server."""

    @mcp.tool(annotations=ToolAnnotations(destructiveHint=True, idempotentHint=False, openWorldHint=False))
    async def server_shutdown() -> ShutdownResponse:
        """Request an orderly server shutdown.

        The stdio transport is owned by the MCP host: calling this tool does
        not kill the process outright. Real termination happens via
        POST /api/shutdown on the web backend (exits after 500 ms) or by the
        host closing the stdio session.

        ## Return Format
        ShutdownResponse JSON: `status` ("ok") plus a `message` describing
        how shutdown proceeds for each transport.

        ## Examples
        ```python
        result = await server_shutdown()
        ```
        """
        return ShutdownResponse(
            status="ok",
            message=(
                "Shutdown acknowledged. Web backend exits via POST /api/shutdown; "
                "the stdio server exits when the MCP host closes the session."
            ),
        )
