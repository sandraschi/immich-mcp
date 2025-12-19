# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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

### Changed
- N/A

### Fixed
- N/A

### Removed
- N/A

---

## How to Update This File

When making changes, add them under the appropriate section:
- **Added** for new features
- **Changed** for changes in existing functionality
- **Deprecated** for soon-to-be removed features
- **Removed** for now removed features
- **Fixed** for any bug fixes
- **Security** for vulnerability fixes
