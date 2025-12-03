"""Error handling middleware for MCP server."""

import logging

from fastmcp import FastMCP

logger = logging.getLogger("mcp_server")


def register_error_handler_middleware(mcp: FastMCP) -> None:
    """Register error handling middleware."""

    @mcp.middleware()
    async def error_handler_middleware(request, call_next):
        """Handle errors and return user-friendly messages."""
        try:
            return await call_next(request)
        except ValueError as e:
            # User input errors - return clear message
            logger.warning(f"User input error: {e}")
            raise
        except Exception as e:
            # Internal errors - log and return generic message
            logger.error(f"Internal error: {e}", exc_info=True)
            raise RuntimeError(f"An error occurred: {str(e)}") from e
