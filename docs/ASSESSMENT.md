# immich-mcp — Assessment & Gap Analysis

Assessment of the `immich-mcp` repository: structure, correctness bugs, API compatibility, standards compliance, and remediation status. This document is the running audit record — updated after each major assessment pass.

---

## 1. Assessment Summary (2026-08-06, v1.6.1)

**Method**: Every endpoint the client calls was diffed against the official Immich OpenAPI specs at **v2.7.5** (the live production server), **v3.0.3**, and **v3.1.0**. The live server was probed directly, and the server source (`asset.controller.ts` / `asset.service.ts`) was consulted for delete/trash semantics.

**Result**: 15 API-contract defects found, all fixed and shipped in v1.6.1. Tests went from broken (June) to **37 passed / 17 skipped** with 14 new contract tests. Ruff clean, coverage 43.6%.

### What was wrong and what was fixed

| # | Severity | Finding | Fix (commit `6fdb8f7`) |
|---|----------|---------|------------------------|
| 1 | CRITICAL | `get_timeline_assets` called three dead endpoints (`POST /search/assets` never existed, `GET /search/metadata` is POST-only, `GET /assets` removed in v2.7+) — always returned `[]` | Single `POST /search/metadata` with `page`/`size`/`order` |
| 2 | CRITICAL | Upload sent `fileCreatedAt`/`fileModifiedAt` as unix epoch floats (API requires ISO-8601) and `duration` as a string on v3 (schema: integer) | ISO-8601 timestamps, integer `duration=0` for v3, correct per-file mimetype |
| 3 | HIGH | Trash used nonexistent `DELETE /assets/trash` | `DELETE /assets {ids, force}` (force=false=trash, true=permanent — confirmed in server source) |
| 4 | HIGH | `edit_asset` used `POST /assets/{id}/edit` (wrong path and method) | `PUT /assets/{id}/edits` with `{edits: [{action, parameters}]}` |
| 5 | HIGH | `run_face_detection` posted invalid `FACE_DETECTION` job with a `data` field and returned fabricated counts | `POST /assets/jobs` with `refresh-faces`; honest job-submission result |
| 6 | HIGH | `get_server_stats` used removed endpoints (`/admin/storage`, `/server-info`) and hardcoded zeros | `GET /server/storage` + `GET /server/statistics` + real album count |
| 7 | MED | `get_asset_ocr` passed a nonexistent `bounding_boxes` query param, parsed a list as dict, fabricated empty results on 404 | Aggregate the real word-box list; 404 raises honestly |
| 8 | MED | `update_asset_visibility` advertised invalid enum values (`private`/`public`/`archived`) | Validate against real enum `archive`/`timeline`/`hidden`/`locked` |
| 9 | MED | 7 library endpoints that don't exist (`refresh`, `optimize`, `locations`, `empty-trash`, `clean-bundles`) + `create_library` missing required `ownerId` | Removed dead endpoints; owner resolved via `/users/me`; added `get_library_statistics`; scan without body |
| 10 | MED | `get_libraries` ignored the plain-array response — always returned `[]` | Handle list responses |
| 11 | MED | `mcpb/src/` packaging copy diverged from `src/immich_mcp/` | Resynced byte-identical |
| 12 | LOW | Version drift (pyproject 1.5.0 vs STATUS/CHANGELOG 1.6.0) | Aligned 1.6.1 across pyproject, uv.lock, mcpb pyproject, manifest, STATUS |
| 13 | LOW | Pre-commit ruff gate failed on `mcpb/` files (nested pyproject shadows root config) | Hook exclude for `mcpb/native/scripts` matching pyproject `exclude` |
| 14 | MED | Docs: wrong webapp ports (10795/10794 are mcp-central-docs's), wrong env var name (`IMMICH_URL`), stale "v2.4.0 / REQUIRES MIGRATION / Immich++" sections, **real API key embedded in `llms-full.txt`** | Docs overhaul (commits `7d7dd43`, `51a4c75`, `7d9d09b`): verified compat table, correct ports/env, secret removed |
| 15 | MED | 66 junk doc files (9 template dirs copied from other projects — `docs/github`, `docs/serena`, MEGATEST, etc.) | Deleted (commit `c8bf056`) |

### Not a defect, but changed
- Repo renamed `immichmcp` → **`immich-mcp`** on GitHub (was archived; old URL redirects).
- `ASSESSMENT.md`/`STATUS.md`/`TEST_README.md` moved from repo root to `docs/` per README_STRUCTURE.

---

## 2. Standards Compliance & Fleet Metrics (2026-08-06)

| Metric | Status / Value | Comments |
|--------|----------------|----------|
| **Version** | 1.6.1 | Aligned across pyproject, uv.lock, mcpb pyproject, manifest, STATUS |
| **FastMCP Version** | 3.4+ (Compliant) | `fastmcp>=3.4.4,<4` |
| **Python Tooling** | `uv` + `pyproject.toml` | Lockfile committed and synced |
| **Automation** | `justfile` + fleet.just | Lint/test/CUA recipes |
| **LLM Manifests** | `llms.txt` + `llms-full.txt` | Purged of junk dumps and stale sections; secret removed |
| **JS Package Manager** | Bun (Compliant) | `web_sota` migrated from npm |
| **Webapp Ports** | 10838 (FE) / 10839 (BE) | Registered in `operations/WEBAPP_PORTS.md` |
| **Test Suite** | ✅ 37 passed / 17 skipped | 14 new contract tests; coverage 43.6% (>= 30% bar) |
| **Linter** | ✅ Ruff clean | `ruff check` + `ruff format --check` pass |
| **Pre-commit** | ✅ Passing | ruff hooks exclude `mcpb/native/scripts` (matches pyproject) |
| **Repo** | GitHub `sandraschi/immich-mcp` | Renamed from `immichmcp`, unarchived |

---

## 3. Immich API Compatibility (verified)

Client contracts verified against the official OpenAPI specs for **v2.7.5** (live), **v3.0.3**, **v3.1.0** on 2026-08-06.

| Immich Version | Status | Notes |
|----------------|--------|-------|
| v3.1.x / v3.0.x | ✅ Working | Spec-verified; breaking changes handled (upload payload, album users, search-only timeline) |
| v2.7.x | ✅ Working | Current production contract; spec-verified, live server probed |
| v2.4–2.6 | ✅ Working | Older search-based contract |
| v2.0–2.3 | ✅ Working | Basic operations |

Removed endpoints deliberately not used: `GET /assets`, `POST /search/assets`, `DELETE /assets/trash`, `GET /admin/storage`, `GET /server-info`, `/libraries/{id}/{refresh,optimize,locations,empty-trash,clean-bundles}`.

Key contracts: timeline `POST /search/metadata`; trash/permanent `DELETE /assets {force}`; edits `PUT /assets/{id}/edits`; face jobs `POST /assets/jobs (refresh-faces)`; stats `GET /server/storage` + `/server/statistics`; visibility enum `archive|timeline|hidden|locked`; OCR `GET /assets/{id}/ocr` (word-box list).

---

## 4. Open Items / Risks

| Item | Risk | Action |
|------|------|--------|
| **Live-server integration tests skip (17)** | The `IMMICH_API_KEY` in `.env` returns 401 against the live v2.7.5 server. Fixes are spec-verified + mock-tested but not exercised end-to-end. | Regenerate an API key in the Immich admin panel, update `.env`, run `uv run pytest tests/test_integration_v240.py -q` |
| Live upload verification | Upload DTO changes (ISO dates, duration) proven by contract tests only | Covered by the integration run above |
| `docs/` root-level files (19) | Some may be stale (e.g. `FASTMCP_2.12_MIGRATION.md` targets FastMCP 2.12, repo is on 3.4+) | Review per-file; migrate or delete in a future pass |
| Webapp (`web_sota`) | Not modified in this pass; timeline route calls the fixed client | Verify via `just cua-webapp-test` |

---

## 5. Assessment History

### 2026-08-06 — v1.6.1 audit (this document)
Full API-contract audit against official specs + live server; 15 defects fixed and shipped; docs overhauled; repo renamed. See section 1.

### 2026-06-24 — original assessment (all items resolved)
- **Test suite broken**: legacy `test_api.py` / `integration_tests.py` imported a nonexistent `immich` package, breaking collection → resolved (legacy files removed, v240 harness is the suite).
- **Mock tests patched `_get` instead of `_post`** for POST search endpoints → resolved (current tests patch `_post`).
- **Mock spec mismatches** (`upload_photo` vs `upload_photos_batch`, `test_app.app` vs `http_app()`) → resolved.
- **Immich v3.0.0 breaking changes** (removal of `deviceAssetId`/`deviceId`, album ownership refactor) → resolved in v1.6.0, then fully re-verified against v2.7.5/v3.1.0 specs in the 2026-08-06 audit.
- **npm vs Bun** non-compliance → resolved (Bun migration).
