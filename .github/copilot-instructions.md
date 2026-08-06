# Immich MCP - GitHub Copilot Instructions

You have access to the user's Immich photo library through the immich-mcp server: semantic CLIP search, OCR text-in-image search, albums, people/faces, libraries, upload and backup tools.

**Before starting work:**
1. Check library state: `search_photos(query="<task topic>", limit=10)` or `list_albums(include_stats=true)`
2. Check server status when relevant: `server_health()` or `get_storage_info()`

**At end of work, save changes:**
- Create/tag albums for organized results: `create_album(name="...")`, `add_to_album(album_id="...", asset_ids=[...])`
- Tag people for future search: `tag_person(person_id="...", name="...")`
- Use `immich_help(category="...")` for tool guidance when unsure
