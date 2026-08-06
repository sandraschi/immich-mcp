"""Generate assets/prompts/examples.json - 100+ structured tool call mappings."""
import json

EXAMPLES = []
ADD = EXAMPLES.append


def t(tool, params, description):
    ADD({"tool": tool, "params": params, "description": description})


# --- search_photos (12) ---
t("search_photos", {"query": "dog playing in snow", "search_type": "smart", "limit": 20},
  "Semantic search for content - default smart mode")
t("search_photos", {"query": "sunset over mountains", "search_type": "smart", "limit": 50},
  "Semantic search with default limit")
t("search_photos", {"query": "receipt electronics store", "search_type": "ocr", "limit": 20},
  "OCR search for text inside images")
t("search_photos", {"query": "invoice", "search_type": "ocr", "limit": 100},
  "Large OCR search - receipts and invoices")
t("search_photos", {"query": "Nikon D850", "search_type": "metadata", "limit": 50},
  "Metadata search by camera body")
t("search_photos", {"query": "ISO 800", "search_type": "metadata", "limit": 50},
  "Metadata search by ISO")
t("search_photos", {"query": "IMG_20260301", "search_type": "filename", "limit": 20},
  "Filename pattern search")
t("search_photos", {"query": "Berlin", "search_type": "smart", "limit": 10},
  "Quick discovery - small page to save tokens")
t("search_photos", {"query": "wedding cake", "search_type": "smart", "limit": 200},
  "Exhaustive sweep capped at max limit")
t("search_photos", {"query": "japanese receipt", "search_type": "ocr", "ocr_language": "japanese", "limit": 20},
  "OCR search with language model hint")
t("search_photos", {"query": "grandma garden", "search_type": "smart", "limit": 50},
  "Smart search for a person-scene combo")
t("search_photos", {"query": "car rental", "search_type": "ocr", "limit": 30},
  "OCR search - travel receipts")

# --- get_photo_info / ocr / download (9) ---
t("get_photo_info", {"asset_id": "550e8400-e29b-41d4-a716-446655440000"},
  "Full EXIF and metadata dossier for one asset")
t("get_photo_info", {"asset_id": "abc123def456"}, "Minimal-form asset id")
t("get_photo_info", {"asset_id": "video-001"}, "Video asset metadata")
t("get_ocr_data", {"asset_id": "550e8400-e29b-41d4-a716-446655440000"},
  "OCR text with word bounding boxes")
t("get_ocr_data", {"asset_id": "receipt-2026-01"}, "Read a receipt's text")
t("get_asset_ocr", {"asset_id": "550e8400-e29b-41d4-a716-446655440000"},
  "Aggregated OCR view (text, words, confidence)")
t("download_photo_to_temp", {"photo_id": "550e8400-e29b-41d4-a716-446655440000"},
  "Download original to temp for local use")
t("download_photo_to_temp", {"photo_id": "video-002"}, "Download a video original")
t("get_photo_info", {"asset_id": "550e8400-e29b-41d4-a716-446655440000"},
  "Check GPS coordinates of a photo")

# --- upload / organize / visibility / edit (10) ---
t("upload_photos", {"file_paths": ["D:/Camera Dump/img_001.jpg", "D:/Camera Dump/img_002.jpg"]},
  "Batch upload with defaults")
t("upload_photos", {"file_paths": ["D:/Camera Dump/img_003.jpg"], "album_name": "Camera Dump 2026"},
  "Upload directly into an album")
t("upload_photos", {"file_paths": ["D:/Camera Dump/img_004.jpg"], "auto_organize": True},
  "Upload with auto date-organization")
t("upload_photos", {"file_paths": ["D:/Camera Dump/missing.jpg", "D:/Camera Dump/img_005.jpg"]},
  "Upload with one missing file - reported, not fatal")
t("organize_photos_by_date", {"asset_ids": ["a1", "a2", "a3"], "album_name": "Prague 2026"},
  "Group photos into a date-based album")
t("organize_photos_by_date", {"asset_ids": ["b1", "b2"]},
  "Date-organize without a base name")
t("update_asset_visibility", {"asset_id": "a1", "visibility": "archive"},
  "Archive out of the timeline")
t("update_asset_visibility", {"asset_id": "a2", "visibility": "hidden"},
  "Hide from search and timeline")
t("update_asset_visibility", {"asset_id": "a3", "visibility": "locked"},
  "Lock against edits")
t("edit_photo", {"asset_id": "a4", "operation": "rotate", "parameters": {"angle": 90}},
  "Rotate a portrait 90 degrees")

# --- delete (5) ---
t("delete_photos", {"asset_ids": ["a1", "a2"], "move_to_trash": True},
  "Move to trash - safe default")
t("delete_photos", {"asset_ids": ["a3"], "move_to_trash": False},
  "Permanent delete - requires explicit user confirmation")
t("delete_photos", {"asset_ids": ["b1", "b2", "b3"], "move_to_trash": True},
  "Batch trash of duplicates")
t("delete_photos", {"asset_ids": ["c1"]}, "Trash one asset (default True)")
t("delete_photos", {"asset_ids": ["d1", "d2", "d3", "d4", "d5"]}, "Trash a group of five")

# --- albums (12) ---
t("list_albums", {"include_stats": True}, "List albums with counts and sizes")
t("list_albums", {"shared": True}, "List only shared albums")
t("list_albums", {"shared": False, "include_stats": False}, "Own albums, no stats")
t("create_album", {"name": "Prague 2026"}, "Create an empty album")
t("create_album", {"name": "Prague 2026", "description": "Trip photos", "asset_ids": ["a1", "a2"]},
  "Create album with assets")
t("create_album", {"name": "2025 Receipts", "description": "Tax season"}, "Tax album")
t("add_to_album", {"album_id": "alb-1", "asset_ids": ["a1", "a2", "a3"]},
  "Add photos to an album")
t("add_to_album", {"album_id": "alb-2", "asset_ids": ["b1"]}, "Add a single photo")
t("share_album", {"album_id": "alb-1", "allow_download": True},
  "Share with download enabled")
t("share_album", {"album_id": "alb-1", "expires_at": "2026-12-31T23:59:59", "allow_download": True},
  "Share with expiry and downloads")
t("share_album", {"album_id": "alb-3", "allow_upload": True, "show_metadata": False},
  "Event share - guests upload, no EXIF")
t("share_album", {"album_id": "alb-4"}, "Default share (downloads on, uploads off)")

# --- people (9) ---
t("detect_people", {"asset_ids": ["a1", "a2", "a3"]}, "Queue face detection for assets")
t("detect_people", {"force_reprocess": True}, "Re-run detection on everything")
t("detect_people", {}, "Queue detection for all assets")
t("tag_person", {"person_id": "p1", "name": "Grandma"}, "Name a detected person")
t("tag_person", {"person_id": "p2", "name": "Benny", "face_asset_ids": ["f1", "f2"]},
  "Name a person restricting face samples")
t("search_by_person", {"person_name": "Grandma", "limit": 100},
  "All photos of a named person")
t("search_by_person", {"person_name": "Benny"}, "Default-limit person search")
t("search_by_person", {"person_name": "Grandma", "include_metadata": False},
  "Person search without metadata payload")
t("detect_people", {"asset_ids": ["v1", "v2"], "force_reprocess": False},
  "Detection on videos too")

# --- libraries (11) ---
t("list_libraries", {}, "List all libraries")
t("get_library_info", {"library_id": "lib-1"}, "One library's details")
t("create_library", {"name": "Archive Disk", "import_paths": ["/mnt/archive/photos"]},
  "Create a library for the current user")
t("create_library", {"name": "Steve's Folder", "import_paths": ["/mnt/steve"], "owner": "steve"},
  "Create a library owned by another user")
t("scan_library", {"library_id": "lib-1"}, "Trigger an import scan")
t("scan_library", {"library_id": "lib-2"}, "Rescan an updated library")
t("manage_library", {"library_id": "lib-1", "operation": "pause"},
  "Pause library processing")
t("manage_library", {"library_id": "lib-1", "operation": "resume"},
  "Resume library processing")
t("get_user_libraries", {"username": "steve"}, "Libraries visible to Steve")
t("get_user_libraries", {}, "Libraries for the current user")
t("create_library", {"name": "Scans", "import_paths": ["/mnt/scans/2026"]}, "Scan-inbox library")

# --- users (9) ---
t("list_users", {}, "List configured users")
t("switch_user", {"username": "steve"}, "Act as Steve")
t("switch_user", {"username": "sandra"}, "Switch back to Sandra")
t("switch_immich_user", {"username": "steve"}, "Alias switch - update client headers")
t("get_current_user", {}, "Active identity and capabilities")
t("get_user_libraries", {"username": "steve"}, "Steve's accessible libraries")
t("list_users", {}, "Verify active user after switching")
t("switch_user", {"username": "shared-account"}, "Switch to a shared account")
t("get_current_user", {}, "Confirm role before destructive ops")

# --- storage / backup (10) ---
t("get_storage_info", {}, "Library storage totals")
t("get_storage_info", {}, "Check before planning a backup")
t("backup_photos", {"backup_path": "D:/Backups/Immich", "album_ids": ["alb-1"]},
  "Back up one album")
t("backup_photos", {"backup_path": "D:/Backups/Immich", "album_ids": ["alb-1", "alb-2"],
                    "include_metadata": True}, "Back up albums with metadata")
t("backup_photos", {"backup_path": "F:/ImmichArchive"}, "Back up everything")
t("sync_metadata_to_exif", {"photo_id": "a1", "local_path": "D:/Backups/img_001.jpg"},
  "Write metadata back into a local file")
t("sync_metadata_to_exif", {"photo_id": "v1", "local_path": "D:/Backups/vid_001.mp4"},
  "EXIF sync on a video sidecar")
t("detect_similar_photos", {}, "Queue the similarity job")
t("backup_photos", {"backup_path": "E:/Tax2025", "album_ids": ["alb-tax"]}, "Tax backup")
t("get_storage_info", {}, "Storage after uploads")

# --- system / agentic / prefab (13) ---
t("server_health", {}, "Liveness probe - version, DB, Redis, uptime")
t("server_health", {}, "Diagnose connection errors")
t("show_server_health_prefab", {}, "Health as a Prefab card")
t("immich_help", {"category": "photos"}, "Help for photo tools")
t("immich_help", {"category": "albums"}, "Help for album tools")
t("immich_help", {"category": "system"}, "Help for system tools")
t("immich_help", {"category": "agentic"}, "Help for agentic tools")
t("immich_help", {}, "Help index")
t("immich_shutdown", {"confirm": True}, "Graceful server shutdown")
t("immich_shutdown", {"confirm": False}, "Aborted shutdown (safe)")
t("agentic_immich_workflow",
   {"workflow_prompt": "Organize all 2025 photos into monthly albums"},
   "Autonomous multi-step organization")
t("intelligent_photo_processing",
   {"photos": [{"id": "a1", "type": "IMAGE"}, {"id": "a2", "type": "IMAGE"}],
    "processing_goal": "Find the keepers", "available_operations": ["keep", "trash"]},
   "Batch decision over a photo set")
t("conversational_immich_assistant",
   {"user_query": "What is the best way to organize a year of photos?"},
   "Planning-oriented chat answer")

# --- cross-domain chains (16) ---
t("search_photos", {"query": "Prague", "search_type": "smart", "limit": 60},
  "Step 1 of trip album: gather")
t("create_album", {"name": "Prague 2026", "description": "Trip"}, "Step 2: album")
t("add_to_album", {"album_id": "alb-1", "asset_ids": ["a1", "a2"]},
  "Step 3: populate")
t("share_album", {"album_id": "alb-1", "expires_at": "2026-12-31T23:59:59"},
  "Step 4: share with expiry")
t("backup_photos", {"backup_path": "D:/Backups", "album_ids": ["alb-1"]},
  "Step 5: local backup")
t("search_photos", {"query": "receipt", "search_type": "ocr", "limit": 100},
  "Tax hunt step 1: OCR gather")
t("create_album", {"name": "2025 Receipts"}, "Tax hunt step 2: album")
t("add_to_album", {"album_id": "alb-tax", "asset_ids": ["r1", "r2", "r3"]},
  "Tax hunt step 3: populate")
t("detect_people", {"asset_ids": ["a1", "a2", "a3"]}, "Face pipeline step 1")
t("tag_person", {"person_id": "p1", "name": "Grandma"}, "Face pipeline step 2")
t("search_by_person", {"person_name": "Grandma", "limit": 100}, "Face pipeline step 3: verify")
t("upload_photos", {"file_paths": ["D:/Dump/img_001.jpg", "D:/Dump/img_002.jpg"]},
  "Cleanup step 1: ingest dump")
t("detect_similar_photos", {}, "Cleanup step 2: find duplicates")
t("delete_photos", {"asset_ids": ["dup1", "dup2"], "move_to_trash": True},
  "Cleanup step 3: trash dupes")
t("get_storage_info", {}, "Audit step 1: size the library")
t("list_users", {}, "Audit step 2: who has access")

assert len(EXAMPLES) >= 100, f"only {len(EXAMPLES)}"
with open("assets/prompts/examples.json", "w", encoding="utf-8") as f:
    json.dump(EXAMPLES, f, indent=2, ensure_ascii=False)
print(f"wrote {len(EXAMPLES)} examples")
