# Webapp API and MCP Tools

## How the frontend gets data

- **Help** – `GET /api/v1/help`
  Returns static help content from the backend. Does **not** call any MCP tool.

- **Tools** – `GET /api/v1/tools`
  Returns `{ success, tools }` where `tools` comes from **`mcp.list_tools()`** in the running FastMCP server.
  So “what tools are found by the frontend” = whatever `list_tools()` returns.

- **Photos, Map, Dashboard, etc.** – `GET /api/v1/photos/*`, `/api/v1/map/*`, `/api/v1/system/*`, …
  These are normal REST endpoints. They use `mcp.immich_client` (Immich API) and server logic. They do **not** look up or call MCP tools by name.

## Where tools are defined

All MCP tools are registered with `@mcp.tool()` in:

1. **`src/immich_mcp/server.py`**
   Core tools: `upload_photos`, `search_photos`, `get_photo_info`, `list_albums`, `create_album`, and the rest of the photo/album/people/system tools.

2. **`src/immich_mcp/agentic.py`**
   Agentic tools: `immich_help`, `agentic_immich_workflow`, `intelligent_photo_processing`, `conversational_immich_assistant`.

So the **Tools** page shows exactly the set of tools returned by `mcp.list_tools()` (i.e. these registered tools). There are no other “tools” the frontend fetches; nothing else uses `get_tool("...")` or invokes a tool by name.

## Why “Help tool not found” happened

The `/help` route used to call `mcp.get_tool("immich_help")` and then `help_tool.fn(...)`. The **tool exists** in `agentic.py`; in FastMCP 3.1 the server does not expose tools that way (no `.fn`), so the call failed and the API returned “Help tool not found”. The route was changed to serve static help content so the webapp does not depend on invoking that MCP tool.
## People page data (REST, with counts)

- **People list** - `GET /api/v1/people?with_counts=true&sort=asset_count&order=desc&include_hidden=true&search=...`
  Returns every person enriched with `asset_count` / `has_more_photos` (bounded
  concurrent per-person sample - exact for low counts, which is what triage needs).
  The page fetches the raw list first (fast paint), then re-fetches with counts.
  Like the other pages, this uses `mcp.immich_client` directly - not MCP tools.

- **Bulk delete** - `POST /api/v1/people/bulk-delete` with `{ ids, confirm: true }`.
  Deletes many clusters at once (photos stay, faces unassigned). One bad id does
  not abort the rest - per-id errors are reported.

- **Crowd cleanup** - `POST /api/v1/people/cleanup` with `{ threshold, dry_run, limit }`.
  `dry_run=true` (default) only reports candidates; `dry_run=false` deletes them.
  Default `threshold=1` targets faces with zero or one photo.

- **Person detail / rename / delete** - `GET|PUT|DELETE /api/v1/people/{id}`,
  thumbnails via `GET /api/v1/people/{id}/thumbnail`.

Note: `GET /api/v1/people/search` is declared before `/people/{person_id}` on
purpose - otherwise the dynamic id route swallows "search".
