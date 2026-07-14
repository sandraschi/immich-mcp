# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
