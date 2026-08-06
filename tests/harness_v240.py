#!/usr/bin/env python3
"""
Comprehensive test harness for ImmichMCP v2.4.0 compatibility
Runs all tests and provides detailed reporting on API compatibility
Austrian efficiency: Complete test coverage with clear pass/fail reporting
"""

import asyncio
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import contextlib

from immich_mcp.config import ImmichConfig
from immich_mcp.immich_api import ImmichAPIClient, ImmichAPIError


class TestHarness:
    """Comprehensive test harness for ImmichMCP v2.4.0 compatibility"""

    def __init__(self):
        self.results = {
            "summary": {"total_tests": 0, "passed": 0, "failed": 0, "skipped": 0, "duration": 0},
            "tests": [],
            "server_info": {},
            "compatibility_score": 0,
        }

        # Get configuration from environment
        self.server_url = os.getenv("IMMICH_SERVER_URL", "http://localhost:2283")
        self.api_key = os.getenv("IMMICH_API_KEY")

        if not self.api_key:
            sys.exit(1)

        self.config = ImmichConfig(server_url=self.server_url, api_key=self.api_key, timeout=60)

    async def run_all_tests(self) -> dict[str, Any]:
        """Run complete test suite"""
        start_time = time.time()

        try:
            # Initialize API client
            self.api_client = ImmichAPIClient(self.config)

            # Test basic connectivity
            await self.test_basic_connectivity()

            # Run all test categories
            await self.test_search_endpoints()
            await self.test_asset_access()
            await self.test_server_info()
            await self.test_backward_compatibility()
            await self.test_ocr_functionality()
            await self.test_performance()
            await self.test_error_handling()

            # Calculate compatibility score
            self.calculate_compatibility_score()

        except Exception as e:
            self.record_test("initialization", False, f"Failed to initialize: {e}")

        finally:
            duration = time.time() - start_time
            self.results["summary"]["duration"] = duration

        return self.results

    def record_test(self, test_name: str, passed: bool, message: str = "", details: dict | None = None):
        """Record a test result"""
        self.results["summary"]["total_tests"] += 1

        if passed:
            self.results["summary"]["passed"] += 1
            status = "PASS"
        else:
            self.results["summary"]["failed"] += 1
            status = "FAIL"

        test_result = {
            "name": test_name,
            "status": status,
            "passed": passed,
            "message": message,
            "details": details or {},
        }

        self.results["tests"].append(test_result)

    async def test_basic_connectivity(self):
        """Test basic server connectivity"""
        try:
            server_info = await self.api_client.get_server_info()
            self.results["server_info"] = server_info

            self.record_test(
                "basic_connectivity",
                True,
                f"Connected to Immich {server_info.get('version', 'Unknown')}",
                {"server_info": server_info},
            )

        except Exception as e:
            self.record_test("basic_connectivity", False, f"Connection failed: {e}")

    async def test_search_endpoints(self):
        """Test search endpoint functionality"""
        # Test search/metadata endpoint (POST only in v2.7+/v3)
        try:
            result = await self.api_client._post("/search/metadata", data={"page": 1, "size": 10})

            if "assets" in result and "items" in result["assets"]:
                self.record_test(
                    "search_metadata_endpoint", True, f"Found {result['assets']['total']} assets via search/metadata"
                )
            else:
                self.record_test("search_metadata_endpoint", False, "Invalid response structure")

        except Exception as e:
            self.record_test("search_metadata_endpoint", False, f"Search endpoint failed: {e}")

        # Test smart search
        try:
            results = await self.api_client.search_photos("test", search_type="smart", limit=5)
            self.record_test("smart_search", True, f"Smart search returned {len(results)} results")
        except Exception as e:
            self.record_test("smart_search", False, f"Smart search failed: {e}")

        # Test filename search
        try:
            results = await self.api_client.search_photos("", search_type="filename", limit=5)
            self.record_test("filename_search", True, f"Filename search returned {len(results)} results")
        except Exception as e:
            self.record_test("filename_search", False, f"Filename search failed: {e}")

    async def test_asset_access(self):
        """Test asset access and retrieval (GET /assets/{id} works since v2.4)"""
        # Test individual asset access
        try:
            assets = await self.api_client.search_photos("", search_type="filename", limit=1)
            if assets:
                asset_id = assets[0]["id"]
                try:
                    asset_info = await self.api_client._get(f"/assets/{asset_id}")
                    if asset_info.get("id") == asset_id:
                        self.record_test("individual_asset_access", True, "Individual asset access works")
                    else:
                        self.record_test("individual_asset_access", False, "Asset access returned wrong asset")
                except ImmichAPIError as e:
                    self.record_test("individual_asset_access", False, f"Asset access failed: {e}")
            else:
                self.record_test("individual_asset_access", True, "No assets to test (expected in empty library)")
        except Exception as e:
            self.record_test("individual_asset_access", False, f"Asset access test failed: {e}")

        # Test get_asset_info
        try:
            assets = await self.api_client.search_photos("", search_type="filename", limit=1)
            if assets:
                asset_id = assets[0]["id"]
                asset_info = await self.api_client.get_asset_info(asset_id)
                if asset_info["id"] == asset_id:
                    self.record_test("asset_info_fallback", True, "Asset info retrieval works correctly")
                else:
                    self.record_test("asset_info_fallback", False, "Asset info retrieval returned wrong asset")
            else:
                self.record_test("asset_info_fallback", True, "No assets to test (expected in empty library)")
        except Exception as e:
            self.record_test("asset_info_fallback", False, f"Asset info retrieval failed: {e}")

    async def test_server_info(self):
        """Test server info adaptation"""
        try:
            server_info = await self.api_client.get_server_info()

            checks = {
                "version_detection": "version" in server_info,
                "v2_plus_detection": server_info.get("is_v2_plus") is True,
                "api_architecture": server_info.get("api_architecture") == "search_based",
                "individual_access_flag": server_info.get("individual_asset_access") is True,
            }

            passed_checks = sum(checks.values())
            total_checks = len(checks)

            if passed_checks == total_checks:
                self.record_test(
                    "server_info_adaptation", True, f"All server info checks passed ({passed_checks}/{total_checks})"
                )
            else:
                failed = [k for k, v in checks.items() if not v]
                self.record_test("server_info_adaptation", False, f"Failed checks: {failed}")

        except Exception as e:
            self.record_test("server_info_adaptation", False, f"Server info test failed: {e}")

        # Test server stats
        try:
            server_stats = await self.api_client.get_server_stats()

            if server_stats.get("api_version") != "unknown":
                self.record_test("server_stats_adaptation", True, "Server stats retrieved from real endpoints")
            else:
                self.record_test("server_stats_adaptation", False, "Server stats not retrieved")

        except Exception as e:
            self.record_test("server_stats_adaptation", False, f"Server stats test failed: {e}")

    async def test_backward_compatibility(self):
        """Test that existing functionality still works"""
        # Test albums API
        try:
            albums = await self.api_client.get_albums()
            self.record_test("albums_api_compatibility", True, f"Albums API works: {len(albums)} albums")
        except Exception as e:
            self.record_test("albums_api_compatibility", False, f"Albums API failed: {e}")

        # Test album creation
        try:
            album = await self.api_client.create_album("Test Album v2.4.0", "Test album for compatibility")
            album_id = album["id"]

            # Clean up
            with contextlib.suppress(BaseException):
                await self.api_client._delete(f"/albums/{album_id}")

            self.record_test("album_creation_compatibility", True, "Album creation works")
        except Exception as e:
            self.record_test("album_creation_compatibility", False, f"Album creation failed: {e}")

    async def test_ocr_functionality(self):
        """Test OCR functionality detection and usage"""
        try:
            server_info = await self.api_client.get_server_info()
            has_ocr = server_info.get("has_ocr", False)

            if has_ocr:
                # Test OCR search
                try:
                    results = await self.api_client.search_photos("test", search_type="ocr", limit=3)
                    self.record_test("ocr_search_functionality", True, f"OCR search works: {len(results)} results")
                except Exception as e:
                    self.record_test("ocr_search_functionality", False, f"OCR search failed: {e}")
            else:
                self.record_test("ocr_detection", True, "OCR correctly detected as unavailable")

        except Exception as e:
            self.record_test("ocr_functionality", False, f"OCR test failed: {e}")

    async def test_performance(self):
        """Test performance characteristics"""
        try:
            import time

            # Test search performance
            start = time.time()
            results = await self.api_client.search_photos("", search_type="filename", limit=50)
            duration = time.time() - start

            if duration < 5.0:  # Should be fast
                self.record_test(
                    "search_performance", True, f"Search performance good: {duration:.2f}s for {len(results)} results"
                )
            else:
                self.record_test(
                    "search_performance", False, f"Search too slow: {duration:.2f}s for {len(results)} results"
                )

        except Exception as e:
            self.record_test("search_performance", False, f"Performance test failed: {e}")

    async def test_error_handling(self):
        """Test error handling and graceful degradation"""
        # Test invalid asset ID
        try:
            await self.api_client.get_asset_info("invalid-asset-id-12345")
            self.record_test("invalid_asset_handling", False, "Should have failed for invalid asset ID")
        except ImmichAPIError as e:
            if "not found" in str(e).lower():
                self.record_test("invalid_asset_handling", True, "Invalid asset ID correctly handled")
            else:
                self.record_test("invalid_asset_handling", False, f"Unexpected error: {e}")

    def calculate_compatibility_score(self):
        """Calculate overall compatibility score"""
        total = self.results["summary"]["total_tests"]
        passed = self.results["summary"]["passed"]

        if total > 0:
            score = (passed / total) * 100
            self.results["compatibility_score"] = score

            if score >= 90 or score >= 80 or score >= 70:
                pass
            else:
                pass

    def print_summary(self):
        """Print detailed test summary"""
        self.results["summary"]

        # Show server info
        if self.results["server_info"]:
            self.results["server_info"]

        # Show failed tests
        failed_tests = [t for t in self.results["tests"] if not t["passed"]]
        if failed_tests:
            for _test in failed_tests:
                pass

        # Show recommendations
        if self.results["compatibility_score"] < 80:
            pass

    def save_results(self, filename: str | None = None):
        """Save test results to JSON file"""
        if not filename:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"immich_mcp_v240_test_results_{timestamp}.json"

        with open(filename, "w") as f:
            json.dump(self.results, f, indent=2, default=str)


async def main():
    """Main test harness execution"""
    harness = TestHarness()

    try:
        await harness.run_all_tests()
        harness.print_summary()

        # Save results
        harness.save_results()

        # Exit with appropriate code
        score = harness.results["compatibility_score"]
        if score >= 80:
            sys.exit(0)
        else:
            sys.exit(1)

    except KeyboardInterrupt:
        sys.exit(130)
    except Exception:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
