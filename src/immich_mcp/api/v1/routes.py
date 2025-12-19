"""
FastMCP 2.10 API routes for ImmichMCP.

This module defines the FastAPI router with all v1 API endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException

from ...immich_api import ImmichAPIClient

router = APIRouter(prefix="/api/v1", tags=["v1"])


# Health check endpoint required by FastMCP 2.10
@router.get("/health")
async def health_check():
    """Health check endpoint for FastMCP 2.10 compatibility."""
    return {"status": "ok", "version": "1.0.0"}


# ===== PHOTO MANAGEMENT ENDPOINTS =====

@router.post("/photos/upload")
async def upload_photos(
    file_paths: list[str],
    album_name: str | None = None,
    auto_organize: bool = False,
    client: ImmichAPIClient = Depends(ImmichAPIClient),
):
    """Upload photos to Immich with batch processing."""
    try:
        from ..server import upload_photos as upload_tool
        return await upload_tool(file_paths, album_name, auto_organize)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

@router.get("/photos/search")
async def search_photos(
    query: str,
    search_type: str = "smart",
    limit: int = 50,
    client: ImmichAPIClient = Depends(ImmichAPIClient),
):
    """Search photos using CLIP smart search or metadata queries."""
    try:
        from ..server import search_photos as search_tool
        return await search_tool(query, search_type, limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

@router.get("/photos/{asset_id}")
async def get_photo_info(
    asset_id: str,
    client: ImmichAPIClient = Depends(ImmichAPIClient),
):
    """Get detailed photo information and metadata."""
    try:
        from ..server import get_photo_info as info_tool
        return await info_tool(asset_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

@router.get("/photos/{asset_id}/ocr")
async def get_ocr_data(
    asset_id: str,
    client: ImmichAPIClient = Depends(ImmichAPIClient),
):
    """Get OCR text extraction data for a photo."""
    try:
        from ..server import get_ocr_data as ocr_tool
        return await ocr_tool(asset_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

@router.get("/photos/{asset_id}/ocr-text")
async def get_asset_ocr(
    asset_id: str,
    client: ImmichAPIClient = Depends(ImmichAPIClient),
):
    """Get OCR text for a photo (alternative endpoint)."""
    try:
        from ..server import get_asset_ocr as ocr_tool
        return await ocr_tool(asset_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

@router.post("/photos/organize")
async def organize_photos_by_date(
    asset_ids: list[str],
    organization_type: str = "year_month",
    client: ImmichAPIClient = Depends(ImmichAPIClient),
):
    """Organize photos into date-based albums."""
    try:
        from ..server import organize_photos_by_date as organize_tool
        return await organize_tool(asset_ids, organization_type)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

@router.delete("/photos")
async def delete_photos(
    asset_ids: list[str],
    move_to_trash: bool = True,
    client: ImmichAPIClient = Depends(ImmichAPIClient),
):
    """Delete photos from Immich."""
    try:
        from ..server import delete_photos as delete_tool
        return await delete_tool(asset_ids, move_to_trash)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

# ===== ALBUM MANAGEMENT ENDPOINTS =====

@router.post("/albums")
async def create_album(
    name: str,
    description: str | None = None,
    client: ImmichAPIClient = Depends(ImmichAPIClient),
):
    """Create a new album."""
    try:
        from ..server import create_album as create_tool
        return await create_tool(name, description)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

@router.get("/albums")
async def list_albums(
    shared: bool | None = None,
    include_stats: bool = True,
    client: ImmichAPIClient = Depends(ImmichAPIClient),
):
    """List all albums."""
    try:
        from ..server import list_albums as list_tool
        return await list_tool(shared, include_stats)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

@router.post("/albums/{album_id}/photos")
async def add_to_album(
    album_id: str,
    asset_ids: list[str],
    client: ImmichAPIClient = Depends(ImmichAPIClient),
):
    """Add photos to an album."""
    try:
        from ..server import add_to_album as add_tool
        return await add_tool(album_id, asset_ids)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

@router.post("/albums/{album_id}/share")
async def share_album(
    album_id: str,
    allow_download: bool = True,
    allow_upload: bool = False,
    expires_at: str | None = None,
    show_metadata: bool = True,
    client: ImmichAPIClient = Depends(ImmichAPIClient),
):
    """Generate share link for an album."""
    try:
        from ..server import share_album as share_tool
        return await share_tool(album_id, expires_at, allow_download, allow_upload, show_metadata)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

# ===== PEOPLE & FACE DETECTION ENDPOINTS =====

@router.post("/people/detect")
async def detect_people(
    asset_ids: list[str] | None = None,
    force_reprocess: bool = False,
    client: ImmichAPIClient = Depends(ImmichAPIClient),
):
    """Run face detection on photos."""
    try:
        from ..server import detect_people as detect_tool
        return await detect_tool(asset_ids, force_reprocess)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

@router.post("/people/{person_id}/tag")
async def tag_person(
    person_id: str,
    name: str,
    face_asset_ids: list[str] | None = None,
    client: ImmichAPIClient = Depends(ImmichAPIClient),
):
    """Assign name to detected person."""
    try:
        from ..server import tag_person as tag_tool
        return await tag_tool(person_id, name, face_asset_ids)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

@router.get("/people/search")
async def search_by_person(
    person_name: str,
    limit: int = 50,
    include_metadata: bool = True,
    client: ImmichAPIClient = Depends(ImmichAPIClient),
):
    """Find all photos containing a specific person."""
    try:
        from ..server import search_by_person as search_tool
        return await search_tool(person_name, limit, include_metadata)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

# ===== SYSTEM & ADMINISTRATION ENDPOINTS =====

@router.get("/system/storage")
async def get_storage_info(
    client: ImmichAPIClient = Depends(ImmichAPIClient),
):
    """Get storage usage statistics."""
    try:
        from ..server import get_storage_info as storage_tool
        return await storage_tool()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

@router.post("/system/backup")
async def backup_photos(
    backup_path: str,
    album_ids: list[str] | None = None,
    include_metadata: bool = True,
    client: ImmichAPIClient = Depends(ImmichAPIClient),
):
    """Create backup of photos."""
    try:
        from ..server import backup_photos as backup_tool
        return await backup_tool(backup_path, album_ids, include_metadata)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

@router.get("/system/health")
async def server_health(
    client: ImmichAPIClient = Depends(ImmichAPIClient),
):
    """Get server health and status."""
    try:
        from ..server import server_health as health_tool
        return await health_tool()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
