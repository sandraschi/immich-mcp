"""
Unit tests for Immich MCP API components
Austrian efficiency: Fast, reliable tests with no stubs
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import pytest
import requests
from typing import Dict, Any

# Import modules to test
from immich.manager import ImmichManager, ImmichManagerError
from immich.asset_operations import AssetOperations
from immich.album_manager import AlbumManager
from immich.search_operations import SearchOperations


class TestImmichManager(unittest.TestCase):
    """Test core Immich manager functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_url = "http://localhost:2283"
        self.test_api_key = "test_api_key_12345"
        self.manager = ImmichManager(self.test_url, self.test_api_key)
    
    def test_init_configuration(self):
        """Test manager initialization with correct settings"""
        self.assertEqual(self.manager.server_url, "http://localhost:2283")
        self.assertEqual(self.manager.api_key, "test_api_key_12345")
        self.assertIn('x-api-key', self.manager.session.headers)
        self.assertEqual(self.manager.session.headers['x-api-key'], self.test_api_key)
    
    def test_url_normalization(self):
        """Test URL normalization (removes trailing slash)"""
        manager_with_slash = ImmichManager("http://localhost:2283/", self.test_api_key)
        self.assertEqual(manager_with_slash.server_url, "http://localhost:2283")
    
    @patch('requests.Session.get')
    def test_get_request_success(self, mock_get):
        """Test successful GET request handling"""
        # Mock successful response
        mock_response = Mock()
        mock_response.json.return_value = {"status": "ok", "version": "1.0.0"}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        result = self.manager.get("/server-info")
        
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["version"], "1.0.0")
        mock_get.assert_called_once()
    
    @patch('requests.Session.get')
    def test_get_request_failure(self, mock_get):
        """Test GET request error handling"""
        # Mock failed response
        mock_get.side_effect = requests.RequestException("Connection failed")
        
        with self.assertRaises(ImmichManagerError) as context:
            self.manager.get("/server-info")
        
        self.assertIn("GET request failed", str(context.exception))
        self.assertIn("Connection failed", str(context.exception))
    
    @patch('requests.Session.get')
    def test_connection_test_success(self, mock_get):
        """Test successful connection test"""
        # Mock successful server-info response
        mock_response = Mock()
        mock_response.json.return_value = {"server": "immich"}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        self.assertTrue(self.manager.test_connection())
    
    @patch('requests.Session.get')
    def test_connection_test_failure(self, mock_get):
        """Test failed connection test"""
        # Mock connection failure
        mock_get.side_effect = requests.RequestException("Connection refused")
        
        self.assertFalse(self.manager.test_connection())


class TestAssetOperations(unittest.TestCase):
    """Test asset management operations"""
    
    def setUp(self):
        """Set up test environment with mocked manager"""
        self.mock_manager = Mock(spec=ImmichManager)
        self.asset_ops = AssetOperations(self.mock_manager)
    
    def test_initialization(self):
        """Test AssetOperations initialization"""
        self.assertEqual(self.asset_ops.manager, self.mock_manager)
    
    def test_upload_photos_validation(self):
        """Test photo upload parameter validation"""
        # Test with empty file paths
        with self.assertRaises(ValueError) as context:
            self.asset_ops.upload_photos([])
        
        self.assertIn("No file paths provided", str(context.exception))
    
    def test_get_asset_info_validation(self):
        """Test asset info retrieval validation"""
        # Test with empty asset ID
        with self.assertRaises(ValueError) as context:
            self.asset_ops.get_asset_info("")
        
        self.assertIn("Asset ID cannot be empty", str(context.exception))


class TestAlbumManager(unittest.TestCase):
    """Test album management operations"""
    
    def setUp(self):
        """Set up test environment with mocked manager"""
        self.mock_manager = Mock(spec=ImmichManager)
        self.album_manager = AlbumManager(self.mock_manager)
    
    def test_initialization(self):
        """Test AlbumManager initialization"""
        self.assertEqual(self.album_manager.manager, self.mock_manager)
    
    def test_create_album_validation(self):
        """Test album creation validation"""
        # Test with empty album name
        with self.assertRaises(ValueError) as context:
            self.album_manager.create_album("")
        
        self.assertIn("Album name cannot be empty", str(context.exception))
    
    def test_add_to_album_validation(self):
        """Test adding assets to album validation"""
        # Test with empty album ID
        with self.assertRaises(ValueError) as context:
            self.album_manager.add_to_album("", ["asset1"])
        
        self.assertIn("Album ID cannot be empty", str(context.exception))
        
        # Test with empty asset list
        with self.assertRaises(ValueError) as context:
            self.album_manager.add_to_album("album1", [])
        
        self.assertIn("No assets provided", str(context.exception))


class TestSearchOperations(unittest.TestCase):
    """Test search and discovery operations"""
    
    def setUp(self):
        """Set up test environment with mocked manager"""
        self.mock_manager = Mock(spec=ImmichManager)
        self.search_ops = SearchOperations(self.mock_manager)
    
    def test_initialization(self):
        """Test SearchOperations initialization"""
        self.assertEqual(self.search_ops.manager, self.mock_manager)
    
    def test_search_photos_validation(self):
        """Test photo search validation"""
        # Test with empty query
        with self.assertRaises(ValueError) as context:
            self.search_ops.search_photos("")
        
        self.assertIn("Search query cannot be empty", str(context.exception))
        
        # Test with invalid limit
        with self.assertRaises(ValueError) as context:
            self.search_ops.search_photos("test", limit=0)
        
        self.assertIn("Limit must be positive", str(context.exception))
    
    def test_search_by_person_validation(self):
        """Test person search validation"""
        # Test with empty person name
        with self.assertRaises(ValueError) as context:
            self.search_ops.search_by_person("")
        
        self.assertIn("Person name cannot be empty", str(context.exception))


class TestErrorHandling(unittest.TestCase):
    """Test comprehensive error handling across all components"""
    
    def setUp(self):
        """Set up test environment"""
        self.manager = ImmichManager("http://localhost:2283", "test_key")
    
    @patch('requests.Session.get')
    def test_http_error_codes(self, mock_get):
        """Test handling of various HTTP error codes"""
        # Test 401 Unauthorized
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = requests.HTTPError("401 Unauthorized")
        mock_get.return_value = mock_response
        
        with self.assertRaises(ImmichManagerError) as context:
            self.manager.get("/albums")
        
        self.assertIn("GET request failed", str(context.exception))
        self.assertIn("401 Unauthorized", str(context.exception))
    
    @patch('requests.Session.get')
    def test_network_timeout(self, mock_get):
        """Test network timeout handling"""
        # Test timeout error
        mock_get.side_effect = requests.Timeout("Request timed out")
        
        with self.assertRaises(ImmichManagerError) as context:
            self.manager.get("/server-info")
        
        self.assertIn("GET request failed", str(context.exception))
        self.assertIn("timed out", str(context.exception))


# Austrian efficiency test utilities
class MockDataFactory:
    """Factory for creating realistic test data"""
    
    @staticmethod
    def create_mock_asset(asset_id: str = "test_asset_123") -> Dict[str, Any]:
        """Create realistic asset data for testing"""
        return {
            "id": asset_id,
            "originalFileName": "Vienna_Schoenbrunn.jpg",
            "fileCreatedAt": "2025-07-22T15:30:00.000Z",
            "fileModifiedAt": "2025-07-22T15:30:00.000Z",
            "fileSize": 2048576,
            "type": "IMAGE",
            "exifInfo": {
                "make": "Canon",
                "model": "EOS R5",
                "dateTimeOriginal": "2025-07-22T15:30:00.000Z",
                "gpsLatitude": 48.1851,
                "gpsLongitude": 16.3099  # Vienna coordinates
            }
        }
    
    @staticmethod
    def create_mock_album(album_id: str = "test_album_456") -> Dict[str, Any]:
        """Create realistic album data for testing"""
        return {
            "id": album_id,
            "albumName": "Vienna Summer 2025",
            "description": "Beautiful photos from Vienna summer",
            "createdAt": "2025-07-22T10:00:00.000Z",
            "updatedAt": "2025-07-22T16:00:00.000Z",
            "assetCount": 25,
            "assets": []
        }
    
    @staticmethod
    def create_mock_person(person_id: str = "test_person_789") -> Dict[str, Any]:
        """Create realistic person data for testing"""
        return {
            "id": person_id,
            "name": "Sandra",
            "thumbnailPath": "/path/to/thumbnail.jpg",
            "faceCount": 15,
            "updatedAt": "2025-07-22T14:00:00.000Z"
        }


if __name__ == "__main__":
    # Austrian efficiency: Run tests with detailed output
    unittest.main(verbosity=2)
