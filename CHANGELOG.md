# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.6.2] - 2026-08-06

### Fixed
- **CRITICAL CORS**: `allow_origins=["*"]` and FastMCP `run_http_async()` (which drops custom middlewares) replaced with the fleet CORS standard: explicit dev/Tauri origins, unconditional Tailscale/LAN/localhost regex, direct `uvicorn.Server` on `mcp.http_app()`.
- **Multi-user tools broken at runtime**: `switch_immich_user`, `switch_user`, `get_current_user`, `get_user_libraries` referenced an unbound `api_client` global (NameError, silently swallowed). Rewired to `get_api_client()`; switching now actually swaps the client API key.
- **REST routes TypeError**: `delete_photos`, `share_album`, `search_by_person`, `backup_photos`, `detect_people` passed keyword-only tool parameters positionally. Now keyword args.
- **Agentic tools crash**: unawaited `ctx.info()` and invalid `ctx.sample(prompt=...)` signature fixed.
- **httpx 0.28 `delete(json=...)`**: switched to `client.request("DELETE", ...)`.
- **Pyright: 36 errors -> 0** (unbound vars, optional access, Prefab `cssClass` alias, settings types, None guards).
- **Native build pipeline**: added `run_server.py` (dual transport) + `immich-mcp-backend.spec`; fixed `native/build.ps1` `$envSrc` bug, added API_BASE check, frozen-binary smoke test, >=5 MB size gate.
- **Webapp**: live backend status (Tauri event + exponential backoff poll + Restart) replacing hardcoded "System Online"; Ctrl+Scroll zoom; zustand LLM store; `color-scheme: dark`; data-testid coverage on all pages.
- **MCPB**: pack now from repo root with real 3-4-100 prompts (3065/4186 words, 116 examples), schema-valid manifest, smoke-verified bundle; stale flattened `mcpb/` removed.

### Added
- `GET /api/v1/capabilities`, `GET /api/v1/diagnostics`, enriched `/api/v1/health` (version, tool_count, providers).
- `immich_shutdown` MCP tool (confirm-guarded).
- Session context injection: `.claude-plugin`, `.cursorrules`/`.windsurfrules`, Copilot instructions, opencode skill.
- pyright to dev dependencies (five-gate).

### Removed
- Tracked `.bak` dross and stale `mcpb/` staging from the index.
## [1.6.1] - 2026-08-06

### Fixed
- **Timeline search (CRITICAL)**: `get_timeline_assets` called three dead endpoints
  (`POST /search/assets` never existed, `GET /search/metadata` is POST-only, `GET /assets`
  was removed in v2.7+) and always returned `[]`. Now uses `POST /search/metadata`
  with `page`/`size`/`order` (verified against the official OpenAPI spec for v2.7.5, v3.0.3, v3.1.0).
- **Upload payload (CRITICAL)**: `fileCreatedAt`/`fileModifiedAt` were sent as unix
  epoch floats but the API requires ISO-8601 date-time strings; `duration` was sent as
  a string on v3 where the schema type is integer. Both now conform, and the correct
  mimetype is sent per file. Verified against the live server spec (v2.7.5) and v3.1.0.
- **Delete/trash**: `DELETE /assets/trash` does not exist; trash and permanent delete
  both go through `DELETE /assets` with `force: false/true` (confirmed in the v2.7.5
  server source: `status: force ? Deleted : Trashed`).
- **Asset edits**: `edit_asset` called `POST /assets/{id}/edit` (nonexistent); now uses
  `PUT /assets/{id}/edits` with the `{edits: [{action, parameters}]}` contract.
- **Face detection**: `run_face_detection` posted an invalid `FACE_DETECTION` job with
  a `data` field the schema does not accept, and returned fabricated counts. Now queues
  the real per-asset job (`POST /assets/jobs`, name `refresh-faces`) and reports
  submission status honestly.
- **Server stats**: `get_server_stats` used removed endpoints (`/admin/storage`,
  `/server-info`) and hardcoded zeros. Now uses `GET /server/storage`,
  `GET /server/statistics` and a real album count.
- **OCR**: `get_asset_ocr` passed a nonexistent `bounding_boxes` query param, parsed the
  response as a dict, and fabricated empty results on 404. The endpoint returns a list
  of word boxes - now aggregated into `text`/`words`/`confidence`, and 404 raises
  honestly instead of returning fake data.
- **Visibility**: `update_asset_visibility` advertised invalid values (`private`,
  `public`, `archived`). The real enum is `archive`, `timeline`, `hidden`, `locked`;
  values are now validated before sending.
- **Libraries**: removed dead endpoints (`refresh`, `optimize`, `locations`,
  `empty-trash`, `clean-bundles`); `create_library` now resolves the required
  `ownerId` via `/users/me`; `scan_library` no longer sends a nonexistent body;
  `get_libraries` handles the plain-array response; added `get_library_statistics`.
- **Version alignment**: `pyproject.toml` bumped from 1.5.0 to 1.6.1 (STATUS/CHANGELOG
  already claimed 1.6.0); `mcpb/` packaging copy resynced with `src/`.

## [1.6.0] - 2026-07-12

### Added
- **Immich v3.0.0+ Compatibility**: Hardened server for the major v3.0.0 release. Automatically checks server version via `is_v3()` dynamic version detection.
- **Payload Schema Adaptation**: Automatically omits `deviceId` and `deviceAssetId` and supplies required `duration` value (`"0"` for images) on v3+ servers to avoid Zod schema validation errors.
- **Album Users Support**: Adapted `_get_album_owner_id()` to parse the restructured `albumUsers` list in v3.0.0 while preserving fallback compatibility for `users` and `ownerId`.
- **GIMP Cross-Connect Tool**: Added `download_photo_to_temp` to retrieve the original asset binaries and store them in a local temp folder.
- **Local EXIF Metadata Syncing**: Added `sync_metadata_to_exif` using `piexif` to write GPS, description, and datetime tags from Immich back into local image files.
- **Duplicates & Similar Photo Detection**: Added `detect_similar_photos` using Immich's machine learning clustering.
- **Bun Migration**: Migrated the `web_sota` frontend to Bun for modern build workflows and execution speed.
- **Test Isolation**: Added automatic mock state resetting in `conftest.py` to prevent state leakages between tests.

## [1.5.1] - 2026-06-14

### Added
- Tauri native wrapper (`native/` directory) with `bundle.resources` + `std::process::Command` support.
- CUA-NSIS build pipelines (NSIS installer recipes and smoke tests).
- Tauri CORS: `tauri://localhost` origins enabled for WebView API access.
- NSIS installer artifacts at `dist/` and `native/target/release/bundle/nsis/`.

### Changed
- Frontend API calls use absolute `http://127.0.0.1:{port}` URLs in production build.
- CORS middleware includes `allow_origin_regex` for `tauri.localhost`.

## [1.5.0] - 2026-04-14

### Added
- **Industrialization (SOTA 2026)**: Full fleet parity with FastMCP 3.4.0 standards.
- **Frontend Evolution**: Migrated web dashboard to **Biome (v1.9.4)** for stabilized linting and formatting.
- **Port Synchronization**: Locked dashboard to port **10795** and API to **10794** for fleet-wide registry compliance.
- **Protocol Hardening**: Unified JSON-RPC stream preservation with absolute `print()` purging in sources.
- **Registry Integration**: Updated fleet manifest for high-fidelity discovery.

### Changed
- Modernized `pyproject.toml` with expanded Ruff rules (`T20`, `C4`, `SIM`, `I`).
- Updated README with SOTA v13.1 registry badges and industrialized versioning.
- Synchronized all internal metadata to April 2026 release standards.

### Fixed
- Fixed documentation/source version inconsistencies between `__init__.py` and `pyproject.toml`.
- Resolved potential JSON-RPC corruption by converting docstring `print` examples to inactive comments.

## [1.1.0] - 2025-01-27

### Added
- OCR search support for Immich v2.2.0+ (text extraction from images)
- Automatic detection of Immich v2.0.0+ server version
- OCR capability detection in server health checks
- Enhanced error handling for v2.0.0+ API response formats

### Changed
- Updated for full compatibility with Immich v2.0.0+ stable release
- Improved error messages with detailed API error information
- Enhanced `server_health` tool to report v2.0.0+ status and OCR support
- Updated `search_photos` tool to support OCR search type

### Fixed
- Better error handling for HTTP status errors with detailed messages
- OCR search gracefully falls back to smart search if OCR endpoint unavailable

## [1.0.0] - 2025-10-21

### Added
- Initial release
- Core functionality implemented
- Documentation created

---

## How to Update This File

When making changes, add them under the appropriate section:
- **Added** for new features
- **Changed** for changes in existing functionality
- **Deprecated** for soon-to-be removed features
- **Removed** for now removed features
- **Fixed** for any bug fixes
- **Security** for vulnerability fixes
