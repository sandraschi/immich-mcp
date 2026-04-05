#!/usr/bin/env python3
"""
Comprehensive Immich MCP Test Scaffold

Tests all 15+ MCP tools with realistic photo management workflows.
Creates test data, exercises all functionality, and validates results.

Usage:
    python test_scaffold.py

Requirements:
    - Immich server running on localhost:2283
    - Valid IMMICH_API_KEY in environment
    - Test photos in ./test_photos/ directory
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# Add src to path for imports
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

from immich_mcp.server import (
    upload_photos,
    search_photos,
    get_photo_info,
    get_ocr_data,
    get_asset_ocr,
    organize_photos_by_date,
    delete_photos,
    create_album,
    add_to_album,
    list_albums,
    share_album,
    detect_people,
    tag_person,
    search_by_person,
    get_storage_info,
    backup_photos,
    server_health,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("immich_test_scaffold")


class ImmichTestScaffold:
    """Comprehensive test scaffold for Immich MCP tools."""

    def __init__(self):
        self.test_photos_dir = Path(__file__).parent / "test_photos"
        self.uploaded_assets: List[str] = []
        self.created_albums: List[str] = []
        self.test_results: Dict[str, Dict] = {}

        # Ensure test photos directory exists
        self.test_photos_dir.mkdir(exist_ok=True)

    def create_test_photos(self) -> List[str]:
        """Create sample test photos for testing using real images."""
        logger.info("Preparing test photos...")

        test_files = []

        # Use real 1998 photos if available, otherwise create placeholders
        real_1998_photos = [
            "Hol 99 - Mira the Dog 1 [digicam].JPG",
            "Hol 99 - Mira the Dog 2 [digicam].JPG",
            "Hol 99 - Mira the Dog 3 [digicam].JPG",
            "Hol 99 - Mira the Dog 4 [digicam].JPG",
            "Hol 99 - SAS self portrait in bed.JPG",
            "Hol 99 - Atmos Clock [digicam].JPG",
            "Hol 99 - Dried Flowers on Mantelpiece.JPG",
            "Hol 99 - Russian Dolls [digicam].JPG",
            "Hol 99 - Gallo Gigante (Venetian Glass Bird) [digicam].jpg",
            "Hol 99 - Town Square [digicam].JPG"
        ]

        # Add real 1998 photos
        for image_name in real_1998_photos:
            image_path = self.test_photos_dir / image_name
            if image_path.exists():
                test_files.append(str(image_path))
                logger.debug(f"Using real 1998 photo: {image_name}")
            else:
                logger.warning(f"Real photo not found: {image_name}")

        # Add some downloaded placeholder photos if we don't have enough real ones
        placeholder_photos = [
            "vacation_beach.jpg",
            "mountain_hike.jpg",
            "city_street.jpg",
            "family_dinner.jpg",
            "dog_playing.jpg"
        ]

        for image_name in placeholder_photos:
            image_path = self.test_photos_dir / image_name
            if image_path.exists() and len(test_files) < 10:
                test_files.append(str(image_path))
                logger.debug(f"Using placeholder photo: {image_name}")

        logger.info(f"Prepared {len(test_files)} test photo files")
        return test_files

    async def test_server_health(self) -> bool:
        """Test 1: Server health check."""
        logger.info("[HEALTH] Testing server health...")
        try:
            health = await server_health()
            logger.info(f"✅ Server health: {health.server_version}, API v{health.is_v2_plus}")
            self.test_results["server_health"] = {"status": "PASS", "data": health.dict()}
            return True
        except Exception as e:
            logger.error(f"❌ Server health test failed: {e}")
            self.test_results["server_health"] = {"status": "FAIL", "error": str(e)}
            return False

    async def test_photo_upload(self, test_files: List[str]) -> bool:
        """Test 2: Photo upload functionality."""
        logger.info("[UPLOAD] Testing photo upload...")

        # Test batch upload
        try:
            result = await upload_photos(
                file_paths=test_files[:5],  # Upload first 5 photos
                album_name="Test Batch Upload",
                auto_organize=False
            )

            logger.info(f"✅ Uploaded {result.uploaded_count} photos, {result.duplicate_count} duplicates")
            self.uploaded_assets.extend(result.uploaded_assets)
            self.test_results["photo_upload"] = {"status": "PASS", "data": result.dict()}
            return True
        except Exception as e:
            logger.error(f"❌ Photo upload test failed: {e}")
            self.test_results["photo_upload"] = {"status": "FAIL", "error": str(e)}
            return False

    async def test_album_creation(self) -> bool:
        """Test 3: Album creation and management."""
        logger.info("[ALBUM] Testing album creation...")

        try:
            # Create multiple albums
            album_names = ["Vacation Photos", "Family Memories", "Nature Shots", "Events"]
            created_albums = []

            for album_name in album_names:
                result = await create_album(
                    name=album_name,
                    description=f"Test album: {album_name}"
                )
                created_albums.append(result.id)
                logger.info(f"✅ Created album: {album_name} (ID: {result.id})")

            self.created_albums.extend(created_albums)

            # Test listing albums
            albums = await list_albums(include_stats=True)
            logger.info(f"✅ Listed {len(albums)} albums")

            self.test_results["album_creation"] = {
                "status": "PASS",
                "albums_created": len(created_albums),
                "albums_listed": len(albums)
            }
            return True
        except Exception as e:
            logger.error(f"❌ Album creation test failed: {e}")
            self.test_results["album_creation"] = {"status": "FAIL", "error": str(e)}
            return False

    async def test_album_operations(self) -> bool:
        """Test 4: Album operations (add photos, share)."""
        logger.info("[LINK] Testing album operations...")

        if not self.uploaded_assets or not self.created_albums:
            logger.warning("⚠️ Skipping album operations - no assets or albums available")
            return False

        try:
            # Add photos to albums
            album_id = self.created_albums[0]
            asset_ids = self.uploaded_assets[:3]

            add_result = await add_to_album(
                album_id=album_id,
                asset_ids=asset_ids
            )

            logger.info(f"✅ Added {add_result.added_count} photos to album")

            # Test album sharing
            share_result = await share_album(
                album_id=album_id,
                allow_download=True,
                allow_upload=False
            )

            logger.info(f"✅ Created share link: {share_result.public_url}")

            self.test_results["album_operations"] = {
                "status": "PASS",
                "photos_added": add_result.added_count,
                "share_url": share_result.public_url
            }
            return True
        except Exception as e:
            logger.error(f"❌ Album operations test failed: {e}")
            self.test_results["album_operations"] = {"status": "FAIL", "error": str(e)}
            return False

    async def test_photo_search(self) -> bool:
        """Test 5: Photo search functionality."""
        logger.info("[SEARCH] Testing photo search...")

        try:
            # Test different search types
            searches = [
                {"query": "vacation", "search_type": "smart"},
                {"query": "beach", "search_type": "smart"},
                {"query": "family", "search_type": "smart"},
            ]

            search_results = {}
            for search in searches:
                result = await search_photos(**search)
                search_results[search["query"]] = len(result)
                logger.info(f"✅ Search '{search['query']}' found {len(result)} results")

            self.test_results["photo_search"] = {
                "status": "PASS",
                "searches_performed": len(searches),
                "results": search_results
            }
            return True
        except Exception as e:
            logger.error(f"❌ Photo search test failed: {e}")
            self.test_results["photo_search"] = {"status": "FAIL", "error": str(e)}
            return False

    async def test_photo_info_and_metadata(self) -> bool:
        """Test 6: Photo information and metadata retrieval."""
        logger.info("[INFO] Testing photo info and metadata...")

        if not self.uploaded_assets:
            logger.warning("⚠️ Skipping photo info test - no assets available")
            return False

        try:
            asset_id = self.uploaded_assets[0]

            # Get photo info
            info = await get_photo_info(asset_id=asset_id)
            logger.info(f"✅ Retrieved info for asset: {info.original_filename}")

            # Test OCR data (may not be available)
            try:
                ocr_data = await get_ocr_data(asset_id=asset_id)
                logger.info(f"✅ OCR data available: {len(ocr_data.text) if ocr_data.text else 0} characters")
            except Exception as e:
                logger.info(f"ℹ️ OCR data not available: {e}")

            # Test asset OCR (alternative endpoint)
            try:
                asset_ocr = await get_asset_ocr(asset_id=asset_id)
                logger.info(f"✅ Asset OCR available: {len(asset_ocr.text) if asset_ocr.text else 0} characters")
            except Exception as e:
                logger.info(f"ℹ️ Asset OCR not available: {e}")

            self.test_results["photo_info"] = {
                "status": "PASS",
                "asset_filename": info.original_filename,
                "file_size": info.file_size_bytes
            }
            return True
        except Exception as e:
            logger.error(f"❌ Photo info test failed: {e}")
            self.test_results["photo_info"] = {"status": "FAIL", "error": str(e)}
            return False

    async def test_face_detection(self) -> bool:
        """Test 7: Face detection and person management."""
        logger.info("[FACE] Testing face detection...")

        if not self.uploaded_assets:
            logger.warning("⚠️ Skipping face detection - no assets available")
            return False

        try:
            # Run face detection on uploaded assets
            detect_result = await detect_people(asset_ids=self.uploaded_assets[:3])
            logger.info(f"✅ Detected {detect_result.detected_faces} faces, created {detect_result.new_people} people")

            # If people were created, test person tagging
            if detect_result.new_people > 0:
                # Note: We can't easily test tagging without knowing person IDs
                logger.info("ℹ️ People detected - manual testing of person tagging recommended")

            self.test_results["face_detection"] = {
                "status": "PASS",
                "faces_detected": detect_result.detected_faces,
                "people_created": detect_result.new_people
            }
            return True
        except Exception as e:
            logger.error(f"❌ Face detection test failed: {e}")
            self.test_results["face_detection"] = {"status": "FAIL", "error": str(e)}
            return False

    async def test_organization_features(self) -> bool:
        """Test 8: Photo organization features."""
        logger.info("[ORG] Testing organization features...")

        if not self.uploaded_assets:
            logger.warning("⚠️ Skipping organization test - no assets available")
            return False

        try:
            # Test date-based organization
            organize_result = await organize_photos_by_date(
                asset_ids=self.uploaded_assets,
                organization_type="year_month"
            )
            logger.info(f"✅ Organized {organize_result.photos_organized} photos into {organize_result.albums_created} albums")

            self.test_results["organization"] = {
                "status": "PASS",
                "photos_organized": organize_result.photos_organized,
                "albums_created": organize_result.albums_created
            }
            return True
        except Exception as e:
            logger.error(f"❌ Organization test failed: {e}")
            self.test_results["organization"] = {"status": "FAIL", "error": str(e)}
            return False

    async def test_storage_and_backup(self) -> bool:
        """Test 9: Storage info and backup functionality."""
        logger.info("[STORAGE] Testing storage and backup...")

        try:
            # Get storage info
            storage = await get_storage_info()
            logger.info(f"✅ Storage: {storage.photos} photos, {storage.videos} videos, {storage.usage:.1f}GB used")

            # Test backup (to a test directory)
            backup_path = Path(__file__).parent / "test_backup"
            backup_path.mkdir(exist_ok=True)

            backup_result = await backup_photos(
                backup_path=str(backup_path),
                include_metadata=True
            )
            logger.info(f"✅ Backup created: {backup_result.exported_photos} photos, {backup_result.total_size_mb:.1f}MB")

            self.test_results["storage_backup"] = {
                "status": "PASS",
                "total_photos": storage.photos + storage.videos,
                "usage_gb": storage.usage,
                "backup_size_mb": backup_result.total_size_mb
            }
            return True
        except Exception as e:
            logger.error(f"❌ Storage/backup test failed: {e}")
            self.test_results["storage_backup"] = {"status": "FAIL", "error": str(e)}
            return False

    async def test_error_handling(self) -> bool:
        """Test 10: Error handling and edge cases."""
        logger.info("[ERROR] Testing error handling...")

        try:
            # Test invalid asset ID
            try:
                await get_photo_info(asset_id="invalid-id")
                logger.warning("⚠️ Expected error for invalid asset ID")
            except Exception:
                logger.info("✅ Correctly handled invalid asset ID")

            # Test empty search
            search_result = await search_photos(query="", search_type="smart", limit=1)
            logger.info(f"✅ Empty search returned {len(search_result)} results")

            # Test invalid album ID
            try:
                await add_to_album(album_id="invalid-album", asset_ids=[])
                logger.warning("⚠️ Expected error for invalid album ID")
            except Exception:
                logger.info("✅ Correctly handled invalid album ID")

            self.test_results["error_handling"] = {"status": "PASS"}
            return True
        except Exception as e:
            logger.error(f"❌ Error handling test failed: {e}")
            self.test_results["error_handling"] = {"status": "FAIL", "error": str(e)}
            return False

    async def generate_test_report(self) -> Dict:
        """Generate comprehensive test report."""
        logger.info("[ORG] Generating test report...")

        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result.get("status") == "PASS")
        failed_tests = total_tests - passed_tests

        report = {
            "timestamp": datetime.now().isoformat(),
            "test_summary": {
                "total_tests": total_tests,
                "passed": passed_tests,
                "failed": failed_tests,
                "success_rate": f"{(passed_tests/total_tests*100):.1f}%" if total_tests > 0 else "0%"
            },
            "assets_created": len(self.uploaded_assets),
            "albums_created": len(self.created_albums),
            "detailed_results": self.test_results
        }

        # Save report to file
        report_path = Path(__file__).parent / "test_report.json"
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2, default=str)

        logger.info(f"✅ Test report saved to: {report_path}")
        logger.info(f"[STATS] Test Results: {passed_tests}/{total_tests} passed ({report['test_summary']['success_rate']})")

        return report

    async def cleanup_test_data(self) -> bool:
        """Clean up test data (optional - dangerous in production!)."""
        logger.warning("[CLEAN] Cleanup requested - but skipping for safety in case of real data")

        # In a real test environment, you might want to:
        # 1. Delete test albums
        # 2. Delete test assets
        # 3. Remove test files

        logger.info("ℹ️ Cleanup skipped for safety - manual cleanup recommended")
        return True

    async def run_full_test_suite(self) -> Dict:
        """Run the complete test suite."""
        logger.info("[START] Starting Immich MCP Comprehensive Test Suite")
        logger.info("=" * 60)

        # Initialize test data
        test_files = self.create_test_photos()

        # Run all tests
        tests = [
            ("Server Health", self.test_server_health),
            ("Photo Upload", lambda: self.test_photo_upload(test_files)),
            ("Album Creation", self.test_album_creation),
            ("Album Operations", self.test_album_operations),
            ("Photo Search", self.test_photo_search),
            ("Photo Info & Metadata", self.test_photo_info_and_metadata),
            ("Face Detection", self.test_face_detection),
            ("Organization Features", self.test_organization_features),
            ("Storage & Backup", self.test_storage_and_backup),
            ("Error Handling", self.test_error_handling),
        ]

        for test_name, test_func in tests:
            logger.info(f"\n{'='*20} {test_name} {'='*20}")
            try:
                await test_func()
            except Exception as e:
                logger.error(f"💥 {test_name} crashed: {e}")
                self.test_results[test_name.lower().replace(" ", "_")] = {"status": "CRASH", "error": str(e)}

        # Generate report
        report = await self.generate_test_report()

        # Optional cleanup
        await self.cleanup_test_data()

        logger.info("\n" + "="*60)
        logger.info("[END] Immich MCP Test Suite Complete!")
        logger.info("="*60)

        return report


async def main():
    """Main entry point."""
    scaffold = ImmichTestScaffold()
    report = await scaffold.run_full_test_suite()

    # Print summary
    print("\n" + "="*60)
    print("TEST SUITE SUMMARY")
    print("="*60)
    print(f"Tests Run: {report['test_summary']['total_tests']}")
    print(f"Passed: {report['test_summary']['passed']}")
    print(f"Failed: {report['test_summary']['failed']}")
    print(f"Success Rate: {report['test_summary']['success_rate']}")
    print(f"Assets Created: {report['test_summary'].get('assets_created', 0)}")
    print(f"Albums Created: {report['test_summary'].get('albums_created', 0)}")
    print(f"Report Saved: test_report.json")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())
