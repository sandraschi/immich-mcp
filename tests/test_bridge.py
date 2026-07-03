import pytest
from unittest.mock import AsyncMock, patch
from pathlib import Path
import tempfile
from immich_mcp.bridge import download_asset_to_temp
from immich_mcp.immich_api import ImmichAPIError

@pytest.mark.asyncio
async def test_download_asset_to_temp_success():
    # Setup mock client
    mock_client = AsyncMock()
    mock_client.get_asset_info = AsyncMock(return_value={
        "id": "test-asset-123",
        "originalFileName": "myphoto.jpg",
        "type": "IMAGE"
    })
    mock_client.get_binary = AsyncMock(return_value=b"fake jpeg data")

    with patch("immich_mcp.bridge.get_api_client", return_value=mock_client):
        local_path = await download_asset_to_temp("test-asset-123")
        
        # Verify calls
        mock_client.get_asset_info.assert_awaited_once_with("test-asset-123")
        mock_client.get_binary.assert_awaited_once_with("/assets/test-asset-123/original")
        
        # Verify file contents
        path = Path(local_path)
        assert path.exists()
        assert path.name == "myphoto.jpg"
        assert path.read_bytes() == b"fake jpeg data"
        
        # Clean up temp file
        path.unlink()

@pytest.mark.asyncio
async def test_download_asset_to_temp_no_filename():
    mock_client = AsyncMock()
    mock_client.get_asset_info = AsyncMock(return_value={
        "id": "test-asset-123",
        "type": "VIDEO"
    })
    mock_client.get_binary = AsyncMock(return_value=b"fake video data")

    with patch("immich_mcp.bridge.get_api_client", return_value=mock_client):
        local_path = await download_asset_to_temp("test-asset-123")
        
        path = Path(local_path)
        assert path.exists()
        assert path.name == "test-asset-123.mp4"
        assert path.read_bytes() == b"fake video data"
        
        path.unlink()

@pytest.mark.asyncio
async def test_download_asset_to_temp_failure():
    mock_client = AsyncMock()
    mock_client.get_asset_info = AsyncMock(side_effect=Exception("API Error"))

    with patch("immich_mcp.bridge.get_api_client", return_value=mock_client):
        with pytest.raises(ImmichAPIError):
            await download_asset_to_temp("test-asset-123")
