"""
Comprehensive test harness for ImmichMCP API client compatibility.
Tests all API endpoints, version adaptation, and mock scenarios.
Austrian efficiency: Flat test structure, precise mocks, no nesting.
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from immich_mcp.config import ImmichConfig
from immich_mcp.immich_api import ImmichAPIClient, ImmichAPIError


# ====== MODULE LEVEL FIXTURES ======

@pytest.fixture
def config():
    """Create test configuration"""
    return ImmichConfig(server_url="http://localhost:2283", api_key="test_api_key_12345", timeout=30)


@pytest.fixture
def api_client(config):
    """Create API client instance"""
    return ImmichAPIClient(config)


@pytest.fixture
def mock_response():
    """Create mock HTTP response"""
    response = Mock()
    response.raise_for_status = Mock()
    return response


# ====== FLAT TEST CLASSES ======

class TestSearchMetadataEndpoint:
    """Test the photo search endpoints (which are POST requests)"""

    @pytest.mark.asyncio
    async def test_search_photos_smart_search(self, api_client, mock_response):
        """Test smart search using POST search/smart"""
        mock_response.json.return_value = [
            {
                "id": "asset1",
                "type": "IMAGE",
                "originalFileName": "test1.jpg",
                "fileCreatedAt": "2024-01-01T00:00:00.000Z",
            },
            {
                "id": "asset2",
                "type": "IMAGE",
                "originalFileName": "test2.jpg",
                "fileCreatedAt": "2024-01-02T00:00:00.000Z",
            },
        ]

        with patch.object(api_client, "_post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response.json()

            result = await api_client.search_photos("test query", search_type="smart")

            # Verify correct endpoint and body parameters
            mock_post.assert_called_with(
                "/search/smart", data={"query": "test query", "size": 50}
            )

            assert len(result) == 2
            assert result[0]["id"] == "asset1"
            assert result[1]["id"] == "asset2"

    @pytest.mark.asyncio
    async def test_search_photos_filename_search(self, api_client, mock_response):
        """Test filename search using POST search/metadata"""
        mock_response.json.return_value = [
            {
                "id": "asset1",
                "type": "IMAGE",
                "originalFileName": "vacation_test.jpg",
                "fileCreatedAt": "2024-01-01T00:00:00.000Z",
            }
        ]

        with patch.object(api_client, "_post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response.json()

            result = await api_client.search_photos("vacation", search_type="filename")

            # Verify correct endpoint and body parameters for filename search
            mock_post.assert_called_with(
                "/search/metadata", data={"originalFileName": "vacation", "size": 50}
            )

            assert len(result) == 1
            assert result[0]["originalFileName"] == "vacation_test.jpg"

    @pytest.mark.asyncio
    async def test_search_photos_metadata_search(self, api_client, mock_response):
        """Test metadata search using POST search/metadata"""
        mock_response.json.return_value = [
            {
                "id": "asset1",
                "type": "IMAGE",
                "originalFileName": "metadata_test.jpg",
                "fileCreatedAt": "2024-01-01T00:00:00.000Z",
            }
        ]

        with patch.object(api_client, "_post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response.json()

            result = await api_client.search_photos("metadata query", search_type="metadata")

            # Verify correct endpoint and body parameters for metadata search
            mock_post.assert_called_with(
                "/search/metadata", data={"query": "metadata query", "size": 50}
            )

            assert len(result) == 1


class TestAssetInfo:
    """Test get_asset_info method using standard GET /assets/{id}"""

    @pytest.mark.asyncio
    async def test_get_asset_info_success(self, api_client, mock_response):
        """Test successful asset info retrieval"""
        mock_response.json.return_value = {
            "id": "test-asset-123",
            "type": "IMAGE",
            "originalFileName": "test.jpg",
            "fileCreatedAt": "2024-01-01T00:00:00.000Z",
        }

        with patch.object(api_client, "_get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response.json()

            result = await api_client.get_asset_info("test-asset-123")

            # Verify correct endpoint
            mock_get.assert_called_with("/assets/test-asset-123")

            assert result["id"] == "test-asset-123"
            assert result["originalFileName"] == "test.jpg"

    @pytest.mark.asyncio
    async def test_get_asset_info_not_found(self, api_client):
        """Test asset info retrieval when asset doesn't exist"""
        with patch.object(api_client, "_get", new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = ImmichAPIError("GET /assets/nonexistent failed - HTTP 404: not found")

            with pytest.raises(ImmichAPIError) as exc_info:
                await api_client.get_asset_info("nonexistent-asset")

            assert "not found" in str(exc_info.value)


class TestServerInfo:
    """Test server stats and server info methods"""

    @pytest.mark.asyncio
    async def test_get_server_stats_fallback(self, api_client):
        """Test server stats when /server/about succeeds and server-info is bypassed"""
        server_about_response = {"version": "v2.x", "users": 3}
        storage_response = {
            "diskUsage": 1000,
            "diskAvailable": 2000,
            "diskSize": 3000,
            "diskUsagePercentage": 33.3,
            "usageByUser": [],
        }
        search_metadata_response = {"assets": {"total": 150, "count": 150, "items": []}}

        with patch.object(api_client, "_get", new_callable=AsyncMock) as mock_get, \
             patch.object(api_client, "_post", new_callable=AsyncMock) as mock_post:
            
            mock_get.side_effect = [
                server_about_response,  # /server/about
                storage_response,       # /admin/storage
            ]
            mock_post.return_value = search_metadata_response  # /search/metadata

            result = await api_client.get_server_stats()

            # Verify results
            assert result["photos"] == 150
            assert result["api_version"] == "v2.x"
            assert result["usage"] == 1000
            assert result["users"] == 3

    @pytest.mark.asyncio
    async def test_get_server_info_healthy(self, api_client):
        """Test server info detection"""
        server_about_response = {"version": "v2.5.0", "features": ["search", "ocr"]}

        with patch.object(api_client, "_get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = server_about_response

            result = await api_client.get_server_info()

            assert result["version"] == "v2.5.0"
            assert result["status"] == "healthy"
            assert result["multilingual_ocr"] is True


class TestEndpointCompatibility:
    """Test that other endpoints still work correctly"""

    @pytest.mark.asyncio
    async def test_albums_endpoints_still_work(self, api_client, mock_response):
        """Test that albums endpoints work"""
        mock_response.json.return_value = [
            {"id": "album1", "albumName": "Test Album", "description": "Test description", "assetCount": 10}
        ]

        with patch.object(api_client, "_get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response.json()

            result = await api_client.get_albums(include_stats=False)

            mock_get.assert_called_with("/albums", params={})
            assert len(result) == 1
            assert result[0]["albumName"] == "Test Album"

    @pytest.mark.asyncio
    async def test_create_album_still_works(self, api_client, mock_response):
        """Test album creation still works"""
        mock_response.json.return_value = {
            "id": "new_album_123",
            "albumName": "New Album",
            "description": "Created album",
            "assetCount": 0,
        }

        with patch.object(api_client, "_post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response.json()

            result = await api_client.create_album("New Album", "Created album")

            mock_post.assert_called_with(
                "/albums", data={"albumName": "New Album", "description": "Created album", "assetIds": []}
            )
            assert result["albumName"] == "New Album"


class TestErrorHandling:
    """Test error handling in API responses"""

    @pytest.mark.asyncio
    async def test_ocr_not_found_fallback(self, api_client):
        """Test asset OCR fallback on 404 error"""
        with patch.object(api_client, "_get", new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = ImmichAPIError("GET /assets/id/ocr failed - HTTP 404: Not Found")

            result = await api_client.get_asset_ocr("test-id")

            assert result["text"] == ""
            assert result["bounding_boxes"] == []
            assert result["language"] == "unknown"


class TestImmichMCPIntegration:
    """Integration checks for configurations"""

    @pytest.fixture
    def server_config(self):
        """Create test server configuration"""
        return {"server_url": "http://localhost:2283", "api_key": "test_api_key_12345", "timeout": 30}

    def test_server_initialization(self, server_config):
        """Test config structure validation"""
        assert "server_url" in server_config
        assert "api_key" in server_config
        assert server_config["timeout"] == 30

    def test_api_client_initialization(self, server_config):
        """Test API client initialization with multi-user awareness"""
        config = ImmichConfig(**server_config)
        client = ImmichAPIClient(config)

        assert client.base_url == "http://localhost:2283"
        assert client.current_user.api_key == "test_api_key_12345"
        assert config.timeout == 30
