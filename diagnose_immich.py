#!/usr/bin/env python3
"""
Quick test for Immich MCP server to diagnose the issues.
"""

import sys
import os
from pathlib import Path

print("🔍 Immich MCP Server Diagnostics")
print("=" * 50)

# Add current directory to path
current_dir = Path(__file__).parent.absolute()
sys.path.insert(0, str(current_dir))

print(f"📁 Working directory: {current_dir}")
print(f"🐍 Python version: {sys.version}")

# Test 1: Check FastMCP import
print("\n1️⃣ Testing FastMCP import...")
try:
    import fastmcp
    print(f"✅ FastMCP imported successfully")
    print(f"   Version: {getattr(fastmcp, '__version__', 'unknown')}")
    
    # Check FastMCP constructor
    from fastmcp import FastMCP
    print(f"   FastMCP class: {FastMCP}")
    
    # Test basic constructor
    test_mcp = FastMCP("test-server")
    print(f"✅ FastMCP constructor works with simple name")
    
except ImportError as e:
    print(f"❌ FastMCP import failed: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ FastMCP constructor failed: {e}")
    sys.exit(1)

# Test 2: Check other dependencies
print("\n2️⃣ Testing other dependencies...")
try:
    import httpx
    print(f"✅ httpx: {httpx.__version__}")
except ImportError:
    print("❌ httpx not available")

try:
    import pydantic
    print(f"✅ pydantic: {pydantic.__version__}")
except ImportError:
    print("❌ pydantic not available")

try:
    from dotenv import load_dotenv
    print(f"✅ python-dotenv available")
except ImportError:
    print("❌ python-dotenv not available")

# Test 3: Environment variables
print("\n3️⃣ Testing environment variables...")
load_dotenv()

immich_url = os.getenv("IMMICH_URL", "http://localhost:2283")
immich_api_key = os.getenv("IMMICH_API_KEY")

print(f"   IMMICH_URL: {immich_url}")
print(f"   IMMICH_API_KEY: {'***' + immich_api_key[-4:] if immich_api_key else 'NOT SET'}")

if not immich_api_key:
    print("⚠️  WARNING: IMMICH_API_KEY not set")

# Test 4: Try importing the main server module
print("\n4️⃣ Testing main server import...")
try:
    import immich_mcp_server
    print(f"✅ Main server module imported successfully")
    print(f"   MCP instance: {type(immich_mcp_server.mcp)}")
    print(f"   Available tools: {len(getattr(immich_mcp_server.mcp, '_tools', {}))}")
    
except Exception as e:
    print(f"❌ Main server import failed: {e}")
    import traceback
    traceback.print_exc()

print("\n🎯 Diagnostics complete!")
print("=" * 50)
