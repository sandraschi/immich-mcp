"""
ImmichMCP - FastMCP 2.10 Server for Immich Photo Management

Austrian efficiency for Sandra's 2000+ photo library.
Provides 15 tools: 5 core photo operations + 4 album management + 3 people/faces + 3 administration
"""

import asyncio
import os
import logging
from typing import Optional, List, Dict, Any, Type, Callable
from datetime import datetime
from pathlib import Path

import httpx
from fastapi import FastAPI, Depends
from fastmcp import FastMCP, FastMCPBase, FastMCPConfig
from pydantic import BaseModel, Field, AnyHttpUrl
from rich.console import Console
from dotenv import load_dotenv

from .immich_api import ImmichAPIClient, ImmichAPIError
from .config import ImmichConfig, get_settings
from .api.v1.routes import router as v1_router

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("immich_mcp")

# Initialize console for rich output
console = Console()

class ImmichMCP(FastMCPBase):
    """ImmichMCP server implementation extending FastMCP 2.10 base."""
    
    def __init__(self, config: Optional[FastMCPConfig] = None):
        """Initialize the ImmichMCP server.
        
        Args:
            config: Optional FastMCP configuration
        """
        super().__init__(config or FastMCPConfig(
            name="ImmichMCP",
            version="1.0.0",
            description="FastMCP 2.10 server for Immich photo management",
        ))
        self.immich_client: Optional[ImmichAPIClient] = None
        self.app = FastAPI(
            title="ImmichMCP",
            description="FastMCP 2.10 server for Immich photo management",
            version="1.0.0",
        )
        
        # Include API routers
        self.app.include_router(v1_router, prefix="/immich-mcp")
        
        # Add startup and shutdown event handlers
        self.app.add_event_handler("startup", self.startup_event)
        self.app.add_event_handler("shutdown", self.shutdown_event)
    
    async def startup_event(self):
        """Initialize resources when the server starts."""
        settings = get_settings()
        try:
            self.immich_client = ImmichAPIClient(
                base_url=settings.immich_url,
                api_key=settings.immich_api_key,
            )
            await self.immich_client.initialize()
            logger.info("Immich client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Immich client: {e}")
            raise
    
    async def shutdown_event(self):
        """Clean up resources when the server shuts down."""
        if self.immich_client:
            await self.immich_client.close()
            logger.info("Immich client closed")
    
    def get_fastapi_app(self) -> FastAPI:
        """Get the FastAPI application instance.
        
        Returns:
            The configured FastAPI application
        """
        return self.app

# Initialize FastMCP server
mcp = ImmichMCP()


# Pydantic Models for all 15 tools
class PhotoSearchResult(BaseModel):
    """Individual photo search result"""
    id: str = Field(description="Photo asset ID")
    original_filename: str = Field(description="Original filename")
    file_path: str = Field(description="File path on server")
    device_asset_id: str = Field(description="Device asset identifier")
    owner_id: str = Field(description="Owner user ID")
    device_id: str = Field(description="Device ID")
    type: str = Field(description="Asset type (IMAGE/VIDEO)")
    created_at: str = Field(description="Creation timestamp")
    updated_at: str = Field(description="Last update timestamp")
    file_created_at: str = Field(description="File creation date")
    local_date_time: str = Field(description="Local date/time from EXIF")
    duration: Optional[str] = Field(default=None, description="Duration for videos")
    is_favorite: bool = Field(description="Favorite status")
    is_archived: bool = Field(description="Archive status")
    is_trashed: bool = Field(description="Trash status")
    checksum: str = Field(description="File checksum")
    smart_search_score: Optional[float] = Field(default=None, description="CLIP search relevance score")


class UploadResult(BaseModel):
    """Photo upload operation result"""
    uploaded_count: int = Field(description="Number of photos uploaded")
    duplicate_count: int = Field(description="Number of duplicates skipped")
    error_count: int = Field(description="Number of upload errors")
    uploaded_assets: List[str] = Field(description="List of uploaded asset IDs")
    errors: List[str] = Field(description="List of error messages")
    total_size_mb: float = Field(description="Total size uploaded in MB")
    upload_time_seconds: float = Field(description="Total upload time")


class PhotoInfo(BaseModel):
    """Detailed photo information with EXIF"""
    id: str
    original_filename: str
    file_path: str
    type: str
    created_at: str
    updated_at: str
    file_created_at: str
    local_date_time: str
    is_favorite: bool
    is_archived: bool
    is_trashed: bool
    checksum: str
    file_size_bytes: int
    exif_info: Dict[str, Any] = Field(default_factory=dict)
    smart_info: Dict[str, Any] = Field(default_factory=dict)
    people: List[str] = Field(default_factory=list)
    albums: List[str] = Field(default_factory=list)


class OrganizeResult(BaseModel):
    """Photo organization operation result"""
    albums_created: int = Field(description="Number of albums created")
    photos_organized: int = Field(description="Number of photos organized")
    organization_type: str = Field(description="Organization method used")
    created_albums: List[str] = Field(description="Names of created albums")
    errors: List[str] = Field(description="Any errors during organization")


class DeletionResult(BaseModel):
    """Photo deletion operation result"""
    deleted_count: int = Field(description="Number of photos deleted")
    trashed_count: int = Field(description="Number of photos moved to trash")
    error_count: int = Field(description="Number of deletion errors")
    deleted_asset_ids: List[str] = Field(description="List of deleted asset IDs")
    errors: List[str] = Field(description="List of error messages")


class AlbumResult(BaseModel):
    """Album creation result"""
    id: str = Field(description="Album ID")
    album_name: str = Field(description="Album name")
    description: Optional[str] = Field(default=None, description="Album description")
    created_at: str = Field(description="Creation timestamp")
    asset_count: int = Field(description="Number of photos in album")
    owner_id: str = Field(description="Album owner ID")


class AlbumInfo(BaseModel):
    """Album information"""
    id: str
    album_name: str
    description: Optional[str] = None
    created_at: str
    updated_at: str
    asset_count: int
    owner_id: str
    shared: bool
    album_thumbnail_asset_id: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None


class AlbumUpdateResult(BaseModel):
    """Album update operation result"""
    album_id: str
    added_count: int = Field(description="Number of photos added")
    duplicate_count: int = Field(description="Number of duplicates skipped")
    new_asset_count: int = Field(description="Total photos in album after update")
    errors: List[str] = Field(default_factory=list)


class ShareResult(BaseModel):
    """Album sharing result"""
    id: str = Field(description="Share link ID")
    key: str = Field(description="Share key")
    public_url: str = Field(description="Public access URL")
    album_id: str = Field(description="Shared album ID")
    expires_at: Optional[str] = Field(default=None, description="Expiration date")
    allow_upload: bool = Field(description="Upload permission")
    allow_download: bool = Field(description="Download permission")
    show_metadata: bool = Field(description="Metadata visibility")
    created_at: str = Field(description="Share creation timestamp")


class PeopleDetectionResult(BaseModel):
    """Face detection operation result"""
    detected_faces: int = Field(description="Number of faces detected")
    new_people: int = Field(description="Number of new person clusters")
    processed_assets: int = Field(description="Number of photos processed")
    processing_time_seconds: float = Field(description="Detection processing time")
    people_found: List[Dict[str, Any]] = Field(description="List of detected people clusters")


class PersonInfo(BaseModel):
    """Person/face cluster information"""
    id: str = Field(description="Person ID")
    name: Optional[str] = Field(default=None, description="Assigned name")
    face_count: int = Field(description="Number of faces in cluster")
    thumbnail_asset_id: Optional[str] = Field(default=None, description="Representative photo ID")
    is_hidden: bool = Field(description="Hidden status")
    birth_date: Optional[str] = Field(default=None, description="Birth date if set")
    created_at: str = Field(description="Person creation timestamp")
    updated_at: str = Field(description="Last update timestamp")


class PersonTagResult(BaseModel):
    """Person tagging operation result"""
    person_id: str
    name: str = Field(description="Assigned name")
    faces_merged: int = Field(description="Number of faces merged")
    total_faces: int = Field(description="Total faces for this person")
    updated_at: str = Field(description="Update timestamp")


class StorageInfo(BaseModel):
    """Storage information and statistics"""
    used_bytes: int = Field(description="Used storage in bytes")
    available_bytes: int = Field(description="Available storage in bytes")
    total_bytes: int = Field(description="Total storage in bytes")
    usage_percentage: float = Field(description="Usage percentage")
    photo_count: int = Field(description="Total number of photos")
    video_count: int = Field(description="Total number of videos")
    user_count: int = Field(description="Number of users")
    album_count: int = Field(description="Number of albums")
    storage_usage_by_user: List[Dict[str, Any]] = Field(description="Per-user storage breakdown")


class BackupResult(BaseModel):
    """Backup operation result"""
    backup_path: str = Field(description="Backup destination path")
    exported_photos: int = Field(description="Number of photos exported")
    exported_videos: int = Field(description="Number of videos exported")
    total_size_mb: float = Field(description="Total backup size in MB")
    backup_time_seconds: float = Field(description="Backup processing time")
    metadata_included: bool = Field(description="Whether metadata was preserved")
    album_structure_preserved: bool = Field(description="Whether album structure was maintained")
    errors: List[str] = Field(default_factory=list)


class HealthStatus(BaseModel):
    """Server health status"""
    server_version: str = Field(description="Immich server version")
    server_features: List[str] = Field(description="Available server features")
    database_connected: bool = Field(description="Database connection status")
    redis_connected: bool = Field(description="Redis connection status")
    storage_accessible: bool = Field(description="Storage accessibility")
    ml_services_available: bool = Field(description="Machine learning services status")
    response_time_ms: int = Field(description="API response time in milliseconds")
    uptime_seconds: int = Field(description="Server uptime in seconds")
    error_messages: List[str] = Field(default_factory=list)


async def get_api_client() -> ImmichAPIClient:
    """Get initialized API client, creating if needed"""
    global api_client
    if api_client is None:
        config = ImmichConfig()
        api_client = ImmichAPIClient(config)
    return api_client


# ====== PHASE 1: CORE PHOTO OPERATIONS (5 tools) ======

@mcp.tool()
async def upload_photos(
    file_paths: List[str],
    album_name: Optional[str] = None,
    auto_organize: bool = False
) -> UploadResult:
    """
    Upload photos to Immich with batch processing and metadata detection.
    
    Austrian efficiency tool for Sandra's photo management workflow.
    Supports batch upload with automatic organization and duplicate detection.
    
    Args:
        file_paths: List of photo file paths to upload
        album_name: Optional album name to add photos to
        auto_organize: Automatically organize by date after upload
        
    Returns:
        Upload summary with success/error counts and asset IDs
        
    Example:
        upload_photos(["/path/to/photos/*.jpg"], album_name="Vienna Summer", auto_organize=True)
    """
    try:
        start_time = asyncio.get_event_loop().time()
        client = await get_api_client()
        
        # Perform batch upload
        result = await client.upload_photos_batch(
            file_paths=file_paths,
            album_name=album_name,
            auto_organize=auto_organize
        )
        
        end_time = asyncio.get_event_loop().time()
        upload_time = end_time - start_time
        
        return UploadResult(
            uploaded_count=result.get('uploaded_count', 0),
            duplicate_count=result.get('duplicate_count', 0),
            error_count=result.get('error_count', 0),
            uploaded_assets=result.get('uploaded_assets', []),
            errors=result.get('errors', []),
            total_size_mb=result.get('total_size_mb', 0.0),
            upload_time_seconds=upload_time
        )
        
    except ImmichAPIError as e:
        console.print(f"[red]Immich API error in upload_photos: {e}[/red]")
        return UploadResult(
            uploaded_count=0,
            duplicate_count=0,
            error_count=len(file_paths),
            uploaded_assets=[],
            errors=[str(e)],
            total_size_mb=0.0,
            upload_time_seconds=0.0
        )


@mcp.tool()
async def search_photos(
    query: str,
    search_type: str = Field("smart", description="Search type: smart, metadata, or filename"),
    limit: int = Field(50, description="Maximum results to return")
) -> List[PhotoSearchResult]:
    """
    Search photos using CLIP smart search or metadata queries.
    
    Austrian efficiency: Natural language search through 2000+ photo library.
    Uses Immich's CLIP-based smart search for content understanding.
    
    Args:
        query: Search terms (natural language for smart search)
        search_type: "smart" for CLIP search, "metadata" for EXIF, "filename" for names
        limit: Maximum number of results (1-200)
        
    Returns:
        List of matching photos with metadata and relevance scores
        
    Example:
        search_photos("Benny playing in park", search_type="smart", limit=20)
    """
    try:
        client = await get_api_client()
        
        # Validate limit
        limit = max(1, min(200, limit))
        
        # Perform search based on type
        results = await client.search_photos(
            query=query,
            search_type=search_type,
            limit=limit
        )
        
        # Convert to response format
        photo_results = []
        for photo in results:
            photo_result = PhotoSearchResult(
                id=photo['id'],
                original_filename=photo.get('originalFileName', 'Unknown'),
                file_path=photo.get('originalPath', ''),
                device_asset_id=photo.get('deviceAssetId', ''),
                owner_id=photo.get('ownerId', ''),
                device_id=photo.get('deviceId', ''),
                type=photo.get('type', 'IMAGE'),
                created_at=photo.get('createdAt', ''),
                updated_at=photo.get('updatedAt', ''),
                file_created_at=photo.get('fileCreatedAt', ''),
                local_date_time=photo.get('localDateTime', ''),
                duration=photo.get('duration'),
                is_favorite=photo.get('isFavorite', False),
                is_archived=photo.get('isArchived', False),
                is_trashed=photo.get('isTrashed', False),
                checksum=photo.get('checksum', ''),
                smart_search_score=photo.get('score')
            )
            photo_results.append(photo_result)
            
        return photo_results
        
    except ImmichAPIError as e:
        console.print(f"[red]Immich API error in search_photos: {e}[/red]")
        return []


@mcp.tool()
async def get_photo_info(asset_id: str) -> PhotoInfo:
    """
    Get complete metadata and EXIF information for a specific photo.
    
    Retrieves all available information including EXIF data, smart info,
    people tags, and album associations.
    
    Args:
        asset_id: Immich asset ID to fetch details for
        
    Returns:
        Complete photo object with all metadata and associations
        
    Example:
        get_photo_info("01234567-89ab-cdef-0123-456789abcdef")
    """
    try:
        client = await get_api_client()
        photo_data = await client.get_asset_info(asset_id)
        
        if not photo_data:
            return PhotoInfo(
                id=asset_id,
                original_filename="Asset not found",
                file_path="",
                type="UNKNOWN",
                created_at="",
                updated_at="",
                file_created_at="",
                local_date_time="",
                is_favorite=False,
                is_archived=False,
                is_trashed=False,
                checksum="",
                file_size_bytes=0
            )
        
        return PhotoInfo(
            id=asset_id,
            original_filename=photo_data.get('originalFileName', 'Unknown'),
            file_path=photo_data.get('originalPath', ''),
            type=photo_data.get('type', 'IMAGE'),
            created_at=photo_data.get('createdAt', ''),
            updated_at=photo_data.get('updatedAt', ''),
            file_created_at=photo_data.get('fileCreatedAt', ''),
            local_date_time=photo_data.get('localDateTime', ''),
            is_favorite=photo_data.get('isFavorite', False),
            is_archived=photo_data.get('isArchived', False),
            is_trashed=photo_data.get('isTrashed', False),
            checksum=photo_data.get('checksum', ''),
            file_size_bytes=photo_data.get('fileSizeInByte', 0),
            exif_info=photo_data.get('exifInfo', {}),
            smart_info=photo_data.get('smartInfo', {}),
            people=photo_data.get('people', []),
            albums=photo_data.get('albums', [])
        )
        
    except ImmichAPIError as e:
        console.print(f"[red]Immich API error in get_photo_info: {e}[/red]")
        return PhotoInfo(
            id=asset_id,
            original_filename=f"Error: {str(e)}",
            file_path="",
            type="ERROR",
            created_at="",
            updated_at="",
            file_created_at="",
            local_date_time="",
            is_favorite=False,
            is_archived=False,
            is_trashed=False,
            checksum="",
            file_size_bytes=0
        )


@mcp.tool()
async def organize_photos_by_date(
    asset_ids: List[str],
    organization_type: str = Field("year_month", description="Organization: year, year_month, or year_month_day")
) -> OrganizeResult:
    """
    Automatically organize photos into date-based albums.
    
    Austrian efficiency: Bulk organization without manual album creation.
    Creates albums based on photo dates and adds photos automatically.
    
    Args:
        asset_ids: List of photo IDs to organize
        organization_type: Grouping method (year, year_month, year_month_day)
        
    Returns:
        Organization summary with created albums and photo counts
        
    Example:
        organize_photos_by_date(["id1", "id2", "id3"], organization_type="year_month")
    """
    try:
        client = await get_api_client()
        
        # Perform organization
        result = await client.organize_photos_by_date(
            asset_ids=asset_ids,
            organization_type=organization_type
        )
        
        return OrganizeResult(
            albums_created=result.get('albums_created', 0),
            photos_organized=result.get('photos_organized', 0),
            organization_type=organization_type,
            created_albums=result.get('created_albums', []),
            errors=result.get('errors', [])
        )
        
    except ImmichAPIError as e:
        console.print(f"[red]Immich API error in organize_photos_by_date: {e}[/red]")
        return OrganizeResult(
            albums_created=0,
            photos_organized=0,
            organization_type=organization_type,
            created_albums=[],
            errors=[str(e)]
        )


@mcp.tool()
async def delete_photos(
    asset_ids: List[str],
    move_to_trash: bool = Field(True, description="Move to trash (true) or permanently delete (false)")
) -> DeletionResult:
    """
    Delete photos with trash/permanent options.
    
    Safe deletion workflow with trash support for recovery.
    Permanently delete only when explicitly requested.
    
    Args:
        asset_ids: List of photo IDs to delete
        move_to_trash: True for trash (recoverable), False for permanent deletion
        
    Returns:
        Deletion summary with counts and any errors
        
    Example:
        delete_photos(["id1", "id2"], move_to_trash=True)  # Safe deletion
    """
    try:
        client = await get_api_client()
        
        # Perform deletion
        result = await client.delete_photos(
            asset_ids=asset_ids,
            move_to_trash=move_to_trash
        )
        
        return DeletionResult(
            deleted_count=result.get('deleted_count', 0),
            trashed_count=result.get('trashed_count', 0),
            error_count=result.get('error_count', 0),
            deleted_asset_ids=result.get('deleted_asset_ids', []),
            errors=result.get('errors', [])
        )
        
    except ImmichAPIError as e:
        console.print(f"[red]Immich API error in delete_photos: {e}[/red]")
        return DeletionResult(
            deleted_count=0,
            trashed_count=0,
            error_count=len(asset_ids),
            deleted_asset_ids=[],
            errors=[str(e)]
        )


# ====== PHASE 2 CATEGORY 1: ALBUM MANAGEMENT (4 tools) ======

@mcp.tool()
async def create_album(
    name: str,
    description: Optional[str] = None,
    asset_ids: Optional[List[str]] = None
) -> AlbumResult:
    """
    Create a new photo album in Immich.
    
    Args:
        name: Album name
        description: Optional album description
        asset_ids: Optional list of photo IDs to add initially
    
    Returns:
        AlbumResult with creation details and album ID
        
    Example:
        create_album("Vienna Summer 2025", "Photos from summer in Vienna", ["id1", "id2"])
    """
    try:
        client = await get_api_client()
        
        result = await client.create_album(
            name=name,
            description=description,
            asset_ids=asset_ids or []
        )
        
        return AlbumResult(
            id=result['id'],
            album_name=result['albumName'],
            description=result.get('description'),
            created_at=result['createdAt'],
            asset_count=result.get('assetCount', 0),
            owner_id=result['ownerId']
        )
        
    except ImmichAPIError as e:
        console.print(f"[red]Immich API error in create_album: {e}[/red]")
        return AlbumResult(
            id="",
            album_name=name,
            description=description,
            created_at="",
            asset_count=0,
            owner_id=""
        )


@mcp.tool()
async def add_to_album(
    album_id: str,
    asset_ids: List[str]
) -> AlbumUpdateResult:
    """
    Add photos to an existing album.
    
    Args:
        album_id: Target album ID
        asset_ids: List of photo IDs to add
    
    Returns:
        AlbumUpdateResult with addition summary
        
    Example:
        add_to_album("album-id-123", ["photo1", "photo2", "photo3"])
    """
    try:
        client = await get_api_client()
        
        result = await client.add_assets_to_album(
            album_id=album_id,
            asset_ids=asset_ids
        )
        
        return AlbumUpdateResult(
            album_id=album_id,
            added_count=result.get('added_count', 0),
            duplicate_count=result.get('duplicate_count', 0),
            new_asset_count=result.get('new_asset_count', 0),
            errors=result.get('errors', [])
        )
        
    except ImmichAPIError as e:
        console.print(f"[red]Immich API error in add_to_album: {e}[/red]")
        return AlbumUpdateResult(
            album_id=album_id,
            added_count=0,
            duplicate_count=0,
            new_asset_count=0,
            errors=[str(e)]
        )


@mcp.tool()
async def list_albums(
    shared: Optional[bool] = None,
    include_stats: bool = True
) -> List[AlbumInfo]:
    """
    List all albums with metadata and statistics.
    
    Args:
        shared: Filter by shared status (None for all)
        include_stats: Include photo count and date range
    
    Returns:
        List of AlbumInfo with comprehensive details
        
    Example:
        list_albums(shared=False, include_stats=True)
    """
    try:
        client = await get_api_client()
        
        albums_data = await client.get_albums(
            shared=shared,
            include_stats=include_stats
        )
        
        albums = []
        for album_data in albums_data:
            album = AlbumInfo(
                id=album_data['id'],
                album_name=album_data['albumName'],
                description=album_data.get('description'),
                created_at=album_data['createdAt'],
                updated_at=album_data['updatedAt'],
                asset_count=album_data.get('assetCount', 0),
                owner_id=album_data['ownerId'],
                shared=album_data.get('shared', False),
                album_thumbnail_asset_id=album_data.get('albumThumbnailAssetId'),
                start_date=album_data.get('startDate'),
                end_date=album_data.get('endDate')
            )
            albums.append(album)
        
        return albums
        
    except ImmichAPIError as e:
        console.print(f"[red]Immich API error in list_albums: {e}[/red]")
        return []


@mcp.tool()
async def share_album(
    album_id: str,
    expires_at: Optional[str] = None,
    allow_download: bool = True,
    allow_upload: bool = False,
    show_metadata: bool = True
) -> ShareResult:
    """
    Generate public share link for album.
    
    Args:
        album_id: Album to share
        expires_at: Optional expiration date (ISO format)
        allow_download: Allow downloading photos
        allow_upload: Allow uploading photos to album
        show_metadata: Show photo metadata to viewers
    
    Returns:
        ShareResult with public URL and settings
        
    Example:
        share_album("album-123", expires_at="2025-12-31T23:59:59Z", allow_download=True)
    """
    try:
        client = await get_api_client()
        
        result = await client.create_shared_link(
            album_id=album_id,
            expires_at=expires_at,
            allow_download=allow_download,
            allow_upload=allow_upload,
            show_metadata=show_metadata
        )
        
        return ShareResult(
            id=result['id'],
            key=result['key'],
            public_url=result['public_url'],
            album_id=album_id,
            expires_at=result.get('expiresAt'),
            allow_upload=result.get('allowUpload', False),
            allow_download=result.get('allowDownload', True),
            show_metadata=result.get('showMetadata', True),
            created_at=result['createdAt']
        )
        
    except ImmichAPIError as e:
        console.print(f"[red]Immich API error in share_album: {e}[/red]")
        return ShareResult(
            id="",
            key="",
            public_url="",
            album_id=album_id,
            expires_at=expires_at,
            allow_upload=allow_upload,
            allow_download=allow_download,
            show_metadata=show_metadata,
            created_at=""
        )


# ====== PHASE 2 CATEGORY 2: PEOPLE & FACES (3 tools) ======

@mcp.tool()
async def detect_people(
    asset_ids: Optional[List[str]] = None,
    force_reprocess: bool = False
) -> PeopleDetectionResult:
    """
    Run face detection on photos and return clustering results.
    
    Args:
        asset_ids: Specific photos to process (None for all)
        force_reprocess: Re-detect faces even if already processed
    
    Returns:
        PeopleDetectionResult with detected faces and clusters
        
    Example:
        detect_people(force_reprocess=False)  # Process all unprocessed photos
    """
    try:
        start_time = asyncio.get_event_loop().time()
        client = await get_api_client()
        
        result = await client.run_face_detection(
            asset_ids=asset_ids,
            force_reprocess=force_reprocess
        )
        
        end_time = asyncio.get_event_loop().time()
        processing_time = end_time - start_time
        
        return PeopleDetectionResult(
            detected_faces=result.get('detected_faces', 0),
            new_people=result.get('new_people', 0),
            processed_assets=result.get('processed_assets', 0),
            processing_time_seconds=processing_time,
            people_found=result.get('people_found', [])
        )
        
    except ImmichAPIError as e:
        console.print(f"[red]Immich API error in detect_people: {e}[/red]")
        return PeopleDetectionResult(
            detected_faces=0,
            new_people=0,
            processed_assets=0,
            processing_time_seconds=0.0,
            people_found=[]
        )


@mcp.tool()
async def tag_person(
    person_id: str,
    name: str,
    face_asset_ids: Optional[List[str]] = None
) -> PersonTagResult:
    """
    Assign name to detected person/face cluster.
    
    Args:
        person_id: Person cluster ID from face detection
        name: Name to assign to person
        face_asset_ids: Additional faces to merge with person
    
    Returns:
        PersonTagResult with tagging summary
        
    Example:
        tag_person("person-123", "Sandra", face_asset_ids=["face1", "face2"])
    """
    try:
        client = await get_api_client()
        
        result = await client.update_person(
            person_id=person_id,
            name=name,
            face_asset_ids=face_asset_ids or []
        )
        
        return PersonTagResult(
            person_id=person_id,
            name=name,
            faces_merged=result.get('faces_merged', 0),
            total_faces=result.get('total_faces', 0),
            updated_at=result.get('updated_at', datetime.now().isoformat())
        )
        
    except ImmichAPIError as e:
        console.print(f"[red]Immich API error in tag_person: {e}[/red]")
        return PersonTagResult(
            person_id=person_id,
            name=name,
            faces_merged=0,
            total_faces=0,
            updated_at=datetime.now().isoformat()
        )


@mcp.tool()
async def search_by_person(
    person_name: str,
    limit: int = 50,
    include_metadata: bool = True
) -> List[PhotoSearchResult]:
    """
    Find all photos containing specific person.
    
    Args:
        person_name: Name of person to search for
        limit: Maximum number of results
        include_metadata: Include photo metadata
    
    Returns:
        List of photos containing the person
        
    Example:
        search_by_person("Sandra", limit=100, include_metadata=True)
    """
    try:
        client = await get_api_client()
        
        # Validate limit
        limit = max(1, min(200, limit))
        
        results = await client.search_photos_by_person(
            person_name=person_name,
            limit=limit,
            include_metadata=include_metadata
        )
        
        # Convert to response format
        photo_results = []
        for photo in results:
            photo_result = PhotoSearchResult(
                id=photo['id'],
                original_filename=photo.get('originalFileName', 'Unknown'),
                file_path=photo.get('originalPath', ''),
                device_asset_id=photo.get('deviceAssetId', ''),
                owner_id=photo.get('ownerId', ''),
                device_id=photo.get('deviceId', ''),
                type=photo.get('type', 'IMAGE'),
                created_at=photo.get('createdAt', ''),
                updated_at=photo.get('updatedAt', ''),
                file_created_at=photo.get('fileCreatedAt', ''),
                local_date_time=photo.get('localDateTime', ''),
                duration=photo.get('duration'),
                is_favorite=photo.get('isFavorite', False),
                is_archived=photo.get('isArchived', False),
                is_trashed=photo.get('isTrashed', False),
                checksum=photo.get('checksum', ''),
                smart_search_score=None  # Not applicable for person search
            )
            photo_results.append(photo_result)
            
        return photo_results
        
    except ImmichAPIError as e:
        console.print(f"[red]Immich API error in search_by_person: {e}[/red]")
        return []


# ====== PHASE 2 CATEGORY 3: ADMINISTRATION (3 tools) ======

@mcp.tool()
async def get_storage_info() -> StorageInfo:
    """
    Get storage usage statistics and performance metrics.
    
    Returns:
        StorageInfo with disk usage, photo counts, and performance data
        
    Example:
        get_storage_info()  # Get current storage statistics
    """
    try:
        client = await get_api_client()
        
        storage_data = await client.get_server_stats()
        
        return StorageInfo(
            used_bytes=storage_data.get('usage', 0),
            available_bytes=storage_data.get('available', 0),
            total_bytes=storage_data.get('total', 0),
            usage_percentage=storage_data.get('usage_percentage', 0.0),
            photo_count=storage_data.get('photos', 0),
            video_count=storage_data.get('videos', 0),
            user_count=storage_data.get('users', 0),
            album_count=storage_data.get('albums', 0),
            storage_usage_by_user=storage_data.get('usage_by_user', [])
        )
        
    except ImmichAPIError as e:
        console.print(f"[red]Immich API error in get_storage_info: {e}[/red]")
        return StorageInfo(
            used_bytes=0,
            available_bytes=0,
            total_bytes=0,
            usage_percentage=0.0,
            photo_count=0,
            video_count=0,
            user_count=0,
            album_count=0,
            storage_usage_by_user=[]
        )


@mcp.tool()
async def backup_photos(
    backup_path: str,
    album_ids: Optional[List[str]] = None,
    include_metadata: bool = True
) -> BackupResult:
    """
    Export photos for backup with metadata preservation.
    
    Args:
        backup_path: Destination directory for backup
        album_ids: Specific albums to backup (None for all)
        include_metadata: Include EXIF and Immich metadata
    
    Returns:
        BackupResult with export summary and file paths
        
    Example:
        backup_photos("D:/Backup/Immich-2025-07", include_metadata=True)
    """
    try:
        start_time = asyncio.get_event_loop().time()
        client = await get_api_client()
        
        result = await client.export_photos(
            backup_path=backup_path,
            album_ids=album_ids,
            include_metadata=include_metadata
        )
        
        end_time = asyncio.get_event_loop().time()
        backup_time = end_time - start_time
        
        return BackupResult(
            backup_path=backup_path,
            exported_photos=result.get('exported_photos', 0),
            exported_videos=result.get('exported_videos', 0),
            total_size_mb=result.get('total_size_mb', 0.0),
            backup_time_seconds=backup_time,
            metadata_included=include_metadata,
            album_structure_preserved=result.get('album_structure_preserved', False),
            errors=result.get('errors', [])
        )
        
    except ImmichAPIError as e:
        console.print(f"[red]Immich API error in backup_photos: {e}[/red]")
        return BackupResult(
            backup_path=backup_path,
            exported_photos=0,
            exported_videos=0,
            total_size_mb=0.0,
            backup_time_seconds=0.0,
            metadata_included=include_metadata,
            album_structure_preserved=False,
            errors=[str(e)]
        )


@mcp.tool()
async def server_health() -> HealthStatus:
    """
    Check Immich server health and connection status.
    
    Returns:
        HealthStatus with server info, API version, and diagnostics
        
    Example:
        server_health()  # Check current server status
    """
    try:
        start_time = asyncio.get_event_loop().time()
        client = await get_api_client()
        
        health_data = await client.get_server_info()
        
        end_time = asyncio.get_event_loop().time()
        response_time_ms = int((end_time - start_time) * 1000)
        
        return HealthStatus(
            server_version=health_data.get('version', 'Unknown'),
            server_features=health_data.get('features', []),
            database_connected=health_data.get('database', True),
            redis_connected=health_data.get('redis', True),
            storage_accessible=health_data.get('storage', True),
            ml_services_available=health_data.get('machine_learning', True),
            response_time_ms=response_time_ms,
            uptime_seconds=health_data.get('uptime', 0),
            error_messages=health_data.get('errors', [])
        )
        
    except ImmichAPIError as e:
        end_time = asyncio.get_event_loop().time()
        response_time_ms = int((end_time - start_time) * 1000)
        
        console.print(f"[red]Immich API error in server_health: {e}[/red]")
        return HealthStatus(
            server_version="Unknown",
            server_features=[],
            database_connected=False,
            redis_connected=False,
            storage_accessible=False,
            ml_services_available=False,
            response_time_ms=response_time_ms,
            uptime_seconds=0,
            error_messages=[str(e)]
        )


def main():
    """Main entry point for ImmichMCP server"""
    console.print("[green]🚀 Starting ImmichMCP - FastMCP 2.1 Server[/green]")
    console.print("[blue]Austrian efficiency for your 2000+ photo library! 📷[/blue]")
    
    # Run the FastMCP server
    mcp.run()


if __name__ == "__main__":
    main()
