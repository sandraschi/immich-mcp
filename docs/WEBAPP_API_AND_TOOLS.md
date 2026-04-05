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
