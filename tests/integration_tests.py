"""
Integration tests for Immich MCP Server
Austrian efficiency: End-to-end testing with real workflow validation
"""

import unittest
import os
import time
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch
from typing import Dict, List, Any

# Import test dependencies
import pytest
from dotenv import load_dotenv

# Import server components
from immich.manager import ImmichManager, ImmichManagerError
from immich.asset_operations import AssetOperations
from immich.album_manager import AlbumManager
from immich.search_operations import SearchOperations


class IntegrationTestBase(unittest.TestCase):
    """Base class for integration tests with common setup"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment - runs once per test class"""
        # Load test environment
        load_dotenv()
        
        # Test configuration
        cls.test_server_url = os.getenv("TEST_IMMICH_URL", "http://localhost:2283")
        cls.test_api_key = os.getenv("TEST_IMMICH_API_KEY", "")
        
        # Skip integration tests if no test server configured
        if not cls.test_api_key:
            pytest.skip("No TEST_IMMICH_API_KEY configured - skipping integration tests")
    
    def setUp(self):
        """Set up individual test case"""
        self.manager = ImmichManager(self.test_server_url, self.test_api_key)
        self.asset_ops = AssetOperations(self.manager)
        self.album_manager = AlbumManager(self.manager)
        self.search_ops = SearchOperations(self.manager)
        
        # Create test data directory
        self.test_data_dir = Path(tempfile.mkdtemp(prefix="immich_mcp_test_"))
        self.addCleanup(self._cleanup_test_data)
    
    def _cleanup_test_data(self):
        """Clean up test data directory"""
        import shutil
        if self.test_data_dir.exists():
            shutil.rmtree(self.test_data_dir)
    
    def _create_test_image(self, filename: str = "test_photo.jpg") -> Path:
        """Create a simple test image file"""
        from PIL import Image
        
        # Create simple 100x100 test image
        image = Image.new('RGB', (100, 100), color='blue')
        image_path = self.test_data_dir / filename
        image.save(image_path, 'JPEG')
        
        return image_path


class TestServerConnection(IntegrationTestBase):
    """Test basic server connection and health"""
    
    def test_server_connection(self):
        """Test that we can connect to Immich server"""
        # Austrian efficiency: Direct test of core functionality
        self.assertTrue(
            self.manager.test_connection(),
            "Cannot connect to Immich server - check TEST_IMMICH_URL and TEST_IMMICH_API_KEY"
        )
    
    def test_server_info_retrieval(self):
        """Test retrieving server information"""
        try:
            server_info = self.manager.get("/server-info")
            
            # Verify we get expected server info structure
            self.assertIn("version", server_info)
            self.assertTrue(server_info["version"])
            
        except ImmichManagerError as e:
            self.fail(f"Failed to retrieve server info: {e}")
    
    def test_api_key_validity(self):
        """Test that API key provides proper access"""
        try:
            # Try to access a protected endpoint
            albums = self.manager.get("/albums")
            
            # Should return list (even if empty)
            self.assertIsInstance(albums, list)
            
        except ImmichManagerError as e:
            if "401" in str(e) or "Unauthorized" in str(e):
                self.fail("API key is invalid or expired")
            else:
                self.fail(f"Unexpected error accessing protected endpoint: {e}")


class TestAssetOperations(IntegrationTestBase):
    """Test asset upload, management, and retrieval operations"""
    
    def test_upload_single_photo(self):
        """Test uploading a single photo to Immich"""
        # Create test image
        test_image = self._create_test_image("vienna_test.jpg")
        
        try:
            # Upload photo
            result = self.asset_ops.upload_photos([str(test_image)])
            
            # Verify upload success
            self.assertIn("assets", result)
            self.assertTrue(len(result["assets"]) > 0)
            
            # Store asset ID for cleanup
            self.uploaded_asset_id = result["assets"][0]["id"]
            
        except Exception as e:
            self.fail(f"Photo upload failed: {e}")
    
    def test_upload_multiple_photos(self):
        """Test uploading multiple photos in batch"""
        # Create multiple test images
        test_images = [
            self._create_test_image("vienna_1.jpg"),
            self._create_test_image("vienna_2.jpg"),
            self._create_test_image("vienna_3.jpg")
        ]
        
        try:
            # Upload all photos
            result = self.asset_ops.upload_photos([str(img) for img in test_images])
            
            # Verify all uploads succeeded
            self.assertIn("assets", result)
            self.assertEqual(len(result["assets"]), 3)
            
            # Store asset IDs for cleanup
            self.uploaded_asset_ids = [asset["id"] for asset in result["assets"]]
            
        except Exception as e:
            self.fail(f"Multiple photo upload failed: {e}")
    
    def test_get_asset_info(self):
        """Test retrieving detailed asset information"""
        # First upload a test photo
        test_image = self._create_test_image("info_test.jpg")
        upload_result = self.asset_ops.upload_photos([str(test_image)])
        asset_id = upload_result["assets"][0]["id"]
        
        try:
            # Get asset info
            asset_info = self.asset_ops.get_asset_info(asset_id)
            
            # Verify asset info structure
            self.assertIn("id", asset_info)
            self.assertEqual(asset_info["id"], asset_id)
            self.assertIn("originalFileName", asset_info)
            self.assertIn("fileSize", asset_info)
            
        except Exception as e:
            self.fail(f"Asset info retrieval failed: {e}")


class TestAlbumWorkflow(IntegrationTestBase):
    """Test complete album creation and management workflow"""
    
    def test_create_album_workflow(self):
        """Test creating album and adding photos"""
        # Create test photos
        test_images = [
            self._create_test_image("album_photo_1.jpg"),
            self._create_test_image("album_photo_2.jpg")
        ]
        
        # Upload photos first
        upload_result = self.asset_ops.upload_photos([str(img) for img in test_images])
        asset_ids = [asset["id"] for asset in upload_result["assets"]]
        
        try:
            # Create album with photos
            album_result = self.album_manager.create_album(
                album_name="Vienna Integration Test Album",
                description="Test album created by MCP integration tests",
                asset_ids=asset_ids
            )
            
            # Verify album creation
            self.assertIn("id", album_result)
            self.assertIn("albumName", album_result)
            self.assertEqual(album_result["albumName"], "Vienna Integration Test Album")
            
            # Store album ID for cleanup
            self.test_album_id = album_result["id"]
            
        except Exception as e:
            self.fail(f"Album creation workflow failed: {e}")
    
    def test_add_photos_to_existing_album(self):
        """Test adding photos to an existing album"""
        # Create album first
        create_result = self.album_manager.create_album("Test Addition Album")
        album_id = create_result["id"]
        
        # Upload photos
        test_image = self._create_test_image("addition_test.jpg")
        upload_result = self.asset_ops.upload_photos([str(test_image)])
        asset_id = upload_result["assets"][0]["id"]
        
        try:
            # Add photo to album
            add_result = self.album_manager.add_to_album(album_id, [asset_id])
            
            # Verify addition succeeded
            self.assertIn("success", add_result)
            self.assertTrue(add_result["success"])
            
        except Exception as e:
            self.fail(f"Adding photos to album failed: {e}")
    
    def test_list_albums(self):
        """Test listing all albums with statistics"""
        try:
            # List albums
            albums = self.album_manager.list_albums()
            
            # Verify response structure
            self.assertIsInstance(albums, list)
            
            # If we have albums, check structure
            if len(albums) > 0:
                album = albums[0]
                self.assertIn("id", album)
                self.assertIn("albumName", album)
                
        except Exception as e:
            self.fail(f"Listing albums failed: {e}")


class TestSearchFunctionality(IntegrationTestBase):
    """Test search and discovery capabilities"""
    
    def test_smart_search(self):
        """Test CLIP-based smart search functionality"""
        try:
            # Search for photos (might be empty on test server)
            search_result = self.search_ops.search_photos("landscape", limit=10)
            
            # Verify search response structure
            self.assertIsInstance(search_result, list)
            
            # If results exist, verify structure
            if len(search_result) > 0:
                photo = search_result[0]
                self.assertIn("id", photo)
                
        except Exception as e:
            # Smart search might not be available on all Immich instances
            if "not available" in str(e).lower() or "not enabled" in str(e).lower():
                self.skipTest("Smart search not available on test server")
            else:
                self.fail(f"Smart search failed: {e}")
    
    def test_people_detection(self):
        """Test face detection and people search"""
        try:
            # List detected people
            people = self.search_ops.list_people()
            
            # Verify people list structure
            self.assertIsInstance(people, list)
            
            # If people detected, verify structure
            if len(people) > 0:
                person = people[0]
                self.assertIn("id", person)
                
        except Exception as e:
            # Face detection might not be available
            if "not available" in str(e).lower() or "not enabled" in str(e).lower():
                self.skipTest("Face detection not available on test server")
            else:
                self.fail(f"People detection failed: {e}")


class TestStorageAndMaintenance(IntegrationTestBase):
    """Test storage monitoring and maintenance operations"""
    
    def test_storage_info(self):
        """Test retrieving storage statistics"""
        try:
            # Get storage info
            storage_info = self.search_ops.get_storage_info()
            
            # Verify storage info structure
            self.assertIn("total", storage_info)
            self.assertIn("used", storage_info)
            self.assertIn("available", storage_info)
            
        except Exception as e:
            self.fail(f"Storage info retrieval failed: {e}")
    
    def test_server_health(self):
        """Test comprehensive server health check"""
        try:
            # Check server health
            health = self.search_ops.server_health()
            
            # Verify health response
            self.assertIn("status", health)
            self.assertIn("api_accessible", health)
            self.assertTrue(health["api_accessible"])
            
        except Exception as e:
            self.fail(f"Server health check failed: {e}")


class TestErrorRecovery(IntegrationTestBase):
    """Test error handling and recovery scenarios"""
    
    def test_invalid_asset_id(self):
        """Test handling of invalid asset IDs"""
        with self.assertRaises(Exception) as context:
            self.asset_ops.get_asset_info("invalid_asset_id_12345")
        
        # Should get meaningful error message
        error_msg = str(context.exception)
        self.assertTrue(
            "not found" in error_msg.lower() or "invalid" in error_msg.lower(),
            f"Error message should indicate invalid ID: {error_msg}"
        )
    
    def test_invalid_album_id(self):
        """Test handling of invalid album IDs"""
        with self.assertRaises(Exception) as context:
            self.album_manager.add_to_album("invalid_album_123", ["asset_123"])
        
        # Should get meaningful error message
        error_msg = str(context.exception)
        self.assertTrue(
            "not found" in error_msg.lower() or "invalid" in error_msg.lower(),
            f"Error message should indicate invalid album: {error_msg}"
        )
    
    def test_network_resilience(self):
        """Test behavior with temporary network issues"""
        # Create manager with short timeout for testing
        test_manager = ImmichManager(self.test_server_url, self.test_api_key)
        
        # Test with invalid URL to simulate network failure
        invalid_manager = ImmichManager("http://invalid-server:9999", self.test_api_key)
        
        # Should handle gracefully
        self.assertFalse(invalid_manager.test_connection())


# Austrian efficiency: Test runner with comprehensive reporting
class TestRunner:
    """Custom test runner with Austrian efficiency reporting"""
    
    @staticmethod
    def run_integration_tests():
        """Run all integration tests with detailed reporting"""
        print("🧪 Starting Immich MCP Integration Tests...")
        print("Austrian efficiency: Comprehensive testing in minutes, not hours")
        print()
        
        # Create test suite
        loader = unittest.TestLoader()
        suite = unittest.TestSuite()
        
        # Add test classes
        test_classes = [
            TestServerConnection,
            TestAssetOperations,
            TestAlbumWorkflow,
            TestSearchFunctionality,
            TestStorageAndMaintenance,
            TestErrorRecovery
        ]
        
        for test_class in test_classes:
            tests = loader.loadTestsFromTestCase(test_class)
            suite.addTests(tests)
        
        # Run tests with detailed output
        runner = unittest.TextTestRunner(
            verbosity=2,
            stream=None,
            descriptions=True,
            failfast=False
        )
        
        print(f"📊 Running {suite.countTestCases()} integration tests...")
        print("-" * 60)
        
        start_time = time.time()
        result = runner.run(suite)
        duration = time.time() - start_time
        
        # Austrian efficiency reporting
        print("\n" + "=" * 60)
        print("🎯 Austrian Efficiency Test Summary:")
        print(f"   • Tests run: {result.testsRun}")
        print(f"   • Failures: {len(result.failures)}")
        print(f"   • Errors: {len(result.errors)}")
        print(f"   • Skipped: {len(result.skipped) if hasattr(result, 'skipped') else 0}")
        print(f"   • Duration: {duration:.2f} seconds")
        print(f"   • Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
        
        if result.wasSuccessful():
            print("✅ All integration tests passed! MCP server is production ready.")
        else:
            print("❌ Some tests failed. Check logs above for details.")
            
        return result.wasSuccessful()


if __name__ == "__main__":
    # Run integration tests
    TestRunner.run_integration_tests()
