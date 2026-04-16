#!/usr/bin/env python3
"""
MCP Client Test Script for Immich MCP Server

Tests all MCP tools using the MCP protocol over stdio.
This simulates how Claude Desktop would interact with the Immich MCP server.

Usage:
    python mcp_test_client.py
"""

import asyncio
import json
import sys
from pathlib import Path

# Add src to path
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

from immich_mcp.server import ImmichMCP


class MCPTestClient:
    """Test client that simulates MCP protocol interactions."""

    def __init__(self):
        self.mcp_server = ImmichMCP()
        self.test_results = {}

    async def initialize_server(self):
        """Initialize the MCP server."""
        await self.mcp_server.startup_event()

    async def call_tool(self, tool_name: str, arguments: dict) -> dict:
        """Call an MCP tool and return the result."""

        try:
            # Find the tool method
            tool_method = getattr(self.mcp_server, tool_name, None)
            if not tool_method:
                raise ValueError(f"Tool '{tool_name}' not found")

            # Call the tool
            result = await tool_method(**arguments)

            if hasattr(result, "dict"):
                pass
            else:
                pass

            return {"status": "success", "result": result}

        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def run_comprehensive_tests(self):
        """Run comprehensive tests of all MCP tools."""

        # Test data - use real 1998 photos
        test_photo_paths = [
            str(Path(__file__).parent / "test_photos" / f)
            for f in [
                "Hol 99 - Mira the Dog 1 [digicam].JPG",
                "Hol 99 - Mira the Dog 2 [digicam].JPG",
                "Hol 99 - SAS self portrait in bed.JPG",
                "Hol 99 - Atmos Clock [digicam].JPG",
                "Hol 99 - Dried Flowers on Mantelpiece.JPG",
            ]
        ]

        # Test 1: Server Health
        result = await self.call_tool("server_health", {})
        self.test_results["server_health"] = result

        # Test 2: Photo Upload
        result = await self.call_tool(
            "upload_photos", {"file_paths": test_photo_paths, "album_name": "MCP Test Album", "auto_organize": False}
        )
        self.test_results["upload_photos"] = result

        # Extract uploaded asset IDs for further tests
        uploaded_assets = []
        if result["status"] == "success" and hasattr(result["result"], "uploaded_assets"):
            uploaded_assets = result["result"].uploaded_assets

        # Test 3: Storage Info
        result = await self.call_tool("get_storage_info", {})
        self.test_results["get_storage_info"] = result

        # Test 4: List Albums
        result = await self.call_tool("list_albums", {"include_stats": True})
        self.test_results["list_albums"] = result

        # Extract album ID for further tests
        if result["status"] == "success" and result["result"]:
            result["result"][0].id if result["result"] else None

        # Test 5: Search Photos (Smart Search)
        result = await self.call_tool("search_photos", {"query": "beach", "search_type": "smart", "limit": 10})
        self.test_results["search_smart"] = result

        # Test 6: Search Photos (Metadata)
        result = await self.call_tool("search_photos", {"query": "vacation", "search_type": "metadata", "limit": 10})
        self.test_results["search_metadata"] = result

        # Test 7: Get Photo Info (if we have assets)
        if uploaded_assets:
            result = await self.call_tool("get_photo_info", {"asset_id": uploaded_assets[0]})
            self.test_results["get_photo_info"] = result

            # Test 8: OCR Data
            result = await self.call_tool("get_ocr_data", {"asset_id": uploaded_assets[0]})
            self.test_results["get_ocr_data"] = result

            # Test 9: Asset OCR
            result = await self.call_tool("get_asset_ocr", {"asset_id": uploaded_assets[0]})
            self.test_results["get_asset_ocr"] = result

        # Test 10: Create Album
        result = await self.call_tool(
            "create_album", {"name": "MCP Created Album", "description": "Album created by MCP test suite"}
        )
        self.test_results["create_album"] = result

        new_album_id = None
        if result["status"] == "success":
            new_album_id = result["result"].id

        # Test 11: Add to Album (if we have both assets and album)
        if uploaded_assets and new_album_id:
            result = await self.call_tool(
                "add_to_album",
                {
                    "album_id": new_album_id,
                    "asset_ids": uploaded_assets[:2],  # Add first 2 assets
                },
            )
            self.test_results["add_to_album"] = result

        # Test 12: Share Album (if we have an album)
        if new_album_id:
            result = await self.call_tool(
                "share_album", {"album_id": new_album_id, "allow_download": True, "allow_upload": False}
            )
            self.test_results["share_album"] = result

        # Test 13: Organize by Date (if we have assets)
        if uploaded_assets:
            result = await self.call_tool(
                "organize_photos_by_date", {"asset_ids": uploaded_assets, "organization_type": "year_month"}
            )
            self.test_results["organize_by_date"] = result

        # Test 14: Face Detection (if we have assets)
        if uploaded_assets:
            result = await self.call_tool(
                "detect_people",
                {
                    "asset_ids": uploaded_assets[:3]  # Test on first 3 assets
                },
            )
            self.test_results["detect_people"] = result

        # Test 15: Backup Photos
        backup_path = str(Path(__file__).parent / "test_backup")
        result = await self.call_tool("backup_photos", {"backup_path": backup_path, "include_metadata": True})
        self.test_results["backup_photos"] = result

        # Generate test report
        await self.generate_report()

    async def generate_report(self):
        """Generate comprehensive test report."""

        total_tests = len(self.test_results)
        successful_tests = sum(1 for result in self.test_results.values() if result["status"] == "success")
        total_tests - successful_tests

        for _test_name, result in self.test_results.items():
            "[OK]" if result["status"] == "success" else "[FAIL]"

        # Save detailed report
        report_path = Path(__file__).parent / "mcp_test_report.json"
        with open(report_path, "w") as f:
            json.dump(self.test_results, f, indent=2, default=str)


async def main():
    """Main test runner."""
    client = MCPTestClient()
    await client.initialize_server()
    await client.run_comprehensive_tests()


if __name__ == "__main__":
    asyncio.run(main())
