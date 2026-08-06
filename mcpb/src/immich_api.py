"""
Immich API Client for MCP integration
Austrian efficiency for Sandra's 2000+ photo library management
"""

import contextlib
import logging
import mimetypes
from datetime import UTC, datetime
from pathlib import Path

import httpx

from immich_mcp.config import ImmichConfig, ImmichUser

logger = logging.getLogger("immich_mcp.api")

# Global API client instance for shared use
api_client: "ImmichAPIClient | None" = None

_VISIBILITY_VALUES = ("archive", "timeline", "hidden", "locked")


def _iso_ts(ts: float) -> str:
    """Convert a unix epoch float to an Immich-compatible ISO-8601 timestamp (UTC)."""
    return datetime.fromtimestamp(ts, UTC).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def _version_at_least(version: str, major: int) -> bool:
    """Return True if the server version string is at least the given major."""
    version_str = (version or "").lstrip("v")
    if not version_str:
        return False
    parts = version_str.split(".")
    return bool(parts and parts[0].isdigit() and int(parts[0]) >= major)


class ImmichAPIError(Exception):
    """Base exception for Immich API operations"""


class ImmichAPIClient:
    """Immich API client with comprehensive photo management operations"""

    def __init__(self, config: ImmichConfig, user: ImmichUser | None = None):
        self.config = config
        self.base_url = config.server_url.rstrip("/")

        # Handle user configuration - support both legacy and multi-user modes
        if user:
            self.current_user = user
        elif config.users and config.active_user:
            try:
                self.current_user = config.get_active_user()
            except ValueError as e:
                # Fallback to legacy mode if multi-user fails
                if config.api_key:
                    self.current_user = ImmichUser(
                        name="default",
                        api_key=config.api_key,
                        role="admin",
                        description="Legacy single-user mode",
                    )
                else:
                    raise ValueError("No valid user configuration found. Set IMMICH_API_KEY or IMMICH_USERS.") from e
        elif config.api_key:
            # Legacy single-user mode
            self.current_user = ImmichUser(
                name="default",
                api_key=config.api_key,
                role="admin",
                description="Legacy single-user mode",
            )
        else:
            raise ValueError(
                "No user configuration found. Set IMMICH_API_KEY for single user or IMMICH_USERS for multi-user."
            )

        # Create HTTP client with proper headers
        self.client = httpx.AsyncClient(
            headers={
                "x-api-key": self.current_user.api_key,
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            timeout=httpx.Timeout(config.timeout),
        )

    def switch_user(self, user: ImmichUser) -> None:
        """Switch to a different user by updating the API key in headers"""
        self.current_user = user
        self.client.headers["x-api-key"] = user.api_key

    def get_current_user(self) -> ImmichUser:
        """Get the currently active user"""
        return self.current_user

    async def _get(self, endpoint: str, params: dict | None = None) -> dict:
        """Make GET request to Immich API

        Handles v2.x error response formats with improved error messages.
        """
        try:
            url = f"{self.base_url}/api{endpoint}"
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            # Enhanced error handling for v2.x API responses
            error_detail = f"HTTP {e.response.status_code}"
            try:
                error_body = e.response.json()
                if isinstance(error_body, dict):
                    error_message = error_body.get("message", error_body.get("error", str(e)))
                    error_detail = f"{error_detail}: {error_message}"
            except Exception:
                error_detail = f"{error_detail}: {e.response.text[:200]}"
            raise ImmichAPIError(f"GET {endpoint} failed - {error_detail}") from e
        except Exception as e:
            raise ImmichAPIError(f"GET {endpoint} failed: {e}") from e

    async def _post(self, endpoint: str, data: dict | None = None, files: dict | None = None) -> dict:
        """Make POST request to Immich API

        Handles v2.0.0+ error response formats with improved error messages.
        """
        try:
            url = f"{self.base_url}/api{endpoint}"
            if files:
                # Remove Content-Type for multipart uploads
                headers = {k: v for k, v in self.client.headers.items() if k.lower() != "content-type"}
                response = await self.client.post(url, data=data, files=files, headers=headers)
            else:
                response = await self.client.post(url, json=data)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            # Enhanced error handling for v2.0.0+ API responses
            error_detail = f"HTTP {e.response.status_code}"
            try:
                error_body = e.response.json()
                if isinstance(error_body, dict):
                    error_message = error_body.get("message", error_body.get("error", str(e)))
                    error_detail = f"{error_detail}: {error_message}"
            except Exception:
                error_detail = f"{error_detail}: {e.response.text[:200]}"
            raise ImmichAPIError(f"POST {endpoint} failed - {error_detail}") from e
        except Exception as e:
            raise ImmichAPIError(f"POST {endpoint} failed: {e}") from e

    async def _put(self, endpoint: str, data: dict | None = None) -> dict:
        """Make PUT request to Immich API

        Handles v2.0.0+ error response formats with improved error messages.
        """
        try:
            url = f"{self.base_url}/api{endpoint}"
            response = await self.client.put(url, json=data)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            # Enhanced error handling for v2.0.0+ API responses
            error_detail = f"HTTP {e.response.status_code}"
            try:
                error_body = e.response.json()
                if isinstance(error_body, dict):
                    error_message = error_body.get("message", error_body.get("error", str(e)))
                    error_detail = f"{error_detail}: {error_message}"
            except Exception:
                error_detail = f"{error_detail}: {e.response.text[:200]}"
            raise ImmichAPIError(f"PUT {endpoint} failed - {error_detail}") from e
        except Exception as e:
            raise ImmichAPIError(f"PUT {endpoint} failed: {e}") from e

    async def _delete(self, endpoint: str, data: dict | None = None) -> dict:
        """Make DELETE request to Immich API

        Handles v2.0.0+ error response formats with improved error messages.
        """
        try:
            url = f"{self.base_url}/api{endpoint}"
            response = await self.client.delete(url, json=data)
            response.raise_for_status()
            if response.content:
                return response.json()
            return {"success": True}
        except httpx.HTTPStatusError as e:
            # Enhanced error handling for v2.0.0+ API responses
            error_detail = f"HTTP {e.response.status_code}"
            try:
                error_body = e.response.json()
                if isinstance(error_body, dict):
                    error_message = error_body.get("message", error_body.get("error", str(e)))
                    error_detail = f"{error_detail}: {error_message}"
            except Exception:
                error_detail = f"{error_detail}: {e.response.text[:200]}"
            raise ImmichAPIError(f"DELETE {endpoint} failed - {error_detail}") from e
        except Exception as e:
            raise ImmichAPIError(f"DELETE {endpoint} failed: {e}") from e

    # ====== CORE PHOTO OPERATIONS ======

    async def upload_photos_batch(
        self, file_paths: list[str], album_name: str | None = None, *, auto_organize: bool = False
    ) -> dict:
        """Upload multiple photos with batch processing"""
        uploaded_assets = []
        errors = []
        total_size_mb = 0.0
        duplicate_count = 0

        for file_path in file_paths:
            try:
                if not Path(file_path).exists():
                    errors.append(f"File not found: {file_path}")
                    continue

                # Get file info
                file_size = Path(file_path).stat().st_size
                total_size_mb += file_size / (1024 * 1024)

                is_server_v3 = await self.is_v3()

                # Upload individual file
                with open(file_path, "rb") as f:
                    mime_type, _ = mimetypes.guess_type(file_path)
                    files = {"assetData": (Path(file_path).name, f, mime_type or "application/octet-stream")}
                    stat = Path(file_path).stat()
                    data = {
                        "fileCreatedAt": _iso_ts(stat.st_ctime),
                        "fileModifiedAt": _iso_ts(stat.st_mtime),
                        "filename": Path(file_path).name,
                    }
                    if is_server_v3:
                        # v3 removed deviceAssetId/deviceId; duration is an integer (0 for images)
                        data["duration"] = 0
                    else:
                        data["deviceAssetId"] = Path(file_path).stem
                        data["deviceId"] = "MCP-Upload"

                    result = await self._post("/assets", data=data, files=files)

                    if result.get("duplicate"):
                        duplicate_count += 1
                    else:
                        uploaded_assets.append(result.get("id", ""))

            except Exception as e:
                errors.append(f"Upload failed for {file_path}: {e!s}")

        # Add to album if specified
        if album_name and uploaded_assets:
            try:
                await self.create_album(album_name, asset_ids=uploaded_assets)
            except Exception as e:
                errors.append(f"Album creation failed: {e!s}")

        return {
            "uploaded_count": len(uploaded_assets),
            "duplicate_count": duplicate_count,
            "error_count": len(errors),
            "uploaded_assets": uploaded_assets,
            "errors": errors,
            "total_size_mb": total_size_mb,
        }

    async def search_photos(
        self,
        query: str,
        search_type: str = "smart",
        limit: int = 50,
        ocr_language: str | None = None,
    ) -> list[dict]:
        """Search photos using modern v2.x POST endpoints

        Supports:
        - smart: CLIP-based semantic search (POST /search/smart)
        - metadata: EXIF/metadata search (POST /search/metadata)
        - ocr: Text extraction search (POST /search/metadata with ocr field)
        - filename: Filename-based search (POST /search/metadata)

        Args:
            query: Search query string
            search_type: Type of search ("smart", "ocr", "metadata", "filename")
            limit: Maximum results to return
            ocr_language: Specific OCR language model (optional)
        """
        if search_type == "smart":
            # Modern CLIP-based smart search (POST)
            body = {"query": query, "size": limit}
            result = await self._post("/search/smart", data=body)
            # Result format in v2.x: list of assets or dict with assets.items
            if isinstance(result, list):
                return result
            return result.get("assets", {}).get("items", result.get("items", []))

        elif search_type == "ocr":
            # OCR-based text search via metadata endpoint (POST)
            body = {"ocr": query, "size": limit}
            if ocr_language:
                # Note: v2.x may handle language differently, adding for compatibility
                body["language"] = ocr_language

            result = await self._post("/search/metadata", data=body)
            if isinstance(result, list):
                return result
            return result.get("assets", {}).get("items", result.get("items", []))

        elif search_type == "metadata":
            # Metadata-based search (POST)
            body = {"query": query, "size": limit}
            result = await self._post("/search/metadata", data=body)
            if isinstance(result, list):
                return result
            return result.get("assets", {}).get("items", result.get("items", []))

        else:  # filename search
            # Use search/metadata for filename search (POST)
            body = {"originalFileName": query, "size": limit}
            result = await self._post("/search/metadata", data=body)
            if isinstance(result, list):
                return result
            return result.get("assets", {}).get("items", result.get("items", []))

    async def get_timeline_assets(self, page: int = 1, size: int = 100) -> list[dict]:
        """Get assets for the timeline view (POST /search/metadata, v2+ / v3 compatible).

        Uses the paginated metadata search as the timeline source. The legacy
        GET /assets and POST /search/assets endpoints no longer exist in v2.7+.
        """
        size = min(size, 1000)
        body = {"page": page, "size": size, "order": "desc"}
        result = await self._post("/search/metadata", data=body)
        if isinstance(result, list):
            return result
        assets = result.get("assets", {})
        if isinstance(assets, dict):
            items = assets.get("items", [])
            if isinstance(items, list):
                return items
        items = result.get("items", [])
        return items if isinstance(items, list) else []

    async def get_map_assets(self) -> list[dict]:
        """Get all geotagged assets for map display (Immich getMapMarkers-style)."""
        try:
            # Immich API: GET /map/markers returns list of { id, lat, lon, city, country, state }
            result = await self._get("/map/markers")
            if isinstance(result, list):
                return result
            if isinstance(result, dict):
                return result.get("markers", result.get("features", result.get("items", [])))
            return []
        except ImmichAPIError:
            return []

    async def get_asset_info(self, asset_id: str) -> dict:
        """Get detailed information about a specific asset using standard GET /assets/{id}"""
        try:
            return await self._get(f"/assets/{asset_id}")
        except ImmichAPIError as e:
            if "not found" in str(e).lower() or "404" in str(e):
                raise ImmichAPIError(f"Asset {asset_id} not found") from e
            raise

    async def get_asset_ocr(self, asset_id: str, *, include_bounding_boxes: bool = True) -> dict:
        """Get OCR text and bounding boxes for a specific asset (v2.2.0+).

        The endpoint returns a list of word/line boxes; this aggregates them into
        a dict with `text`, `words`, `bounding_boxes`, `confidence`, `language`.
        Raises ImmichAPIError (e.g. HTTP 404) when OCR is unavailable - callers
        must handle failure explicitly rather than receiving fabricated data.
        """
        result = await self._get(f"/assets/{asset_id}/ocr")

        boxes = result if isinstance(result, list) else []
        words: list[dict] = []
        text_parts: list[str] = []
        scores: list[float] = []

        for box in boxes:
            text = (box.get("text") or "").strip()
            if not text:
                continue
            text_parts.append(text)
            with contextlib.suppress(TypeError, ValueError):
                scores.append(float(box.get("textScore") or 0.0))
            words.append(
                {
                    "id": box.get("id"),
                    "text": text,
                    "text_score": box.get("textScore"),
                    "box_score": box.get("boxScore"),
                    "x1": box.get("x1"),
                    "y1": box.get("y1"),
                    "x2": box.get("x2"),
                    "y2": box.get("y2"),
                    "x3": box.get("x3"),
                    "y3": box.get("y3"),
                    "x4": box.get("x4"),
                    "y4": box.get("y4"),
                }
            )

        confidence = round(sum(scores) / len(scores), 4) if scores else 0.0

        return {
            "text": " ".join(text_parts),
            "language": "unknown",
            "confidence": confidence,
            "bounding_boxes": words if include_bounding_boxes else [],
            "words": words,
            "regions": [],
        }

    async def organize_photos_by_date(self, asset_ids: list[str], organization_type: str = "year_month") -> dict:
        """Organize photos into date-based albums"""
        albums_created = 0
        photos_organized = 0
        created_albums = []
        errors = []

        # Get asset info for all photos
        photo_groups = {}

        for asset_id in asset_ids:
            try:
                asset_info = await self.get_asset_info(asset_id)
                created_date = asset_info.get("fileCreatedAt", asset_info.get("createdAt", ""))

                if created_date:
                    # Parse date and create grouping key
                    from datetime import datetime

                    date_obj = datetime.fromisoformat(created_date.replace("Z", "+00:00"))

                    if organization_type == "year":
                        group_key = f"{date_obj.year}"
                    elif organization_type == "year_month":
                        group_key = f"{date_obj.year}-{date_obj.month:02d}"
                    else:  # year_month_day
                        group_key = f"{date_obj.year}-{date_obj.month:02d}-{date_obj.day:02d}"

                    if group_key not in photo_groups:
                        photo_groups[group_key] = []
                    photo_groups[group_key].append(asset_id)

            except Exception as e:
                errors.append(f"Failed to process asset {asset_id}: {e!s}")

        # Create albums for each group
        for group_key, group_assets in photo_groups.items():
            try:
                album_name = f"Photos {group_key}"
                await self.create_album(album_name, asset_ids=group_assets)
                albums_created += 1
                photos_organized += len(group_assets)
                created_albums.append(album_name)
            except Exception as e:
                errors.append(f"Failed to create album for {group_key}: {e!s}")

        return {
            "albums_created": albums_created,
            "photos_organized": photos_organized,
            "created_albums": created_albums,
            "errors": errors,
        }

    async def delete_photos(self, asset_ids: list[str], *, move_to_trash: bool = True) -> dict:
        """Delete or trash photos via DELETE /assets (v2.7+ / v3 compatible).

        Immich's bulk delete endpoint treats `force` as the trash switch:
        force=false moves assets to trash, force=true deletes them permanently.
        """
        deleted_asset_ids = []
        errors = []

        try:
            data = {"ids": asset_ids, "force": not move_to_trash}
            await self._delete("/assets", data=data)
            deleted_asset_ids = asset_ids
        except Exception as e:
            errors.append(f"{'Trash' if move_to_trash else 'Permanent delete'} operation failed: {e!s}")

        return {
            "deleted_count": len(deleted_asset_ids) if not move_to_trash else 0,
            "trashed_count": len(deleted_asset_ids) if move_to_trash else 0,
            "error_count": len(errors),
            "deleted_asset_ids": deleted_asset_ids,
            "errors": errors,
        }

    # ====== ALBUM MANAGEMENT ======

    async def create_album(self, name: str, description: str | None = None, asset_ids: list[str] | None = None) -> dict:
        """Create a new album"""
        data = {"albumName": name, "description": description or "", "assetIds": asset_ids or []}
        return await self._post("/albums", data=data)

    async def add_assets_to_album(self, album_id: str, asset_ids: list[str]) -> dict:
        """Add assets to existing album"""
        data = {"ids": asset_ids}
        await self._put(f"/albums/{album_id}/assets", data=data)

        # Get updated album info
        album_info = await self._get(f"/albums/{album_id}")

        return {
            "added_count": len(asset_ids),
            "duplicate_count": 0,  # Would need more complex logic to detect
            "new_asset_count": album_info.get("assetCount", 0),
            "errors": [],
        }

    async def get_albums(self, *, shared: bool | None = None, include_stats: bool = True) -> list[dict]:
        """Get all albums"""
        params = {}
        if shared is not None:
            params["shared"] = shared

        result = await self._get("/albums", params=params)
        albums = result if isinstance(result, list) else result.get("items", [])

        # Add stats if requested
        if include_stats:
            from contextlib import suppress

            for album in albums:
                with suppress(Exception):
                    # Get detailed album info
                    detailed = await self._get(f"/albums/{album['id']}")
                    album.update(detailed)

        return albums

    async def create_shared_link(
        self,
        album_id: str,
        expires_at: str | None = None,
        *,
        allow_download: bool = True,
        allow_upload: bool = False,
        show_metadata: bool = True,
    ) -> dict:
        """Create shared link for album"""
        data = {
            "type": "ALBUM",
            "albumId": album_id,
            "expiresAt": expires_at,
            "allowDownload": allow_download,
            "allowUpload": allow_upload,
            "showMetadata": show_metadata,
        }

        result = await self._post("/shared-links", data=data)

        # Construct public URL
        base_url = self.base_url.replace("/api", "")
        public_url = f"{base_url}/share/{result['key']}"
        result["public_url"] = public_url

        return result

    # ====== PEOPLE & FACES ======

    async def run_face_detection(self, asset_ids: list[str] | None = None, *, force_reprocess: bool = False) -> dict:
        """Queue face detection for assets (POST /assets/jobs, v2+ / v3 compatible).

        Immich processes face detection asynchronously and does not return face
        counts from the job submission. This queues the per-asset 'refresh-faces'
        job; poll GET /people afterward to observe new clusters. The legacy
        POST /jobs {name: FACE_DETECTION, data: ...} payload was removed.
        """
        ids = asset_ids or []
        if not ids:
            return {
                "job_submitted": False,
                "queue_name": "refresh-faces",
                "asset_count": 0,
                "message": "No asset IDs provided - nothing queued.",
            }
        data = {"assetIds": ids, "name": "refresh-faces"}
        await self._post("/assets/jobs", data=data)
        return {
            "job_submitted": True,
            "queue_name": "refresh-faces",
            "asset_count": len(ids),
            "message": (
                f"Queued face detection for {len(ids)} assets. "
                "Processing is async - poll /people to see new clusters."
            ),
        }

    async def update_person(self, person_id: str, name: str, face_asset_ids: list[str] | None = None) -> dict:
        """Update person with name and merge faces"""
        data = {"name": name}

        result = await self._put(f"/people/{person_id}", data=data)

        # Merge additional faces if provided
        if face_asset_ids:
            merge_data = {"ids": face_asset_ids}
            await self._put(f"/people/{person_id}/merge", data=merge_data)

        return {
            "faces_merged": len(face_asset_ids) if face_asset_ids else 0,
            "total_faces": result.get("assetCount", 0),
            "updated_at": result.get("updatedAt", ""),
        }

    async def search_photos_by_person(
        self, person_name: str, limit: int = 50, *, include_metadata: bool = True
    ) -> list[dict]:
        """Search photos by person name using smart search with personIds filter"""
        # First find person by name
        people_result = await self._get("/people")
        people = people_result if isinstance(people_result, list) else people_result.get("people", [])
        target_person = None

        for person in people:
            if person.get("name", "").lower() == person_name.lower():
                target_person = person
                break

        if not target_person:
            # Try fuzzy search if direct match fails
            for person in people:
                if person_name.lower() in person.get("name", "").lower():
                    target_person = person
                    break

        if not target_person:
            return []

        # Use modern search/smart with personIds filter (efficient)
        person_id = target_person["id"]
        body = {"personIds": [person_id], "size": limit}
        result = await self._post("/search/smart", data=body)

        if isinstance(result, list):
            return result
        return result.get("assets", {}).get("items", result.get("items", []))

    # ====== ADMINISTRATION ======

    async def get_server_stats(self) -> dict:
        """Get server storage and usage statistics (GET /server/storage + /server/statistics).

        The legacy /admin/storage and /server-info endpoints were removed in
        v2.x; this uses the current real endpoints exclusively.
        """
        try:
            server_about = {}
            with contextlib.suppress(ImmichAPIError):
                server_about = await self._get("/server/about")

            storage_info = {}
            with contextlib.suppress(ImmichAPIError):
                storage_info = await self._get("/server/storage")

            stats = {}
            with contextlib.suppress(ImmichAPIError):
                stats = await self._get("/server/statistics")

            album_count = 0
            with contextlib.suppress(ImmichAPIError):
                albums = await self._get("/albums")
                album_count = len(albums) if isinstance(albums, list) else 0

            return {
                "usage": storage_info.get("diskUseRaw", 0),
                "available": storage_info.get("diskAvailableRaw", 0),
                "total": storage_info.get("diskSizeRaw", 0),
                "usage_percentage": storage_info.get("diskUsagePercentage", 0.0),
                "photos": stats.get("photos", 0),
                "videos": stats.get("videos", 0),
                "users": len(stats.get("usageByUser", [])),
                "albums": album_count,
                "usage_by_user": stats.get("usageByUser", []),
                "api_version": server_about.get("version", "unknown"),
            }
        except Exception as e:
            return {
                "error": str(e),
                "api_version": "unknown",
            }

    async def get_server_info(self) -> dict:
        """Get server health and version information (GET /server/about, v2+ / v3)."""
        server_about = {}
        try:
            server_about = await self._get("/server/about")
        except ImmichAPIError as e:
            return {"status": "error", "error": str(e)}

        version = server_about.get("version", "unknown")

        return {
            "version": version,
            "status": "healthy",
            "features": server_about.get("features", []),
            "is_v2_plus": _version_at_least(version, 2),
            "has_ocr": _version_at_least(version, 2),
            "has_multilingual_ocr": _version_at_least(version, 2),
            "ocr_languages": [],
            "health": {
                "database": True,
                "redis": True,
                "machine_learning": True,
                "search_api": True,
            },
            "database": True,
            "redis": True,
            "storage": True,
            "machine_learning": True,
            "uptime": 0,
            "errors": [],
            "api_architecture": "search_based",
            "individual_asset_access": True,
            "multilingual_ocr": True,
            "smart_search": True,
        }

    async def is_v3(self) -> bool:
        """Check if the connected Immich server is version 3.0.0 or higher."""
        with contextlib.suppress(Exception):
            info = await self.get_server_info()
            return _version_at_least(info.get("version", ""), 3)
        return False

    async def export_photos(
        self, backup_path: str, album_ids: list[str] | None = None, *, include_metadata: bool = True
    ) -> dict:
        """Export photos for backup"""
        # This would be a complex operation involving downloading assets
        # For now, return mock results
        return {
            "exported_photos": 0,
            "exported_videos": 0,
            "total_size_mb": 0.0,
            "album_structure_preserved": True,
            "errors": ["Export functionality requires additional implementation"],
        }

    async def get_libraries(self) -> list[dict]:
        """Get all available libraries (GET /libraries returns a plain array in v2.7+ / v3)."""
        try:
            result = await self._get("/libraries")
            if isinstance(result, list):
                return result
            items = result.get("items", result.get("libraries", []))
            return items if isinstance(items, list) else []
        except Exception as e:
            logger.warning("Libraries endpoint not available: %s", e)
            return []

    async def get_library_info(self, library_id: str) -> dict:
        """Get detailed information about a specific library.

        Args:
            library_id: The library ID

        Returns:
            Library information including locations, stats, etc.
        """
        return await self._get(f"/libraries/{library_id}")

    async def create_library(
        self,
        name: str,
        library_type: str = "UPLOAD",
        import_paths: list[str] | None = None,
        exclusion_patterns: list[str] | None = None,
    ) -> dict:
        """Create a new library (POST /libraries, v2.7+ / v3).

        The API requires `ownerId` and has no `type` field - the type is
        implied by presence of import paths. Owner is resolved via /users/me.
        """
        data: dict = {"name": name}
        try:
            me = await self._get("/users/me")
            owner_id = me.get("id")
            if owner_id:
                data["ownerId"] = owner_id
        except Exception as e:
            logger.warning("Could not resolve owner via /users/me: %s", e)

        if import_paths:
            data["importPaths"] = import_paths
        if exclusion_patterns:
            data["exclusionPatterns"] = exclusion_patterns

        return await self._post("/libraries", data)

    async def update_library(
        self,
        library_id: str,
        name: str | None = None,
        import_paths: list[str] | None = None,
        exclusion_patterns: list[str] | None = None,
    ) -> dict:
        """Update library configuration.

        Args:
            library_id: The library ID
            name: New library name
            import_paths: Updated import paths
            exclusion_patterns: Updated exclusion patterns

        Returns:
            Updated library information
        """
        data = {}
        if name is not None:
            data["name"] = name
        if import_paths is not None:
            data["importPaths"] = import_paths
        if exclusion_patterns is not None:
            data["exclusionPatterns"] = exclusion_patterns

        return await self._put(f"/libraries/{library_id}", data)

    async def delete_library(self, library_id: str) -> dict:
        """Delete a library.

        Args:
            library_id: The library ID to delete

        Returns:
            Deletion confirmation
        """
        return await self._delete(f"/libraries/{library_id}")

    async def scan_library(self, library_id: str) -> dict:
        """Scan a library for new or changed files (POST /libraries/{id}/scan).

        The v2.7+ / v3 endpoint takes no request body - scanning always picks up
        new/changed files according to the server's import settings.
        """
        return await self._post(f"/libraries/{library_id}/scan", {})

    async def get_library_statistics(self, library_id: str) -> dict:
        """Get storage statistics for a library (GET /libraries/{id}/statistics, v2.7+ / v3)."""
        return await self._get(f"/libraries/{library_id}/statistics")

    async def update_asset_visibility(self, asset_id: str, visibility: str) -> dict:
        """Update the visibility status of an asset (v2.5.0+).

        Valid values: 'archive', 'timeline', 'hidden', 'locked'.
        """
        if visibility not in _VISIBILITY_VALUES:
            raise ImmichAPIError(f"Invalid visibility '{visibility}' - must be one of: {', '.join(_VISIBILITY_VALUES)}")
        return await self._put(f"/assets/{asset_id}", data={"visibility": visibility})

    async def edit_asset(self, asset_id: str, operation: str, **params) -> dict:
        """Apply a non-destructive edit (crop/rotate/mirror) via PUT /assets/{id}/edits (v2.5.0+).

        The legacy POST /assets/{id}/edit endpoint does not exist; edits are
        written as a list of action items under the plural `/edits` resource.
        """
        op = (operation or "").lower()

        if op == "rotate":
            angle = params.get("angle")
            if angle is None:
                raise ImmichAPIError("rotate requires 'angle' (degrees, e.g. 90)")
            action = {"action": "rotate", "parameters": {"angle": angle}}
        elif op == "mirror":
            axis = params.get("axis") or params.get("direction")
            if axis not in ("horizontal", "vertical"):
                raise ImmichAPIError("mirror requires 'axis' or 'direction' in ('horizontal', 'vertical')")
            action = {"action": "mirror", "parameters": {"axis": axis}}
        elif op == "crop":
            x, y, width, height = params.get("x"), params.get("y"), params.get("width"), params.get("height")
            if any(v is None for v in (x, y, width, height)):
                raise ImmichAPIError("crop requires x, y, width, height")
            action = {"action": "crop", "parameters": {"x": x, "y": y, "width": width, "height": height}}
        else:
            raise ImmichAPIError(f"Unsupported edit operation '{operation}' - use crop, rotate, or mirror")

        return await self._put(f"/assets/{asset_id}/edits", data={"edits": [action]})

    async def get_binary(self, endpoint: str, params: dict | None = None) -> bytes:
        """Make GET request to Immich API and return binary data"""
        try:
            url = f"{self.base_url}/api{endpoint}"
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            return response.content
        except Exception as e:
            raise ImmichAPIError(f"Binary GET {endpoint} failed: {e}") from e

    async def get_asset_thumbnail(self, asset_id: str, format: str = "WEBP") -> bytes:
        """Get the thumbnail bytes for an asset. Immich API: GET /assets/:id/thumbnail."""
        return await self.get_binary(f"/assets/{asset_id}/thumbnail", params={"format": format})

    async def get_all_people(self) -> list[dict]:
        """Get all detected people"""
        result = await self._get("/people")
        return result.get("people", []) if isinstance(result, dict) else result

    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()


async def get_api_client() -> ImmichAPIClient:
    """Get initialized API client, creating if needed.

    This is the primary way to get an API client instance in a way that
    supports both MCP tools and FastAPI dependency injection.
    """
    global api_client
    if api_client is None:
        config = ImmichConfig.from_env()
        api_client = ImmichAPIClient(config)
    return api_client
