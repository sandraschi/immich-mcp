"""
Pytest configuration and fixtures for ImmichMCP tests.
"""
import asyncio
import os
from pathlib import Path
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from fastmcp.settings import Settings as FastMCPSettings

from immich_mcp import ImmichMCP, get_settings
from immich_mcp.immich_api import ImmichAPIClient

# Test configuration
TEST_CONFIG = {
    "app_name": "TestImmichMCP",
    "app_version": "1.0.0-test",
    "host": "127.0.0.1",
    "port": 8000,
    "log_level": "debug",
    "immich_url": "http://test-immich:2283",
    "immich_api_key": "test-api-key-123",
    "immich_timeout": 10,
    "immich_max_retries": 2,
}

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    policy = asyncio.WindowsSelectorEventLoopPolicy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(autouse=True)
def mock_settings(monkeypatch, tmp_path):
    """Override settings for all tests."""
    # Set environment variables
    for key, value in TEST_CONFIG.items():
        monkeypatch.setenv(f"IMMICH_MCP_{key.upper()}", str(value))
    
    # Create test directories
    upload_dir = tmp_path / "uploads"
    upload_dir.mkdir()
    
    # Patch settings
    with patch("immich_mcp.settings.Settings") as mock_settings:
        settings = get_settings()
        for key, value in TEST_CONFIG.items():
            setattr(settings, key, value)
        settings.upload_dir = upload_dir
        mock_settings.return_value = settings
        yield settings

@pytest.fixture
def mock_immich_client():
    """Create a mock Immich API client."""
    with patch('immich_mcp.immich_api.ImmichAPIClient') as mock:
        client = AsyncMock(spec=ImmichAPIClient)
        client.base_url = TEST_CONFIG["immich_url"]
        client.api_key = TEST_CONFIG["immich_api_key"]
        
        # Set up mock methods
        client.initialize = AsyncMock(return_value=None)
        client.close = AsyncMock(return_value=None)
        client.search_photos = AsyncMock(return_value=[])
        client.upload_photo = AsyncMock(return_value={"id": "test-photo-id"})
        client.get_photo_info = AsyncMock(return_value={"id": "test-photo-id"})
        
        mock.return_value = client
        yield client

@pytest.fixture
def test_app(mock_immich_client, mock_settings):
    """Create a test FastMCP application."""
    # Create FastMCP settings
    config = FastMCPSettings(
        name=mock_settings.app_name,
        version=mock_settings.app_version,
        description="Test ImmichMCP server",
    )
    
    app = ImmichMCP(config=config)
    
    # Store the mock client on the app instance for test access
    app.immich_client = mock_immich_client
    
    return app

@pytest.fixture
def test_client(test_app):
    """Create a test client for the FastAPI app."""
    with TestClient(test_app.app) as client:
        yield client

@pytest.fixture
def test_photo(tmp_path) -> Path:
    """Create a test photo file."""
    photo_path = tmp_path / "test.jpg"
    photo_path.write_bytes(b"fake image data")
    return photo_path
