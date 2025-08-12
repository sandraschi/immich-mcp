#!/usr/bin/env python3
"""
Quick verification that the Immich MCP server imports correctly after the fix.
"""

import sys
import traceback
from pathlib import Path

# Add the current directory to the path
sys.path.insert(0, str(Path(__file__).parent))

print("🔧 Testing Immich MCP Server Fix...")
print("=" * 50)

try:
    # Test FastMCP import and basic initialization
    print("1️⃣ Testing FastMCP import...")
    from fastmcp import FastMCP
    
    # Test basic constructor (what we fixed)
    test_mcp = FastMCP("test-server")
    print(f"✅ FastMCP constructor works: {type(test_mcp)}")
    
    # Test importing the main server module
    print("\n2️⃣ Testing immich_mcp_server import...")
    import immich_mcp_server
    print(f"✅ Server module imported successfully")
    print(f"   MCP instance type: {type(immich_mcp_server.mcp)}")
    
    # Check if tools are registered
    if hasattr(immich_mcp_server.mcp, '_tools'):
        tool_count = len(immich_mcp_server.mcp._tools)
        print(f"   Registered tools: {tool_count}")
        if tool_count > 0:
            tool_names = list(immich_mcp_server.mcp._tools.keys())[:5]  # First 5
            print(f"   Sample tools: {tool_names}")
    
    print("\n🎉 SUCCESS: Server should now work with Claude Desktop!")
    print("✅ FastMCP constructor fix is working")
    print("✅ All imports successful")
    print("✅ MCP server instance created")
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    print("\nFull traceback:")
    traceback.print_exc()
    
print("\n" + "=" * 50)
