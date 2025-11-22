"""Middleware for MCP server."""

from .logging import register_logging_middleware
from .error_handler import register_error_handler_middleware

__all__ = [
    "register_logging_middleware",
    "register_error_handler_middleware",
]

