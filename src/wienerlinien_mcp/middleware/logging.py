"""Logging middleware for MCP server (FastMCP 3.4 API)."""

import logging

from fastmcp import FastMCP
from fastmcp.server.middleware import CallNext, Middleware, MiddlewareContext

logger = logging.getLogger("wienerlinien_mcp")


class LoggingMiddleware(Middleware):
    """Log every tool call and its outcome."""

    async def on_call_tool(self, context: MiddlewareContext, call_next: CallNext):
        tool_name = getattr(getattr(context, "message", None), "name", "unknown")
        logger.info(f"MCP tool call: {tool_name}")
        try:
            response = await call_next(context)
            logger.info(f"MCP tool response: {tool_name} - success")
            return response
        except Exception as e:
            logger.error(f"MCP tool error: {tool_name} - {e}", exc_info=True)
            raise


def register_logging_middleware(mcp: FastMCP) -> None:
    """Register logging middleware to log all tool calls."""
    mcp.add_middleware(LoggingMiddleware())
