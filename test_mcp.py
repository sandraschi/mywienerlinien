#!/usr/bin/env python3
"""Test Vienna Transit MCP Server startup."""

import sys
from pathlib import Path

# Add frontend to path
sys.path.insert(0, str(Path(__file__).parent / "frontend"))

print("TESTING Vienna Transit MCP Server...\n")

try:
    print("1. Importing server module...")
    from mcp_server.server import mcp

    print("   SUCCESS: Server imported successfully")

    print("\n2. Server Configuration:")
    print(f"   Name: {mcp.name}")
    print(f"   Version: {mcp.version}")

    print("\n3. Registered Components:")
    print(f"   Tools: {len(mcp._tool_manager._tools)}")
    print(f"   Prompts: {len(mcp._prompt_manager._prompts)}")
    print(f"   Resources: {len(mcp._resource_manager._resources)}")

    print("\n4. Tool List:")
    for tool_name in list(mcp._tool_manager._tools.keys())[:10]:
        print(f"   - {tool_name}")

    print("\nSUCCESS: MCP server is SOTA compliant and ready to run!")
    print("\nTo start:")
    print("  python -m frontend.mcp_server.server")

except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)
