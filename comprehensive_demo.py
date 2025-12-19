#!/usr/bin/env python3
"""
Comprehensive Immich MCP Demo

Demonstrates all 15+ MCP tools working together with real 1998 photos.
Shows complete photo management workflow from upload to organization.
"""

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

# Add src to path
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

from immich_mcp.server import (
    upload_photos,
    search_photos,
    get_photo_info,
    get_ocr_data,
    organize_photos_by_date,
    create_album,
    add_to_album,
    list_albums,
    detect_people,
    get_storage_info,
    server_health,
)


async def comprehensive_demo():
    """Run comprehensive demo of all MCP tools."""

    print("[DEMO] Immich MCP Comprehensive Demo with 1998 Photos")
    print("=" * 60)
    print("This demo showcases all MCP tools working together")
    print("Using real photos from Sandra's 1998 collection")
    print("=" * 60)

    # Step 1: Server Health Check
    print("\n[1/10] Checking server health...")
    health = await server_health()
    print(f"   [OK] Immich v{health.server_version} - {'v2+' if health.is_v2_plus else 'v1.x'}")
    if health.has_ocr:
        print("   [OK] OCR support available")
    if health.has_multilingual_ocr:
        print("   [OK] Multilingual OCR available")

    # Step 2: Prepare test photos (real 1998 photos)
    print("\n[2/10] Preparing 1998 photo collection...")
    test_photos = [
        "Hol 99 - Mira the Dog 1 [digicam].JPG",
        "Hol 99 - Mira the Dog 2 [digicam].JPG",
        "Hol 99 - Mira the Dog 3 [digicam].JPG",
        "Hol 99 - Mira the Dog 4 [digicam].JPG",
        "Hol 99 - SAS self portrait in bed.JPG",
        "Hol 99 - Atmos Clock [digicam].JPG",
        "Hol 99 - Dried Flowers on Mantelpiece.JPG",
        "Hol 99 - Russian Dolls [digicam].JPG"
    ]

    photo_paths = []
    for photo_name in test_photos:
        photo_path = Path(__file__).parent / "test_photos" / photo_name
        if photo_path.exists():
            photo_paths.append(str(photo_path))
            print(f"   [OK] {photo_name}")

    print(f"   → {len(photo_paths)} photos ready for upload")

    # Step 3: Upload photos to Immich
    print("\n[3/10] Uploading photos to Immich...")
    upload_result = await upload_photos(
        file_paths=photo_paths,
        album_name="1998 Demo Collection",
        auto_organize=False
    )

    print(f"   [OK] Uploaded {upload_result.uploaded_count} photos")
    print(f"   [OK] {upload_result.duplicate_count} duplicates skipped")
    uploaded_assets = upload_result.uploaded_assets

    if not uploaded_assets:
        print("   [FAIL] No assets uploaded - cannot continue demo")
        return

    # Step 4: Get photo information
    print("\n[4/10] Retrieving photo metadata...")
    asset_id = uploaded_assets[0]
    photo_info = await get_photo_info(asset_id=asset_id)
    print(f"   [OK] Photo: {photo_info.original_filename}")
    print(f"   [OK] Size: {photo_info.file_size_bytes:,} bytes")
    print(f"   [OK] Created: {photo_info.created_at}")

    # Step 5: Test OCR functionality
    print("\n[5/10] Testing OCR capabilities...")
    try:
        ocr_data = await get_ocr_data(asset_id=asset_id)
        if ocr_data.text:
            print(f"   [OK] OCR extracted {len(ocr_data.text)} characters")
            print(f"   [OK] Language: {ocr_data.language}")
            print(f"   [OK] Confidence: {ocr_data.confidence:.2f}")
        else:
            print("   [INFO] No text found in image")
    except Exception as e:
        print(f"   [INFO] OCR not available: {e}")

    # Step 6: Create organized albums
    print("\n[6/10] Creating organized albums...")

    # Create album for dog photos
    dog_album = await create_album(
        name="Mira the Dog (1998)",
        description="Photos of Sandra's dog Mira from 1998"
    )
    print(f"   [OK] Created album: {dog_album.album_name}")

    # Create album for household items
    household_album = await create_album(
        name="1998 Household Items",
        description="Various household items photographed in 1998"
    )
    print(f"   [OK] Created album: {household_album.album_name}")

    # Step 7: Add photos to albums
    print("\n[7/10] Organizing photos into albums...")

    # Add dog photos to dog album
    dog_photo_ids = [aid for aid, path in zip(uploaded_assets, photo_paths)
                    if "Mira the Dog" in Path(path).name]
    if dog_photo_ids:
        add_result = await add_to_album(
            album_id=dog_album.id,
            asset_ids=dog_photo_ids
        )
        print(f"   [OK] Added {add_result.added_count} dog photos to album")

    # Add household items to household album
    household_photo_ids = [aid for aid, path in zip(uploaded_assets, photo_paths)
                          if any(item in Path(path).name for item in ["Clock", "Flowers", "Dolls"])]
    if household_photo_ids:
        add_result = await add_to_album(
            album_id=household_album.id,
            asset_ids=household_photo_ids
        )
        print(f"   [OK] Added {add_result.added_count} household photos to album")

    # Step 8: Search functionality
    print("\n[8/10] Testing search capabilities...")

    # Search for dog photos
    dog_search = await search_photos(
        query="dog",
        search_type="smart",
        limit=10
    )
    print(f"   [OK] Smart search 'dog': {len(dog_search)} results")

    # Search by filename pattern
    filename_search = await search_photos(
        query="Mira",
        search_type="filename",
        limit=10
    )
    print(f"   [OK] Filename search 'Mira': {len(filename_search)} results")

    # Step 9: Face detection
    print("\n[9/10] Testing face detection...")
    try:
        detect_result = await detect_people(asset_ids=uploaded_assets[:3])
        print(f"   [OK] Detected {detect_result.detected_faces} faces")
        print(f"   [OK] Created {detect_result.new_people} people clusters")
    except Exception as e:
        print(f"   [INFO] Face detection not available: {e}")

    # Step 10: Storage and organization
    print("\n[10/10] Storage analysis and organization...")

    # Get storage info
    storage = await get_storage_info()
    print(f"   [OK] Storage: {storage.photos} photos, {storage.usage:.1f}GB total")

    # Organize by date
    organize_result = await organize_photos_by_date(
        asset_ids=uploaded_assets,
        organization_type="year_month"
    )
    print(f"   [OK] Organized into {organize_result.albums_created} date-based albums")

    # Step 11: List all albums
    print("\n[EXTRA] Listing all albums...")
    albums = await list_albums(include_stats=True)
    print(f"   [OK] Total albums: {len(albums)}")
    for album in albums[-3:]:  # Show last 3 albums
        print(f"      - {album.album_name} ({album.asset_count} photos)")

    # Summary
    print("\n" + "="*60)
    print("[SUCCESS] COMPREHENSIVE DEMO COMPLETED SUCCESSFULLY!")
    print("="*60)
    print(f"[PHOTOS] Photos Uploaded: {len(uploaded_assets)}")
    print(f"[ALBUMS] Albums Created: 2")
    print(f"[SEARCH] Searches Performed: 2")
    print(f"[FACES] Faces Detected: {detect_result.detected_faces if 'detect_result' in locals() else 'N/A'}")
    print(f"[STORAGE] Storage Used: {storage.usage:.1f}GB")
    print("="*60)
    print("All MCP tools demonstrated with real 1998 photographs!")
    print("Demo data created for testing and development purposes.")
    print("="*60)


async def main():
    """Main entry point."""
    try:
        await comprehensive_demo()
    except KeyboardInterrupt:
        print("\n[STOP] Demo interrupted by user")
    except Exception as e:
        print(f"\n[ERROR] Demo failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
