"""Error handling middleware for MCP server (FastMCP 3.4 API)."""

import logging

from fastmcp import FastMCP
from fastmcp.server.middleware import CallNext, Middleware, MiddlewareContext

logger = logging.getLogger("wienerlinien_mcp")


class ErrorHandlerMiddleware(Middleware):
    """Turn internal errors into logged, user-friendly failures."""

    async def on_call_tool(self, context: MiddlewareContext, call_next: CallNext):
        try:
            return await call_next(context)
        except ValueError as e:
            # User input errors - return clear message
            logger.warning(f"User input error: {e}")
            raise
        except Exception as e:
            # Internal errors - log and return generic message
            logger.error(f"Internal error: {e}", exc_info=True)
            raise RuntimeError(f"An error occurred: {e!s}") from e


def register_error_handler_middleware(mcp: FastMCP) -> None:
    """Register error handling middleware."""
    mcp.add_middleware(ErrorHandlerMiddleware())
