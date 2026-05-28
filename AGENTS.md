# vienna-transit-mcp — Agent Guide

## Overview
Vienna Transit MCP Server - FastMCP 3.1.0x compliant MCP server for Vienna public transport information

## Entry Points
- `uv run vienna-transit-mcp` → `wienerlinien_mcp.server:mcp.run`

## Standards
- FastMCP 3.2+ portmanteau tool pattern — tools use `operation` enum param
- Responses: structured dicts with `success`, `message`, domain-specific fields
- Dual transport: stdio (Claude Desktop) + HTTP (`MCP_TRANSPORT=http`)
- See [mcp-central-docs](https://github.com/sandraschi/mcp-central-docs) for fleet-wide coding standards

## Key Files
- `README.md` — full documentation
- `pyproject.toml` — build config and entry points
- `CLAUDE.md` — Claude Code context (if present)
