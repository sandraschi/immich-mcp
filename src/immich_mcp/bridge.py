import tempfile
from pathlib import Path

from .immich_api import ImmichAPIError, get_api_client


async def download_asset_to_temp(asset_id: str) -> str:
    """Download the original file of an asset to a local temporary path.

    Args:
        asset_id: The UUID of the asset to download.

    Returns:
        The absolute local path of the downloaded file.
    """
    client = await get_api_client()
    try:
        # Get asset info to determine filename
        asset_info = await client.get_asset_info(asset_id)
        original_filename = asset_info.get("originalFileName")
        if not original_filename:
            # Fallback to UUID and type extension
            ext = ".jpg"
            if asset_info.get("type") == "VIDEO":
                ext = ".mp4"
            original_filename = f"{asset_id}{ext}"

        # Download binary content
        content = await client.get_binary(f"/assets/{asset_id}/original")

        # Save to temp directory
        temp_dir = Path(tempfile.gettempdir()) / "immich_mcp_bridge"
        temp_dir.mkdir(parents=True, exist_ok=True)

        temp_file_path = temp_dir / original_filename
        temp_file_path.write_bytes(content)

        return str(temp_file_path.resolve())
    except Exception as e:
        raise ImmichAPIError(f"Failed to download asset {asset_id} to temp: {e}") from e
