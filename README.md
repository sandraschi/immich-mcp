# Immich MCP Server

<p align="center">
  <a href="https://github.com/casey/just"><img src="https://img.shields.io/badge/just-ready_to_go-7c5cfc?style=flat-square&logo=just&logoColor=white" alt="Just"></a>
  <a href="https://github.com/astral-sh/ruff"><img src="https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json" alt="Ruff"></a>
  <a href="https://python.org"><img src="https://img.shields.io/badge/Python-3.13+-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python"></a>
  <a href="https://github.com/PrefectHQ/fastmcp"><img src="https://img.shields.io/badge/FastMCP-3.4-7c5cfc?style=flat-square" alt="FastMCP"></a>
</p>


> 📖 **[Installation Guide](INSTALL.md)** — quick start, manual setup, and troubleshooting

**Industrialized FastMCP 3.4** | **Austrian Efficiency** | **Conversational AI & Sampling**

Efficient Immich photo library management through the MCP (Model Context Protocol). Simple, reliable, effective.

> **Status**: [SOTA v13.1] Operational with Immich v2.x and v3.0.0+, FastMCP 3.4 parity, Biome-stabilized, conversational AI and sampling.

## Quick Start

```powershell
git clone https://github.com/sandraschi/immich-mcp
cd immich-mcp
just
```

This opens an interactive dashboard showing all available commands. Run `just bootstrap` to install dependencies, then `just serve` or `just dev` to start.

### Manual Setup

If you don't have `just` installed:
### 1. Prerequisites
- Python 3.11+
- [Immich server](https://immich.app/) running and accessible
-  **Immich v3.0.0+ / v3.1.x**: Full compatibility (verified against the official OpenAPI spec)
-  **Immich v2.7.x**: Full compatibility (current production contract, verified live)
-  **Immich v2.2.0+**: OCR search support
- Immich API key (get from Administration  API Keys)

##  Installation

### Prerequisites
- [uv](https://docs.astral.sh/uv/) installed (RECOMMENDED)
- Python 3.12+

###  Quick Start
Run immediately via `uvx`:
```bash
uvx immich-mcp
```

###  Claude Desktop Integration
Add to your `claude_desktop_config.json`:
```json
"mcpServers": {
  "immich-mcp": {
    "command": "uv",
    "args": ["--directory", "D:/Dev/repos/immich-mcp", "run", "immich-mcp"]
  }
}
```
#### **Option 1: PyPI Package Install (Recommended)**

**Simple pip installation - no repository cloning required!**

```bash
# Install from PyPI
pip install immich-mcp

# Configure Cursor MCP
{
  "mcpServers": {
    "immich-mcp": {
      "command": "python",
      "args": ["-m", "immich_mcp.server"],
      "env": {
        "IMMICH_SERVER_URL": "http://your-immich-server:2283",
        "IMMICH_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

**Advantages:**
-  **Universal compatibility** - Works with any MCP client
-  **Simple installation** - Just one pip command
-  **Always up-to-date** - Install latest version directly
-  **No repository cloning** - Clean, minimal setup
-  **Easy updates** - `pip install --upgrade immich-mcp`

---

##  Installation

### Prerequisites
- [uv](https://docs.astral.sh/uv/) installed (RECOMMENDED)
- Python 3.12+

###  Quick Start
Run immediately via `uvx`:
```bash
uvx immich-mcp
```

###  Claude Desktop Integration
Add to your `claude_desktop_config.json`:
```json
"mcpServers": {
  "immich-mcp": {
    "command": "uv",
    "args": ["--directory", "D:/Dev/repos/immich-mcp", "run", "immich-mcp"]
  }
}
```
### 3. LLM Configuration for Enhanced AI Features

Immich supports multiple LLM providers for advanced AI capabilities including smart search, object detection, face recognition, and automatic tagging. Configure your preferred LLM for enhanced photo management:

#### **Supported LLM Providers**

- **OpenAI** (GPT-4, GPT-3.5-turbo)
- **Anthropic** (Claude-3, Claude-2)
- **Ollama** (Local models: Llama, Mistral, etc.)
- **Local AI** (Custom local LLM servers)

#### **LLM Configuration in Immich**

Configure LLM settings in Immich Administration  Settings  Machine Learning:

```yaml
# Example LLM configuration
machine_learning:
  enabled: true
  url: "http://localhost:11434"  # Ollama default
  model: "llama3.2:3b"           # Ollama model name
  api_key: "your-api-key"        # For cloud providers
```

#### **Environment Variables for ImmichMCP**

For ImmichMCP to leverage LLM-enhanced features, ensure your Immich server has LLM configured:

```bash
# Required for LLM features
IMMICH_LLM_ENABLED=true
IMMICH_LLM_PROVIDER=ollama  # or openai, anthropic
IMMICH_LLM_MODEL=llama3.2:3b
IMMICH_LLM_API_KEY=your_key_here  # if using cloud provider
```

#### **Enhanced AI Features with LLM**

- **Smart Search**: Natural language photo search ("find photos of my dog playing")
- **Object Detection**: Automatic object and scene recognition
- **Face Recognition**: AI-powered face detection and naming
- **Auto-tagging**: Intelligent photo categorization
- **OCR Enhancement**: Improved text extraction from images
- **Content Analysis**: Deep understanding of photo content

#### **LLM Performance Tips**

- **Local Models (Ollama)**:  for privacy, works offline
- **Cloud Models**: Higher accuracy, requires API key
- **Model Size**: Larger models = better results but slower processing
- **Batch Processing**: Enable for bulk photo analysis

> **Note**: LLM features require Immich server v2.2.0+ with machine learning enabled. Some features may require additional hardware resources.

### 4. Cursor Integration

ImmichMCP integrates with Cursor through MCP (Model Context Protocol):

#### **Automatic Setup (Recommended)**
Cursor will automatically detect and configure ImmichMCP if you have the repository cloned.

#### **Manual Configuration**
ImmichMCP is configured in your user profile: `~/.cursor/mcp.json` (typically `C:\Users\%USERNAME%\.cursor\mcp.json` on Windows). If you need to modify it, edit that file:

```json
{
  "mcpServers": {
    "immich-mcp": {
      "command": "python",
      "args": ["D:/Dev/repos/immich-mcp/src/immich_mcp/server.py"],
      "env": {
        "IMMICH_SERVER_URL": "http://213.47.34.131:2283",
        "IMMICH_API_KEY": "eCWNLTQZ7UwAVgbQmtGl0Q8AMEjeuddHy1BVCTWRtNA",
        "PYTHONPATH": "D:/Dev/repos/immich-mcp/src",
        "PYTHONUNBUFFERED": "1"
      }
    }
  }
}
```

**Restart Cursor** after adding the configuration.

#### **Troubleshooting Cursor Integration**

** "Immich MCP server started successfully"**
- Server should appear in Cursor's Output tab  "MCP" panel
- Look for the startup banner with Austrian efficiency message
- Check for "Starting MCP server 'ImmichMCP'" in logs

** "Immich MCP server not found in output"**
- Check Cursor's Output tab  "MCP" panel
- Look for error messages in the log
- Verify MCP configuration in `~/.cursor/mcp.json` (`C:\Users\%USERNAME%\.cursor\mcp.json` on Windows)
- Ensure environment variables are set: `IMMICH_SERVER_URL` and `IMMICH_API_KEY`
- Try restarting Cursor after configuration changes

** "Connection failed" or "API key invalid"**
- Verify Immich server is running on the configured URL (`http://213.47.34.131:2283`)
- Check API key in Immich settings  Account  API Keys
- Test connection manually: `curl -H "x-api-key: eCWNLTQZ7UwAVgbQmtGl0Q8AMEjeuddHy1BVCTWRtNA" http://213.47.34.131:2283/api/auth/status`

** "Import errors" or "Module not found"**
- Ensure you're using Python 3.11+
- Install dependencies: `uv pip install -r requirements.txt`
- Check PYTHONPATH in Cursor MCP configuration (`D:/Dev/repos/immich-mcp/src`)

** "Environment variable issues"**
- Cursor MCP configuration should override .env file settings
- Verify the env block in `~/.cursor/mcp.json` contains correct values

### 4. Environment Configuration

```powershell
# Clone repository
git clone https://github.com/sandraschi/immichmcp.git
cd immichmcp

# Create and activate virtual environment
uv venv
.\venv\Scripts\Activate.ps1

# Install dependencies
uv pip install -r requirements.txt

# Copy and configure environment
Copy-Item .env.example .env -Force
# Edit .env with your Immich URL and API key
```

### 5. Configuration

Edit `.env` file with your Immich server details:

```bash
# Required
IMMICH_API_KEY=your_api_key_here
IMMICH_URL=http://localhost:2283

# Optional: Logging
LOG_LEVEL=INFO
```

### 6. Run Server

For development and testing:

```powershell
# Run the server
python src/immich_mcp/server.py
```

For Claude Desktop integration, use the MCPB package.

## Immich API Compatibility (v2.7+ / v3)

The client is verified against the official Immich OpenAPI specs for **v2.7.5**, **v3.0.3** and **v3.1.0** (checked 2026-08-06). Key contracts:

| Area | Endpoint(s) |
|------|-------------|
| Upload | `POST /assets` (ISO-8601 `fileCreatedAt`/`fileModifiedAt`; `deviceAssetId`/`deviceId` for < v3, `duration` integer for v3) |
| Search | `POST /search/smart`, `POST /search/metadata` |
| Timeline | `POST /search/metadata` (`page`/`size`/`order`) — the legacy `GET /assets` was removed in v2.7 |
| Delete/Trash | `DELETE /assets` (`force: false` = trash, `force: true` = permanent) |
| Edits | `PUT /assets/{id}/edits` (`crop`/`rotate`/`mirror` actions, v2.5.0+) |
| Face detection | `POST /assets/jobs` (`refresh-faces`) |
| OCR | `GET /assets/{id}/ocr` (returns word boxes; aggregated client-side) |
| Stats | `GET /server/storage`, `GET /server/statistics` |
| Visibility | `PUT /assets/{id}` — enum `archive` / `timeline` / `hidden` / `locked` |
| Libraries | `POST /libraries` (requires `ownerId`), `GET /libraries/{id}/statistics`, `POST /libraries/{id}/scan` |

Removed in v2.7+/v3 and **not used**: `GET /assets`, `POST /search/assets`, `DELETE /assets/trash`,
`GET /admin/storage`, `GET /server-info`, `/libraries/{id}/{refresh,optimize,locations,empty-trash,clean-bundles}`.

### Testing Compatibility
Run the built-in test harness to verify your Immich server compatibility:

```powershell
# Test against your Immich server (unit + contract tests)
uv run pytest tests/ -q

# Live-server integration tests (requires valid IMMICH_SERVER_URL + IMMICH_API_KEY)
uv run pytest tests/test_integration_v240.py -q
```

## Features

### Core Photo Operations

- **Upload photos/videos** with metadata preservation
- **Smart search** using CLIP-based natural language queries
- **Enhanced OCR search** with multilingual support (Greek, Korean, Russian, Thai, etc.) - v2.4.0+
- **OCR bounding boxes** for precise text location highlighting - v2.4.0+
- **Organize photos** by date, location, or custom criteria
- **Get detailed metadata** including OCR data from any photo/video
- **Library management** for external photo folders - v2.4.0+
- **Multi-user support** with user switching and permissions - v2.4.0+
- **Cursor integration** with seamless MCP protocol support

### Available Tools

1. **Upload Photos**
   - Batch upload with progress tracking
   - Automatic duplicate detection
   - Metadata preservation

   Example:

   ```bash
   Upload all photos from /vacation/2025/Vienna to album "Vienna Summer 2025"
   ```

2. **Get Photo Info**
   - View detailed metadata including OCR text
   - Check storage location
   - See creation/modification dates
   - Access OCR bounding boxes (v2.3.0+)

   Example:

   ```bash
   Show metadata for photo ID abc123
   ```

3. **Get OCR Data** (v2.3.0+)
   - Extract text with bounding box coordinates
   - Multilingual OCR support
   - Confidence scores and language detection

   Example:

   ```bash
   Get OCR data with bounding boxes for photo abc123
   ```

4. **Server Health**
   - Check Immich server status
   - Verify API connectivity
   - View version information

   Example:
   ```bash
   Check server health
   ```

5. **Download Photo to Temp** (`download_photo_to_temp`)
   - Download original asset files to local temp directory
   - Acts as a bridge for local image editors (like GIMP)

   Example:
   ```bash
   Download photo ID abc123 to a temporary file
   ```

6. **Sync Metadata to EXIF** (`sync_metadata_to_exif`)
   - Sync description, GPS coordinates, and date/time from Immich back into local image EXIF tags

   Example:
   ```bash
   Sync metadata of photo abc123 to local file edited.jpg
   ```

7. **Detect Similar Photos** (`detect_similar_photos`)
   - Retrieve clusters of duplicates/visually similar photos from Immich's ML engine with suggested keep IDs

   Example:
   ```bash
   Detect all similar and duplicate photos in my library
   ```

###  Library Management (External Folders Solution)

ImmichMCP solves the "unwieldy external folder management" problem with comprehensive library management tools:

- **Create Libraries** - Organize photos from different external folders
- **Add/Remove Locations** - Easily manage which folders are included in libraries
- **Scan Libraries** - Automatically import new photos from configured folders
- **Library Maintenance** - Optimize, clean bundles, empty trash
- **Multi-Location Support** - Combine multiple external folders in one library

**Example Workflow:**
```bash
# Create a library for vacation photos
Create library "Vacations" with import paths ["D:/Photos/Vacation/2024", "D:/Photos/Vacation/2025"]

# Add a new location to existing library
Add location "D:/Photos/Vacation/2026" to library "Vacations"

# Scan for new photos
Scan library "Vacations" with refresh modified files
```

###  Multi-User Support

Full multi-user Immich support for shared installations:

- **User Switching** - Switch between different Immich user accounts
- **Role-Based Access** - Respect user permissions (admin, user, shared)
- **User-Specific Libraries** - Access libraries based on user permissions
- **Context Management** - Maintain separate contexts for different users

**Environment Configuration:**
```env
# Multiple users configuration
IMMICH_USERS=sandra:api_key_sandra:admin:Sandra's account,family:api_key_family:user:Shared family account
IMMICH_ACTIVE_USER=sandra
```

**Example Usage:**
```bash
# Switch to family user account
Switch to user "family"

# List libraries accessible to current user
List user libraries

# Switch back to admin user
Switch to user "sandra"
```

## Architecture

### Project Structure

```
immichmcp/
 .env.example        # Environment template
 .gitignore         # Git exclusions
 README.md          # This file
 src/
    immich_mcp/
        server.py  # Main server file
 requirements.txt   # Python dependencies
 tests/             # Test suite (coming soon)
```

##  Dual Transport Support

ImmichMCP supports **dual transport modes** for different integration scenarios:

###  Stdio Mode (MCP Protocol)
**For Claude Desktop integration:**
```bash
python -m immich_mcp.server
# Runs MCP server over stdio for AI assistant integration
```

###  HTTP Mode (REST API)
**For Immich++ and other applications:**
```bash
python run_http_server.py --transport http --port 8000
```

**Available REST endpoints:**
- `GET /immich-mcp/api/v1/health` - Health check
- `POST /immich-mcp/api/v1/photos/upload` - Upload photos
- `GET /immich-mcp/api/v1/photos/search` - Search photos
- `GET /immich-mcp/api/v1/photos/{asset_id}` - Get photo info
- `GET /immich-mcp/api/v1/albums` - List albums
- `POST /immich-mcp/api/v1/albums` - Create album
- `POST /immich-mcp/api/v1/albums/{id}/photos` - Add photos to album
- `GET /immich-mcp/api/v1/system/storage` - Storage info
- `POST /immich-mcp/api/v1/system/backup` - Backup photos
- *And 6+ additional endpoints...*

### Integration Benefits

** With Immich++:**
- **Tool Reuse**: Immich++ calls MCP tools via HTTP
- **Automatic Fallback**: MCP proxy fails  Direct API
- **Single Source of Truth**: Centralized Immich API logic
- **Future-Proof**: MCP updates benefit Immich++ automatically

** With Claude Desktop:**
- **Native MCP Support**: Full protocol compliance
- **Conversational Access**: All tools via AI chat
- **Optimized Performance**: Streamlined for AI workflows

---

## Configuration

### Environment Variables

| Variable | Required | Description | Default |
|----------|----------|-------------|---------|
| `IMMICH_URL` | Yes | URL of your Immich server | `http://localhost:2283` |
| `IMMICH_API_KEY` | Yes | Your Immich API key | - |
| `LOG_LEVEL` | No | Logging level (DEBUG, INFO, WARNING, ERROR) | `INFO` |
|----------|----------|-------------|---------|
| `IMMICH_URL` |  | Immich server URL | - |
| `IMMICH_API_KEY` |  | API key from Immich | - |
| `MCP_SERVER_NAME` |  | Server display name | `"Immich Photo Management MCP "` |
| `LOG_LEVEL` |  | Logging verbosity | `INFO` |

### Advanced Configuration

See `docs/Configuration.md` for detailed setup including:

- Environment-specific configurations
- Performance tuning for Austrian efficiency
- Vienna-specific deployment settings
- SSL/TLS configuration
- Feature flag management
- OCR language model configuration (v2.3.0+)
- Multilingual OCR settings

##  Testing

### Run Unit Tests

```bash
python -m pytest tests/test_api.py -v
```

### Run Integration Tests

```bash
# Requires test Immich server
export TEST_IMMICH_URL=http://localhost:2283
export TEST_IMMICH_API_KEY=your_test_key

python tests/integration_tests.py
```

### Austrian Efficiency Test Metrics

- **Unit tests**: ~30 seconds
- **Integration tests**: ~2 minutes
- **Coverage**: >90% of core functionality
- **Real workflow validation**: End-to-end photo management

##  Troubleshooting

### Common Issues

**Connection Problems:**

```bash
# Test connection
python -c "from immich.manager import ImmichManager; print(' OK' if ImmichManager('http://localhost:2283', 'your_key').test_connection() else ' Failed')"
```

**Upload Issues:**

- Check file size limits in `config/settings.yaml`
- Verify supported formats (JPEG, PNG, MP4, etc.)
- Ensure Immich server has sufficient storage

**Performance Issues:**

- Reduce `concurrent_uploads` in configuration
- Enable `optimize_bandwidth` for Austrian budget efficiency
- Check Immich server resources

For detailed troubleshooting: `docs/Troubleshooting.md`

##  Austrian Context Features

### Direct Communication

- Clear, actionable error messages
- No gaslighting about failures
- Honest limitations and recovery suggestions

### Budget Awareness

- Optimized for ~100/month AI tools usage
- Bandwidth optimization options
- Efficient API call patterns

### Vienna-Specific

- Europe/Vienna timezone support
- DD.MM.YYYY date format
- German language character support (, , , )

### Rapid Development

- Working solutions in hours, not days
- Realistic AI-assisted development timelines
- Practical Austrian efficiency throughout

##  Performance

### Austrian Efficiency Metrics

- **Photo upload**: ~2-5 seconds per image (depending on size)
- **Smart search**: ~1-3 seconds for CLIP queries
- **Album operations**: ~0.5-1 seconds for typical operations
- **Face detection**: ~5-10 seconds per batch (server-dependent)

### Optimization Features

- **Concurrent uploads**: Configurable parallelism
- **Request caching**: Reduce API calls
- **Bandwidth optimization**: Austrian budget consideration
- **Batch operations**: Efficient bulk processing

##  Contributing

1. **Follow Austrian efficiency principles**
2. **Write working code, not stubs**
3. **Test comprehensively**
4. **Document clearly and directly**
5. **No rah-rah, just solutions**

### Development Setup

```bash
# Install development dependencies
uv pip install -r requirements.txt

# Run tests
python -m pytest tests/ -v

# Check code style
python -m black immich/ tests/
python -m isort immich/ tests/
```


## 🛡️ Industrial Quality Stack

This project adheres to **SOTA 14.1** industrial standards for high-fidelity agentic orchestration:

- **Python (Core)**: [Ruff](https://astral.sh/ruff) for linting and formatting. Zero-tolerance for `print` statements in core handlers (`T201`).
- **Webapp (UI)**: [Biome](https://biomejs.dev/) for sub-millisecond linting. Strict `noConsoleLog` enforcement.
- **Protocol Compliance**: Hardened `stdout/stderr` isolation to ensure crash-resistant JSON-RPC communication.
- **Automation**: [Justfile](./justfile) recipes for all fleet operations (`just lint`, `just fix`, `just dev`).
- **Security**: Automated audits via `bandit` and `safety`.

##  License

[Your chosen license - typically MIT for MCP servers]

##  Related Projects

- **[Immich](https://immich.app/)**: Self-hosted photo and video backup solution
- **[FastMCP](https://github.com/jlowin/fastmcp)**: Framework for building MCP servers
- **[MCP Protocol](https://spec.modelcontextprotocol.io/)**: Model Context Protocol specification

##  API Compatibility Status

### Immich Version Compatibility Matrix

| Immich Version | ImmichMCP Status | Notes |
|----------------|------------------|-------|
| **v3.1.x** | ✅ Working | Verified against official OpenAPI spec (2026-08-06) |
| **v3.0.x** | ✅ Working | Breaking changes handled (upload payload, album users) |
| **v2.7.x** | ✅ Working | Current production contract; verified live |
| **v2.4-2.6** | ✅ Working | Search-based API (older contract) |
| **v2.3.1** | ✅ Working | Basic + OCR operations |
| **v2.0-2.2** | ✅ Working | Basic operations |

---

##  Changelog

### v1.4.0 (2025-12-18) - Dual Transport Architecture

-  **Dual transport implemented** - MCP stdio + HTTP REST API support
-  **HTTP REST API endpoints** - All 15+ MCP tools available via HTTP
-  **Immich++ integration** - Seamless integration with web frontend
-  **CORS support** - Web client access enabled
-  **Comprehensive API documentation** - All endpoints documented
-  **Automatic fallback support** - Immich++ can use MCP or direct API

### v1.3.0 (2025-12-18) - API Migration Discovery

-  **Immich v2.4.0 compatibility issue discovered** - Major API architecture change
-  **Search-based asset access** - New `/api/search/metadata` endpoint required
-  **Direct asset endpoints removed** - `/api/assets` and `/api/assets/:id` no longer exist
-  **Migration documentation added** - Comprehensive API change analysis
-  **Alternative solution available** - Immich++ updated for v2.4.0 compatibility

### v1.2.0 (2025-12-18)

-  **Immich v2.3.1+ compatibility** - Full support for latest stable release
-  **Enhanced multilingual OCR** - Support for Greek, Korean, Russian, Belarusian, Ukrainian, Thai, Latin script languages
-  **OCR bounding boxes** - Precise text location coordinates for highlighting
-  **Advanced OCR tools** - New `get_ocr_data` tool with bounding box support
-  **Language-specific OCR models** - Choose optimal models for different languages
-  **Improved version detection** - Automatic detection of v2.3.x features and capabilities

### v1.1.0 (2025-01-27)

-  **Immich v2.0.0+ compatibility** - Full support for stable Immich v2.0.0+
-  **OCR search support** - Text extraction search for Immich v2.2.0+
-  **Enhanced error handling** - Improved v2.0.0+ API error messages
-  **Version detection** - Automatic detection of Immich v2.0.0+ and OCR capabilities

### v1.0.0 (2025-07-22)

-  **Initial FastMCP 3.1 implementation**
-  **15 comprehensive photo management tools**
-  **Austrian efficiency optimization**
-  **Complete documentation and testing**
-  **Vienna-specific localization support**

---

**Built with Austrian efficiency**  | **Working solutions in hours, not days**  | **Sin temor y sin esperanza**


##  Webapp Dashboard

This MCP server includes a free, premium web interface (React + Vite + Tailwind) for monitoring and control.

**Registered ports** (fleet WEBAPP_PORTS.md):

| Port | Service |
|------|---------|
| 10838 | Webapp frontend (Vite dev) |
| 10839 | Backend (FastAPI + MCP HTTP) |

To start the webapp:
1. Navigate to the `web_sota` directory.
2. Run `start.bat` (Windows) or `./start.ps1` (PowerShell).
3. Open `http://localhost:10838` in your browser.
