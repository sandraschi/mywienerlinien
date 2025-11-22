"""Logging middleware for MCP server."""

import logging
from fastmcp import FastMCP

logger = logging.getLogger("mcp_server")


def register_logging_middleware(mcp: FastMCP) -> None:
    """Register logging middleware to log all tool calls."""
    
    @mcp.middleware()
    async def logging_middleware(request, call_next):
        """Log tool calls and responses."""
        tool_name = getattr(request, "tool_name", "unknown")
        logger.info(f"MCP tool call: {tool_name}")
        
        try:
            response = await call_next(request)
            logger.info(f"MCP tool response: {tool_name} - success")
            return response
        except Exception as e:
            logger.error(f"MCP tool error: {tool_name} - {e}", exc_info=True)
            raise

