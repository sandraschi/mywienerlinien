"""Middleware for MCP server."""

from .error_handler import register_error_handler_middleware
from .logging import register_logging_middleware

__all__ = [
    "register_logging_middleware",
    "register_error_handler_middleware",
]
