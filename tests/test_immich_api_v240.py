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
            mock_post.assert_called_with("/search/smart", data={"query": "test query", "size": 50})

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
            mock_post.assert_called_with("/search/metadata", data={"originalFileName": "vacation", "size": 50})

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
            mock_post.assert_called_with("/search/metadata", data={"query": "metadata query", "size": 50})

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
    async def test_get_server_stats_real_endpoints(self, api_client):
        """Test server stats using the current /server/storage + /server/statistics endpoints"""
        server_about_response = {"version": "v2.7.5"}
        storage_response = {
            "diskUseRaw": 1000,
            "diskAvailableRaw": 2000,
            "diskSizeRaw": 3000,
            "diskUsagePercentage": 33.3,
        }
        stats_response = {
            "photos": 150,
            "videos": 20,
            "usage": 1000,
            "usageByUser": [{"userId": "u1", "photos": 150}],
        }
        albums_response = [{"id": "a1"}, {"id": "a2"}]

        with (
            patch.object(api_client, "_get", new_callable=AsyncMock) as mock_get,
        ):
            mock_get.side_effect = [
                server_about_response,  # /server/about
                storage_response,  # /server/storage
                stats_response,  # /server/statistics
                albums_response,  # /albums
            ]

            result = await api_client.get_server_stats()

            # Verify results
            assert result["photos"] == 150
            assert result["videos"] == 20
            assert result["api_version"] == "v2.7.5"
            assert result["usage"] == 1000
            assert result["users"] == 1
            assert result["albums"] == 2
            assert result["available"] == 2000
            assert result["total"] == 3000

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
            assert result["is_v2_plus"] is True
            assert result["api_architecture"] == "search_based"
            assert result["individual_asset_access"] is True

    @pytest.mark.asyncio
    async def test_get_server_info_v3_detection(self, api_client):
        """Test v3 detection via is_v3"""
        server_about_response = {"version": "3.1.0"}

        with patch.object(api_client, "_get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = server_about_response

            assert await api_client.is_v3() is True


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
    async def test_ocr_not_found_raises(self, api_client):
        """Test that asset OCR raises on 404 (no fabricated empty results)"""
        with patch.object(api_client, "_get", new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = ImmichAPIError("GET /assets/id/ocr failed - HTTP 404: Not Found")

            with pytest.raises(ImmichAPIError):
                await api_client.get_asset_ocr("test-id")


class TestCurrentApiContracts:
    """Tests for the v2.7+/v3 API contracts"""

    @pytest.mark.asyncio
    async def test_timeline_uses_search_metadata(self, api_client):
        """Timeline must use POST /search/metadata (GET /assets was removed in v2.7+)"""
        page_response = {"assets": {"items": [{"id": "a1"}, {"id": "a2"}], "total": 2}}

        with patch.object(api_client, "_post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = page_response

            result = await api_client.get_timeline_assets(page=2, size=50)

            mock_post.assert_called_with("/search/metadata", data={"page": 2, "size": 50, "order": "desc"})
            assert [a["id"] for a in result] == ["a1", "a2"]

    @pytest.mark.asyncio
    async def test_delete_to_trash_uses_force_false(self, api_client):
        """Trash must use DELETE /assets with force=false (no /assets/trash endpoint)"""
        with patch.object(api_client, "_delete", new_callable=AsyncMock) as mock_delete:
            mock_delete.return_value = {"success": True}

            result = await api_client.delete_photos(["a1", "a2"], move_to_trash=True)

            mock_delete.assert_called_with("/assets", data={"ids": ["a1", "a2"], "force": False})
            assert result["trashed_count"] == 2
            assert result["deleted_count"] == 0

    @pytest.mark.asyncio
    async def test_permanent_delete_uses_force_true(self, api_client):
        """Permanent delete must use DELETE /assets with force=true"""
        with patch.object(api_client, "_delete", new_callable=AsyncMock) as mock_delete:
            mock_delete.return_value = {"success": True}

            result = await api_client.delete_photos(["a1"], move_to_trash=False)

            mock_delete.assert_called_with("/assets", data={"ids": ["a1"], "force": True})
            assert result["deleted_count"] == 1

    @pytest.mark.asyncio
    async def test_edit_asset_uses_edits_endpoint(self, api_client):
        """Edits must use PUT /assets/{id}/edits with action/parameters (v2.5.0+)"""
        with patch.object(api_client, "_put", new_callable=AsyncMock) as mock_put:
            mock_put.return_value = {"edits": []}

            await api_client.edit_asset("asset-1", "rotate", angle=90)

            mock_put.assert_called_with(
                "/assets/asset-1/edits", data={"edits": [{"action": "rotate", "parameters": {"angle": 90}}]}
            )

    @pytest.mark.asyncio
    async def test_edit_asset_crop_params(self, api_client):
        """Crop must map x/y/width/height into parameters"""
        with patch.object(api_client, "_put", new_callable=AsyncMock) as mock_put:
            mock_put.return_value = {"edits": []}

            await api_client.edit_asset("asset-1", "crop", x=10, y=20, width=100, height=50)

            mock_put.assert_called_with(
                "/assets/asset-1/edits",
                data={"edits": [{"action": "crop", "parameters": {"x": 10, "y": 20, "width": 100, "height": 50}}]},
            )

    @pytest.mark.asyncio
    async def test_edit_asset_unknown_operation_raises(self, api_client):
        """Unknown edit operations must raise instead of hitting a nonexistent endpoint"""
        with pytest.raises(ImmichAPIError):
            await api_client.edit_asset("asset-1", "blur")

    @pytest.mark.asyncio
    async def test_upload_uses_iso_dates(self, api_client, tmp_path):
        """Upload must send ISO-8601 dates and per-version fields"""
        photo = tmp_path / "test.jpg"
        photo.write_bytes(b"fake image data")

        with (
            patch.object(api_client, "is_v3", new_callable=AsyncMock) as mock_v3,
            patch.object(api_client, "_post", new_callable=AsyncMock) as mock_post,
        ):
            mock_v3.return_value = False
            mock_post.return_value = {"id": "asset-1", "duplicate": False}

            result = await api_client.upload_photos_batch([str(photo)])

            assert result["uploaded_count"] == 1
            call_data = mock_post.call_args.kwargs["data"]
            assert call_data["deviceAssetId"] == "test"
            assert call_data["deviceId"] == "MCP-Upload"
            assert call_data["fileCreatedAt"].endswith("Z")
            assert "T" in call_data["fileCreatedAt"]

    @pytest.mark.asyncio
    async def test_upload_v3_omits_legacy_fields(self, api_client, tmp_path):
        """v3 upload must omit deviceAssetId/deviceId and send integer duration"""
        photo = tmp_path / "test.jpg"
        photo.write_bytes(b"fake image data")

        with (
            patch.object(api_client, "is_v3", new_callable=AsyncMock) as mock_v3,
            patch.object(api_client, "_post", new_callable=AsyncMock) as mock_post,
        ):
            mock_v3.return_value = True
            mock_post.return_value = {"id": "asset-1", "duplicate": False}

            result = await api_client.upload_photos_batch([str(photo)])

            assert result["uploaded_count"] == 1
            call_data = mock_post.call_args.kwargs["data"]
            assert "deviceAssetId" not in call_data
            assert "deviceId" not in call_data
            assert call_data["duration"] == 0

    @pytest.mark.asyncio
    async def test_face_detection_uses_assets_jobs(self, api_client):
        """Face detection must queue via POST /assets/jobs with refresh-faces"""
        with patch.object(api_client, "_post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = {}

            result = await api_client.run_face_detection(["a1", "a2"])

            mock_post.assert_called_with("/assets/jobs", data={"assetIds": ["a1", "a2"], "name": "refresh-faces"})
            assert result["job_submitted"] is True
            assert result["asset_count"] == 2

    @pytest.mark.asyncio
    async def test_ocr_aggregates_box_list(self, api_client):
        """OCR must aggregate the word-box list from the real endpoint"""
        box_response = [
            {
                "id": "b1",
                "text": "Hello",
                "textScore": 0.95,
                "x1": 1,
                "y1": 2,
                "x2": 3,
                "y2": 4,
                "x3": 5,
                "y3": 6,
                "x4": 7,
                "y4": 8,
            },
            {
                "id": "b2",
                "text": "World",
                "textScore": 0.85,
                "x1": 9,
                "y1": 10,
                "x2": 11,
                "y2": 12,
                "x3": 13,
                "y3": 14,
                "x4": 15,
                "y4": 16,
            },
        ]

        with patch.object(api_client, "_get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = box_response

            result = await api_client.get_asset_ocr("asset-1")

            assert result["text"] == "Hello World"
            assert result["confidence"] == 0.9
            assert len(result["bounding_boxes"]) == 2
            assert result["bounding_boxes"][0]["x1"] == 1

    @pytest.mark.asyncio
    async def test_visibility_validation(self, api_client):
        """Visibility must be validated against the real enum"""
        with pytest.raises(ImmichAPIError):
            await api_client.update_asset_visibility("asset-1", "private")

        with patch.object(api_client, "_put", new_callable=AsyncMock) as mock_put:
            mock_put.return_value = {"visibility": "archive"}
            result = await api_client.update_asset_visibility("asset-1", "archive")
            mock_put.assert_called_with("/assets/asset-1", data={"visibility": "archive"})
            assert result["visibility"] == "archive"

    @pytest.mark.asyncio
    async def test_get_libraries_handles_plain_array(self, api_client):
        """GET /libraries returns a plain array in v2.7+"""
        with patch.object(api_client, "_get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = [{"id": "lib1", "name": "Default"}]

            result = await api_client.get_libraries()

            assert len(result) == 1
            assert result[0]["name"] == "Default"

    @pytest.mark.asyncio
    async def test_create_library_includes_owner_id(self, api_client):
        """create_library must resolve ownerId via /users/me (required field)"""
        with (
            patch.object(api_client, "_get", new_callable=AsyncMock) as mock_get,
            patch.object(api_client, "_post", new_callable=AsyncMock) as mock_post,
        ):
            mock_get.return_value = {"id": "user-1"}
            mock_post.return_value = {"id": "lib-1"}

            result = await api_client.create_library("Test", import_paths=["D:/Photos"])

            mock_post.assert_called_with(
                "/libraries", {"name": "Test", "ownerId": "user-1", "importPaths": ["D:/Photos"]}
            )
            assert result["id"] == "lib-1"


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
