#!/usr/bin/env python3
"""
Comprehensive Immich MCP Demo

Demonstrates all 15+ MCP tools working together with real 1998 photos.
Shows complete photo management workflow from upload to organization.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

import contextlib

from immich_mcp.server import (
    add_to_album,
    create_album,
    detect_people,
    get_ocr_data,
    get_photo_info,
    get_storage_info,
    list_albums,
    organize_photos_by_date,
    search_photos,
    server_health,
    upload_photos,
)


async def comprehensive_demo():
    """Run comprehensive demo of all MCP tools."""

    # Step 1: Server Health Check
    health = await server_health()
    if health.has_ocr:
        pass
    if health.has_multilingual_ocr:
        pass

    # Step 2: Prepare test photos (real 1998 photos)
    test_photos = [
        "Hol 99 - Mira the Dog 1 [digicam].JPG",
        "Hol 99 - Mira the Dog 2 [digicam].JPG",
        "Hol 99 - Mira the Dog 3 [digicam].JPG",
        "Hol 99 - Mira the Dog 4 [digicam].JPG",
        "Hol 99 - SAS self portrait in bed.JPG",
        "Hol 99 - Atmos Clock [digicam].JPG",
        "Hol 99 - Dried Flowers on Mantelpiece.JPG",
        "Hol 99 - Russian Dolls [digicam].JPG",
    ]

    photo_paths = []
    for photo_name in test_photos:
        photo_path = Path(__file__).parent / "test_photos" / photo_name
        if photo_path.exists():
            photo_paths.append(str(photo_path))

    # Step 3: Upload photos to Immich
    upload_result = await upload_photos(file_paths=photo_paths, album_name="1998 Demo Collection", auto_organize=False)

    uploaded_assets = upload_result.uploaded_assets

    if not uploaded_assets:
        return

    # Step 4: Get photo information
    asset_id = uploaded_assets[0]
    await get_photo_info(asset_id=asset_id)

    # Step 5: Test OCR functionality
    try:
        ocr_data = await get_ocr_data(asset_id=asset_id)
        if ocr_data.text:
            pass
        else:
            pass
    except Exception:
        pass

    # Step 6: Create organized albums

    # Create album for dog photos
    dog_album = await create_album(name="Mira the Dog (1998)", description="Photos of Sandra's dog Mira from 1998")

    # Create album for household items
    household_album = await create_album(
        name="1998 Household Items", description="Various household items photographed in 1998"
    )

    # Step 7: Add photos to albums

    # Add dog photos to dog album
    dog_photo_ids = [
        aid for aid, path in zip(uploaded_assets, photo_paths, strict=False) if "Mira the Dog" in Path(path).name
    ]
    if dog_photo_ids:
        await add_to_album(album_id=dog_album.id, asset_ids=dog_photo_ids)

    # Add household items to household album
    household_photo_ids = [
        aid
        for aid, path in zip(uploaded_assets, photo_paths, strict=False)
        if any(item in Path(path).name for item in ["Clock", "Flowers", "Dolls"])
    ]
    if household_photo_ids:
        await add_to_album(album_id=household_album.id, asset_ids=household_photo_ids)

    # Step 8: Search functionality

    # Search for dog photos
    await search_photos(query="dog", search_type="smart", limit=10)

    # Search by filename pattern
    await search_photos(query="Mira", search_type="filename", limit=10)

    # Step 9: Face detection
    with contextlib.suppress(Exception):
        await detect_people(asset_ids=uploaded_assets[:3])

    # Step 10: Storage and organization

    # Get storage info
    await get_storage_info()

    # Organize by date
    await organize_photos_by_date(asset_ids=uploaded_assets, organization_type="year_month")

    # Step 11: List all albums
    albums = await list_albums(include_stats=True)
    for _album in albums[-3:]:  # Show last 3 albums
        pass

    # Summary


async def main():
    """Main entry point."""
    try:
        await comprehensive_demo()
    except KeyboardInterrupt:
        pass
    except Exception:
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
