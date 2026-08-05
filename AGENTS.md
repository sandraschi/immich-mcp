# immich-mcp Agent Context

Fleet MCP server: FastMCP 3.4+ wrapper for the Immich photo library (v2.7+ / v3 verified).

## Quick Ref

```powershell
uv run pytest tests/ -q        # unit + contract tests (mocked)
uv run ruff check src/ tests/  # lint
uv run ruff format src/ tests/ # format
```

## Ports (WEBAPP_PORTS.md registry)

| Port | Service |
|------|---------|
| 10838 | Webapp frontend (Vite dev, `web_sota/`) |
| 10839 | Backend (FastAPI + MCP HTTP) |

## Key Files

| File | Purpose |
|------|---------|
| `src/immich_mcp/immich_api.py` | Immich REST client — all endpoint contracts live here |
| `src/immich_mcp/server.py` | MCP tools (33) + FastMCP instance |
| `src/immich_mcp/api/v1/routes.py` | FastAPI REST routes for the webapp |
| `src/immich_mcp/config.py` | Env config: `IMMICH_SERVER_URL`, `IMMICH_API_KEY`, `IMMICH_USERS` |
| `mcpb/src/` | Packaging copy of the package — keep in sync with `src/immich_mcp/` |

## API Contract Notes (verified 2026-08-06 against v2.7.5 / v3.0.3 / v3.1.0 specs)

- Timeline/search: `POST /search/metadata` — `GET /assets` was removed in v2.7+
- Trash vs permanent: `DELETE /assets {ids, force}` (force=false=trash)
- Edits: `PUT /assets/{id}/edits` with `{edits: [{action, parameters}]}`
- Face jobs: `POST /assets/jobs` with name `refresh-faces`
- Stats: `GET /server/storage` + `GET /server/statistics`
- Visibility enum: `archive` / `timeline` / `hidden` / `locked`
- Libraries: `create_library` requires `ownerId` (resolved via `/users/me`)
- OCR: `GET /assets/{id}/ocr` returns a word-box list (aggregated client-side)
- Do NOT add endpoints that are not in the official OpenAPI spec — check first.
