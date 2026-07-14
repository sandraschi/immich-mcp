"""
Tests for the ImmichMCP FastMCP 2.10 server implementation.
"""

import pytest

# Test data
TEST_CONFIG = {
    "app_name": "TestImmichMCP",
    "app_version": "1.0.0-test",
    "immich_url": "http://test-immich:2283",
    "immich_api_key": "test-api-key",
}


@pytest.mark.asyncio
async def test_server_startup(test_app, mock_immich_client):
    """Test that the server starts up and initializes the Immich client."""
    # Simulate server startup
    await test_app.startup_event()

    # Verify the client is initialized
    assert test_app.immich_client is not None


@pytest.mark.asyncio
async def test_server_shutdown(test_app, mock_immich_client):
    """Test that the server shuts down cleanly."""
    # First start the server
    test_app.immich_client = mock_immich_client

    # Then shut it down
    await test_app.shutdown_event()

    # Verify the client's close method was called
    mock_immich_client.close.assert_awaited_once()


def test_health_endpoint(test_client):
    """Test the health check endpoint."""
    response = test_client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "version": "1.0.0"}


@pytest.mark.asyncio
async def test_upload_photos_endpoint(test_client, mock_immich_client, tmp_path):
    """Test the photo upload endpoint."""
    # Create a test file
    test_file = tmp_path / "test.jpg"
    test_file.write_bytes(b"test image data")

    # Make the request: file_paths is in the JSON body, album_name is a query parameter
    response = test_client.post(
        "/api/v1/photos/upload",
        json=[str(test_file)],
        params={"album_name": "Test Album"},
    )

    # Verify the response
    assert response.status_code == 200

    # Verify the upload method was called
    mock_immich_client.upload_photos_batch.assert_awaited_once()


@pytest.mark.asyncio
async def test_search_photos_endpoint(test_client, mock_immich_client):
    """Test the photo search endpoint."""
    # Mock the search response
    mock_immich_client.search_photos.return_value = [
        {"id": "photo1", "filename": "test1.jpg"},
        {"id": "photo2", "filename": "test2.jpg"},
    ]

    # Make the request
    response = test_client.get("/api/v1/photos/search", params={"query": "test", "limit": 2})

    # Verify the response
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["id"] == "photo1"
    assert data[1]["id"] == "photo2"

    # Verify the search method was called with the correct arguments
    mock_immich_client.search_photos.assert_awaited_once()
    kwargs = mock_immich_client.search_photos.call_args[1]
    assert kwargs["query"] == "test"
    assert kwargs["search_type"] == "smart"
    assert kwargs["limit"] == 2


@pytest.mark.asyncio
async def test_download_photo_to_temp(test_app):
    from unittest.mock import patch

    from immich_mcp.server import download_photo_to_temp

    with patch("immich_mcp.bridge.download_asset_to_temp", return_value="C:/temp/photo.jpg") as mock_download:
        result = await download_photo_to_temp("photo123")
        assert result["success"] is True
        assert result["local_path"] == "C:/temp/photo.jpg"
        mock_download.assert_awaited_once_with("photo123")


@pytest.mark.asyncio
async def test_sync_metadata_to_exif(test_app, mock_immich_client, tmp_path):
    from unittest.mock import patch

    from immich_mcp.server import sync_metadata_to_exif

    # Create a dummy file
    dummy_file = tmp_path / "dummy.jpg"
    dummy_file.write_bytes(b"dummy jpeg content")

    mock_immich_client.get_asset_info.return_value = {
        "id": "photo123",
        "description": "My Sunset",
        "localDateTime": "2026-06-24T20:30:00Z",
        "exifInfo": {
            "latitude": 48.2082,
            "longitude": 16.3738
        }
    }

    # Mock piexif calls to avoid real image manipulation issues
    with patch("piexif.load", return_value={"0th": {}, "Exif": {}, "GPS": {}, "1st": {}, "thumbnail": None}), \
         patch("piexif.dump", return_value=b"new exif bytes"), \
         patch("piexif.insert") as mock_insert:

        result = await sync_metadata_to_exif("photo123", str(dummy_file))
        assert result["success"] is True
        assert "description" in result["updated_fields"]
        assert "date_time" in result["updated_fields"]
        assert "gps" in result["updated_fields"]
        mock_insert.assert_called_once()


@pytest.mark.asyncio
async def test_detect_similar_photos(test_app, mock_immich_client):
    from immich_mcp.server import detect_similar_photos

    mock_immich_client._get.return_value = [
        {
            "duplicateId": "dup1",
            "suggestedKeepAssetIds": ["photo1"],
            "assets": [
                {"id": "photo1", "originalFileName": "test1.jpg", "fileSizeBytes": 1000},
                {"id": "photo2", "originalFileName": "test2.jpg", "fileSizeBytes": 900}
            ]
        }
    ]

    result = await detect_similar_photos()
    assert result["success"] is True
    assert result["count"] == 1
    assert len(result["duplicate_groups"]) == 1
    assert result["duplicate_groups"][0]["duplicate_id"] == "dup1"

