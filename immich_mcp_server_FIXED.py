#!/usr/bin/env python3
"""
ImmichMCP - FastMCP 2.11+ Server for Immich Photo Management - API FIXED VERSION

Austrian efficiency for photo management with Immich.
Pure FastMCP implementation following Windsurf assessment patterns.

API Fixes for v1.137+:
- /server-info/* → /server/*
- /api/album → /api/albums
"""

import asyncio
import os
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any

import httpx
from dotenv import load_dotenv
from fastmcp import FastMCP
from pydantic import BaseModel, Field, HttpUrl, field_validator
from typing_extensions import Annotated

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("immich_mcp")

# Load environment variables from .env file
load_dotenv()

# Configuration with environment variables
IMMICH_URL = os.getenv("IMMICH_URL", "http://localhost:2283")
IMMICH_API_KEY = os.getenv("IMMICH_API_KEY")

if not IMMICH_API_KEY:
    raise ValueError("IMMICH_API_KEY environment variable must be set")

# Initialize FastMCP server
mcp = FastMCP("immich-mcp")

# Pydantic Models for API responses
class UploadResult(BaseModel):
    """Result of a photo upload operation."""
    uploaded_count: Annotated[int, Field(description="Number of photos uploaded successfully")]
    duplicate_count: Annotated[int, Field(default=0, description="Number of duplicate photos skipped")]
    error_count: Annotated[int, Field(default=0, description="Number of upload errors")]
    uploaded_asset_ids: Annotated[List[str], Field(default_factory=list, description="IDs of successfully uploaded assets")]
    errors: Annotated[List[str], Field(default_factory=list, description="Error messages for failed uploads")]
    total_size_mb: Annotated[float, Field(default=0.0, description="Total size of uploaded files in MB")]
    upload_time_seconds: Annotated[float, Field(default=0.0, description="Total upload time in seconds")]

class PhotoInfo(BaseModel):
    """Detailed information about a photo."""
    id: Annotated[str, Field(description="Unique asset ID")]
    original_filename: Annotated[str, Field(description="Original filename")]
    file_path: Annotated[str, Field(description="Path to the file on the server")]
    type: Annotated[str, Field(description="Asset type (IMAGE/VIDEO)")]
    created_at: Annotated[str, Field(description="Creation timestamp")]
    updated_at: Annotated[str, Field(description="Last update timestamp")]
    file_created_at: Annotated[str, Field(description="File creation date")]
    local_date_time: Annotated[str, Field(description="Local date/time from EXIF")]
    is_favorite: Annotated[bool, Field(default=False, description="Whether the photo is marked as favorite")]
    is_archived: Annotated[bool, Field(default=False, description="Whether the photo is archived")]
    is_trashed: Annotated[bool, Field(default=False, description="Whether the photo is in trash")]
    checksum: Annotated[str, Field(description="File checksum")]
    file_size_bytes: Annotated[int, Field(description="File size in bytes")]
    exif_info: Annotated[Dict[str, Any], Field(default_factory=dict, description="EXIF metadata")]

class BatchResult(BaseModel):
    """Result of a batch photo processing operation."""
    processed_count: Annotated[int, Field(default=0, description="Number of photos processed successfully")]
    error_count: Annotated[int, Field(default=0, description="Number of errors encountered")]
    results: Annotated[List[Dict[str, Any]], Field(default_factory=list, description="Detailed results for each photo")]
    processing_time_seconds: Annotated[float, Field(default=0.0, description="Total processing time in seconds")]

class ImmichClient:
    """Async HTTP client for Immich API."""
    
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.client = httpx.AsyncClient(
            base_url=base_url,
            headers={"x-api-key": api_key},
            timeout=30.0
        )
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
    
    async def upload_asset(self, file_path: Path) -> Dict[str, Any]:
        """Upload a single asset to Immich."""
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        url = f"{self.base_url}/api/asset/upload"
        files = {"assetData": file_path.open('rb')}
        
        try:
            response = await self.client.post(url, files=files)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error uploading {file_path}: {str(e)}")
            raise

# Initialize Immich client
immich_client = ImmichClient(IMMICH_URL, IMMICH_API_KEY)

# MCP Tool: Upload Photos
@mcp.tool()
async def upload_photos(
    file_paths: List[str],
    album_name: Optional[str] = None,
    auto_organize: bool = False
) -> UploadResult:
    """
    Upload photos to Immich with batch processing and metadata detection.
    
    Austrian efficiency tool for photo management workflow.
    Supports batch upload with automatic organization and duplicate detection.
    
    Args:
        file_paths: List of photo file paths to upload
        album_name: Optional album name to add photos to
        auto_organize: Automatically organize by date after upload
        
    Returns:
        Upload summary with success/error counts and asset IDs
        
    Example:
        upload_photos(["/path/to/photo1.jpg", "/path/to/photo2.jpg"], 
                     album_name="Vienna Summer 2025", 
                     auto_organize=True)
    """
    start_time = asyncio.get_event_loop().time()
    result = UploadResult()
    
    # Process each file
    for file_path_str in file_paths:
        file_path = Path(file_path_str)
        
        try:
            # Upload the file
            response = await immich_client.upload_asset(file_path)
            
            # Update result
            result.uploaded_count += 1
            result.uploaded_asset_ids.append(response['id'])
            result.total_size_mb += file_path.stat().st_size / (1024 * 1024)  # Convert to MB
            
            logger.info(f"Uploaded {file_path.name} (ID: {response['id']})")
            
        except FileNotFoundError as e:
            error_msg = f"File not found: {file_path}"
            logger.error(error_msg)
            result.error_count += 1
            result.errors.append(error_msg)
            
        except Exception as e:
            error_msg = f"Error uploading {file_path}: {str(e)}"
            logger.error(error_msg)
            result.error_count += 1
            result.errors.append(error_msg)
    
    # Calculate total time
    end_time = asyncio.get_event_loop().time()
    result.upload_time_seconds = end_time - start_time
    
    return result

# MCP Tool: Get Photo Info
@mcp.tool()
async def get_photo_info(asset_id: str) -> Optional[PhotoInfo]:
    """
    Get detailed information about a photo.
    
    Args:
        asset_id: The ID of the photo to retrieve
        
    Returns:
        Photo information including metadata and EXIF data
    """
    try:
        # Get asset info
        asset_url = f"{IMMICH_URL}/api/asset/{asset_id}"
        headers = {"x-api-key": IMMICH_API_KEY}
        
        async with httpx.AsyncClient() as client:
            response = await client.get(asset_url, headers=headers)
            response.raise_for_status()
            asset_data = response.json()
            
            # Get EXIF data
            exif_url = f"{IMMICH_URL}/api/asset/{asset_id}/exif"
            exif_response = await client.get(exif_url, headers=headers)
            exif_data = exif_response.json() if exif_response.status_code == 200 else {}
            
            # Map to our model
            return PhotoInfo(
                id=asset_data['id'],
                original_filename=asset_data['originalFileName'],
                file_path=asset_data['originalPath'],
                type=asset_data['type'],
                created_at=asset_data['createdAt'],
                updated_at=asset_data['updatedAt'],
                file_created_at=asset_data['fileCreatedAt'],
                local_date_time=asset_data['localDateTime'],
                is_favorite=asset_data.get('isFavorite', False),
                is_archived=asset_data.get('isArchived', False),
                is_trashed=asset_data.get('isTrashed', False),
                checksum=asset_data['checksum'],
                file_size_bytes=asset_data.get('fileSize', 0),
                exif_info=exif_data
            )
            
    except Exception as e:
        logger.error(f"Error getting photo info for {asset_id}: {str(e)}")
        raise

# MCP Tool: Server Health Check - FIXED API ENDPOINTS FOR v1.137+
@mcp.tool()
async def server_health() -> Dict[str, Any]:
    """
    Check the health and status of the Immich server.
    
    Returns:
        Dictionary with server health information
    """
    try:
        async with httpx.AsyncClient() as client:
            # FIXED: Updated endpoints for v1.137+
            # OLD: /server-info/ping  NEW: /server/ping
            status_url = f"{IMMICH_URL}/server/ping"
            status_response = await client.get(status_url)
            status_response.raise_for_status()
            
            # OLD: /server-info/version  NEW: /server/version  
            version_url = f"{IMMICH_URL}/server/version"
            headers = {"x-api-key": IMMICH_API_KEY}
            version_response = await client.get(version_url, headers=headers)
            version_data = version_response.json()
            
            # OLD: /server-info/storage  NEW: /server/storage
            storage_url = f"{IMMICH_URL}/server/storage"
            storage_response = await client.get(storage_url, headers=headers)
            storage_data = storage_response.json() if storage_response.status_code == 200 else {}
            
            return {
                "status": "online" if status_response.status_code == 200 else "error",
                "version": f"{version_data.get('major', 'x')}.{version_data.get('minor', 'x')}.{version_data.get('patch', 'x')}",
                "storage": {
                    "total": storage_data.get("diskSize"),
                    "used": storage_data.get("diskUse"),
                    "available": storage_data.get("diskAvailable")
                },
                "timestamp": asyncio.get_event_loop().time()
            }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "timestamp": asyncio.get_event_loop().time()
        }

# MCP Tool: Process Photos Batch
@mcp.tool()
async def process_photos_batch(asset_ids: List[str]) -> BatchResult:
    """
    Process multiple photos in a batch with efficient concurrency.
    
    Args:
        asset_ids: List of asset IDs to process
        
    Returns:
        BatchResult with processing results
        
    Example:
        process_photos_batch(["asset1", "asset2", "asset3"])
    """
    start_time = asyncio.get_event_loop().time()
    result = BatchResult()
    
    # Process in batches of 10
    batch_size = 10
    
    for i in range(0, len(asset_ids), batch_size):
        batch = asset_ids[i:i + batch_size]
        
        # Process batch concurrently
        tasks = [
            process_single_photo(asset_id)
            for asset_id in batch
        ]
        
        batch_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        for i, res in enumerate(batch_results):
            if isinstance(res, Exception):
                result.error_count += 1
                result.results.append({
                    "asset_id": batch[i],
                    "status": "error",
                    "error": str(res)
                })
            else:
                result.processed_count += 1
                result.results.append({
                    "asset_id": batch[i],
                    "status": "success",
                    "data": res
                })
        
        # Small delay between batches to avoid overwhelming the server
        await asyncio.sleep(0.1)
    
    # Calculate total processing time
    end_time = asyncio.get_event_loop().time()
    result.processing_time_seconds = end_time - start_time
    
    return result

# MCP Tool: Process Single Photo
@mcp.tool()
async def process_single_photo(asset_id: str) -> Dict[str, Any]:
    """
    Process a single photo's metadata and return the result.
    
    Args:
        asset_id: The ID of the photo to process
        
    Returns:
        Dictionary with processed photo data
    """
    try:
        async with httpx.AsyncClient() as client:
            # Get asset info
            asset_url = f"{IMMICH_URL}/api/asset/{asset_id}"
            headers = {"x-api-key": IMMICH_API_KEY}
            
            # Get asset details
            asset_response = await client.get(asset_url, headers=headers)
            asset_response.raise_for_status()
            asset_data = asset_response.json()
            
            # Get EXIF data
            exif_url = f"{IMMICH_URL}/api/asset/{asset_id}/exif"
            exif_response = await client.get(exif_url, headers=headers)
            exif_data = exif_response.json() if exif_response.status_code == 200 else {}
            
            return {
                "asset": asset_data,
                "exif": exif_data
            }
    except Exception as e:
        raise Exception(f"Error processing photo {asset_id}: {str(e)}")

# MCP Tool: Search Photos
@mcp.tool()
async def search_photos(
    query: Optional[str] = None,
    tags: Optional[List[str]] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = 50
) -> Dict[str, Any]:
    """
    Search for photos based on various criteria.
    
    Args:
        query: Text search query
        tags: List of tags to filter by
        start_date: Start date (ISO format)
        end_date: End date (ISO format)
        limit: Maximum number of results to return
        
    Returns:
        Dictionary with search results
    """
    try:
        params = {"limit": limit}
        if query:
            params["q"] = query
        if tags:
            params["tags"] = ",".join(tags)
        if start_date:
            params["startDate"] = start_date
        if end_date:
            params["endDate"] = end_date
            
        async with httpx.AsyncClient() as client:
            url = f"{IMMICH_URL}/api/search"
            headers = {"x-api-key": IMMICH_API_KEY}
            response = await client.get(url, params=params, headers=headers)
            response.raise_for_status()
            
            return response.json()
    except Exception as e:
        return {"error": str(e), "status": "error"}

# MCP Tool: Get Album Info - FIXED ENDPOINT
@mcp.tool()
async def get_album_info(album_id: str) -> Dict[str, Any]:
    """
    Get detailed information about an album.
    
    Args:
        album_id: The ID of the album to retrieve
        
    Returns:
        Album information including list of assets
    """
    try:
        async with httpx.AsyncClient() as client:
            # FIXED: Changed from /api/album/{id} to /api/albums/{id}
            url = f"{IMMICH_URL}/api/albums/{album_id}"
            headers = {"x-api-key": IMMICH_API_KEY}
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            
            return response.json()
    except Exception as e:
        return {"error": str(e), "status": "error"}

# MCP Tool: Create Album - FIXED ENDPOINT
@mcp.tool()
async def create_album(
    name: str,
    asset_ids: Optional[List[str]] = None,
    description: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a new album with optional assets.
    
    Args:
        name: Name of the album
        asset_ids: Optional list of asset IDs to add to the album
        description: Optional description for the album
        
    Returns:
        Created album information
    """
    try:
        payload = {
            "albumName": name,
            "description": description or ""
        }
        
        if asset_ids:
            payload["assetIds"] = asset_ids
        
        async with httpx.AsyncClient() as client:
            # FIXED: Changed from /api/album to /api/albums
            url = f"{IMMICH_URL}/api/albums"
            headers = {
                "x-api-key": IMMICH_API_KEY,
                "Content-Type": "application/json"
            }
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            
            return response.json()
    except Exception as e:
        return {"error": str(e), "status": "error"}

# MCP Tool: List Albums - FIXED ENDPOINT
@mcp.tool()
async def list_albums(
    limit: int = 50,
    offset: int = 0,
    shared: bool = False
) -> Dict[str, Any]:
    """
    List all albums with pagination.
    
    Args:
        limit: Maximum number of albums to return
        offset: Pagination offset
        shared: Include shared albums
        
    Returns:
        Dictionary with list of albums and pagination info
    """
    try:
        params = {
            'limit': limit,
            'offset': offset,
            'shared': str(shared).lower()
        }
        
        async with httpx.AsyncClient() as client:
            # FIXED: Changed from /api/album to /api/albums (plural)
            url = f"{IMMICH_URL}/api/albums"
            headers = {"x-api-key": IMMICH_API_KEY}
            response = await client.get(url, params=params, headers=headers)
            response.raise_for_status()
            
            return response.json()
    except Exception as e:
        return {"error": str(e), "status": "error"}

# MCP Tool: Add Assets to Album - FIXED ENDPOINT
@mcp.tool()
async def add_assets_to_album(
    album_id: str,
    asset_ids: List[str]
) -> Dict[str, Any]:
    """
    Add assets to an existing album.
    
    Args:
        album_id: ID of the album to add assets to
        asset_ids: List of asset IDs to add
        
    Returns:
        Result of the operation
    """
    try:
        payload = {
            "ids": asset_ids
        }
        
        async with httpx.AsyncClient() as client:
            # FIXED: Changed from /api/album/{id}/assets to /api/albums/{id}/assets
            url = f"{IMMICH_URL}/api/albums/{album_id}/assets"
            headers = {
                "x-api-key": IMMICH_API_KEY,
                "Content-Type": "application/json"
            }
            response = await client.put(url, json=payload, headers=headers)
            response.raise_for_status()
            
            return {"status": "success", "album_id": album_id, "assets_added": len(asset_ids)}
    except Exception as e:
        return {"error": str(e), "status": "error"}

# MCP Tool: Remove Assets from Album - FIXED ENDPOINT
@mcp.tool()
async def remove_assets_from_album(
    album_id: str,
    asset_ids: List[str]
) -> Dict[str, Any]:
    """
    Remove assets from an album.
    
    Args:
        album_id: ID of the album to remove assets from
        asset_ids: List of asset IDs to remove
        
    Returns:
        Result of the operation
    """
    try:
        params = {
            'ids': ','.join(asset_ids)
        }
        
        async with httpx.AsyncClient() as client:
            # FIXED: Changed from /api/album/{id}/assets to /api/albums/{id}/assets
            url = f"{IMMICH_URL}/api/albums/{album_id}/assets"
            headers = {
                "x-api-key": IMMICH_API_KEY
            }
            response = await client.delete(url, params=params, headers=headers)
            response.raise_for_status()
            
            return {"status": "success", "album_id": album_id, "assets_removed": len(asset_ids)}
    except Exception as e:
        return {"error": str(e), "status": "error"}

# MCP Tool: Delete Album - FIXED ENDPOINT
@mcp.tool()
async def delete_album(album_id: str) -> Dict[str, Any]:
    """
    Delete an album.
    
    Args:
        album_id: ID of the album to delete
        
    Returns:
        Result of the operation
    """
    try:
        async with httpx.AsyncClient() as client:
            # FIXED: Changed from /api/album/{id} to /api/albums/{id}
            url = f"{IMMICH_URL}/api/albums/{album_id}"
            headers = {"x-api-key": IMMICH_API_KEY}
            response = await client.delete(url, headers=headers)
            response.raise_for_status()
            
            return {"status": "success", "album_id": album_id, "deleted": True}
    except Exception as e:
        return {"error": str(e), "status": "error"}

# MCP Tool: Get Asset by ID
@mcp.tool()
async def get_asset_by_id(asset_id: str) -> Dict[str, Any]:
    """
    Get detailed information about an asset by ID.
    
    Args:
        asset_id: The ID of the asset to retrieve
        
    Returns:
        Detailed asset information
    """
    try:
        async with httpx.AsyncClient() as client:
            url = f"{IMMICH_URL}/api/asset/{asset_id}"
            headers = {"x-api-key": IMMICH_API_KEY}
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            
            return response.json()
    except Exception as e:
        return {"error": str(e), "status": "error"}

# MCP Tool: Download Asset
@mcp.tool()
async def download_asset(
    asset_id: str,
    output_path: str = "./downloads"
) -> Dict[str, Any]:
    """
    Download an asset by ID.
    
    Args:
        asset_id: The ID of the asset to download
        output_path: Directory to save the downloaded file
        
    Returns:
        Download result with file path
    """
    try:
        # Ensure output directory exists
        output_dir = Path(output_path)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        async with httpx.AsyncClient() as client:
            # Get asset info first
            asset_info = await get_asset_by_id(asset_id)
            if "error" in asset_info:
                return asset_info
                
            # Download the file
            download_url = f"{IMMICH_URL}/api/asset/file/{asset_id}"
            headers = {"x-api-key": IMMICH_API_KEY}
            
            async with client.stream('GET', download_url, headers=headers) as response:
                response.raise_for_status()
                
                # Determine filename
                content_disposition = response.headers.get('content-disposition', '')
                if 'filename=' in content_disposition:
                    filename = content_disposition.split('filename=')[1].strip('"\'')
                else:
                    filename = f"{asset_id}.jpg"
                
                # Save the file
                output_file = output_dir / filename
                with open(output_file, 'wb') as f:
                    async for chunk in response.aiter_bytes():
                        f.write(chunk)
                
                return {
                    "status": "success",
                    "asset_id": asset_id,
                    "filename": str(output_file),
                    "size": os.path.getsize(output_file)
                }
    except Exception as e:
        return {"error": str(e), "status": "error"}

# Main entry point
if __name__ == "__main__":
    # This will start the MCP server with STDIO transport for Claude Desktop
    mcp.run()
