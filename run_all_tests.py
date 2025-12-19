#!/usr/bin/env python3
"""
Unified Test Runner for Immich MCP

Runs comprehensive tests using both direct function calls and MCP protocol.
Provides unified reporting and test management.

Usage:
    python run_all_tests.py              # Run all tests
    python run_all_tests.py --quick      # Quick smoke test
    python run_all_tests.py --mcp-only   # MCP protocol only
    python run_all_tests.py --funcs-only # Function tests only
    python run_all_tests.py --cleanup    # Clean up test data
"""

import argparse
import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

# Add src to path
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))


class UnifiedTestRunner:
    """Unified test runner for all Immich MCP testing."""

    def __init__(self):
        self.results = {}
        self.test_data = {
            "assets": [],
            "albums": [],
            "start_time": None,
            "end_time": None
        }

    async def run_smoke_test(self) -> dict:
        """Quick smoke test to verify basic functionality."""
        print("[SMOKE] Running Smoke Test...")

        from immich_mcp.server import server_health

        try:
            health = await server_health()
            return {
                "status": "PASS",
                "server_version": health.server_version,
                "is_v2_plus": health.is_v2_plus
            }
        except Exception as e:
            return {"status": "FAIL", "error": str(e)}

    async def run_function_tests(self) -> dict:
        """Run direct function tests."""
        print("[FUNC] Running Function Tests...")

        from test_scaffold import ImmichTestScaffold

        scaffold = ImmichTestScaffold()
        test_files = scaffold.create_test_photos()

        # Run key tests
        results = {}

        # Health check
        results["server_health"] = await scaffold.test_server_health()

        # Upload test
        results["photo_upload"] = await scaffold.test_photo_upload(test_files)

        # Extract uploaded assets
        if results["photo_upload"]["status"] == "PASS":
            self.test_data["assets"] = results["photo_upload"]["data"]["uploaded_assets"]

        # Album tests
        results["album_creation"] = await scaffold.test_album_creation()
        if results["album_creation"]["status"] == "PASS":
            self.test_data["albums"] = results["album_creation"]["albums_created"]

        # Search test
        results["photo_search"] = await scaffold.test_photo_search()

        # Storage test
        results["storage_backup"] = await scaffold.test_storage_and_backup()

        return results

    async def run_mcp_tests(self) -> dict:
        """Run MCP protocol tests."""
        print("[MCP] Running MCP Protocol Tests...")

        from mcp_test_client import MCPTestClient

        client = MCPTestClient()
        await client.initialize_server()

        # Run comprehensive MCP tests
        await client.run_comprehensive_tests()

        return client.test_results

    async def cleanup_test_data(self) -> dict:
        """Clean up test data (CAUTION: destructive)."""
        print("[CLEAN] Cleaning up test data...")

        # This would be implemented to safely remove test albums/assets
        # For now, just return status
        return {"status": "SKIPPED", "message": "Cleanup not implemented for safety"}

    async def run_full_test_suite(self, args) -> dict:
        """Run complete test suite based on arguments."""
        self.test_data["start_time"] = datetime.now()

        print("[TARGET] Immich MCP Unified Test Suite")
        print("=" * 50)

        results = {
            "timestamp": datetime.now().isoformat(),
            "test_config": vars(args),
            "test_results": {}
        }

        # Smoke test (always run)
        if not args.mcp_only:
            print("\n" + "-"*30 + " SMOKE TEST " + "-"*30)
            results["test_results"]["smoke_test"] = await self.run_smoke_test()

        # Function tests
        if not args.mcp_only:
            print("\n" + "-"*30 + " FUNCTION TESTS " + "-"*30)
            results["test_results"]["function_tests"] = await self.run_function_tests()

        # MCP tests
        if not args.funcs_only:
            print("\n" + "-"*30 + " MCP PROTOCOL TESTS " + "-"*30)
            results["test_results"]["mcp_tests"] = await self.run_mcp_tests()

        # Cleanup
        if args.cleanup:
            print("\n" + "-"*30 + " CLEANUP " + "-"*30)
            results["test_results"]["cleanup"] = await self.cleanup_test_data()

        self.test_data["end_time"] = datetime.now()

        # Generate summary
        results["summary"] = self.generate_summary(results)

        # Save results
        self.save_results(results)

        return results

    def generate_summary(self, results: dict) -> dict:
        """Generate test summary."""
        summary = {
            "total_tests": 0,
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "success_rate": "0%"
        }

        def count_results(data):
            if isinstance(data, dict):
                if "status" in data:
                    summary["total_tests"] += 1
                    status = data["status"]
                    if status in ["PASS", "success"]:
                        summary["passed"] += 1
                    elif status in ["FAIL", "error"]:
                        summary["failed"] += 1
                    elif status == "SKIPPED":
                        summary["skipped"] += 1

                for value in data.values():
                    count_results(value)
            elif isinstance(data, list):
                for item in data:
                    count_results(item)

        count_results(results["test_results"])

        if summary["total_tests"] > 0:
            summary["success_rate"] = ".1f"

        return summary

    def save_results(self, results: dict):
        """Save test results to file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"test_results_{timestamp}.json"

        with open(filename, 'w') as f:
            json.dump(results, f, indent=2, default=str)

        print(f"\n[SAVE] Results saved to: {filename}")

        # Also save latest results
        with open("latest_test_results.json", 'w') as f:
            json.dump(results, f, indent=2, default=str)

    def print_summary(self, results: dict):
        """Print human-readable summary."""
        summary = results["summary"]

        print("\n" + "="*60)
        print("[TARGET] TEST SUITE SUMMARY")
        print("="*60)
        print(f"Total Tests: {summary['total_tests']}")
        print(f"Passed:      {summary['passed']}")
        print(f"Failed:      {summary['failed']}")
        print(f"Skipped:     {summary['skipped']}")
        print(f"Success:     {summary['success_rate']}")
        print("="*60)

        if self.test_data["assets"]:
            print(f"📸 Assets Created: {len(self.test_data['assets'])}")
        if self.test_data["albums"]:
            print(f"📁 Albums Created: {len(self.test_data['albums'])}")

        duration = None
        if self.test_data["start_time"] and self.test_data["end_time"]:
            duration = self.test_data["end_time"] - self.test_data["start_time"]
            print(f"[TIME]  Duration: {duration.total_seconds():.1f}s")

        print("="*60)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Immich MCP Test Runner")
    parser.add_argument("--quick", action="store_true", help="Run quick smoke test only")
    parser.add_argument("--funcs-only", action="store_true", help="Run function tests only")
    parser.add_argument("--mcp-only", action="store_true", help="Run MCP protocol tests only")
    parser.add_argument("--cleanup", action="store_true", help="Clean up test data after testing")

    args = parser.parse_args()

    # Handle quick test
    if args.quick:
        async def quick_test():
            runner = UnifiedTestRunner()
            result = await runner.run_smoke_test()
            print(f"Smoke Test: {'✅ PASS' if result['status'] == 'PASS' else '❌ FAIL'}")
            if result["status"] == "FAIL":
                print(f"Error: {result.get('error', 'Unknown')}")
        asyncio.run(quick_test())
        return

    # Run full test suite
    runner = UnifiedTestRunner()
    results = asyncio.run(runner.run_full_test_suite(args))
    runner.print_summary(results)


if __name__ == "__main__":
    main()
