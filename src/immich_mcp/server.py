"""
ImmichMCP - FastMCP 3.1 Server for Immich Photo Management

Efficient Immich photo library management via MCP. 25+ tools: photo ops, albums, people/faces, library and admin.
"""

# CRITICAL: Set stdio to binary mode on Windows for Antigravity IDE compatibility
# Antigravity IDE is strict about JSON-RPC protocol and interprets trailing \r as "invalid trailing data"
# This must happen BEFORE any imports that might write to stdout
import os
import sys

if os.name == "nt":  # Windows only
    try:
        # Force binary mode for stdin/stdout to prevent CRLF conversion
        import msvcrt

        msvcrt.setmode(sys.stdin.fileno(), os.O_BINARY)
        msvcrt.setmode(sys.stdout.fileno(), os.O_BINARY)
    except (OSError, AttributeError):
        # Fallback: just ensure no CRLF conversion
        pass


# DevNullStdout class for stdio mode to prevent any console output during initialization
class DevNullStdout:
    """Suppress all stdout writes during stdio mode to prevent JSON-RPC protocol corruption."""

    def __init__(self, original_stdout):
        self.original_stdout = original_stdout
        self.buffer = []

    def write(self, text):
        # Buffer output instead of writing to stdout
        self.buffer.append(text)

    def flush(self):
        # Do nothing - prevent any stdout writes
        pass

    def get_buffered_output(self):
        """Get all buffered output for debugging if needed."""
        return "".join(self.buffer)

    def restore(self):
        """Restore original stdout."""
        sys.stdout = self.original_stdout


# CRITICAL: Detect stdio mode BEFORE importing logger
# This must be done before ANY logging imports
_is_stdio_mode = not sys.stdout.isatty()

# NUCLEAR OPTION: Completely disable logger during stdio mode
# Import logger first, then replace it with a no-op to prevent any stdout writes
import logging

if _is_stdio_mode:
    # Replace stdout with our devnull version to catch any accidental writes
    original_stdout = sys.stdout
    sys.stdout = DevNullStdout(original_stdout)

    # The DevNullStdout override above will catch accidental direct prints to stdout.
    # For standard logging, we ensure it goes to stderr to prevent breaking the JSON-RPC
    # protocol that uses stdout.
    pass

import asyncio
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_path)

# Add the src directory to Python path so imports work when run directly
src_dir = Path(__file__).parent.parent
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))
from datetime import datetime  # noqa: E402
from pathlib import Path  # noqa: E402
from typing import Any  # noqa: E402

from dotenv import load_dotenv  # noqa: E402
from fastapi import FastAPI  # noqa: E402
from fastmcp import FastMCP  # noqa: E402
from pydantic import BaseModel, Field  # noqa: E402

from immich_mcp.api.v1.routes import router as v1_router  # noqa: E402
from immich_mcp.config import ImmichConfig, get_config  # noqa: E402
from immich_mcp.immich_api import ImmichAPIClient, ImmichAPIError  # noqa: E402

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    stream=sys.stderr,
)
logger = logging.getLogger("immich_mcp")

# Global config instance for user management
config: ImmichConfig | None = None


class ImmichMCP(FastMCP):
    """ImmichMCP server implementation (FastMCP 3.1)."""

    def __init__(self, **kwargs):
        """Initialize the ImmichMCP server."""
        kwargs.setdefault("name", "ImmichMCP")
        kwargs.setdefault("version", "1.0.0")
        super().__init__(
            name=kwargs["name"],
            version=kwargs["version"],
            instructions="""You are ImmichMCP, a comprehensive FastMCP 3.1 server for Immich photo management.

CORE CAPABILITIES:
- Photo Management: Browse, search, upload, and organize your Immich photo library
- Album Operations: Create, manage, and organize photo albums and collections
- People & Faces: Face recognition, person identification, and facial clustering
- Library Administration: Multi-user support, library management, and user permissions
- Asset Organization: Tagging, metadata management, and advanced search capabilities

CONVERSATIONAL FEATURES:
- Tools return natural language responses alongside structured data
- Sampling allows autonomous orchestration of complex photo operations
- Agentic capabilities for intelligent content discovery and management

RESPONSE FORMAT:
- All tools return dictionaries with 'success' boolean and 'message' for conversational responses
- Error responses include 'error' field with descriptive message
- Success responses include relevant data fields and natural language summaries

PORTMANTEAU DESIGN:
Tools are consolidated into logical groups. Each portmanteau tool handles multiple related operations through an 'operation' parameter.
""",
        )
        self.immich_client: ImmichAPIClient | None = None

    async def startup_event(self):
        """Initialize resources when the server starts."""
        global config
        try:
            config = get_config()
            self.immich_client = ImmichAPIClient(config=config)
            logger.info("Immich client initialized for user: %s", config.active_user)
        except Exception as e:
            logger.error("Failed to initialize Immich client: %s", e)
            raise

    async def shutdown_event(self):
        """Clean up resources when the server shuts down."""
        if self.immich_client:
            await self.immich_client.close()
            logger.info("Immich client closed")


# Initialize FastMCP server
mcp = ImmichMCP()

# Register agentic workflow tools
from .agentic import register_agentic_tools

register_agentic_tools()

# CRITICAL: After server initialization, restore stdout for stdio mode
if _is_stdio_mode:
    if hasattr(sys.stdout, "restore"):
        sys.stdout.restore()

# FastMCP 3.1: separate FastAPI app for custom routes; mount MCP HTTP app at /mcp
from contextlib import asynccontextmanager


@asynccontextmanager
async def _web_lifespan(_app: FastAPI):
    await mcp.startup_event()
    try:
        yield
    finally:
        await mcp.shutdown_event()


_web_app = FastAPI(
    title="ImmichMCP",
    description="FastMCP 3.1 server for Immich photo management",
    version="1.0.0",
    lifespan=_web_lifespan,
)
_web_app.include_router(v1_router, prefix="/api/v1")
_web_app.mount("/mcp", mcp.http_app())

# Expose for uvicorn (e.g. web_sota/start.ps1)
app = _web_app


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
    duration: str | None = Field(default=None, description="Duration for videos")
    is_favorite: bool = Field(description="Favorite status")
    is_archived: bool = Field(description="Archive status")
    is_trashed: bool = Field(description="Trash status")
    checksum: str = Field(description="File checksum")
    smart_search_score: float | None = Field(
        default=None, description="CLIP search relevance score"
    )
    latitude: float | None = Field(default=None, description="GPS Latitude")
    longitude: float | None = Field(default=None, description="GPS Longitude")


class UploadResult(BaseModel):
    """Photo upload operation result"""

    uploaded_count: int = Field(description="Number of photos uploaded")
    duplicate_count: int = Field(description="Number of duplicates skipped")
    error_count: int = Field(description="Number of upload errors")
    uploaded_assets: list[str] = Field(description="List of uploaded asset IDs")
    errors: list[str] = Field(description="List of error messages")
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
    exif_info: dict[str, Any] = Field(default_factory=dict)
    smart_info: dict[str, Any] = Field(default_factory=dict)
    people: list[str] = Field(default_factory=list)
    albums: list[str] = Field(default_factory=list)
    ocr_text: str | None = Field(default=None, description="Extracted OCR text (v2.2.0+)")
    ocr_bounding_boxes: list[dict[str, Any]] = Field(
        default_factory=list, description="OCR bounding boxes (v2.3.0+)"
    )
    ocr_language: str | None = Field(default=None, description="OCR language used (v2.3.0+)")
    ocr_confidence: float | None = Field(default=None, description="OCR confidence score (v2.3.0+)")


class OrganizeResult(BaseModel):
    """Photo organization operation result"""

    albums_created: int = Field(description="Number of albums created")
    photos_organized: int = Field(description="Number of photos organized")
    organization_type: str = Field(description="Organization method used")
    created_albums: list[str] = Field(description="Names of created albums")
    errors: list[str] = Field(description="Any errors during organization")


class DeletionResult(BaseModel):
    """Photo deletion operation result"""

    deleted_count: int = Field(description="Number of photos deleted")
    trashed_count: int = Field(description="Number of photos moved to trash")
    error_count: int = Field(description="Number of deletion errors")
    deleted_asset_ids: list[str] = Field(description="List of deleted asset IDs")
    errors: list[str] = Field(description="List of error messages")


class AlbumResult(BaseModel):
    """Album creation result"""

    id: str = Field(description="Album ID")
    album_name: str = Field(description="Album name")
    description: str | None = Field(default=None, description="Album description")
    created_at: str = Field(description="Creation timestamp")
    asset_count: int = Field(description="Number of photos in album")
    owner_id: str = Field(description="Album owner ID")


class AlbumInfo(BaseModel):
    """Album information"""

    id: str
    album_name: str
    description: str | None = None
    created_at: str
    updated_at: str
    asset_count: int
    owner_id: str
    shared: bool
    album_thumbnail_asset_id: str | None = None
    start_date: str | None = None
    end_date: str | None = None


class AlbumUpdateResult(BaseModel):
    """Album update operation result"""

    album_id: str
    added_count: int = Field(description="Number of photos added")
    duplicate_count: int = Field(description="Number of duplicates skipped")
    new_asset_count: int = Field(description="Total photos in album after update")
    errors: list[str] = Field(default_factory=list)


class ShareResult(BaseModel):
    """Album sharing result"""

    id: str = Field(description="Share link ID")
    key: str = Field(description="Share key")
    public_url: str = Field(description="Public access URL")
    album_id: str = Field(description="Shared album ID")
    expires_at: str | None = Field(default=None, description="Expiration date")
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
    people_found: list[dict[str, Any]] = Field(description="List of detected people clusters")


class PersonInfo(BaseModel):
    """Person/face cluster information"""

    id: str = Field(description="Person ID")
    name: str | None = Field(default=None, description="Assigned name")
    face_count: int = Field(description="Number of faces in cluster")
    thumbnail_asset_id: str | None = Field(default=None, description="Representative photo ID")
    is_hidden: bool = Field(description="Hidden status")
    birth_date: str | None = Field(default=None, description="Birth date if set")
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
    storage_usage_by_user: list[dict[str, Any]] = Field(description="Per-user storage breakdown")


class OCRResult(BaseModel):
    """OCR extraction result with bounding boxes (v2.3.0+)"""

    asset_id: str = Field(description="Asset ID")
    text: str = Field(description="Extracted text content")
    language: str = Field(description="OCR language model used")
    confidence: float = Field(description="Overall confidence score (0.0-1.0)")
    bounding_boxes: list[dict[str, Any]] = Field(description="Text bounding box coordinates")
    words: list[dict[str, Any]] = Field(description="Individual word data with positions")
    regions: list[dict[str, Any]] = Field(description="Text regions (paragraphs/blocks)")


class BackupResult(BaseModel):
    """Backup operation result"""

    backup_path: str = Field(description="Backup destination path")
    exported_photos: int = Field(description="Number of photos exported")
    exported_videos: int = Field(description="Number of videos exported")
    total_size_mb: float = Field(description="Total backup size in MB")
    backup_time_seconds: float = Field(description="Backup processing time")
    metadata_included: bool = Field(description="Whether metadata was preserved")
    album_structure_preserved: bool = Field(description="Whether album structure was maintained")
    errors: list[str] = Field(default_factory=list)


class HealthStatus(BaseModel):
    """Server health status"""

    server_version: str = Field(description="Immich server version")
    server_features: list[str] = Field(description="Available server features")
    is_v2_plus: bool = Field(default=False, description="Whether server is v2.0.0+")
    has_ocr: bool = Field(default=False, description="Whether server supports OCR search (v2.2.0+)")
    has_multilingual_ocr: bool = Field(
        default=False, description="Whether server supports multilingual OCR (v2.3.0+)"
    )
    ocr_languages: list[str] = Field(default_factory=list, description="Supported OCR languages")
    database_connected: bool = Field(description="Database connection status")
    redis_connected: bool = Field(description="Redis connection status")
    storage_accessible: bool = Field(description="Storage accessibility")
    ml_services_available: bool = Field(description="Machine learning services status")
    response_time_ms: int = Field(description="API response time in milliseconds")
    uptime_seconds: int = Field(description="Server uptime in seconds")
    error_messages: list[str] = Field(default_factory=list)


class OcrInfo(BaseModel):
    """OCR information for an asset"""

    text: str = Field(description="Extracted OCR text")
    bounding_boxes: list[dict[str, Any]] = Field(
        default_factory=list, description="Text bounding boxes with coordinates"
    )
    language: str = Field(description="Detected or configured OCR language")
    confidence: float = Field(description="OCR confidence score (0.0-1.0)")
    asset_id: str = Field(description="Asset ID")
    has_bounding_boxes: bool = Field(description="Whether bounding box data is available (v2.3.0+)")


from .immich_api import get_api_client


# ====== PHASE 1: CORE PHOTO OPERATIONS (5 tools) ======


@mcp.tool()
async def upload_photos(
    file_paths: list[str], album_name: str | None = None, *, auto_organize: bool = False
) -> UploadResult:
    r"""Upload photos to Immich with batch processing and metadata detection.

    Austrian efficiency tool for photo management workflow. Supports batch upload
    with automatic organization and duplicate detection. Processes multiple photos
    concurrently for optimal performance. Automatically extracts EXIF metadata and
    handles duplicate detection based on file checksums.

    Prerequisites:
        - IMMICH_URL and IMMICH_API_KEY environment variables must be set
        - Immich server must be accessible and running
        - All file paths must exist and be readable
        - Files must be valid image or video formats supported by Immich

    Parameters:
        file_paths (List[str], REQUIRED):
            List of absolute or relative file paths to upload.
            Format: ["/path/to/photo1.jpg", "/path/to/photo2.jpg"]
            Supports: JPG, PNG, HEIC, RAW, MP4, MOV, and other Immich-supported formats.
            Example: ["C:\\Users\\sandr\\Pictures\\vacation\\IMG_001.jpg"]
            Windows: Use double backslashes or raw strings: r"C:\Users\sandr\Pictures\photo.jpg"
            Linux/Mac: Use forward slashes: "/home/user/Pictures/photo.jpg"
            Note: Glob patterns not supported - provide explicit file paths.

        album_name (str, OPTIONAL):
            Name of album to add uploaded photos to.
            If album doesn't exist, it will be created automatically.
            If None, photos are uploaded without album assignment.
            Default: None
            Example: "Vienna Summer 2025", "Family Photos", "Vacation 2024"

        auto_organize (bool, OPTIONAL):
            Whether to automatically organize photos by date after upload.
            When True, photos are organized into date-based folders.
            Default: False
            Note: Organization happens server-side after upload completes.

    Returns:
        UploadResult containing:
            - uploaded_count (int): Number of photos uploaded successfully
            - duplicate_count (int): Number of duplicate photos skipped (checksum-based)
            - error_count (int): Number of upload errors encountered
            - uploaded_assets (List[str]): IDs of successfully uploaded assets
            - errors (List[str]): Error messages for failed uploads
            - total_size_mb (float): Total size of uploaded files in MB
            - upload_time_seconds (float): Total upload time in seconds

    Usage:
        Use this tool to upload photos from local storage to your Immich server.
        Ideal for bulk imports, backup workflows, or organizing photo collections.
        The tool handles duplicate detection automatically, so safe to re-run on
        the same files.

        Common scenarios:
        - Bulk import from camera SD card or external drive
        - Backup photos from local storage to Immich
        - Organize vacation photos into albums
        - Import photos from multiple sources with automatic deduplication

        Best practices:
        - Upload in batches of 50-100 photos for optimal performance
        - Use album_name to organize photos by event or date
        - Check error_count and errors list after upload to identify issues
        - Use uploaded_assets to add photos to additional albums later

    Examples:
        # Basic upload - single photo
        result = await upload_photos(
            file_paths=["C:\\Users\\sandr\\Pictures\\photo.jpg"]
        )
        # Returns: UploadResult with uploaded_count=1, uploaded_assets=["abc123"]

        # Batch upload with album
        result = await upload_photos(
            file_paths=[
                "C:\\Users\\sandr\\Pictures\\vacation\\IMG_001.jpg",
                "C:\\Users\\sandr\\Pictures\\vacation\\IMG_002.jpg",
                "C:\\Users\\sandr\\Pictures\\vacation\\IMG_003.jpg"
            ],
            album_name="Summer Vacation 2024"
        )
        # Returns: UploadResult with uploaded_count=3, album created if needed

        # Upload with auto-organization
        result = await upload_photos(
            file_paths=["/home/user/photos/photo1.jpg", "/home/user/photos/photo2.jpg"],
            auto_organize=True
        )
        # Returns: UploadResult with photos organized by date on server

        # Error handling
        result = await upload_photos(
            file_paths=["/nonexistent/photo.jpg", "/valid/photo.jpg"]
        )
        if result.error_count > 0:
            # Log errors: logger.error(f"Upload errors: {result.errors}")
        # Returns: UploadResult with error_count=1, errors=["File not found: /nonexistent/photo.jpg"]

    Common Issues:
        1. "File not found" error
           → Verify file paths are correct and files exist
           → Use absolute paths instead of relative paths
           → Check file permissions (must be readable)
           → Windows: Ensure paths use double backslashes or raw strings

        2. "IMMICH_API_KEY not set" error
           → Set IMMICH_API_KEY environment variable
           → Verify .env file exists in project root
           → Check API key is valid in Immich settings

        3. "Connection refused" or timeout errors
           → Verify IMMICH_URL is correct (default: http://localhost:2283)
           → Check Immich server is running and accessible
           → Verify network connectivity to Immich server
           → Check firewall settings if connecting to remote server

        4. Duplicate photos still uploading
           → Duplicate detection is based on file checksum
           → Photos with same content but different filenames are detected
           → Photos with same filename but different content are uploaded separately

    Platform Notes:
        Windows:
            - Use double backslashes: "C:\\Users\\sandr\\Pictures\\photo.jpg"
            - Or raw strings: r"C:\Users\sandr\Pictures\photo.jpg"
            - UNC paths supported: "\\\\server\\share\\photo.jpg"

        Linux:
            - Use forward slashes: "/home/user/Pictures/photo.jpg"
            - Tilde expansion: "~/Pictures/photo.jpg" (expanded by shell, not Python)

        macOS:
            - Use forward slashes: "/Users/sandr/Pictures/photo.jpg"
            - Spaces in paths are handled automatically

    See Also:
        - get_photo_info: Get detailed information about uploaded photos
        - create_album: Create albums before uploading to organize photos
        - search_photos: Find photos after upload using semantic search
    """
    try:
        start_time = asyncio.get_event_loop().time()
        client = await get_api_client()

        # Perform batch upload
        result = await client.upload_photos_batch(
            file_paths=file_paths, album_name=album_name, auto_organize=auto_organize
        )

        end_time = asyncio.get_event_loop().time()
        upload_time = end_time - start_time

        return UploadResult(
            uploaded_count=result.get("uploaded_count", 0),
            duplicate_count=result.get("duplicate_count", 0),
            error_count=result.get("error_count", 0),
            uploaded_assets=result.get("uploaded_assets", []),
            errors=result.get("errors", []),
            total_size_mb=result.get("total_size_mb", 0.0),
            upload_time_seconds=upload_time,
        )

    except ImmichAPIError as e:
        logger.error("Immich API error in upload_photos: %s", e)
        return UploadResult(
            uploaded_count=0,
            duplicate_count=0,
            error_count=len(file_paths),
            uploaded_assets=[],
            errors=[str(e)],
            total_size_mb=0.0,
            upload_time_seconds=0.0,
        )


@mcp.tool()
async def search_photos(
    query: str,
    search_type: str = Field("smart", description="Search type: smart, ocr, metadata, or filename"),
    limit: int = Field(50, description="Maximum results to return"),
    ocr_language: str = Field(
        default=None,
        description="OCR language model (v2.3.0+): english, english_only, chinese_simplified, chinese_traditional, japanese, greek, korean, russian, belarusian, ukrainian, thai, latin_script_languages",
    ),
) -> list[PhotoSearchResult]:
    r"""Search photos using CLIP smart search, OCR text search, or metadata queries.

    Powerful search tool that uses Immich's vector database and OCR capabilities to find
    photos matching natural language descriptions, extracted text, or metadata. Supports
    multiple search methods including CLIP-based semantic search and OCR text extraction.
    Austrian efficiency: Natural language search through 2000+ photo library.

        Prerequisites:
        - IMMICH_URL and IMMICH_API_KEY environment variables must be set
        - Immich server must be accessible
        - For OCR search: Requires Immich v2.2.0+ with OCR features enabled
        - For multilingual OCR: Requires Immich v2.3.0+ with enhanced OCR models
        - For smart search: Requires Immich v1.0+ with CLIP/ML features enabled

    Parameters:
        query (str, REQUIRED):
            Search terms for finding photos.
            Format: Natural language for smart/OCR search, keywords for metadata/filename.
            Examples:
                - Smart: "Benny playing in park", "sunset over mountains"
                - OCR: "invoice number 12345", "receipt total $50"
                - Metadata: "Canon EOS", "iPhone 14", "f/2.8"
                - Filename: "IMG_001", "vacation_2024", "photo"
            Note: Smart and OCR use natural language; metadata/filename use keywords.

        search_type (str, OPTIONAL):
            Type of search to perform.
            Valid values:
                - "smart": CLIP-based semantic search (v1.0+)
                - "ocr": Text extraction search (v2.2.0+ with multilingual support in v2.3.0+)
                - "metadata": EXIF/metadata search (v1.0+)
                - "filename": Filename-based search (v1.0+)
            Default: "smart"
            Note: OCR requires Immich v2.2.0+ with OCR enabled. v2.3.0+ adds multilingual support.

        limit (int, OPTIONAL):
            Maximum number of results to return.
            Range: 1-200
            Default: 50
            Note: Higher limits may take longer. Recommended: 20-50 for most searches.

    Returns:
        List[PhotoSearchResult] containing matching photos with:
            - id (str): Unique asset ID
            - original_filename (str): Original filename
            - file_path (str): Path to file on server
            - device_asset_id (str): Device asset identifier
            - owner_id (str): Owner user ID
            - device_id (str): Device identifier
            - type (str): Asset type ("IMAGE" or "VIDEO")
            - created_at (str): ISO timestamp when created
            - updated_at (str): ISO timestamp when updated
            - file_created_at (str): File creation date
            - local_date_time (str): Local date/time from EXIF
            - duration (Optional[str]): Video duration (videos only)
            - is_favorite (bool): Whether marked as favorite
            - is_archived (bool): Whether archived
            - is_trashed (bool): Whether in trash
            - checksum (str): File checksum
            - smart_search_score (Optional[float]): Relevance score (0.0-1.0)

        Returns empty list on error.

    Usage:
        Use this tool to find photos in your Immich library using natural language queries,
        extracted text, metadata, or filenames. Essential for discovering photos, organizing
        collections, or finding specific content. Smart search is particularly powerful for
        finding photos by content description rather than just metadata.

        Common scenarios:
        - Find photos by content description ("dog playing in snow")
        - Search for photos containing specific text (OCR search for documents/receipts)
        - Find photos by camera or settings (metadata search)
        - Locate photos by filename pattern
        - Combine with other tools to organize or process found photos

        Best practices:
        - Use descriptive queries for smart search ("sunset over mountains" vs "sunset")
        - Use OCR search for finding documents, receipts, or photos with text
        - Use metadata search for finding photos by camera, settings, or tags
        - Start with lower limits (20-50) and increase if needed
        - Check smart_search_score for relevance (higher = more relevant)

    Examples:
        # Smart semantic search
        results = await search_photos("Benny playing in park", search_type="smart", limit=20)
        for photo in results:
            # Access photo data: photo.original_filename, photo.smart_search_score

        # OCR text search (v2.2.0+)
        results = await search_photos("invoice number 12345", search_type="ocr", limit=10)
        # Returns: Photos containing the text "invoice number 12345"

        # Metadata search
        results = await search_photos("Canon EOS", search_type="metadata", limit=50)
        # Returns: Photos taken with Canon EOS cameras

        # Filename search
        results = await search_photos("vacation_2024", search_type="filename", limit=100)
        # Returns: Photos with "vacation_2024" in filename

        # Error handling
        results = await search_photos("", search_type="smart", limit=50)
        if not results:
            # No results found or search error occurred

    Common Issues:
        1. No results found
           → Try broader search terms
           → Check search_type is appropriate for your query
           → Verify photos exist in Immich library
           → For OCR: Ensure photos contain extractable text
           → For smart: Try different descriptive phrases

        2. "OCR search not available" error
           → Requires Immich v2.2.0+ with OCR features enabled
           → Check Immich server version and OCR configuration
           → Use "smart" or "metadata" search as alternative

        3. "Smart search not available" error
           → Requires Immich v1.0+ with CLIP/ML features enabled
           → Check Immich server version and ML configuration
           → Use "metadata" or "filename" search as alternative

        4. Results not relevant (smart search)
           → Try more descriptive queries
           → Check smart_search_score (higher = more relevant)
           → Use min_score filtering if supported
           → Try different phrasing or keywords

    See Also:
        - get_photo_info: Get detailed information about photos from search results
        - organize_photos_by_date: Organize found photos into date-based albums
        - create_album: Create albums for organizing search results
    """
    try:
        client = await get_api_client()

        # Validate limit
        limit = max(1, min(200, limit))

        # Perform search based on type
        results = await client.search_photos(
            query=query, search_type=search_type, limit=limit, ocr_language=ocr_language
        )

        # Convert to response format
        photo_results = []
        for photo in results:
            photo_result = PhotoSearchResult(
                id=photo["id"],
                original_filename=photo.get("originalFileName", "Unknown"),
                file_path=photo.get("originalPath", ""),
                device_asset_id=photo.get("deviceAssetId", ""),
                owner_id=photo.get("ownerId", ""),
                device_id=photo.get("deviceId", ""),
                type=photo.get("type", "IMAGE"),
                created_at=photo.get("createdAt", ""),
                updated_at=photo.get("updatedAt", ""),
                file_created_at=photo.get("fileCreatedAt", ""),
                local_date_time=photo.get("localDateTime", ""),
                duration=photo.get("duration"),
                is_favorite=photo.get("isFavorite", False),
                is_archived=photo.get("isArchived", False),
                is_trashed=photo.get("isTrashed", False),
                checksum=photo.get("checksum", ""),
                smart_search_score=photo.get("score"),
                latitude=photo.get("exifInfo", {}).get("latitude"),
                longitude=photo.get("exifInfo", {}).get("longitude"),
            )
            photo_results.append(photo_result)

        return photo_results

    except ImmichAPIError as e:
        logger.error("Immich API error in search_photos: %s", e)
        return []


@mcp.tool()
async def update_asset_visibility(asset_id: str, visibility: str) -> dict:
    """Update visibility status of a photo or video (v2.5.0+ / Early 2026).

    Visibility options: 'hidden', 'archived', 'private', 'public'.
    Required for advanced asset categorization and privacy management.

    Parameters:
        asset_id (str, REQUIRED): Unique identifier of the asset.
        visibility (str, REQUIRED): Target visibility state ("hidden", "archived", "private", "public").

    Returns:
        Dict with success status and descriptive message.
    """
    try:
        client = await get_api_client()
        result = await client.update_asset_visibility(asset_id, visibility)
        return {
            "success": True,
            "message": f"Asset {asset_id} visibility set to {visibility}",
            "data": result,
        }
    except Exception as e:
        logger.error(f"Error updating visibility for {asset_id}: {e}")
        return {"success": False, "error": str(e)}


@mcp.tool()
async def edit_photo(
    asset_id: str,
    operation: str,
    angle: int | None = None,
    direction: str | None = None,
    x: int | None = None,
    y: int | None = None,
    width: int | None = None,
    height: int | None = None,
) -> dict:
    """Perform basic image editing: crop, rotate, or mirror (Early 2026).

    Supports non-destructive edits using Immich's native image processor.

    Operations:
        - rotate: params={angle: 90 | 180 | 270}
        - mirror: params={direction: 'horizontal' | 'vertical'}
        - crop: params={x: int, y: int, width: int, height: int}

    Parameters:
        asset_id (str, REQUIRED): Unique identifier of the asset.
        operation (str, REQUIRED): Edit operation name ("rotate", "mirror", "crop").
        angle (int, OPTIONAL): Rotation angle (90, 180, 270).
        direction (str, OPTIONAL): Mirror direction ('horizontal', 'vertical').
        x, y, width, height (int, OPTIONAL): Crop rectangle coordinates and dimensions.

    Returns:
        Dict with success status and edit details.
    """
    try:
        client = await get_api_client()
        # Filter out None values to send only relevant parameters
        params = {
            k: v
            for k, v in {
                "angle": angle,
                "direction": direction,
                "x": x,
                "y": y,
                "width": width,
                "height": height,
            }.items()
            if v is not None
        }
        result = await client.edit_asset(asset_id, operation, **params)
        return {
            "success": True,
            "message": f"Successfully performed {operation} on photo {asset_id}",
            "data": result,
        }
    except Exception as e:
        logger.error(f"Error editing photo {asset_id}: {e}")
        return {"success": False, "error": str(e)}


@mcp.tool()
async def switch_immich_user(username: str) -> dict:
    """Switch the active Immich user context for the MCP server.

    Changes the API key used for subsequent requests to the specified user's key.
    Useful for multi-account management or switching between admin/user contexts.

    Parameters:
        username (str, REQUIRED): The username of the account to switch to.
            Must be one of the users configured in IMMICH_USERS.

    Returns:
        Dict indicating success and the new active user.
    """
    try:
        global config, api_client
        if not config:
            config = get_config()

        user = config.switch_user(username)
        # Ensure the global client is updated if it exists
        if api_client:
            api_client.switch_user(user)

        return {
            "success": True,
            "message": f"Switched active Immich user to '{username}'",
            "active_user": username,
        }
    except Exception as e:
        logger.error(f"Failed to switch user to {username}: {e}")
        return {"success": False, "error": str(e)}


async def get_photo_info(asset_id: str) -> PhotoInfo:
    r"""Get complete metadata and EXIF information for a specific photo.

    Retrieves comprehensive information about a specific photo asset from Immich,
    including file metadata, EXIF data, smart info (AI-generated tags/descriptions),
    people tags, and album associations. This is the most complete way to access
    all available information about a photo.

    Prerequisites:
        - IMMICH_URL and IMMICH_API_KEY environment variables must be set
        - Immich server must be accessible
        - asset_id must be a valid asset ID from Immich

    Parameters:
        asset_id (str, REQUIRED):
            Unique identifier of the photo asset in Immich.
            Format: UUID string (e.g., "550e8400-e29b-41d4-a716-446655440000")
            Obtain from: upload_photos response, search_photos results, or album listings.
            Example: "abc123def456", "550e8400-e29b-41d4-a716-446655440000"

    Returns:
        PhotoInfo object containing:
            - id (str): Unique asset ID
            - original_filename (str): Original filename when uploaded
            - file_path (str): Path to file on Immich server
            - type (str): Asset type ("IMAGE" or "VIDEO")
            - created_at (str): ISO timestamp when created in Immich
            - updated_at (str): ISO timestamp when last updated
            - file_created_at (str): File creation date from filesystem
            - local_date_time (str): Local date/time from EXIF metadata
            - is_favorite (bool): Whether marked as favorite
            - is_archived (bool): Whether archived
            - is_trashed (bool): Whether in trash
            - checksum (str): File checksum for duplicate detection
            - file_size_bytes (int): File size in bytes
            - exif_info (Dict): Complete EXIF metadata dictionary
                Common fields: make, model, iso, fNumber, exposureTime, focalLength,
                dateTimeOriginal, gpsLatitude, gpsLongitude, width, height
            - smart_info (Dict): AI-generated tags and descriptions
            - people (List): List of detected people/faces in the photo
            - albums (List): List of albums this photo belongs to

    Usage:
        Use this tool to inspect photo details, access EXIF metadata, verify uploads,
        or check photo status and associations. Essential for debugging upload issues,
        accessing camera metadata, or understanding photo organization.

        Common scenarios:
        - Verify photo was uploaded correctly after upload_photos
        - Access EXIF metadata (camera settings, GPS coordinates, dates)
        - Check photo status (favorite, archived, trashed)
        - View AI-generated tags and descriptions (smart_info)
        - See which albums contain this photo
        - Check detected people/faces in the photo

    Examples:
        # Get basic photo information
        photo = await get_photo_info(asset_id="abc123def456")
        # Access photo data: photo.original_filename, photo.file_size_bytes, photo.is_favorite
        # Access EXIF metadata: photo.exif_info.get('make'), photo.exif_info.get('model'), etc.
        # Check smart info: photo.smart_info.get('tags', []), photo.smart_info.get('objects', [])
        # Check people and albums: photo.people, photo.albums

        # Error handling
        photo = await get_photo_info(asset_id="invalid_id")
        if photo.type == "ERROR" or photo.original_filename.startswith("Error"):
            # Photo not found or error occurred

    Common Issues:
        1. "Asset not found" (returns error in filename field)
           → Verify asset_id is correct
           → Check asset exists in Immich (may have been deleted)
           → Verify API key has access to this asset
           → Use search_photos to find correct asset_id

        2. "Access denied" (returns error in filename field)
           → Verify API key has read permissions
           → Check if asset belongs to another user (if using shared library)
           → Verify IMMICH_API_KEY is correct

        3. Empty EXIF or smart_info
           → Some photos may not have EXIF metadata
           → Smart info requires Immich ML features to be enabled
           → RAW files typically have more EXIF data than processed images

    See Also:
        - upload_photos: Get asset_id from upload results
        - search_photos: Find photos and get their asset_ids
        - list_albums: Find albums containing this photo
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
                file_size_bytes=0,
                ocr_text=None,
                ocr_bounding_boxes=[],
                ocr_language=None,
                ocr_confidence=None,
            )

        # Get OCR data if available (v2.2.0+)
        ocr_data = {}
        try:
            ocr_data = await client.get_asset_ocr(asset_id, include_bounding_boxes=True)
        except Exception:
            # OCR not available or failed, continue without OCR data
            pass

        return PhotoInfo(
            id=asset_id,
            original_filename=photo_data.get("originalFileName", "Unknown"),
            file_path=photo_data.get("originalPath", ""),
            type=photo_data.get("type", "IMAGE"),
            created_at=photo_data.get("createdAt", ""),
            updated_at=photo_data.get("updatedAt", ""),
            file_created_at=photo_data.get("fileCreatedAt", ""),
            local_date_time=photo_data.get("localDateTime", ""),
            is_favorite=photo_data.get("isFavorite", False),
            is_archived=photo_data.get("isArchived", False),
            is_trashed=photo_data.get("isTrashed", False),
            checksum=photo_data.get("checksum", ""),
            file_size_bytes=photo_data.get("fileSizeInByte", 0),
            exif_info=photo_data.get("exifInfo", {}),
            smart_info=photo_data.get("smartInfo", {}),
            people=photo_data.get("people", []),
            albums=photo_data.get("albums", []),
            ocr_text=ocr_data.get("text"),
            ocr_bounding_boxes=ocr_data.get("bounding_boxes", []),
            ocr_language=ocr_data.get("language"),
            ocr_confidence=ocr_data.get("confidence"),
        )

    except ImmichAPIError as e:
        logger.error("Immich API error in get_photo_info: %s", e)
        return PhotoInfo(
            id=asset_id,
            original_filename=f"Error: {e!s}",
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
            file_size_bytes=0,
            ocr_text=None,
            ocr_bounding_boxes=[],
            ocr_language=None,
            ocr_confidence=None,
        )


@mcp.tool()
async def get_ocr_data(
    asset_id: str,
    include_bounding_boxes: bool = Field(
        default=True, description="Include bounding box coordinates"
    ),
) -> OCRResult:
    r"""Get OCR text extraction and bounding box data for a photo (v2.2.0+ with v2.3.0+ enhancements).

    Retrieves detailed OCR information including extracted text, bounding boxes for text location,
    confidence scores, and language detection. Enhanced in v2.3.0+ with multilingual support
    and improved bounding box accuracy.

    Prerequisites:
        - IMMICH_URL and IMMICH_API_KEY environment variables must be set
        - Immich server must be accessible
        - OCR must be enabled and processed for the asset (v2.2.0+)
        - asset_id must be a valid asset ID from Immich

    Parameters:
        asset_id (str, REQUIRED):
            Unique identifier of the photo asset in Immich.
            Format: UUID string (e.g., "550e8400-e29b-41d4-a716-446655440000")
            Obtain from: upload_photos response, search_photos results, or get_photo_info.

        include_bounding_boxes (bool, OPTIONAL):
            Whether to include detailed bounding box coordinates for text regions.
            When True: Returns precise coordinates for text positioning (v2.3.0+).
            When False: Returns basic OCR text without positional data.
            Default: True
            Note: Bounding boxes provide exact text location for highlighting/display.

    Returns:
        OCRResult containing comprehensive OCR data:
            - asset_id (str): Asset ID that was processed
            - text (str): Full extracted text content
            - language (str): Detected or configured language model
            - confidence (float): Overall OCR confidence score (0.0-1.0)
            - bounding_boxes (List[Dict]): Precise text bounding box coordinates
                Format: [{"x": 100, "y": 200, "width": 150, "height": 30, "text": "word"}]
            - words (List[Dict]): Individual word data with positions
            - regions (List[Dict]): Text regions (paragraphs/blocks) with coordinates

    Usage:
        Use this tool to access detailed OCR information for photos, including exact text
        positioning for display or processing. Essential for applications needing precise
        text location data or multi-language OCR processing.

        Common scenarios:
        - Display OCR text with highlighting at exact positions
        - Extract specific text regions from photos
        - Process multilingual documents with accurate language detection
        - Build OCR-powered search with positional context
        - Analyze document layout and text flow

        Best practices:
        - Check confidence scores for OCR accuracy assessment
        - Use bounding boxes for text highlighting in UI applications
        - Process by language when dealing with multilingual content
        - Handle cases where OCR data may not be available

    Examples:
        # Get complete OCR data with bounding boxes
        ocr_data = await get_ocr_data(asset_id="abc123def456", include_bounding_boxes=True)
        # Access extracted text: ocr_data.text
        # Access bounding boxes: ocr_data.bounding_boxes
        # Check confidence: ocr_data.confidence

        # Get basic OCR text only
        ocr_data = await get_ocr_data(asset_id="abc123def456", include_bounding_boxes=False)
        # Returns OCRResult with text but minimal bounding box data

    Common Issues:
        1. "OCR data not available"
           → OCR must be enabled and processed for this asset
           → Check server_health() for OCR capability detection
           → Run OCR processing job in Immich admin panel

        2. "Asset not found"
           → Verify asset_id is correct and exists
           → Asset may have been deleted or moved

        3. Empty bounding boxes
           → Bounding boxes require Immich v2.3.0+
           → Check server version with server_health()

        4. Low confidence scores
           → Text may be handwritten, stylized, or poor quality
           → Consider re-processing with different language model
           → Check image quality and text clarity

    Platform Notes:
        - Requires Immich v2.2.0+ for basic OCR functionality
        - Bounding boxes and enhanced multilingual support: v2.3.0+
        - Language detection accuracy improves with v2.3.0+ models

    See Also:
        - search_photos: Search using OCR with specific language models
        - get_photo_info: Get basic photo info including OCR text
        - server_health: Check OCR capability and version support
    """
    try:
        client = await get_api_client()
        ocr_data = await client.get_asset_ocr(
            asset_id, include_bounding_boxes=include_bounding_boxes
        )

        return OCRResult(
            asset_id=asset_id,
            text=ocr_data.get("text", ""),
            language=ocr_data.get("language", "unknown"),
            confidence=ocr_data.get("confidence", 0.0),
            bounding_boxes=ocr_data.get("bounding_boxes", []),
            words=ocr_data.get("words", []),
            regions=ocr_data.get("regions", []),
        )

    except ImmichAPIError as e:
        logger.error("Immich API error in get_ocr_data: %s", e)
        return OCRResult(
            asset_id=asset_id,
            text="",
            language="error",
            confidence=0.0,
            bounding_boxes=[],
            words=[],
            regions=[],
        )


@mcp.tool()
async def get_asset_ocr(asset_id: str) -> OcrInfo:
    r"""Get OCR text and bounding boxes from a specific photo (v2.2.0+ with v2.3.0+ enhancements).

    Extracts text content from images using OCR technology. In Immich v2.3.0+,
    this includes bounding box coordinates for text positioning and multilingual support.

    Austrian efficiency: Extract searchable text from photos for organization and search.

    Prerequisites:
        - IMMICH_URL and IMMICH_API_KEY environment variables must be set
        - Immich server must be accessible
        - asset_id must be a valid asset ID from Immich
        - OCR must be enabled on the Immich server (v2.2.0+)
        - For bounding boxes: Requires Immich v2.3.0+

    Parameters:
        asset_id (str, REQUIRED):
            Unique identifier of the photo asset in Immich.
            Format: UUID string (e.g., "550e8400-e29b-41d4-a716-446655440000")
            Obtain from: upload_photos response, search_photos results, or album listings.

    Returns:
        OcrInfo object containing:
            - text (str): Full extracted text from the image
            - bounding_boxes (List[Dict]): Text regions with coordinates (v2.3.0+)
                Each box contains: x, y, width, height, text, confidence
            - language (str): Detected OCR language
            - confidence (float): Overall OCR confidence score (0.0-1.0)
            - asset_id (str): Asset ID that was processed
            - has_bounding_boxes (bool): Whether bounding box data is available

        Returns empty result if OCR is not available for the asset.

    Usage:
        Use this tool to extract searchable text from photos, enabling content-based
        organization and search. Particularly useful for documents, receipts, signs,
        and any photos containing readable text.

        Common scenarios:
        - Extract text from receipts or invoices for expense tracking
        - Get text from documents for content indexing
        - Read text from signs or labels in photos
        - Enable search across photo content beyond just filenames/metadata
        - View bounding boxes to see where text was detected (v2.3.0+)

    Examples:
        # Get OCR text from a photo
        ocr_info = await get_asset_ocr(asset_id="abc123def456")
        # Access extracted text: ocr_info.text
        # Check if bounding boxes available: ocr_info.has_bounding_boxes
        # Get bounding boxes: ocr_info.bounding_boxes

        # Process bounding boxes (v2.3.0+)
        if ocr_info.has_bounding_boxes:
            for box in ocr_info.bounding_boxes:
                # Each box has: x, y, width, height, text, confidence
                print(f"Text: {box['text']} at ({box['x']}, {box['y']})")

        # Error handling
        ocr_info = await get_asset_ocr(asset_id="invalid_id")
        if not ocr_info.text and not ocr_info.has_bounding_boxes:
            # No OCR data available or asset not found

    Common Issues:
        1. "OCR not available" (returns empty text)
           → Asset may not contain readable text
           → OCR processing may not have completed yet
           → Check server_health for OCR availability

        2. "Asset not found"
           → Verify asset_id is correct
           → Check asset exists in Immich library
           → Ensure API key has access to this asset

        3. No bounding boxes (pre-v2.3.0)
           → Bounding boxes require Immich v2.3.0+
           → Check has_bounding_boxes flag
           → has_bounding_boxes will be False for older versions

    See Also:
        - search_photos: Search for photos containing specific OCR text
        - get_photo_info: Get general photo metadata
        - server_health: Check OCR availability and version
    """
    try:
        client = await get_api_client()
        ocr_data = await client.get_asset_ocr(asset_id)

        # Extract bounding box information if available (v2.3.0+)
        bounding_boxes = ocr_data.get("bounding_boxes", [])
        has_bounding_boxes = len(bounding_boxes) > 0

        return OcrInfo(
            text=ocr_data.get("text", ""),
            bounding_boxes=bounding_boxes,
            language=ocr_data.get("language", "unknown"),
            confidence=ocr_data.get("confidence", 0.0),
            asset_id=asset_id,
            has_bounding_boxes=has_bounding_boxes,
        )

    except ImmichAPIError as e:
        logger.error("Immich API error in get_asset_ocr: %s", e)
        return OcrInfo(
            text="",
            bounding_boxes=[],
            language="unknown",
            confidence=0.0,
            asset_id=asset_id,
            has_bounding_boxes=False,
        )


@mcp.tool()
async def organize_photos_by_date(
    asset_ids: list[str],
    organization_type: str = Field(
        "year_month", description="Organization: year, year_month, or year_month_day"
    ),
) -> OrganizeResult:
    r"""Automatically organize photos into date-based albums.

    Austrian efficiency: Bulk organization without manual album creation.
    Creates albums based on photo dates and adds photos automatically.

    Parameters:
        asset_ids (List[str], REQUIRED):
            List of photo IDs to organize.
            Format: ["id1", "id2", "id3"]
            Each ID must be a valid asset ID from Immich.

        organization_type (str, OPTIONAL):
            Grouping method for organization.
            Valid values: "year", "year_month", "year_month_day"
            Default: "year_month"
            - "year": Group by year only
            - "year_month": Group by year and month
            - "year_month_day": Group by full date

    Returns:
        OrganizeResult containing:
            - albums_created (int): Number of albums created
            - photos_organized (int): Number of photos organized
            - organization_type (str): Type of organization used
            - created_albums (List[str]): List of created album names
            - errors (List[str]): Any errors encountered
    """
    try:
        client = await get_api_client()

        # Perform organization
        result = await client.organize_photos_by_date(
            asset_ids=asset_ids, organization_type=organization_type
        )

        return OrganizeResult(
            albums_created=result.get("albums_created", 0),
            photos_organized=result.get("photos_organized", 0),
            organization_type=organization_type,
            created_albums=result.get("created_albums", []),
            errors=result.get("errors", []),
        )

    except ImmichAPIError as e:
        logger.error("Immich API error in organize_photos_by_date: %s", e)
        return OrganizeResult(
            albums_created=0,
            photos_organized=0,
            organization_type=organization_type,
            created_albums=[],
            errors=[str(e)],
        )


@mcp.tool()
async def delete_photos(
    asset_ids: list[str],
    *,
    move_to_trash: bool = Field(
        default=True, description="Move to trash (true) or permanently delete (false)"
    ),
) -> DeletionResult:
    r"""Delete photos with trash/permanent options.

    Safe deletion workflow with trash support for recovery.
    Permanently delete only when explicitly requested.

    Parameters:
        asset_ids (List[str], REQUIRED):
            List of photo IDs to delete.
            Format: ["id1", "id2", "id3"]
            Each ID must be a valid asset ID from Immich.

        move_to_trash (bool, OPTIONAL):
            Whether to move to trash (recoverable) or permanently delete.
            When True: Photos moved to trash (can be recovered).
            When False: Photos permanently deleted (cannot be recovered).
            Default: True (safe deletion)

    Returns:
        DeletionResult containing:
            - deleted_count (int): Number of photos permanently deleted
            - trashed_count (int): Number of photos moved to trash
            - error_count (int): Number of deletion errors
            - deleted_asset_ids (List[str]): IDs of deleted/trashed assets
            - errors (List[str]): Error messages for failed deletions
    """
    try:
        client = await get_api_client()

        # Perform deletion
        result = await client.delete_photos(asset_ids=asset_ids, move_to_trash=move_to_trash)

        return DeletionResult(
            deleted_count=result.get("deleted_count", 0),
            trashed_count=result.get("trashed_count", 0),
            error_count=result.get("error_count", 0),
            deleted_asset_ids=result.get("deleted_asset_ids", []),
            errors=result.get("errors", []),
        )

    except ImmichAPIError as e:
        logger.error("Immich API error in delete_photos: %s", e)
        return DeletionResult(
            deleted_count=0,
            trashed_count=0,
            error_count=len(asset_ids),
            deleted_asset_ids=[],
            errors=[str(e)],
        )


# ====== PHASE 2 CATEGORY 1: ALBUM MANAGEMENT (4 tools) ======


@mcp.tool()
async def create_album(
    name: str, description: str | None = None, asset_ids: list[str] | None = None
) -> AlbumResult:
    r"""Create a new album with optional assets and description.

    Creates a new album in Immich with the specified name, optionally adding assets
    and a description. Albums are useful for organizing photos by event, theme, or
    any other categorization. Assets can be added during creation or later using
    add_to_album.

    Prerequisites:
        - IMMICH_URL and IMMICH_API_KEY environment variables must be set
        - Immich server must be accessible
        - asset_ids (if provided) must be valid asset IDs from Immich

    Parameters:
        name (str, REQUIRED):
            Name of the album to create.
            Format: Any string (album names are not unique).
            Example: "Summer Vacation 2024", "Family Photos", "Vienna Trip"
            Note: Multiple albums can have the same name.

        description (str, OPTIONAL):
            Optional description for the album.
            Format: Any text string.
            Example: "Photos from our summer vacation in Vienna"
            Default: None (no description)
            Note: Useful for adding context or notes about the album.

        asset_ids (List[str], OPTIONAL):
            List of asset IDs to add to the album during creation.
            Format: ["asset_id1", "asset_id2", "asset_id3"]
            Each ID must be a valid asset ID from Immich.
            Example: ["abc123", "def456", "ghi789"]
            Obtain from: upload_photos response, search_photos results, or get_photo_info.
            Default: None (creates empty album)
            Note: Assets can be added later using add_to_album.

    Returns:
        AlbumResult containing:
            - id (str): Unique album ID (use for future operations)
            - album_name (str): Name of the album
            - description (Optional[str]): Album description (if provided)
            - created_at (str): ISO timestamp when album was created
            - asset_count (int): Number of assets in the album
            - owner_id (str): ID of album owner

    Usage:
        Use this tool to create new albums for organizing photos. Essential for
        organizing photo collections by event, theme, date, or any other category.
        Can create empty albums or albums with initial assets.

        Common scenarios:
        - Create album for a specific event or vacation
        - Organize photos by theme or category
        - Create albums before uploading photos (then add photos during upload)
        - Group related photos together

        Best practices:
        - Use descriptive names that make albums easy to find
        - Add descriptions for context (especially for albums with similar names)
        - Create albums before uploading photos for better organization
        - Use consistent naming conventions across albums

    Examples:
        # Create empty album
        album = await create_album(name="Summer Vacation 2024")
        # Album created: album.album_name, album.id

        # Create album with description
        album = await create_album(
            name="Family Gathering",
            description="Photos from the family reunion in Vienna"
        )

        # Create album with initial assets
        album = await create_album(
            name="Vienna Trip",
            asset_ids=["abc123", "def456", "ghi789"],
            description="Photos from our trip to Vienna"
        )
        # Album created with album.asset_count photos

        # Create album, then add photos from search
        album = await create_album(name="Nature Photos")
        search_results = await search_photos(query="nature landscape", limit=20)
        asset_ids = [photo.id for photo in search_results]
        await add_to_album(album_id=album.id, asset_ids=asset_ids)

    Common Issues:
        1. "Invalid asset ID" error
           → Verify all asset_ids are valid
           → Check assets exist using get_photo_info
           → Ensure asset_ids are correct format

    See Also:
        - add_to_album: Add photos to existing albums
        - list_albums: List all albums
        - search_photos: Find photos to add to albums
    """
    try:
        client = await get_api_client()

        result = await client.create_album(
            name=name, description=description, asset_ids=asset_ids or []
        )

        return AlbumResult(
            id=result["id"],
            album_name=result["albumName"],
            description=result.get("description"),
            created_at=result["createdAt"],
            asset_count=result.get("assetCount", 0),
            owner_id=result["ownerId"],
        )

    except ImmichAPIError as e:
        logger.error("Immich API error in create_album: %s", e)
        return AlbumResult(
            id="",
            album_name=name,
            description=description,
            created_at="",
            asset_count=0,
            owner_id="",
        )


@mcp.tool()
async def add_to_album(album_id: str, asset_ids: list[str]) -> AlbumUpdateResult:
    r"""Add photos to an existing album.

    Parameters:
        album_id (str, REQUIRED):
            Target album ID to add photos to.
            Must be a valid album ID from Immich.

        asset_ids (List[str], REQUIRED):
            List of photo IDs to add to the album.
            Format: ["photo1", "photo2", "photo3"]
            Each ID must be a valid asset ID from Immich.

    Returns:
        AlbumUpdateResult containing:
            - album_id (str): Album ID that was updated
            - added_count (int): Number of photos successfully added
            - duplicate_count (int): Number of duplicates skipped
            - new_asset_count (int): Total assets in album after addition
            - errors (List[str]): Error messages for failed additions
    """
    try:
        client = await get_api_client()

        result = await client.add_assets_to_album(album_id=album_id, asset_ids=asset_ids)

        return AlbumUpdateResult(
            album_id=album_id,
            added_count=result.get("added_count", 0),
            duplicate_count=result.get("duplicate_count", 0),
            new_asset_count=result.get("new_asset_count", 0),
            errors=result.get("errors", []),
        )

    except ImmichAPIError as e:
        logger.error("Immich API error in add_to_album: %s", e)
        return AlbumUpdateResult(
            album_id=album_id, added_count=0, duplicate_count=0, new_asset_count=0, errors=[str(e)]
        )


@mcp.tool()
async def list_albums(*, shared: bool | None = None, include_stats: bool = True) -> list[AlbumInfo]:
    r"""List all albums with metadata and statistics.

    Retrieves a list of all albums in your Immich library, including album metadata,
    asset counts, date ranges, and basic information. Supports filtering by shared
    status and optional statistics. Essential for discovering albums, finding album
    IDs, or browsing your album collection.

    Prerequisites:
        - IMMICH_URL and IMMICH_API_KEY environment variables must be set
        - Immich server must be accessible

    Parameters:
        shared (bool, OPTIONAL):
            Filter albums by shared status.
            When True: Only returns albums shared with you by other users.
            When False: Only returns albums you own.
            When None: Returns all albums (both owned and shared).
            Default: None (all albums)

        include_stats (bool, OPTIONAL):
            Whether to include statistics in album information.
            When True: Includes asset_count, start_date, end_date.
            When False: Returns basic album information only.
            Default: True
            Note: Statistics may take slightly longer to compute.

    Returns:
        List[AlbumInfo] containing album objects with:
            - id (str): Unique album ID
            - album_name (str): Name of the album
            - description (Optional[str]): Album description (if set)
            - created_at (str): ISO timestamp when album was created
            - updated_at (str): ISO timestamp when album was last updated
            - asset_count (int): Number of assets in the album (if include_stats=True)
            - owner_id (str): ID of album owner
            - shared (bool): Whether album is shared
            - album_thumbnail_asset_id (Optional[str]): ID of thumbnail asset
            - start_date (Optional[str]): Earliest photo date (if include_stats=True)
            - end_date (Optional[str]): Latest photo date (if include_stats=True)

        Returns empty list on error.

    Usage:
        Use this tool to discover albums, find album IDs for other operations,
        or browse your album collection. Essential for album management workflows
        and accessing organized photo collections.

        Common scenarios:
        - Find album IDs for get_photo_info or other operations
        - Browse all albums in your library
        - Check album names and asset counts
        - Discover shared albums
        - Find albums by name or date range

        Best practices:
        - Use include_stats=True to see photo counts and date ranges
        - Filter by shared status to find specific album types
        - Use album IDs from results for other operations

    Examples:
        # List all albums with statistics
        albums = await list_albums(include_stats=True)
        # Found len(albums) albums, iterate: album.album_name, album.asset_count

        # List only your albums (not shared)
        my_albums = await list_albums(shared=False, include_stats=True)

        # List only shared albums
        shared_albums = await list_albums(shared=True, include_stats=True)

        # Find specific album by name
        albums = await list_albums(include_stats=True)
        for album in albums:
            if album.album_name == "Summer Vacation 2024":
                # Found album ID: album.id
                break

        # List albums without statistics (faster)
        albums = await list_albums(include_stats=False)

    Common Issues:
        1. Empty albums list
           → You may not have any albums yet
           → Use create_album to create albums
           → Check shared parameter if looking for shared albums

        2. Album not in results
           → Check shared parameter (album may be shared or owned)
           → Verify album exists in Immich
           → Refresh and try again

    See Also:
        - get_photo_info: Get detailed information about a specific album (if supported)
        - create_album: Create new albums
        - search_photos: Find photos to add to albums
    """
    try:
        client = await get_api_client()

        albums_data = await client.get_albums(shared=shared, include_stats=include_stats)

        albums = []
        for album_data in albums_data:
            album = AlbumInfo(
                id=album_data["id"],
                album_name=album_data["albumName"],
                description=album_data.get("description"),
                created_at=album_data["createdAt"],
                updated_at=album_data["updatedAt"],
                asset_count=album_data.get("assetCount", 0),
                owner_id=album_data["ownerId"],
                shared=album_data.get("shared", False),
                album_thumbnail_asset_id=album_data.get("albumThumbnailAssetId"),
                start_date=album_data.get("startDate"),
                end_date=album_data.get("endDate"),
            )
            albums.append(album)

        return albums

    except ImmichAPIError as e:
        logger.error("Immich API error in list_albums: %s", e)
        return []


@mcp.tool()
async def share_album(
    album_id: str,
    expires_at: str | None = None,
    *,
    allow_download: bool = True,
    allow_upload: bool = False,
    show_metadata: bool = True,
) -> ShareResult:
    r"""Generate public share link for album.

    Parameters:
        album_id (str, REQUIRED):
            Album ID to create share link for.
            Must be a valid album ID from Immich.

        expires_at (str, OPTIONAL):
            Optional expiration date for the share link.
            Format: ISO 8601 datetime string (e.g., "2025-12-31T23:59:59Z")
            Default: None (no expiration)

        allow_download (bool, OPTIONAL):
            Whether to allow downloading photos from the share link.
            Default: True

        allow_upload (bool, OPTIONAL):
            Whether to allow uploading photos to the album via share link.
            Default: False

        show_metadata (bool, OPTIONAL):
            Whether to show photo metadata to viewers.
            Default: True

    Returns:
        ShareResult containing:
            - id (str): Share link ID
            - key (str): Share link key
            - public_url (str): Public URL for sharing
            - album_id (str): Album ID that was shared
            - expires_at (Optional[str]): Expiration date if set
            - allow_upload (bool): Upload permission setting
            - allow_download (bool): Download permission setting
            - show_metadata (bool): Metadata visibility setting
            - created_at (str): ISO timestamp when share was created
    """
    try:
        client = await get_api_client()

        result = await client.create_shared_link(
            album_id=album_id,
            expires_at=expires_at,
            allow_download=allow_download,
            allow_upload=allow_upload,
            show_metadata=show_metadata,
        )

        return ShareResult(
            id=result["id"],
            key=result["key"],
            public_url=result["public_url"],
            album_id=album_id,
            expires_at=result.get("expiresAt"),
            allow_upload=result.get("allowUpload", False),
            allow_download=result.get("allowDownload", True),
            show_metadata=result.get("showMetadata", True),
            created_at=result["createdAt"],
        )

    except ImmichAPIError as e:
        logger.error("Immich API error in share_album: %s", e)
        return ShareResult(
            id="",
            key="",
            public_url="",
            album_id=album_id,
            expires_at=expires_at,
            allow_upload=allow_upload,
            allow_download=allow_download,
            show_metadata=show_metadata,
            created_at="",
        )


# ====== PHASE 2 CATEGORY 2: PEOPLE & FACES (3 tools) ======


@mcp.tool()
async def detect_people(
    asset_ids: list[str] | None = None, *, force_reprocess: bool = False
) -> PeopleDetectionResult:
    r"""Run face detection on photos and return clustering results.

    Parameters:
        asset_ids (List[str], OPTIONAL):
            Specific photos to process.
            Format: ["id1", "id2", "id3"]
            When None: Processes all unprocessed photos in library.
            Default: None

        force_reprocess (bool, OPTIONAL):
            Whether to re-detect faces even if already processed.
            When True: Re-processes all specified photos.
            When False: Skips photos that already have face detection.
            Default: False

    Returns:
        PeopleDetectionResult containing:
            - detected_faces (int): Number of faces detected
            - new_people (int): Number of new people clusters created
            - processed_assets (int): Number of photos processed
            - processing_time_seconds (float): Time taken for processing
            - people_found (List[Dict]): List of detected people with metadata
    """
    try:
        start_time = asyncio.get_event_loop().time()
        client = await get_api_client()

        result = await client.run_face_detection(
            asset_ids=asset_ids, force_reprocess=force_reprocess
        )

        end_time = asyncio.get_event_loop().time()
        processing_time = end_time - start_time

        return PeopleDetectionResult(
            detected_faces=result.get("detected_faces", 0),
            new_people=result.get("new_people", 0),
            processed_assets=result.get("processed_assets", 0),
            processing_time_seconds=processing_time,
            people_found=result.get("people_found", []),
        )

    except ImmichAPIError as e:
        logger.error("Immich API error in detect_people: %s", e)
        return PeopleDetectionResult(
            detected_faces=0,
            new_people=0,
            processed_assets=0,
            processing_time_seconds=0.0,
            people_found=[],
        )


@mcp.tool()
async def tag_person(
    person_id: str, name: str, face_asset_ids: list[str] | None = None
) -> PersonTagResult:
    r"""Assign name to detected person/face cluster.

    Parameters:
        person_id (str, REQUIRED):
            Person cluster ID from face detection.
            Obtain from detect_people results.

        name (str, REQUIRED):
            Name to assign to the person.
            Format: Any string (e.g., "Sandra", "John Doe")

        face_asset_ids (List[str], OPTIONAL):
            Additional face IDs to merge with this person.
            Format: ["face1", "face2", "face3"]
            Default: None (no additional faces to merge)

    Returns:
        PersonTagResult containing:
            - person_id (str): Person cluster ID
            - name (str): Assigned name
            - faces_merged (int): Number of faces merged
            - total_faces (int): Total faces in this person cluster
            - updated_at (str): ISO timestamp when person was updated
    """
    try:
        client = await get_api_client()

        result = await client.update_person(
            person_id=person_id, name=name, face_asset_ids=face_asset_ids or []
        )

        return PersonTagResult(
            person_id=person_id,
            name=name,
            faces_merged=result.get("faces_merged", 0),
            total_faces=result.get("total_faces", 0),
            updated_at=result.get("updated_at", datetime.now().isoformat()),
        )

    except ImmichAPIError as e:
        logger.error("Immich API error in tag_person: %s", e)
        return PersonTagResult(
            person_id=person_id,
            name=name,
            faces_merged=0,
            total_faces=0,
            updated_at=datetime.now().isoformat(),
        )


@mcp.tool()
async def search_by_person(
    person_name: str, limit: int = 50, *, include_metadata: bool = True
) -> list[PhotoSearchResult]:
    r"""Find all photos containing specific person.

    Parameters:
        person_name (str, REQUIRED):
            Name of person to search for.
            Must match a name assigned via tag_person.
            Format: Exact name match (case-sensitive)

        limit (int, OPTIONAL):
            Maximum number of results to return.
            Range: 1-200
            Default: 50

        include_metadata (bool, OPTIONAL):
            Whether to include full photo metadata in results.
            When True: Returns complete PhotoSearchResult objects.
            When False: Returns minimal photo information.
            Default: True

    Returns:
        List[PhotoSearchResult] containing photos with the person:
            - id (str): Unique asset ID
            - original_filename (str): Original filename
            - file_path (str): Path to file on server
            - type (str): Asset type ("IMAGE" or "VIDEO")
            - created_at (str): ISO timestamp when created
            - is_favorite (bool): Whether marked as favorite
            - is_archived (bool): Whether archived
            - is_trashed (bool): Whether in trash
            - (and other PhotoSearchResult fields if include_metadata=True)

        Returns empty list if person not found or no photos match.
    """
    try:
        client = await get_api_client()

        # Validate limit
        limit = max(1, min(200, limit))

        results = await client.search_photos_by_person(
            person_name=person_name, limit=limit, include_metadata=include_metadata
        )

        # Convert to response format
        photo_results = []
        for photo in results:
            photo_result = PhotoSearchResult(
                id=photo["id"],
                original_filename=photo.get("originalFileName", "Unknown"),
                file_path=photo.get("originalPath", ""),
                device_asset_id=photo.get("deviceAssetId", ""),
                owner_id=photo.get("ownerId", ""),
                device_id=photo.get("deviceId", ""),
                type=photo.get("type", "IMAGE"),
                created_at=photo.get("createdAt", ""),
                updated_at=photo.get("updatedAt", ""),
                file_created_at=photo.get("fileCreatedAt", ""),
                local_date_time=photo.get("localDateTime", ""),
                duration=photo.get("duration"),
                is_favorite=photo.get("isFavorite", False),
                is_archived=photo.get("isArchived", False),
                is_trashed=photo.get("isTrashed", False),
                checksum=photo.get("checksum", ""),
                smart_search_score=None,  # Not applicable for person search
            )
            photo_results.append(photo_result)

        return photo_results

    except ImmichAPIError as e:
        logger.error("Immich API error in search_by_person: %s", e)
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
            used_bytes=storage_data.get("usage", 0),
            available_bytes=storage_data.get("available", 0),
            total_bytes=storage_data.get("total", 0),
            usage_percentage=storage_data.get("usage_percentage", 0.0),
            photo_count=storage_data.get("photos", 0),
            video_count=storage_data.get("videos", 0),
            user_count=storage_data.get("users", 0),
            album_count=storage_data.get("albums", 0),
            storage_usage_by_user=storage_data.get("usage_by_user", []),
        )

    except ImmichAPIError as e:
        logger.error("Immich API error in get_storage_info: %s", e)
        raise


@mcp.tool()
async def backup_photos(
    backup_path: str, album_ids: list[str] | None = None, *, include_metadata: bool = True
) -> BackupResult:
    r"""Export photos for backup with metadata preservation.

    Parameters:
        backup_path (str, REQUIRED):
            Destination directory for backup.
            Format: Absolute or relative path
            Example: "D:/Backup/Immich-2025-07", "/backup/immich"
            Note: Directory will be created if it doesn't exist.

        album_ids (List[str], OPTIONAL):
            Specific albums to backup.
            Format: ["album_id1", "album_id2"]
            When None: Backs up all photos in library.
            Default: None (all photos)

        include_metadata (bool, OPTIONAL):
            Whether to include EXIF and Immich metadata.
            When True: Exports metadata files alongside photos.
            When False: Exports photos only.
            Default: True

    Returns:
        BackupResult containing:
            - backup_path (str): Path where backup was saved
            - exported_photos (int): Number of photos exported
            - exported_videos (int): Number of videos exported
            - total_size_mb (float): Total size of backup in MB
            - backup_time_seconds (float): Time taken for backup
            - metadata_included (bool): Whether metadata was included
            - album_structure_preserved (bool): Whether album structure was preserved
            - errors (List[str]): Error messages for failed exports
    """
    try:
        start_time = asyncio.get_event_loop().time()
        client = await get_api_client()

        result = await client.export_photos(
            backup_path=backup_path, album_ids=album_ids, include_metadata=include_metadata
        )

        end_time = asyncio.get_event_loop().time()
        backup_time = end_time - start_time

        return BackupResult(
            backup_path=backup_path,
            exported_photos=result.get("exported_photos", 0),
            exported_videos=result.get("exported_videos", 0),
            total_size_mb=result.get("total_size_mb", 0.0),
            backup_time_seconds=backup_time,
            metadata_included=include_metadata,
            album_structure_preserved=result.get("album_structure_preserved", False),
            errors=result.get("errors", []),
        )

    except ImmichAPIError as e:
        logger.error("Immich API error in backup_photos: %s", e)
        return BackupResult(
            backup_path=backup_path,
            exported_photos=0,
            exported_videos=0,
            total_size_mb=0.0,
            backup_time_seconds=0.0,
            metadata_included=include_metadata,
            album_structure_preserved=False,
            errors=[str(e)],
        )


@mcp.tool()
async def server_health() -> HealthStatus:
    r"""Check Immich server health and connection status.

    Performs a comprehensive health check of the Immich server, verifying connectivity,
    retrieving server version information, API status, and system diagnostics. Useful for
    monitoring server status, troubleshooting connection issues, or verifying server
    configuration before performing operations.

    Prerequisites:
        - IMMICH_URL and IMMICH_API_KEY environment variables must be set
        - Immich server must be accessible (network connectivity)

    Parameters:
        None (no parameters required)

    Returns:
        HealthStatus containing:
            - server_version (str): Immich server version string
            - server_features (list[str]): Available server features
            - is_v2_plus (bool): Whether server is v2.0.0+
            - has_ocr (bool): Whether server supports OCR search (v2.2.0+)
            - has_multilingual_ocr (bool): Whether server supports multilingual OCR (v2.3.0+)
            - ocr_languages (list[str]): Supported OCR languages
            - database_connected (bool): Database connection status
            - redis_connected (bool): Redis connection status
            - storage_accessible (bool): Storage accessibility
            - ml_services_available (bool): Machine learning services status
            - response_time_ms (int): API response time in milliseconds
            - uptime_seconds (int): Server uptime in seconds
            - error_messages (list[str]): Any error messages

    Usage:
        Use this tool to verify Immich server is running and accessible before
        performing operations. Essential for troubleshooting connection issues,
        monitoring server health, or checking feature availability.

        Common scenarios:
        - Verify server connectivity before bulk operations
        - Check server version for compatibility
        - Monitor server health and performance
        - Troubleshoot connection issues
        - Check feature availability (ML, OCR)
        - Health monitoring and alerting

    Examples:
        # Basic health check
        health = await server_health()
        # Check status: health.server_version, health.has_ocr, health.has_multilingual_ocr
        # Check OCR languages: health.ocr_languages (v2.3.0+ shows multilingual support)
        # Check features: health.server_features, health.ml_services_available
        # Access all fields: health.status, health.server_version, health.response_time_ms, health.timestamp

    Common Issues:
        1. "Connection refused" or timeout
           → Verify IMMICH_URL is correct (default: http://localhost:2283)
           → Check Immich server is running
           → Verify network connectivity
           → Check firewall settings

        2. "Unauthorized" or "Invalid API key"
           → Verify IMMICH_API_KEY is set correctly
           → Check API key is valid in Immich settings
           → Regenerate API key if needed

        3. Server returns "unhealthy" status
           → Check Immich server logs for details
           → Verify server is not in maintenance mode
           → Check server resources (CPU, memory, disk)
           → Verify database and storage are accessible

    See Also:
        - upload_photos: Upload photos after verifying server health
        - search_photos: Search photos after confirming server is online
        - get_storage_info: Get detailed storage information
    """
    try:
        start_time = asyncio.get_event_loop().time()
        client = await get_api_client()

        health_data = await client.get_server_info()

        end_time = asyncio.get_event_loop().time()
        response_time_ms = int((end_time - start_time) * 1000)

        return HealthStatus(
            server_version=health_data.get("version", "Unknown"),
            server_features=health_data.get("features", []),
            is_v2_plus=health_data.get("is_v2_plus", False),
            has_ocr=health_data.get("has_ocr", False),
            has_multilingual_ocr=health_data.get("has_multilingual_ocr", False),
            ocr_languages=health_data.get("ocr_languages", []),
            database_connected=health_data.get("database", True),
            redis_connected=health_data.get("redis", True),
            storage_accessible=health_data.get("storage", True),
            ml_services_available=health_data.get("machine_learning", True),
            response_time_ms=response_time_ms,
            uptime_seconds=health_data.get("uptime", 0),
            error_messages=health_data.get("errors", []),
        )

    except ImmichAPIError as e:
        logger.error("Immich API error in server_health: %s", e)
        raise


# ===== LIBRARY MANAGEMENT TOOLS =====


@mcp.tool()
async def list_libraries() -> list[dict]:
    """List all available Immich libraries.

    Returns comprehensive information about all libraries configured on the server,
    including their types, locations, and statistics. Essential for understanding
    your photo library organization and managing external folder imports.

    Austrian efficiency: Complete library overview in one call.
    """
    try:
        client = await get_api_client()
        libraries = await client.get_libraries()

        # Add some user-friendly enhancements
        for lib in libraries:
            lib["location_count"] = len(lib.get("importPaths", []))
            lib["has_exclusions"] = bool(lib.get("exclusionPatterns"))

        return libraries
    except Exception as e:
        logger.error(f"Failed to list libraries: {e}")
        return []


@mcp.tool()
async def get_library_info(library_id: str) -> dict:
    """Get detailed information about a specific Immich library.

    Provides comprehensive details about a library including its configuration,
    import paths, exclusion patterns, statistics, and current status. Perfect for
    understanding how external folders are configured and monitored.

    Args:
        library_id: The unique identifier of the library to examine

    Returns:
        Complete library information with metadata and configuration details
    """
    try:
        client = await get_api_client()
        library_info = await client.get_library_info(library_id)

        # Get additional location details
        try:
            locations = await client.get_library_locations(library_id)
            library_info["locations"] = locations
        except Exception:
            library_info["locations"] = []

        return library_info
    except Exception as e:
        logger.error(f"Failed to get library info for {library_id}: {e}")
        return {"error": str(e), "library_id": library_id}


@mcp.tool()
async def create_library(
    name: str,
    library_type: str = "UPLOAD",
    import_paths: list[str] | None = None,
    exclusion_patterns: list[str] | None = None,
) -> dict:
    """Create a new Immich library for organizing external photo folders.

    Libraries allow you to organize photos from different external folders,
    set up import paths, and configure exclusion patterns. This solves the
    'unwieldy external folder management' problem by providing structured
    library organization.

    Args:
        name: Descriptive name for the library (e.g., "Vacation Photos", "Work Projects")
        library_type: Type of library - "UPLOAD" for user uploads, "IMPORT" for external folders
        import_paths: List of file system paths to import photos from (for IMPORT libraries)
        exclusion_patterns: Glob patterns to exclude from imports (e.g., ["*.tmp", "cache/**"])

    Returns:
        Created library information with ID and configuration details

    Austrian efficiency: One-click library creation with full configuration.
    """
    try:
        client = await get_api_client()

        # Validate import paths exist (for IMPORT libraries)
        if library_type == "IMPORT" and import_paths:
            for path in import_paths:
                if not Path(path).exists():
                    return {
                        "error": f"Import path does not exist: {path}",
                        "suggestion": "Verify the path is accessible and try again",
                    }

        library = await client.create_library(
            name=name,
            library_type=library_type,
            import_paths=import_paths,
            exclusion_patterns=exclusion_patterns,
        )

        return {
            "success": True,
            "library": library,
            "message": f"Library '{name}' created successfully",
            "type": library_type,
            "import_paths_count": len(import_paths or []),
            "next_steps": [
                "Add more import paths if needed",
                "Configure exclusion patterns",
                "Run initial scan to import photos",
            ],
        }
    except Exception as e:
        logger.error(f"Failed to create library '{name}': {e}")
        return {"error": str(e), "suggestion": "Check library name uniqueness and path permissions"}


@mcp.tool()
async def scan_library(
    library_id: str, refresh_modified_files: bool = False, refresh_all_files: bool = False
) -> dict:
    """Scan a library for new or changed photos from external folders.

    This is the key solution to 'unwieldy external folder management' - instead
    of manually managing folder imports, libraries can be scanned to automatically
    discover and import new photos from configured external paths.

    Args:
        library_id: The library ID to scan
        refresh_modified_files: Also refresh metadata for modified files (slower)
        refresh_all_files: Refresh all files regardless of modification date (slowest)

    Returns:
        Scan results with statistics on discovered and imported photos

    Austrian efficiency: Automated photo discovery from external folders.
    """
    try:
        client = await get_api_client()

        # Get library info first for context
        library_info = await client.get_library_info(library_id)

        # Perform the scan
        scan_result = await client.scan_library(
            library_id=library_id,
            refresh_modified_files=refresh_modified_files,
            refresh_all_files=refresh_all_files,
        )

        # Calculate scan scope
        scope = "new files only"
        if refresh_modified_files:
            scope = "new and modified files"
        if refresh_all_files:
            scope = "all files (full refresh)"

        return {
            "success": True,
            "library_name": library_info.get("name", "Unknown"),
            "scan_scope": scope,
            "scan_result": scan_result,
            "message": f"Library scan completed for {scope}",
            "tips": [
                "Use refresh_modified_files for regular updates",
                "Use refresh_all_files for initial setup or major changes",
                "Check scan results for any import errors",
            ],
        }
    except Exception as e:
        logger.error(f"Failed to scan library {library_id}: {e}")
        return {
            "error": str(e),
            "library_id": library_id,
            "suggestion": "Verify library exists and has valid import paths",
        }


@mcp.tool()
async def add_library_location(library_id: str, path: str) -> dict:
    """Add a new external folder path to an Immich library.

    This directly addresses the 'unwieldy external folder management' issue by
    allowing you to easily add new photo folders to your library organization.
    No more manual folder management - just add the path and scan.

    Args:
        library_id: The library ID to add the location to
        path: Full file system path to add (e.g., "D:\\Photos\\Vacation")

    Returns:
        Updated library configuration with new location

    Austrian efficiency: Simple external folder integration.
    """
    try:
        client = await get_api_client()

        # Validate path exists
        if not Path(path).exists():
            return {
                "error": f"Path does not exist: {path}",
                "suggestion": "Verify the path is correct and accessible",
            }

        # Add the location
        result = await client.add_library_location(library_id, path)

        # Get updated library info
        library_info = await client.get_library_info(library_id)

        return {
            "success": True,
            "library_name": library_info.get("name", "Unknown"),
            "new_location": path,
            "total_locations": len(library_info.get("importPaths", [])),
            "result": result,
            "message": f"Added location '{path}' to library",
            "next_steps": [
                "Run scan_library to import photos from new location",
                "Configure exclusion patterns if needed",
            ],
        }
    except Exception as e:
        logger.error(f"Failed to add location {path} to library {library_id}: {e}")
        return {
            "error": str(e),
            "library_id": library_id,
            "path": path,
            "suggestion": "Check library permissions and path accessibility",
        }


@mcp.tool()
async def remove_library_location(library_id: str, path: str) -> dict:
    """Remove an external folder path from an Immich library.

    Clean up your library organization by removing folders that are no longer
    needed. This helps maintain tidy library configurations.

    Args:
        library_id: The library ID to remove the location from
        path: Full file system path to remove

    Returns:
        Updated library configuration without the removed location
    """
    try:
        client = await get_api_client()

        # Remove the location
        result = await client.remove_library_location(library_id, path)

        # Get updated library info
        library_info = await client.get_library_info(library_id)

        return {
            "success": True,
            "library_name": library_info.get("name", "Unknown"),
            "removed_location": path,
            "remaining_locations": len(library_info.get("importPaths", [])),
            "result": result,
            "message": f"Removed location '{path}' from library",
            "warning": "Photos from this location may still exist in the library",
        }
    except Exception as e:
        logger.error(f"Failed to remove location {path} from library {library_id}: {e}")
        return {
            "error": str(e),
            "library_id": library_id,
            "path": path,
            "suggestion": "Verify the location exists in the library",
        }


@mcp.tool()
async def manage_library(
    library_id: str,
    action: str,
    name: str | None = None,
    import_paths: list[str] | None = None,
    exclusion_patterns: list[str] | None = None,
) -> dict:
    """Perform various management actions on an Immich library.

    Comprehensive library management including updates, optimization, cleanup,
    and maintenance operations. This provides the control needed for managing
    external photo folder imports effectively.

    Args:
        library_id: The library ID to manage
        action: Management action to perform:
            - "update": Update library configuration
            - "refresh": Refresh all metadata
            - "optimize": Optimize database performance
            - "empty_trash": Remove deleted items permanently
            - "clean_bundles": Remove old bundle files to free space
        name: New library name (for update action)
        import_paths: Updated import paths (for update action)
        exclusion_patterns: Updated exclusion patterns (for update action)

    Returns:
        Action results with status and any relevant statistics

    Austrian efficiency: Complete library lifecycle management.
    """
    try:
        client = await get_api_client()

        # Get library info for context
        library_info = await client.get_library_info(library_id)
        library_name = library_info.get("name", "Unknown")

        if action == "update":
            if not any([name, import_paths, exclusion_patterns]):
                return {
                    "error": "Update action requires at least one parameter to change",
                    "suggestion": "Provide name, import_paths, or exclusion_patterns",
                }

            result = await client.update_library(
                library_id=library_id,
                name=name,
                import_paths=import_paths,
                exclusion_patterns=exclusion_patterns,
            )
            message = f"Updated library '{library_name}' configuration"

        elif action == "refresh":
            result = await client.refresh_library_metadata(library_id)
            message = f"Refreshed metadata for library '{library_name}'"

        elif action == "optimize":
            result = await client.optimize_library(library_id)
            message = f"Optimized database for library '{library_name}'"

        elif action == "empty_trash":
            result = await client.empty_library_trash(library_id)
            message = f"Emptied trash for library '{library_name}'"

        elif action == "clean_bundles":
            result = await client.clean_library_bundles(library_id)
            message = f"Cleaned bundles for library '{library_name}'"

        else:
            return {
                "error": f"Unknown action: {action}",
                "available_actions": [
                    "update",
                    "refresh",
                    "optimize",
                    "empty_trash",
                    "clean_bundles",
                ],
            }

        return {
            "success": True,
            "library_name": library_name,
            "action": action,
            "result": result,
            "message": message,
            "library_id": library_id,
        }

    except Exception as e:
        logger.error(f"Failed to {action} library {library_id}: {e}")
        return {
            "error": str(e),
            "library_id": library_id,
            "action": action,
            "suggestion": "Verify library exists and action is valid",
        }


# ===== MULTI-USER MANAGEMENT TOOLS =====


@mcp.tool()
async def list_users() -> dict:
    """List all configured Immich users.

    Shows all users configured in the system with their roles and descriptions.
    Essential for managing multi-user Immich installations where different users
    have different access levels and library permissions.

    Returns:
        Dictionary with user list and current active user information
    """
    global config
    try:
        if not config:
            config = get_config()

        users_info = []
        for username, user in config.users.items():
            users_info.append(
                {
                    "name": user.name,
                    "role": user.role,
                    "description": user.description,
                    "is_active": username == config.active_user,
                }
            )

        return {
            "success": True,
            "users": users_info,
            "active_user": config.active_user,
            "total_users": len(config.users),
            "message": f"Found {len(config.users)} configured users",
        }
    except Exception as e:
        logger.error(f"Failed to list users: {e}")
        return {"error": str(e), "suggestion": "Check user configuration in environment variables"}


@mcp.tool()
async def switch_user(username: str) -> dict:
    """Switch to a different Immich user context.

    Changes the active user for all subsequent operations. This allows managing
    multiple Immich accounts/libraries from a single MCP server instance.
    Essential for multi-user Immich setups where you need to work with different
    users' libraries and permissions.

    Args:
        username: Name of the user to switch to

    Returns:
        Confirmation of user switch with new active user information
    """
    global config, api_client
    try:
        if not config:
            config = get_config()

        # Switch user in config
        new_user = config.switch_user(username)

        # Update API client to use new user
        if api_client:
            api_client.switch_user(new_user)

        return {
            "success": True,
            "switched_to_user": username,
            "user_role": new_user.role,
            "user_description": new_user.description,
            "message": f"Successfully switched to user '{username}' ({new_user.role})",
            "note": "All subsequent operations will use this user's permissions and libraries",
        }
    except Exception as e:
        logger.error(f"Failed to switch to user {username}: {e}")
        return {
            "error": str(e),
            "requested_user": username,
            "suggestion": "Verify user exists in configuration",
        }


@mcp.tool()
async def get_current_user() -> dict:
    """Get information about the currently active Immich user.

    Shows which user is currently active and their permissions. Useful for
    understanding the current access context and available operations.

    Returns:
        Current user information and permissions
    """
    global config, api_client
    try:
        if not config:
            config = get_config()

        current_user = config.get_active_user()

        # Get user-specific capabilities if API client is available
        capabilities = {}
        if api_client:
            try:
                # Try to get user capabilities (this might vary by Immich version)
                capabilities["can_create_libraries"] = current_user.role in ["admin", "owner"]
                capabilities["can_manage_users"] = current_user.role == "admin"
                capabilities["can_delete_content"] = current_user.role in ["admin", "user"]
            except Exception:
                pass

        return {
            "success": True,
            "current_user": current_user.name,
            "role": current_user.role,
            "description": current_user.description,
            "capabilities": capabilities,
            "message": f"Active user: {current_user.name} ({current_user.role})",
        }
    except Exception as e:
        logger.error(f"Failed to get current user: {e}")
        return {"error": str(e), "suggestion": "Check user configuration"}


@mcp.tool()
async def get_user_libraries(username: str | None = None) -> dict:
    """Get libraries accessible to a specific user or the current user.

    Shows which libraries a user can access based on their permissions.
    In multi-user Immich setups, different users may have access to different
    libraries or shared libraries.

    Args:
        username: User to check libraries for (defaults to current user)

    Returns:
        List of accessible libraries for the specified user
    """
    global config, api_client
    try:
        if not config:
            config = get_config()

        target_user = username or config.active_user
        if target_user != config.active_user:
            # Temporarily switch to target user to get their libraries
            original_user = config.get_active_user()
            target_user_obj = config.users[target_user]
            api_client.switch_user(target_user_obj)
            libraries = await api_client.get_libraries()
            # Switch back
            api_client.switch_user(original_user)
        else:
            # Current user - just get libraries
            libraries = await api_client.get_libraries()

        return {
            "success": True,
            "user": target_user,
            "libraries": libraries,
            "library_count": len(libraries),
            "message": f"User '{target_user}' has access to {len(libraries)} libraries",
        }
    except Exception as e:
        logger.error(f"Failed to get libraries for user {username}: {e}")
        return {
            "error": str(e),
            "user": username or "current",
            "suggestion": "Verify user exists and has library access permissions",
        }


def main():
    """Main entry point with unified transport handling (FastMCP 3.1)."""
    from .transport import run_server

    logger.info("Starting ImmichMCP - FastMCP 3.1 Server")
    run_server(mcp, server_name="immich-mcp")


if __name__ == "__main__":
    main()
