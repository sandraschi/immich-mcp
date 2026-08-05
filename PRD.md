# Immich MCP — Product Requirements Document

**Version**: 1.6.1 (2026-08-06)
**Status**: Active / SOTA v13.1
**Stack**: FastMCP 3.4+, Python 3.12+, httpx, FastAPI, React + Vite + Tailwind (webapp)

## Purpose

An MCP server that lets AI agents (Claude Desktop, Cursor, opencode) manage a self-hosted
Immich photo library: upload, search (CLIP smart search, OCR, metadata, filename), organize
into albums, manage people/faces, administer libraries, create share links, and report
storage/health — with a React dashboard (ports 10838/10839).

## Architecture

```
Agent (MCP stdio) ──┐
                    ├──> immich_mcp.server (33 FastMCP tools)
Webapp (React) ─────┤         │
    :10838          │         ▼
                    ├──> api/v1/routes.py (FastAPI REST, :10839)
                    │         │
                    └─────────┴──> immich_api.py ──> Immich REST API (x-api-key)
```

- **Dual transport**: stdio (MCP clients) + HTTP (webapp/REST), see `transport.py`.
- **Multi-user**: per-user API keys via `IMMICH_USERS`, runtime user switching.
- **Version-aware client**: `is_v3()` branches upload payloads between v2 (`deviceAssetId`/`deviceId`)
  and v3 (integer `duration`) contracts.

## Shipped Features

- Photo upload (batch, dedupe via server, ISO-8601 timestamps, correct mimetypes)
- Search: smart (CLIP), OCR, metadata, filename — `POST /search/*`
- Timeline listing via `POST /search/metadata`
- Albums: create, add assets, list (v3 `albumUsers` ownership parsed), share links
- People: queue `refresh-faces` jobs, tag/merge persons, search by person
- Libraries: list/create/scan/statistics (v2.7+/v3 endpoint set)
- Asset edits (crop/rotate/mirror via `PUT /assets/{id}/edits`), visibility (archive/timeline/hidden/locked)
- Trash/permanent delete (`DELETE /assets` force flag)
- OCR extraction (`GET /assets/{id}/ocr`, aggregated word boxes)
- Server stats (`/server/storage`, `/server/statistics`), health, Prefab UI card
- GIMP bridge: download original to temp, sync EXIF metadata back via piexif
- Duplicate/similar detection (`GET /duplicates`)

## API Compatibility Contract

Verified 2026-08-06 against official OpenAPI specs: v2.7.5 (live), v3.0.3, v3.1.0.
See README "Immich API Compatibility" section for the endpoint table and the list of
removed endpoints that must NOT be used (`GET /assets`, `/assets/trash`, `/admin/storage`,
`/server-info`, `/libraries/{id}/optimize`, etc.).

## Non-Goals

- Not a replacement for the Immich web UI; does not implement admin user management UI.
- No local media processing beyond EXIF syncing; edits are server-side (Immich).
- No scheduled jobs; all operations are request-driven.
