"""
FastMCP 3.1 API routes for ImmichMCP.

FastAPI router with all v1 API endpoints (health, users, thumbnails, system).
"""

import asyncio
import logging
import os

import httpx
from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel

from ...immich_api import ImmichAPIClient, ImmichAPIError, get_api_client

router = APIRouter(tags=["v1"])
logger = logging.getLogger(__name__)


class ChatRequest(BaseModel):
    message: str
    provider: str = "ollama"
    model: str = "llama3.3"


_PROVIDER_BASES = {
    "ollama": "http://localhost:11434/v1",
    "lm-studio": "http://localhost:1234/v1",
    "openrouter": "https://openrouter.ai/api/v1",
}

_CHAT_SYSTEM_PROMPT = (
    "You are the Immich photo library assistant. You help with photo organization, "
    "searching, albums, metadata, people/faces, and library management for the user's "
    "Immich server (photo library). Answer concisely and practically. If a task requires "
    "specific photo data, explain what the user can do in the app or ask for the photo/album "
    "details you need."
)


@router.post("/chat")
async def chat_with_immich(request: ChatRequest):
    """Handle chat requests from the webapp by calling the selected LLM provider."""
    base = _PROVIDER_BASES.get(request.provider)
    if not base:
        return {
            "success": False,
            "error": f"Unknown provider '{request.provider}'",
            "suggestions": ["Use 'ollama' or 'lm-studio'"],
        }
    url = f"{base}/chat/completions"
    headers = {"Content-Type": "application/json"}
    if request.provider == "openrouter":
        api_key = os.environ.get("OPENROUTER_API_KEY", "")
        if not api_key:
            return {
                "success": False,
                "error": "OPENROUTER_API_KEY not set in .env",
                "suggestions": ["Set OPENROUTER_API_KEY or switch to a local provider"],
            }
        headers["Authorization"] = f"Bearer {api_key}"
    payload = {
        "model": request.model,
        "messages": [
            {"role": "system", "content": _CHAT_SYSTEM_PROMPT},
            {"role": "user", "content": request.message},
        ],
        "temperature": 0.3,
        "max_tokens": 512,
    }
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(90.0, connect=5.0)) as client:
            resp = await client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
        content = data["choices"][0]["message"]["content"]
        return {"success": True, "response": content, "debug": {"provider": request.provider, "model": request.model}}
    except httpx.HTTPStatusError as e:
        return {
            "success": False,
            "error": f"Provider returned HTTP {e.response.status_code}",
            "suggestions": ["Check that the model name exists on the provider", "Try a different model"],
        }
    except httpx.ConnectError:
        return {
            "success": False,
            "error": f"Cannot reach {request.provider} at {base}. Is the local LLM running?",
            "suggestions": ["Start Ollama or LM Studio", "Check the provider URL in Settings"],
        }
    except (httpx.TimeoutException, httpx.ReadTimeout):
        return {
            "success": False,
            "error": f"{request.provider} timed out generating a response.",
            "suggestions": ["Use a smaller/faster model", "Try again"],
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.get("/health")
async def health_check():
    """Health check for FastMCP 3.1 / webapp."""
    return {"status": "ok", "version": "1.0.0"}


# ===== USER MANAGEMENT ENDPOINTS =====


@router.get("/users")
async def get_users():
    """Get list of configured Immich users."""
    try:
        from ...server import config

        if not config:
            return {"users": [], "active_user": None}

        users_list = [{"name": k, "role": v.role, "description": v.description} for k, v in config.users.items()]
        return {"users": users_list, "active_user": config.active_user}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


class UserSwitchRequest(BaseModel):
    username: str


@router.post("/users/active")
async def set_active_user(request: UserSwitchRequest):
    """Switch the active user for Immich API operations."""
    try:
        from ...server import config, mcp

        if not config or not mcp.immich_client:
            raise HTTPException(status_code=500, detail="Server not fully initialized")

        user = config.switch_user(request.username)
        mcp.immich_client.switch_user(user)
        return {"success": True, "active_user": request.username}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/people/{person_id}/thumbnail")
async def get_person_thumbnail(person_id: str):
    """Proxy for person thumbnails."""
    try:
        from ...server import mcp

        content = await mcp.immich_client.get_binary(f"/person/{person_id}/thumbnail")
        return Response(content=content, media_type="image/webp")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/photos/{asset_id}/thumbnail")
async def get_photo_thumbnail(asset_id: str):
    """Proxy for photo thumbnails."""
    try:
        from ...server import mcp

        content = await mcp.immich_client.get_asset_thumbnail(asset_id)
        return Response(content=content, media_type="image/webp")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/people")
async def get_people():
    """Get list of detected people."""
    try:
        from ...server import mcp

        if not mcp.immich_client:
            raise HTTPException(
                status_code=503,
                detail=(
                    "Immich client not initialized. Check .env (IMMICH_SERVER_URL, IMMICH_API_KEY) "
                    "and restart the backend."
                ),
            )
        people = await mcp.immich_client.get_all_people()
        return people
    except ImmichAPIError as e:
        raise _immich_error_to_http(e) from e
    except (httpx.ConnectError, httpx.TimeoutException) as e:
        raise HTTPException(
            status_code=503,
            detail="Cannot reach Immich server. Check IMMICH_SERVER_URL in .env and that Immich is running.",
        ) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/map/features")
async def get_map_features():
    """Get geotagged assets for map display. Returns a list (empty on error)."""
    try:
        from ...server import mcp

        if not mcp.immich_client:
            return []
        features = await mcp.immich_client.get_map_assets()
        return features if isinstance(features, list) else []
    except Exception:
        return []


# ===== PHOTO MANAGEMENT ENDPOINTS =====


@router.post("/photos/upload")
async def upload_photos(
    file_paths: list[str],
    album_name: str | None = None,
    *,
    auto_organize: bool = False,
    client: ImmichAPIClient = Depends(get_api_client),
):
    """Upload photos to Immich with batch processing."""
    try:
        from ...server import upload_photos as upload_tool

        return await upload_tool(file_paths, album_name, auto_organize=auto_organize)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/photos/timeline")
async def get_timeline(
    page: int = 1,
    limit: int = 100,
    client: ImmichAPIClient = Depends(get_api_client),
):
    """Get timeline assets (all/recent). Default view for Photos page."""
    try:
        from ...server import mcp

        if not mcp.immich_client:
            raise HTTPException(
                status_code=503,
                detail=(
                    "Immich client not initialized. Check .env (IMMICH_SERVER_URL, IMMICH_API_KEY) "
                    "and restart the backend."
                ),
            )
        items = await mcp.immich_client.get_timeline_assets(page=page, size=limit)
        out = []
        for photo in items:
            out.append(
                {
                    "id": photo.get("id", ""),
                    "original_filename": photo.get("originalFileName", "Unknown"),
                    "created_at": photo.get("createdAt", photo.get("fileCreatedAt", "")),
                    "smart_search_score": photo.get("score"),
                }
            )
        return out
    except ImmichAPIError as e:
        raise _immich_error_to_http(e) from e
    except (httpx.ConnectError, httpx.TimeoutException) as e:
        raise HTTPException(
            status_code=503,
            detail="Cannot reach Immich server. Check IMMICH_SERVER_URL in .env and that Immich is running.",
        ) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/photos/search")
async def search_photos(
    query: str,
    search_type: str = "smart",
    limit: int = 50,
    client: ImmichAPIClient = Depends(get_api_client),
):
    """Search photos using CLIP smart search or metadata queries."""
    try:
        from ...server import search_photos as search_tool

        return await search_tool(query, search_type, limit)
    except ImmichAPIError as e:
        raise _immich_error_to_http(e) from e
    except (httpx.ConnectError, httpx.TimeoutException) as e:
        raise HTTPException(
            status_code=503,
            detail="Cannot reach Immich server. Check IMMICH_SERVER_URL in .env and that Immich is running.",
        ) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/photos/{asset_id}")
async def get_photo_info(
    asset_id: str,
    client: ImmichAPIClient = Depends(get_api_client),
):
    """Get detailed photo information and metadata."""
    try:
        from ...server import get_photo_info as info_tool

        return await info_tool(asset_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/photos/{asset_id}/ocr")
async def get_ocr_data(
    asset_id: str,
    client: ImmichAPIClient = Depends(get_api_client),
):
    """Get OCR text extraction data for a photo."""
    try:
        from ...server import get_ocr_data as ocr_tool

        return await ocr_tool(asset_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/photos/{asset_id}/ocr-text")
async def get_asset_ocr(
    asset_id: str,
    client: ImmichAPIClient = Depends(get_api_client),
):
    """Get OCR text for a photo (alternative endpoint)."""
    try:
        from ...server import get_asset_ocr as ocr_tool

        return await ocr_tool(asset_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/photos/organize")
async def organize_photos_by_date(
    asset_ids: list[str],
    organization_type: str = "year_month",
    client: ImmichAPIClient = Depends(get_api_client),
):
    """Organize photos into date-based albums."""
    try:
        from ...server import organize_photos_by_date as organize_tool

        return await organize_tool(asset_ids, organization_type)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.delete("/photos")
async def delete_photos(
    asset_ids: list[str],
    *,
    move_to_trash: bool = True,
    client: ImmichAPIClient = Depends(get_api_client),
):
    """Delete photos from Immich."""
    try:
        from ...server import delete_photos as delete_tool

        return await delete_tool(asset_ids, move_to_trash)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


# ===== ALBUM MANAGEMENT ENDPOINTS =====


@router.post("/albums")
async def create_album(
    name: str,
    description: str | None = None,
    client: ImmichAPIClient = Depends(get_api_client),
):
    """Create a new album."""
    try:
        from ...server import create_album as create_tool

        return await create_tool(name, description)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/albums")
async def list_albums(
    shared: bool | None = None,
    *,
    include_stats: bool = True,
    client: ImmichAPIClient = Depends(get_api_client),
):
    """List all albums."""
    try:
        from ...server import list_albums as list_tool

        return await list_tool(shared=shared, include_stats=include_stats)
    except ImmichAPIError as e:
        raise _immich_error_to_http(e) from e
    except (httpx.ConnectError, httpx.TimeoutException) as e:
        raise HTTPException(
            status_code=503,
            detail="Cannot reach Immich server. Check IMMICH_SERVER_URL in .env and that Immich is running.",
        ) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/albums/{album_id}/photos")
async def add_to_album(
    album_id: str,
    asset_ids: list[str],
    client: ImmichAPIClient = Depends(get_api_client),
):
    """Add photos to an album."""
    try:
        from ...server import add_to_album as add_tool

        return await add_tool(album_id, asset_ids)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/albums/{album_id}/share")
async def share_album(
    album_id: str,
    *,
    allow_download: bool = True,
    allow_upload: bool = False,
    expires_at: str | None = None,
    show_metadata: bool = True,
    client: ImmichAPIClient = Depends(get_api_client),
):
    """Generate share link for an album."""
    try:
        from ...server import share_album as share_tool

        return await share_tool(album_id, expires_at, allow_download, allow_upload, show_metadata)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


# ===== PEOPLE & FACE DETECTION ENDPOINTS =====


@router.post("/people/detect")
async def detect_people(
    asset_ids: list[str] | None = None,
    *,
    force_reprocess: bool = False,
    client: ImmichAPIClient = Depends(get_api_client),
):
    """Run face detection on photos."""
    try:
        from ...server import detect_people as detect_tool

        return await detect_tool(asset_ids, force_reprocess)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/people/{person_id}/tag")
async def tag_person(
    person_id: str,
    name: str,
    face_asset_ids: list[str] | None = None,
    client: ImmichAPIClient = Depends(get_api_client),
):
    """Assign name to detected person."""
    try:
        from ...server import tag_person as tag_tool

        return await tag_tool(person_id, name, face_asset_ids)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/people/search")
async def search_by_person(
    person_name: str,
    limit: int = 50,
    *,
    include_metadata: bool = True,
    client: ImmichAPIClient = Depends(get_api_client),
):
    """Find all photos containing a specific person."""
    try:
        from ...server import search_by_person as search_tool

        return await search_tool(person_name, limit, include_metadata)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


# ===== SYSTEM & ADMINISTRATION ENDPOINTS =====


def _immich_error_to_http(e: Exception) -> HTTPException:
    """Map Immich/connection errors to HTTP status and user-facing message."""
    msg = str(e).lower()
    if "401" in msg or "unauthorized" in msg or "api key" in msg or "invalid" in msg or "forbidden" in msg:
        return HTTPException(
            status_code=401,
            detail=(
                "Immich rejected the API key. Check .env IMMICH_API_KEY and that the key is valid in "
                "Immich (Administration -> API Keys)."
            ),
        )
    if "connection" in msg or "refused" in msg or "timeout" in msg or "cannot connect" in msg or "network" in msg:
        return HTTPException(
            status_code=503,
            detail="Cannot reach Immich server. Check IMMICH_SERVER_URL in .env and that Immich is running.",
        )
    return HTTPException(status_code=502, detail=str(e))


@router.get("/system/storage")
async def get_storage_info(
    client: ImmichAPIClient = Depends(get_api_client),
):
    """Get storage usage statistics."""
    try:
        from ...server import get_storage_info as storage_tool

        return await storage_tool()
    except ImmichAPIError as e:
        raise _immich_error_to_http(e) from e
    except (httpx.ConnectError, httpx.TimeoutException) as e:
        raise HTTPException(
            status_code=503,
            detail="Cannot reach Immich server. Check IMMICH_SERVER_URL in .env and that Immich is running.",
        ) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/system/backup")
async def backup_photos(
    backup_path: str,
    album_ids: list[str] | None = None,
    *,
    include_metadata: bool = True,
    client: ImmichAPIClient = Depends(get_api_client),
):
    """Create backup of photos."""
    try:
        from ...server import backup_photos as backup_tool

        return await backup_tool(backup_path, album_ids, include_metadata)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/system/health")
async def server_health(
    client: ImmichAPIClient = Depends(get_api_client),
):
    """Get server health and status."""
    try:
        from ...server import server_health as health_tool

        return await health_tool()
    except ImmichAPIError as e:
        raise _immich_error_to_http(e) from e
    except (httpx.ConnectError, httpx.TimeoutException) as e:
        raise HTTPException(
            status_code=503,
            detail="Cannot reach Immich server. Check IMMICH_SERVER_URL in .env and that Immich is running.",
        ) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/tools")
async def list_mcp_tools():
    """List tools from the running MCP server via list_tools().

    Tools shown here are exactly what FastMCP returns: every @mcp.tool() in
    server.py (upload_photos, search_photos, list_albums, ...) and agentic.py
    (immich_help, agentic_immich_workflow, ...). No get_tool/by-name used.
    Returns empty list if MCP not available or list_tools fails.
    """
    try:
        from ...server import mcp

        if not hasattr(mcp, "list_tools"):
            return {"success": True, "tools": []}
        raw = mcp.list_tools()
        tool_list = await raw if asyncio.iscoroutine(raw) else raw
        if not isinstance(tool_list, list):
            return {"success": True, "tools": []}
        tools = []
        for t in tool_list:
            name = getattr(t, "name", None) or getattr(t, "title", str(t))
            desc = getattr(t, "description", "") or ""
            params = (
                getattr(t, "parameters", None) or getattr(t, "inputSchema", {}) or getattr(t, "input_schema", {}) or {}
            )
            tools.append({"name": name, "description": desc, "parameters": params})
        return {"success": True, "tools": tools}
    except Exception:
        return {"success": True, "tools": []}


@router.get("/logs")
async def get_logs(limit: int = 200):
    """Retrieve recent server logs from the in-memory ring buffer."""
    try:
        from ...logs import get_recent_logs, install_log_capture

        install_log_capture()
        return {"success": True, "logs": get_recent_logs(limit)}
    except Exception as e:
        return {"success": False, "error": str(e), "logs": []}


@router.get("/llm/providers")
async def get_llm_providers():
    """List supported LLM providers for the webapp."""
    return {
        "success": True,
        "providers": [
            {"id": "ollama", "name": "Ollama (Local)", "url": "http://localhost:11434"},
            {"id": "openrouter", "name": "OpenRouter (Cloud)", "url": "https://openrouter.ai/api/v1"},
            {"id": "lm-studio", "name": "LM Studio (Local)", "url": "http://localhost:1234/v1"},
        ],
    }


@router.get("/llm/models")
async def get_llm_models(provider: str = "ollama"):
    """Fetch models from a specific provider (proxied)."""
    if provider == "ollama":
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get("http://localhost:11434/api/tags", timeout=2.0)
                if resp.status_code == 200:
                    data = resp.json()
                    models = [m["name"] for m in data.get("models", [])]
                    return {"success": True, "models": models}
        except Exception:
            return {
                "success": False,
                "error": "Cannot reach Ollama at http://localhost:11434. Is it running?",
                "models": [],
            }

    if provider == "openrouter":
        return {
            "success": False,
            "error": "OpenRouter model list requires the OPENROUTER_API_KEY. Set it in .env.",
            "models": [],
        }

    if provider == "lm-studio":
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get("http://localhost:1234/v1/models", timeout=2.0)
                if resp.status_code == 200:
                    data = resp.json()
                    models = [m["id"] for m in data.get("data", [])]
                    return {"success": True, "models": models}
        except Exception:
            return {
                "success": False,
                "error": "Cannot reach LM Studio at http://localhost:1234. Is it running?",
                "models": [],
            }

    return {"success": False, "error": f"Unknown provider '{provider}'", "models": []}


# Static help content for webapp (no MCP tool dependency)
HELP_CONTENT: dict[str, str] = {
    "overview": (
        "Immich MCP Server provides photo library management through the Model Context Protocol. "
        "Use the webapp to browse timeline photos, search, view albums and people, "
        "and see geotagged assets on the map. "
        "Configure Immich server URL and API key in Settings."
    ),
    "photos": (
        "Photos page shows your Immich timeline by default. Use the search bar for smart (CLIP) or metadata search. "
        "Thumbnails load via the backend proxy. Ensure IMMICH_SERVER_URL and API key are set for the backend."
    ),
    "albums": (
        "Albums list and manage your Immich albums. Create albums, add or remove assets, and share albums via the API."
    ),
    "people": ("People and face recognition data from Immich. View detected people and link faces to names."),
    "map": (
        "Map view shows assets that have GPS (EXIF) data. If the map is empty, "
        "ensure photos have location metadata and Immich has processed them. "
        "The backend calls Immich /map/markers."
    ),
    "tools": (
        "MCP Tools are listed from the running FastMCP server. If the list is empty, the backend may not be connected "
        "to the MCP process or list_tools may be unavailable. Health and storage endpoints work independently."
    ),
    "settings": (
        "Set Immich server URL, API key, and optional multi-user config. "
        "Restart the backend after changing env or config."
    ),
    "immich": (
        "Immich is a high-performance self-hosted photo and video management solution. "
        "It features mobile app support, facial recognition, and CLIP-based semantic search. "
        "Visit https://immich.app for official documentation."
    ),
    "webapp": (
        "This dashboard is a React-based frontend built with Vite and Tailwind CSS. "
        "It provides a premium visual interface for the Immich MCP Server, allowing you to "
        "browse your library, use AI tools, and monitor system health."
    ),
    "mcp_server": (
        "The MCP Server (ImmichMCP) is the bridge between AI agents and your photo library. "
        "It implements the Model Context Protocol (FastMCP 3.1) and exposes tools for "
        "search, upload, and organization that can be used by models like Claude or Gemini."
    ),
}


@router.get("/help")
async def get_mcp_help(category: str | None = None):
    """Return help content for the webapp. Does not depend on MCP tool."""
    try:
        if category and category.lower() in HELP_CONTENT:
            return {
                "success": True,
                "message": "Help",
                "category": category,
                "help": HELP_CONTENT[category.lower()],
            }
        return {
            "success": True,
            "message": "Documentation and usage guide for Immich MCP Server.",
            "categories": list(HELP_CONTENT.keys()),
            "all_help": HELP_CONTENT,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/libraries")
async def list_libraries(client: ImmichAPIClient = Depends(get_api_client)):
    """List external libraries with import paths, refresh status, and stats."""
    try:
        from ...server import mcp

        if not mcp.immich_client:
            raise HTTPException(
                status_code=503,
                detail="Immich client not initialized. Check .env (IMMICH_SERVER_URL, IMMICH_API_KEY) and restart the backend.",
            )
        libraries = await mcp.immich_client.get_libraries()
        out = []
        for lib in libraries:
            stats = {}
            try:
                stats = await mcp.immich_client.get_library_statistics(lib.get("id", "")) or {}
            except Exception:
                stats = {}
            out.append(
                {
                    "id": lib.get("id", ""),
                    "name": lib.get("name", "Unnamed library"),
                    "type": lib.get("type", "EXTERNAL"),
                    "import_paths": lib.get("importPaths", []),
                    "exclusion_patterns": lib.get("exclusionPatterns", []),
                    "refreshed_at": lib.get("refreshedAt"),
                    "created_at": lib.get("createdAt"),
                    "asset_count": int(stats.get("total", 0) or 0),
                    "photo_count": int(stats.get("photos", 0) or 0),
                    "video_count": int(stats.get("videos", 0) or 0),
                    "size_bytes": int(stats.get("usage", 0) or 0),
                }
            )
        return out
    except ImmichAPIError as e:
        raise _immich_error_to_http(e) from e
    except (httpx.ConnectError, httpx.TimeoutException) as e:
        raise HTTPException(
            status_code=503,
            detail="Cannot reach Immich server. Check IMMICH_SERVER_URL in .env and that Immich is running.",
        ) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/libraries/{library_id}/scan")
async def scan_library(library_id: str, client: ImmichAPIClient = Depends(get_api_client)):
    """Trigger a scan of an external library (picks up new/changed files)."""
    try:
        from ...server import mcp

        if not mcp.immich_client:
            raise HTTPException(
                status_code=503,
                detail="Immich client not initialized. Check .env (IMMICH_SERVER_URL, IMMICH_API_KEY) and restart the backend.",
            )
        await mcp.immich_client.scan_library(library_id)
        return {"success": True, "message": f"Scan triggered for library {library_id}", "library_id": library_id}
    except ImmichAPIError as e:
        raise _immich_error_to_http(e) from e
    except (httpx.ConnectError, httpx.TimeoutException) as e:
        raise HTTPException(status_code=503, detail="Cannot reach Immich server.") from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.delete("/libraries/{library_id}")
async def delete_library(library_id: str, client: ImmichAPIClient = Depends(get_api_client)):
    """Delete a library (only safe when it has no import paths / assets)."""
    try:
        from ...server import mcp

        if not mcp.immich_client:
            raise HTTPException(
                status_code=503,
                detail="Immich client not initialized. Check .env (IMMICH_SERVER_URL, IMMICH_API_KEY) and restart the backend.",
            )
        await mcp.immich_client.delete_library(library_id)
        return {"success": True, "message": f"Library {library_id} deleted", "library_id": library_id}
    except ImmichAPIError as e:
        raise _immich_error_to_http(e) from e
    except (httpx.ConnectError, httpx.TimeoutException) as e:
        raise HTTPException(status_code=503, detail="Cannot reach Immich server.") from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/libraries/{library_id}/statistics")
async def library_statistics(library_id: str, client: ImmichAPIClient = Depends(get_api_client)):
    """Storage statistics for one library."""
    try:
        from ...server import mcp

        if not mcp.immich_client:
            raise HTTPException(status_code=503, detail="Immich client not initialized.")
        return await mcp.immich_client.get_library_statistics(library_id)
    except ImmichAPIError as e:
        raise _immich_error_to_http(e) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
