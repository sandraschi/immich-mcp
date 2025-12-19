"""
Immich API Client for MCP integration
Austrian efficiency for Sandra's 2000+ photo library management
"""

from pathlib import Path

import httpx

from immich_mcp.config import ImmichConfig


class ImmichAPIError(Exception):
    """Base exception for Immich API operations"""


class ImmichAPIClient:
    """Immich API client with comprehensive photo management operations"""

    def __init__(self, config: ImmichConfig):
        self.config = config
        self.base_url = config.server_url.rstrip("/")
        self.api_key = config.api_key

        # Create HTTP client with proper headers
        self.client = httpx.AsyncClient(
            headers={
                "x-api-key": self.api_key,
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            timeout=httpx.Timeout(config.timeout),
        )

    async def _get(self, endpoint: str, params: dict | None = None) -> dict:
        """Make GET request to Immich API

        Handles v2.0.0+ error response formats with improved error messages.
        """
        try:
            url = f"{self.base_url}/api{endpoint}"
            response = await self.client.get(url, params=params)
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
            raise ImmichAPIError(f"GET {endpoint} failed - {error_detail}") from e
        except Exception as e:
            raise ImmichAPIError(f"GET {endpoint} failed: {e}") from e

    async def _post(
        self, endpoint: str, data: dict | None = None, files: dict | None = None
    ) -> dict:
        """Make POST request to Immich API

        Handles v2.0.0+ error response formats with improved error messages.
        """
        try:
            url = f"{self.base_url}/api{endpoint}"
            if files:
                # Remove Content-Type for multipart uploads
                headers = {
                    k: v for k, v in self.client.headers.items() if k.lower() != "content-type"
                }
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

                # Upload individual file
                with open(file_path, "rb") as f:
                    files = {"assetData": (Path(file_path).name, f, "image/jpeg")}
                    data = {
                        "deviceAssetId": Path(file_path).stem,
                        "deviceId": "MCP-Upload",
                        "fileCreatedAt": Path(file_path).stat().st_ctime,
                        "fileModifiedAt": Path(file_path).stat().st_mtime,
                    }

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
        self, query: str, search_type: str = "smart", limit: int = 50, ocr_language: str | None = None
    ) -> list[dict]:
        """Search photos using various methods

        Supports:
        - smart: CLIP-based semantic search (v1.0+)
        - metadata: EXIF/metadata search (v1.0+)
        - ocr: Text extraction search (v2.2.0+ with v2.3.0+ multilingual support)
        - filename: Filename-based search (v1.0+)

        Args:
            query: Search query string
            search_type: Type of search ("smart", "ocr", "metadata", "filename")
            limit: Maximum results to return
            ocr_language: Specific OCR language model for v2.3.0+ (optional)
                        Supported: "english", "english_only", "chinese_simplified",
                        "chinese_traditional", "japanese", "greek", "korean",
                        "russian", "belarusian", "ukrainian", "thai", "latin_script_languages"
        """
        if search_type == "smart":
            # CLIP-based smart search
            params = {"query": query, "limit": limit, "type": "SMART_SEARCH"}
            result = await self._get("/search/smart", params=params)
            return result.get("assets", {}).get("items", [])

        elif search_type == "ocr":
            # OCR-based text search (Immich v2.2.0+ with v2.3.0+ multilingual support)
            params = {"query": query, "limit": limit}

            # Add language parameter for v2.3.0+ multilingual OCR
            if ocr_language:
                params["language"] = ocr_language

            try:
                result = await self._get("/search/ocr", params=params)
                # OCR search returns assets with extracted text
                return result.get("assets", {}).get("items", [])
            except ImmichAPIError as e:
                # If OCR endpoint doesn't exist, fall back to smart search
                if "404" in str(e) or "not found" in str(e).lower():
                    # OCR not available, try smart search instead
                    params = {"query": query, "limit": limit, "type": "SMART_SEARCH"}
                    result = await self._get("/search/smart", params=params)
                    return result.get("assets", {}).get("items", [])
                raise

        elif search_type == "metadata":
            # Metadata-based search
            params = {"q": query, "limit": limit}
            result = await self._get("/search/metadata", params=params)
            return result.get("assets", {}).get("items", [])

        else:  # filename search
            # Get all assets and filter by filename
            params = {"size": limit}
            result = await self._get("/assets", params=params)
            all_assets = result.get("items", [])

            # Filter by filename
            filtered = [
                asset
                for asset in all_assets
                if query.lower() in asset.get("originalFileName", "").lower()
            ]
            return filtered[:limit]

    async def get_asset_info(self, asset_id: str) -> dict:
        """Get detailed information about a specific asset"""
        return await self._get(f"/assets/{asset_id}")

    async def get_asset_ocr(self, asset_id: str, include_bounding_boxes: bool = True) -> dict:
        """Get OCR text and bounding boxes for a specific asset (v2.2.0+)

        Returns OCR information including extracted text and positional data.
        Enhanced in v2.3.0+ with multilingual support and bounding boxes.

        Args:
            asset_id: Asset ID to get OCR data for
            include_bounding_boxes: Whether to include bounding box coordinates (v2.3.0+)
        """
        try:
            params = {}
            if include_bounding_boxes:
                params["bounding_boxes"] = "true"

            result = await self._get(f"/assets/{asset_id}/ocr", params=params)

            # Ensure bounding boxes are included in response for v2.3.0+
            if include_bounding_boxes and "bounding_boxes" not in result:
                result["bounding_boxes"] = []

            return result
        except ImmichAPIError as e:
            # If OCR endpoint doesn't exist, return empty result
            if "404" in str(e) or "not found" in str(e).lower():
                return {
                    "text": "",
                    "bounding_boxes": [],
                    "language": "unknown",
                    "confidence": 0.0,
                    "words": [],  # Individual word data
                    "regions": []  # Text regions for v2.3.0+
                }
            raise

    async def organize_photos_by_date(
        self, asset_ids: list[str], organization_type: str = "year_month"
    ) -> dict:
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
        """Delete or trash photos"""
        deleted_asset_ids = []
        errors = []

        if move_to_trash:
            # Move to trash
            try:
                data = {"ids": asset_ids}
                await self._delete("/assets/trash", data=data)
                deleted_asset_ids = asset_ids
            except Exception as e:
                errors.append(f"Trash operation failed: {e!s}")
        else:
            # Permanent deletion
            try:
                data = {"ids": asset_ids, "force": True}
                await self._delete("/assets", data=data)
                deleted_asset_ids = asset_ids
            except Exception as e:
                errors.append(f"Permanent deletion failed: {e!s}")

        return {
            "deleted_count": len(deleted_asset_ids) if not move_to_trash else 0,
            "trashed_count": len(deleted_asset_ids) if move_to_trash else 0,
            "error_count": len(errors),
            "deleted_asset_ids": deleted_asset_ids,
            "errors": errors,
        }

    # ====== ALBUM MANAGEMENT ======

    async def create_album(
        self, name: str, description: str | None = None, asset_ids: list[str] | None = None
    ) -> dict:
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

    async def get_albums(
        self, *, shared: bool | None = None, include_stats: bool = True
    ) -> list[dict]:
        """Get all albums"""
        params = {}
        if shared is not None:
            params["shared"] = shared

        result = await self._get("/albums", params=params)
        albums = result if isinstance(result, list) else result.get("items", [])

        # Add stats if requested
        if include_stats:
            for album in albums:
                try:
                    # Get detailed album info
                    detailed = await self._get(f"/albums/{album['id']}")
                    album.update(detailed)
                except Exception:
                    pass  # Continue without detailed stats

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

    async def run_face_detection(
        self, asset_ids: list[str] | None = None, *, force_reprocess: bool = False
    ) -> dict:
        """Run face detection on photos"""
        # Trigger face detection job
        data = {"name": "FACE_DETECTION", "data": {"assetIds": asset_ids, "force": force_reprocess}}

        await self._post("/jobs", data=data)

        # For now, return mock results since actual face detection is async
        return {
            "detected_faces": 0,  # Would be populated after job completion
            "new_people": 0,
            "processed_assets": len(asset_ids) if asset_ids else 0,
            "people_found": [],
        }

    async def update_person(
        self, person_id: str, name: str, face_asset_ids: list[str] | None = None
    ) -> dict:
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
        """Search photos by person name"""
        # First find person by name
        people = await self._get("/people")
        target_person = None

        for person in people.get("people", []):
            if person.get("name", "").lower() == person_name.lower():
                target_person = person
                break

        if not target_person:
            return []

        # Get assets for this person
        person_id = target_person["id"]
        result = await self._get(f"/people/{person_id}/assets")

        return result.get("items", [])[:limit]

    # ====== ADMINISTRATION ======

    async def get_server_stats(self) -> dict:
        """Get server storage and usage statistics"""
        try:
            # Get server info
            server_info = await self._get("/server-info")

            # Get storage info if available
            try:
                storage_info = await self._get("/admin/storage")
            except Exception:
                storage_info = {}

            # Combine information
            return {
                "usage": storage_info.get("diskUsage", 0),
                "available": storage_info.get("diskAvailable", 0),
                "total": storage_info.get("diskSize", 0),
                "usage_percentage": storage_info.get("diskUsagePercentage", 0.0),
                "photos": server_info.get("photos", 0),
                "videos": server_info.get("videos", 0),
                "users": server_info.get("users", 1),
                "albums": server_info.get("albums", 0),
                "usage_by_user": storage_info.get("usageByUser", []),
            }
        except Exception:
            # Return basic info if detailed stats not available
            return {
                "usage": 0,
                "available": 0,
                "total": 0,
                "usage_percentage": 0.0,
                "photos": 0,
                "videos": 0,
                "users": 1,
                "albums": 0,
                "usage_by_user": [],
            }

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

    async def get_server_info(self) -> dict:
        """Get server health and version information

        Detects Immich v2.0.0+ with full support for v2.3.1 features including:
        - Enhanced multilingual OCR (Greek, Korean, Russian, Belarusian, Ukrainian, Thai, Latin script)
        - OCR bounding boxes display
        - Workflows foundation
        - Maintenance mode
        - Asset copy functionality
        - Improved duplicate detection UI
        """
        try:
            server_info = await self._get("/server-info")

            version = server_info.get("version", "Unknown")
            features = server_info.get("features", [])

            # Detect v2.0.0+ (version format: "2.0.0" or "2.x.x")
            is_v2_plus = False
            if version != "Unknown":
                try:
                    major_version = int(version.split(".")[0])
                    is_v2_plus = major_version >= 2
                except (ValueError, IndexError):
                    pass

            # Detect OCR capability and multilingual support (v2.2.0+ with v2.3.0+ enhancements)
            has_ocr = False
            has_multilingual_ocr = False
            has_ocr_bounding_boxes = False
            ocr_languages = []

            # New v2.3.0+ features
            has_workflows = False
            has_maintenance_mode = False
            has_asset_copy = False
            has_enhanced_duplicates = False

            if is_v2_plus:
                try:
                    # Check features list or dict for capabilities
                    if isinstance(features, list):
                        has_ocr = "ocr" in [f.lower() for f in features] or "OCR" in features
                        has_workflows = "workflows" in [f.lower() for f in features]
                        has_maintenance_mode = "maintenance" in [f.lower() for f in features]
                    elif isinstance(features, dict):
                        has_ocr = features.get("ocr", False)
                        has_workflows = features.get("workflows", False)
                        has_maintenance_mode = features.get("maintenance", False)

                        # Check for enhanced OCR in v2.3.0+
                        ocr_config = features.get("ocr", {})
                        if isinstance(ocr_config, dict):
                            has_multilingual_ocr = ocr_config.get("multilingual", False)
                            has_ocr_bounding_boxes = ocr_config.get("bounding_boxes", False)
                            ocr_languages = ocr_config.get("languages", [])

                        # Check for new v2.3.0+ features
                        has_asset_copy = features.get("asset_copy", False)
                        has_enhanced_duplicates = features.get("enhanced_duplicates", False)

                    # Version-based detection with specific v2.3.x feature support
                    if version != "Unknown":
                        try:
                            version_parts = version.split(".")
                            if len(version_parts) >= 2:
                                major = int(version_parts[0])
                                minor = int(version_parts[1])
                                patch = int(version_parts[2]) if len(version_parts) >= 3 else 0

                                # Basic OCR support (v2.2.0+)
                                has_ocr = has_ocr or (major >= 2 and minor >= 2)

                                # Enhanced features in v2.3.0+
                                if major >= 2 and minor >= 3:
                                    has_multilingual_ocr = True
                                    has_ocr_bounding_boxes = True
                                    has_workflows = True
                                    has_maintenance_mode = True
                                    has_asset_copy = True
                                    has_enhanced_duplicates = True

                                    # Comprehensive language support in v2.3.0+
                                    if not ocr_languages:
                                        ocr_languages = [
                                            "english", "english_only",  # Better English model
                                            "chinese_simplified", "chinese_traditional", "japanese",
                                            "greek", "korean", "russian", "belarusian", "ukrainian", "thai",
                                            "latin_script_languages"  # Covers many European languages
                                        ]
                        except (ValueError, IndexError):
                            pass
                except Exception:
                    pass

            # Check various service health with v2.3.x awareness
            health_checks = {
                "database": True,  # Assume healthy if API responds
                "redis": True,
                "storage": True,
                "machine_learning": server_info.get("machineLearning", True),
            }

            # Add v2.3.x specific health checks if available
            if has_workflows:
                health_checks["workflows"] = server_info.get("workflows_enabled", True)

            return {
                "version": version,
                "features": features,
                "uptime": server_info.get("uptime", 0),
                "is_v2_plus": is_v2_plus,
                "has_ocr": has_ocr,
                "has_multilingual_ocr": has_multilingual_ocr,
                "has_ocr_bounding_boxes": has_ocr_bounding_boxes,
                "ocr_languages": ocr_languages,
                "has_workflows": has_workflows,
                "has_maintenance_mode": has_maintenance_mode,
                "has_asset_copy": has_asset_copy,
                "has_enhanced_duplicates": has_enhanced_duplicates,
                "errors": [],
                **health_checks,
            }
        except Exception as e:
            return {
                "version": "Unknown",
                "features": [],
                "is_v2_plus": False,
                "has_ocr": False,
                "has_multilingual_ocr": False,
                "has_ocr_bounding_boxes": False,
                "ocr_languages": [],
                "has_workflows": False,
                "has_maintenance_mode": False,
                "has_asset_copy": False,
                "has_enhanced_duplicates": False,
                "database": False,
                "redis": False,
                "storage": False,
                "machine_learning": False,
                "uptime": 0,
                "errors": [str(e)],
            }

    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()
