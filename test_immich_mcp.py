#!/usr/bin/env python3
"""
Test script for ImmichMCP server.

This script demonstrates how to use the ImmichMCP server functionality directly.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the current directory to the path so we can import immich_mcp_server
sys.path.append(str(Path(__file__).parent))

from immich_mcp_server import (
    ImmichClient,
    UploadResult,
    PhotoInfo,
    server_health
)

async def test_connection():
    """Test connection to Immich server."""
    print("\n=== Testing Server Connection ===")
    health = await server_health()
    print(f"Server Health: {health}")

async def test_upload_photos():
    """Test photo upload functionality."""
    print("\n=== Testing Photo Upload ===")
    
    # Create a test file
    test_file = Path("test_photo.jpg")
    try:
        # Create a small test file (1KB)
        test_file.write_bytes(b"\x00" * 1024)
        
        # Test upload
        client = ImmichClient(
            base_url=os.getenv("IMMICH_URL", "http://localhost:2283"),
            api_key=os.getenv("IMMICH_API_KEY", "")
        )
        
        result = await client.upload_asset(test_file)
        print(f"Upload Result: {result}")
        
        # Test getting photo info
        if "id" in result:
            print("\n=== Testing Get Photo Info ===")
            photo_info = await client.get_photo_info(result["id"])
            print(f"Photo Info: {photo_info}")
    
    finally:
        # Clean up test file
        if test_file.exists():
            test_file.unlink()

async def main():
    """Run all tests."""
    print("=== Starting ImmichMCP Tests ===")
    
    # Check required environment variables
    if not os.getenv("IMMICH_API_KEY"):
        print("Error: IMMICH_API_KEY environment variable is required")
        return
    
    await test_connection()
    await test_upload_photos()
    
    print("\n=== Tests Complete ===")

if __name__ == "__main__":
    asyncio.run(main())
