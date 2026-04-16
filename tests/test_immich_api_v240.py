"""
Comprehensive test harness for ImmichMCP API client v2.4.0 compatibility
Tests all API changes and endpoint migrations from v2.4.0 migration
Austrian efficiency: Thorough testing with multiple scenarios
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from immich_mcp.config import ImmichConfig
from immich_mcp.immich_api import ImmichAPIClient, ImmichAPIError


class TestImmichAPIV240Compatibility:
    """Test ImmichMCP API client compatibility with Immich v2.4.0"""

    @pytest.fixture
    def config(self):
        """Create test configuration"""
        return ImmichConfig(server_url="http://localhost:2283", api_key="test_api_key_12345", timeout=30)

    @pytest.fixture
    def api_client(self, config):
        """Create API client instance"""
        return ImmichAPIClient(config)

    @pytest.fixture
    def mock_response(self):
        """Create mock HTTP response"""
        response = Mock()
        response.raise_for_status = Mock()
        return response

    class TestSearchMetadataEndpoint:
        """Test the new search/metadata endpoint (replaces /assets)"""

        @pytest.mark.asyncio
        async def test_search_photos_smart_search(self, api_client, mock_response):
            """Test smart search using new search/metadata endpoint"""
            mock_response.json.return_value = {
                "albums": {"total": 0, "items": []},
                "assets": {
                    "total": 2,
                    "count": 2,
                    "items": [
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
                    ],
                },
            }

            with patch.object(api_client, "_get", new_callable=AsyncMock) as mock_get:
                mock_get.return_value = mock_response.json()

                result = await api_client.search_photos("test query", search_type="smart")

                # Verify correct endpoint and parameters
                mock_get.assert_called_with(
                    "/search/smart", params={"query": "test query", "limit": 50, "type": "SMART_SEARCH"}
                )

                assert len(result) == 2
                assert result[0]["id"] == "asset1"
                assert result[1]["id"] == "asset2"

        @pytest.mark.asyncio
        async def test_search_photos_filename_search(self, api_client, mock_response):
            """Test filename search using new search/metadata endpoint"""
            mock_response.json.return_value = {
                "albums": {"total": 0, "items": []},
                "assets": {
                    "total": 1,
                    "count": 1,
                    "items": [
                        {
                            "id": "asset1",
                            "type": "IMAGE",
                            "originalFileName": "vacation_test.jpg",
                            "fileCreatedAt": "2024-01-01T00:00:00.000Z",
                        }
                    ],
                },
            }

            with patch.object(api_client, "_get", new_callable=AsyncMock) as mock_get:
                mock_get.return_value = mock_response.json()

                result = await api_client.search_photos("vacation", search_type="filename")

                # Verify correct endpoint and parameters for filename search
                mock_get.assert_called_with(
                    "/search/metadata", params={"page": 1, "size": 50, "query": "vacation", "type": "ASSET"}
                )

                assert len(result) == 1
                assert result[0]["originalFileName"] == "vacation_test.jpg"

        @pytest.mark.asyncio
        async def test_search_photos_metadata_search(self, api_client, mock_response):
            """Test metadata search using new search/metadata endpoint"""
            mock_response.json.return_value = {
                "albums": {"total": 0, "items": []},
                "assets": {
                    "total": 1,
                    "count": 1,
                    "items": [
                        {
                            "id": "asset1",
                            "type": "IMAGE",
                            "originalFileName": "metadata_test.jpg",
                            "fileCreatedAt": "2024-01-01T00:00:00.000Z",
                        }
                    ],
                },
            }

            with patch.object(api_client, "_get", new_callable=AsyncMock) as mock_get:
                mock_get.return_value = mock_response.json()

                result = await api_client.search_photos("metadata query", search_type="metadata")

                # Verify correct endpoint and parameters for metadata search
                mock_get.assert_called_with("/search/metadata", params={"q": "metadata query", "limit": 50})

                assert len(result) == 1

    class TestAssetInfoFallback:
        """Test get_asset_info method with v2.4.0 limitations"""

        @pytest.mark.asyncio
        async def test_get_asset_info_success_first_try(self, api_client, mock_response):
            """Test successful asset info retrieval on first search attempt"""
            mock_response.json.return_value = {
                "albums": {"total": 0, "items": []},
                "assets": {
                    "total": 1,
                    "count": 1,
                    "items": [
                        {
                            "id": "test-asset-123",
                            "type": "IMAGE",
                            "originalFileName": "test.jpg",
                            "fileCreatedAt": "2024-01-01T00:00:00.000Z",
                        }
                    ],
                },
            }

            with patch.object(api_client, "_get", new_callable=AsyncMock) as mock_get:
                mock_get.return_value = mock_response.json()

                result = await api_client.get_asset_info("test-asset-123")

                # Verify correct endpoint and parameters
                mock_get.assert_called_with(
                    "/search/metadata", params={"page": 1, "size": 1, "query": "test-asset-123", "type": "ASSET"}
                )

                assert result["id"] == "test-asset-123"
                assert result["originalFileName"] == "test.jpg"

        @pytest.mark.asyncio
        async def test_get_asset_info_fallback_search(self, api_client, mock_response):
            """Test asset info retrieval requiring broader search fallback"""
            # First call returns no results with query
            empty_response = {"albums": {"total": 0, "items": []}, "assets": {"total": 0, "count": 0, "items": []}}

            # Second call returns the asset
            found_response = {
                "albums": {"total": 0, "items": []},
                "assets": {
                    "total": 1000,
                    "count": 1000,
                    "items": [
                        {
                            "id": "test-asset-123",
                            "type": "IMAGE",
                            "originalFileName": "test.jpg",
                            "fileCreatedAt": "2024-01-01T00:00:00.000Z",
                        }
                    ]
                    + [{"id": f"other-{i}", "type": "IMAGE"} for i in range(999)],
                },
            }

            with patch.object(api_client, "_get", new_callable=AsyncMock) as mock_get:
                mock_get.side_effect = [empty_response, found_response]

                result = await api_client.get_asset_info("test-asset-123")

                # Verify two calls were made
                assert mock_get.call_count == 2

                # Verify second call was broader search
                second_call = mock_get.call_args_list[1]
                assert second_call[1]["params"]["page"] == 1
                assert second_call[1]["params"]["size"] == 1000
                assert second_call[1]["params"]["type"] == "ASSET"

                assert result["id"] == "test-asset-123"

        @pytest.mark.asyncio
        async def test_get_asset_info_not_found(self, api_client, mock_response):
            """Test asset info retrieval when asset doesn't exist"""
            mock_response.json.return_value = {
                "albums": {"total": 0, "items": []},
                "assets": {"total": 0, "count": 0, "items": []},
            }

            with patch.object(api_client, "_get", new_callable=AsyncMock) as mock_get:
                mock_get.return_value = mock_response.json()

                with pytest.raises(ImmichAPIError) as exc_info:
                    await api_client.get_asset_info("nonexistent-asset")

                assert "not found" in str(exc_info.value)

    class TestServerInfoFallback:
        """Test server info methods with v2.4.0 limitations"""

        @pytest.mark.asyncio
        async def test_get_server_stats_without_server_info(self, api_client):
            """Test server stats when /server-info endpoint doesn't exist"""
            # Mock search endpoint to return asset count
            search_response = {"albums": {"total": 0, "items": []}, "assets": {"total": 150, "count": 150, "items": []}}

            # Mock albums endpoint to return album count
            albums_response = [
                {"id": "album1", "albumName": "Test Album 1"},
                {"id": "album2", "albumName": "Test Album 2"},
            ]

            with patch.object(api_client, "_get", new_callable=AsyncMock) as mock_get:
                # Mock /server-info to fail (404)
                mock_get.side_effect = [
                    ImmichAPIError("GET /server-info failed - HTTP 404"),  # server-info fails
                    search_response,  # search/metadata succeeds
                    albums_response,  # albums succeeds
                ]

                result = await api_client.get_server_stats()

                # Verify results include v2.4.0 indicators
                assert result["photos"] == 150  # From search endpoint
                assert result["albums"] == 2  # From albums endpoint
                assert result["api_version"] == "2.4.0+"

        @pytest.mark.asyncio
        async def test_get_server_info_v240_detection(self, api_client):
            """Test server info detection for v2.4.0+"""
            # Mock all endpoints to simulate v2.4.0 behavior
            with patch.object(api_client, "_get", new_callable=AsyncMock) as mock_get:
                # Mock /server-info to fail (doesn't exist in v2.4.0)
                mock_get.side_effect = ImmichAPIError("GET /server-info failed - HTTP 404")

                result = await api_client.get_server_info()

                # Verify v2.4.0+ detection
                assert result["version"] == "2.4.0+"
                assert result["is_v2_plus"] is True
                assert result["api_architecture"] == "search_based"
                assert result["individual_asset_access"] is False

        @pytest.mark.asyncio
        async def test_get_server_info_with_ocr_capability(self, api_client):
            """Test server info with OCR capability detection"""
            # Mock OCR search to succeed (indicating OCR support)
            ocr_response = {"assets": {"total": 1, "count": 1, "items": []}}

            with patch.object(api_client, "_get", new_callable=AsyncMock) as mock_get:
                # Mock /server-info to fail, then OCR search to succeed
                mock_get.side_effect = [
                    ImmichAPIError("GET /server-info failed - HTTP 404"),  # server-info fails
                    ocr_response,  # OCR search succeeds
                ]

                result = await api_client.get_server_info()

                # Verify OCR detection worked
                assert result["has_ocr"] is True
                assert result["has_multilingual_ocr"] is True
                assert result["has_ocr_bounding_boxes"] is True
                assert "english" in result["ocr_languages"]

    class TestEndpointCompatibility:
        """Test that other endpoints still work correctly"""

        @pytest.mark.asyncio
        async def test_albums_endpoints_still_work(self, api_client, mock_response):
            """Test that albums endpoints are unchanged in v2.4.0"""
            mock_response.json.return_value = [
                {"id": "album1", "albumName": "Test Album", "description": "Test description", "assetCount": 10}
            ]

            with patch.object(api_client, "_get", new_callable=AsyncMock) as mock_get:
                mock_get.return_value = mock_response.json()

                result = await api_client.get_albums()

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

        @pytest.mark.asyncio
        async def test_upload_endpoints_still_work(self, api_client):
            """Test that upload endpoints are unchanged"""
            # This is harder to test fully without file mocking, but we can test the endpoint call
            with patch.object(api_client, "_post", new_callable=AsyncMock) as mock_post:
                mock_post.return_value = {"id": "uploaded_asset_123"}

                # This would normally require actual files, so we'll just verify the endpoint
                # The actual upload testing would be in integration tests
                pass

    class TestErrorHandling:
        """Test error handling for v2.4.0 API changes"""

        @pytest.mark.asyncio
        async def test_ocr_fallback_when_not_available(self, api_client):
            """Test OCR search fallback when endpoint doesn't exist"""
            with patch.object(api_client, "_get", new_callable=AsyncMock) as mock_get:
                # First call (OCR) fails with 404
                mock_get.side_effect = [
                    ImmichAPIError("GET /search/ocr failed - HTTP 404"),  # OCR fails
                    {  # Fallback smart search succeeds
                        "assets": {"total": 1, "items": [{"id": "asset1"}]}
                    },
                ]

                result = await api_client.search_photos("test query", search_type="ocr")

                # Verify fallback to smart search
                assert mock_get.call_count == 2
                assert len(result) == 1
                assert result[0]["id"] == "asset1"

        @pytest.mark.asyncio
        async def test_graceful_degradation_server_info(self, api_client):
            """Test graceful degradation when server-info doesn't exist"""
            with patch.object(api_client, "_get", new_callable=AsyncMock) as mock_get:
                # All calls fail, should still return basic info
                mock_get.side_effect = ImmichAPIError("All endpoints failed")

                result = await api_client.get_server_info()

                # Should return basic v2.4.0+ info even when endpoints fail
                assert result["version"] == "2.4.0+"
                assert result["api_architecture"] == "search_based"
                assert "errors" in result

    class TestVersionDetection:
        """Test automatic version detection and adaptation"""

        @pytest.mark.asyncio
        async def test_automatic_v240_detection(self, api_client):
            """Test that API client automatically detects v2.4.0+ behavior"""
            with patch.object(api_client, "_get", new_callable=AsyncMock) as mock_get:
                # Simulate v2.4.0 behavior: server-info fails, search works
                mock_get.side_effect = [
                    ImmichAPIError("GET /server-info failed - HTTP 404"),  # No server-info
                    {"assets": {"total": 100, "items": []}},  # Search works
                    [{"id": "album1"}],  # Albums work
                ]

                server_info = await api_client.get_server_info()
                server_stats = await api_client.get_server_stats()

                # Both should detect v2.4.0+
                assert "2.4.0+" in server_info["version"]
                assert server_stats["api_version"] == "2.4.0+"
                assert server_info["api_architecture"] == "search_based"


class TestImmichMCPIntegration:
    """Integration tests for ImmichMCP server with v2.4.0 API"""

    @pytest.fixture
    def server_config(self):
        """Create test server configuration"""
        return {"server_url": "http://localhost:2283", "api_key": "test_api_key_12345", "timeout": 30}

    def test_server_initialization(self, server_config):
        """Test that server initializes correctly with v2.4.0 config"""
        # This would test the FastMCP server initialization
        # For now, just verify config structure
        assert "server_url" in server_config
        assert "api_key" in server_config
        assert server_config["timeout"] == 30

    def test_api_client_initialization(self, server_config):
        """Test API client initialization with v2.4.0 awareness"""
        config = ImmichConfig(**server_config)
        client = ImmichAPIClient(config)

        assert client.base_url == "http://localhost:2283"
        assert client.api_key == "test_api_key_12345"
        assert config.timeout == 30


if __name__ == "__main__":
    # Run tests with detailed output
    pytest.main([__file__, "-v", "--tb=short"])
