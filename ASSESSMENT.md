# immich-mcp — Assessment & Gap Analysis

A comprehensive assessment of the `immich-mcp` repository was conducted to evaluate its structure, identify correctness bugs, scalability gaps, standards compliance, and prepare for upcoming Immich API changes.

---

## 📊 1. Standards Compliance & Fleet Metrics

| Metric | Status / Value | Comments |
|--------|----------------|----------|
| **FastMCP Version** | 3.2.4 (Compliant) | Satisfies the June 2026 minimum bar of `fastmcp>=3.2.0` |
| **Python Tooling** | `uv` + `pyproject.toml` | Lockfile `uv.lock` is present and active |
| **Automation** | `justfile` (Compliant) | Standardized tasks are defined for code quality and packaging |
| **LLM Manifests** | `llms.txt` + `llms-full.txt` | Present and properly formatted in the repository root |
| **JS Package Manager** | 🔴 **Non-Compliant (npm)** | `web_sota` uses `npm` (`package-lock.json`) instead of `Bun` |
| **Webapp Ports** | 10838 (FE) / 10839 (BE) | Registered in `operations/WEBAPP_PORTS.md` (Approved Exception) |
| **Test Suite** | 🔴 **Broken** | 100% of collected tests fail due to configuration and mock issues |

---

## 🔄 2. Immich API Changes (v2.4.0 Scaffold vs. v3.0.0 Stable)

The codebase was scaffolded targeting **Immich v2.4.0** (released Dec 2025). As Immich heads toward **v3.0.0** in mid-2026, several breaking changes have been introduced that will break the server in production:

### ⚠️ API Change 1: Removal of `deviceAssetId` and `deviceId`
* **Affected Files**: 
  - [immich_api.py](file:///D:/Dev/repos/immich-mcp/src/immich_mcp/immich_api.py#L207)
  - [server.py](file:///D:/Dev/repos/immich-mcp/src/immich_mcp/server.py#L229)
* **Impact**: 
  - In `upload_photos_batch`, the client passes `deviceAssetId` and `deviceId` during multipart asset uploads (`POST /assets`). In v3.0.0, these fields are removed, causing uploads to fail or be ignored.
  - The `PhotoSearchResult` Pydantic model requires `device_asset_id` and `device_id` as non-nullable string fields. If they are removed from the Immich API response schema, Pydantic validation will raise `ValidationError`, crashing search tool responses.
* **Fix**: Make these fields optional in the Pydantic schemas and remove them from the asset upload payload.

### ⚠️ API Change 2: Refactoring of Album Ownership
* **Affected Files**:
  - [server.py](file:///D:/Dev/repos/immich-mcp/src/immich_mcp/server.py#L313)
* **Impact**:
  - Immich v3.0.0 migrates `album.owner` to the `album.users` list (assigning the owner user a role of `"owner"`). The top-level `ownerId` field is removed.
  - Calling `album_data["ownerId"]` (e.g. in `server.py` line 1587 and 1756) will raise `KeyError`, crashing the `list_albums` and `create_album` tools.
* **Fix**: Extract the owner ID by searching the `users` array in the album response:
  ```python
  owner = next((u for u in album_data.get("users", []) if u.get("role") == "owner"), {})
  owner_id = owner.get("id", "")
  ```

---

## 🐛 3. Critical Code Bugs & Gaps

Static code analysis and test execution revealed multiple critical bugs that prevent testing and integration:

### 🔴 Bug 1: Broken Test Collection (Legacy Files)
* **Files**: 
  - [test_api.py](file:///D:/Dev/repos/immich-mcp/tests/test_api.py#L11)
  - [integration_tests.py](file:///D:/Dev/repos/immich-mcp/tests/integration_tests.py#L15)
* **Description**: Both files import modules from a non-existent `immich` package (e.g. `from immich.album_manager import AlbumManager`). Running `pytest` fails immediately during collection, preventing any tests from running.
* **Fix**: Delete or rename these legacy files, as they have been replaced by the `v240` test harness.

### 🔴 Bug 2: Test Mocks Patching GET instead of POST
* **File**: [test_immich_api_v240.py](file:///D:/Dev/repos/immich-mcp/tests/test_immich_api_v240.py#L63)
* **Description**: Mock tests patch `api_client._get` to return mock data for photo searches. However, the real client uses `self._post` for smart search, metadata search, and filename search (as required by the Immich API). Because `_post` is unpatched, it attempts to make a real network connection to `http://localhost:2283`, which fails with `httpcore.ConnectError: All connection attempts failed`.
* **Fix**: Patch `api_client._post` instead of `_get` for POST search endpoints.

### 🔴 Bug 3: Attribute Errors in Mock Specifications
* **File**: [test_server.py](file:///D:/Dev/repos/immich-mcp/tests/test_server.py#L73)
* **Description**: `conftest.py` configures `mock_immich_client` with `spec=ImmichAPIClient`. The tests call `mock_immich_client.upload_photo` and `mock_immich_client.search_photos`. However:
  1. `ImmichAPIClient` only implements `upload_photos_batch` (not `upload_photo`).
  2. Because of `spec=ImmichAPIClient`, calling the non-existent method raises `AttributeError: 'AsyncMock' object has no attribute 'upload_photo'`.
* **Fix**: Update the mock methods in `conftest.py` and the assertions in `test_server.py` to match `upload_photos_batch`.

### 🔴 Bug 4: Incorrect FastAPI Router Assertions
* **File**: [test_server.py](file:///D:/Dev/repos/immich-mcp/tests/test_server.py#L41)
* **Description**:
  1. Tests request `/immich-mcp/api/v1/health` and `/immich-mcp/api/v1/photos/...`. However, the server router is mounted directly at `/api/v1/...` on the FastAPI application. This leads to `404 Not Found` errors.
  2. `conftest.py` invokes `test_app.app` to initialize the FastAPI `TestClient`, but `ImmichMCP` subclassing `FastMCP` does not expose an `.app` attribute in FastMCP 3.x. The Starlette application is retrieved via `.http_app()`.
* **Fix**: Change `test_app.app` to `test_app.http_app()` in `conftest.py`, and remove the `/immich-mcp` prefix in `test_server.py`.

---

## 🚀 4. Actionable Improvement Plans

### 🛠️ Phase 1: Test Suite Stabilization (Immediate)
1. **Clean Legacy Tests**: Remove `test_api.py` and `integration_tests.py`.
2. **Correct Mock Endpoints**: Update `test_immich_api_v240.py` to mock `_post` calls rather than `_get` for search endpoints.
3. **Fix API Spec Mocking**: Align `test_server.py` and `conftest.py` with `upload_photos_batch` and `http_app()`.
4. **Remove Path Prefix**: Strip the `/immich-mcp` prefix from client endpoint routes in tests.

### 🛠️ Phase 2: Immich v3.0 Compatibility Hardening
1. **Pydantic Validation Guard**: Update Pydantic response schemas (e.g. `PhotoSearchResult`) in `server.py` to mark `device_id` and `device_asset_id` as `None | str = None` to handle v3.0.0 responses gracefully.
2. **Payload Safety**: Ensure `upload_photos_batch` does not fail when `deviceId` is omitted.
3. **Upgrade Album Owner Logic**: Refactor album owner parsing in `server.py` to read from the `users` array fallback.

### 🛠️ Phase 3: Standards Convergence
1. **Migrate to Bun**: Refactor `web_sota` to use `bun` instead of `npm`. Convert `package-lock.json` to a Bun lockfile, and update the scripts in `start.ps1` to use `bun install` and `bun run dev`.

---

*Assessment generated on 2026-06-24*
