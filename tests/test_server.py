"""
Tests for the ImmichMCP FastMCP 2.10 server implementation.
"""
import asyncio
from pathlib import Path
from unittest.mock import patch

import pytest
from fastmcp.settings import Settings as FastMCPSettings

from immich_mcp import ImmichMCP

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
    
    # Verify the client's initialize method was called
    mock_immich_client.initialize.assert_awaited_once()

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
    response = test_client.get("/immich-mcp/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "version": "1.0.0"}

@pytest.mark.asyncio
async def test_upload_photos_endpoint(test_client, mock_immich_client, tmp_path):
    """Test the photo upload endpoint."""
    # Create a test file
    test_file = tmp_path / "test.jpg"
    test_file.write_bytes(b"test image data")
    
    # Mock the upload response
    mock_immich_client.upload_photo.return_value = {
        "id": "test-photo-id",
        "original_filename": "test.jpg",
        "status": "success"
    }
    
    # Make the request
    with open(test_file, "rb") as f:
        response = test_client.post(
            "/immich-mcp/api/v1/photos/upload",
            files={"file": ("test.jpg", f, "image/jpeg")},
            data={"album_name": "Test Album"}
        )
    
    # Verify the response
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    
    # Verify the upload method was called with the correct arguments
    mock_immich_client.upload_photo.assert_awaited_once()

@pytest.mark.asyncio
async def test_search_photos_endpoint(test_client, mock_immich_client):
    """Test the photo search endpoint."""
    # Mock the search response
    mock_immich_client.search_photos.return_value = [
        {"id": "photo1", "filename": "test1.jpg"},
        {"id": "photo2", "filename": "test2.jpg"},
    ]
    
    # Make the request
    response = test_client.get(
        "/immich-mcp/api/v1/photos/search",
        params={"query": "test", "limit": 2}
    )
    
    # Verify the response
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["id"] == "photo1"
    assert data[1]["id"] == "photo2"
    
    # Verify the search method was called with the correct arguments
    mock_immich_client.search_photos.assert_awaited_once_with("test", 2)
