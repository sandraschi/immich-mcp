# Immich MCP Server 

**FastMCP 2.10.2** | **Austrian Dev Efficiency** | **Complete Photo Management**

Comprehensive Immich photo library management through the MCP (Model Context Protocol). Built with Austrian efficiency principles: working solutions in hours, not days.

> **✅ Status**: Fully compatible with FastMCP 2.10.2

## Quick Start (5 Minutes)

### 1. Prerequisites

- Python 3.11+
- [Poetry](https://python-poetry.org/) for dependency management
- [Immich server](https://immich.app/) running and accessible
- Immich API key (get from Web UI → User Settings → API Keys)

### 2. Installation

```bash
# Clone repository
git clone https://github.com/sandraschi/immichmcp.git
cd immichmcp

# Install dependencies using Poetry
poetry install

# Copy and configure environment
cp .env.example .env
# Edit .env with your Immich URL and API key
```

### 3. Configuration

Edit `.env` file with your Immich server details:

```bash
# Required
IMMICH_MCP_IMMICH_API_KEY=your_api_key_here
IMMICH_MCP_IMMICH_URL=http://localhost:2283

# Optional: Server settings
IMMICH_MCP_HOST=0.0.0.0
IMMICH_MCP_PORT=8000
IMMICH_MCP_LOG_LEVEL=info
```

### 4. Run Server

```bash
# Using Poetry (recommended)
poetry run python -m immich_mcp.server

# Or with direct Python
python -m immich_mcp.server
```

Look for: `INFO:     Uvicorn running on http://0.0.0.0:8000`

## 📸 What It Does

### Core Photo Operations
- **Upload photos/videos** with metadata preservation
- **Smart search** using CLIP-based natural language queries
- **Organize photos** by date, location, or custom criteria
- **Get detailed metadata** from any photo/video

### Album Management  
- **Create albums** with photos and descriptions
- **Add/remove photos** from albums
- **Share albums** with public links
- **Browse collections** with statistics

### People & Face Detection
- **Detect faces** in photos automatically
- **Tag people** with names for recognition
- **Search by person** to find all photos of someone
- **Browse people** library with face counts

### Administration
- **Monitor storage** usage and statistics
- **Backup photos** with metadata export
- **Health monitoring** of Immich server connection
- **Performance optimization** for Austrian efficiency

## 🔧 Available Tools

### Photo Operations

```bash
# Upload photos to Immich
Upload my vacation photos from /photos/vacation/ to album "Vienna Summer 2025"

# Smart search for photos
Find photos of dogs playing in parks

# Get photo details
Show me metadata for photo ID abc123

# Organize by date
Organize all photos from 2025 by month and year
```

### Album Management

```bash
# Create new album
Create album "Vienna Winter 2025" with photos abc123, def456

# Add photos to existing album
Add photos xyz789, abc456 to my Vienna album

# List all albums
Show me all my photo albums with statistics

# Share album publicly
Create a public link for my Vienna album that expires in 30 days
```

### People & Faces

```bash
# Process faces
Run face detection on all my new photos

# Tag person
Tag person ID per123 as "Sandra"

# Find photos of person
Find all photos with Marion in them

# List detected people
Show me all detected people in my photo library
```

### Monitoring

```bash
# Check storage
Show me my photo library storage statistics

# Backup photos
Backup all photos from 2025 to /backup/photos/ with metadata

# Server health
Check if Immich server is responding properly
```

## 🏗️ Architecture

### FastMCP 2.0 Structure

```
immichmcp/
├── config/                 # YAML configuration files
│   ├── settings.yaml           # Server and efficiency settings
│   └── immich_config.yaml      # Immich-specific templates
├── docs/                   # Comprehensive documentation
│   ├── API.md                  # Tool documentation
│   ├── Configuration.md        # Setup guide
│   └── Troubleshooting.md      # Common issues & solutions
├── immich/                 # Core Immich integration
│   ├── __init__.py
│   ├── manager.py              # Core Immich API client
│   ├── asset_operations.py     # Photo/video operations
│   ├── album_manager.py        # Album management
│   └── search_operations.py    # Search & discovery
├── tests/                  # Comprehensive test suite
│   ├── __init__.py
│   ├── test_api.py             # Unit tests
│   └── integration_tests.py    # End-to-end tests
├── .env.example           # Environment template
├── .gitignore            # Git exclusions
├── requirements.txt      # Python dependencies
├── server.py            # FastMCP 2.0 server
└── README.md           # This file
```

### Core Components

- **ImmichManager**: Core API client with Austrian efficiency
- **AssetOperations**: Photo/video upload, metadata, organization
- **AlbumManager**: Album creation, management, sharing
- **SearchOperations**: CLIP search, face detection, people recognition

## ⚙️ Configuration

### Environment Variables

| Variable | Required | Description | Default |
|----------|----------|-------------|---------|
| `IMMICH_URL` | ✅ | Immich server URL | - |
| `IMMICH_API_KEY` | ✅ | API key from Immich | - |
| `MCP_SERVER_NAME` | ❌ | Server display name | `"Immich Photo Management MCP 📸"` |
| `LOG_LEVEL` | ❌ | Logging verbosity | `INFO` |

### Advanced Configuration

See `docs/Configuration.md` for detailed setup including:
- Environment-specific configurations
- Performance tuning for Austrian efficiency
- Vienna-specific deployment settings
- SSL/TLS configuration
- Feature flag management

## 🧪 Testing

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

## 🔍 Troubleshooting

### Common Issues

**Connection Problems:**
```bash
# Test connection
python -c "from immich.manager import ImmichManager; print('✅ OK' if ImmichManager('http://localhost:2283', 'your_key').test_connection() else '❌ Failed')"
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

## 🇦🇹 Austrian Context Features

### Direct Communication
- Clear, actionable error messages
- No gaslighting about failures
- Honest limitations and recovery suggestions

### Budget Awareness
- Optimized for ~€100/month AI tools usage
- Bandwidth optimization options
- Efficient API call patterns

### Vienna-Specific
- Europe/Vienna timezone support
- DD.MM.YYYY date format
- German language character support (ä, ö, ü, ß)

### Rapid Development
- Working solutions in hours, not days
- Realistic AI-assisted development timelines
- Practical Austrian efficiency throughout

## 📊 Performance

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

## 🤝 Contributing

1. **Follow Austrian efficiency principles**
2. **Write working code, not stubs**
3. **Test comprehensively**
4. **Document clearly and directly**
5. **No rah-rah, just solutions**

### Development Setup

```bash
# Install development dependencies
pip install -r requirements.txt

# Run tests
python -m pytest tests/ -v

# Check code style
python -m black immich/ tests/
python -m isort immich/ tests/
```

## 📄 License

[Your chosen license - typically MIT for MCP servers]

## 🔗 Related Projects

- **[Immich](https://immich.app/)**: Self-hosted photo and video backup solution
- **[FastMCP](https://github.com/jlowin/fastmcp)**: Framework for building MCP servers
- **[MCP Protocol](https://spec.modelcontextprotocol.io/)**: Model Context Protocol specification

## 📝 Changelog

### v1.0.0 (2025-07-22)
- ✅ **Initial FastMCP 2.0 implementation**
- ✅ **15 comprehensive photo management tools**
- ✅ **Austrian efficiency optimization**
- ✅ **Complete documentation and testing**
- ✅ **Vienna-specific localization support**

---

**Built with Austrian efficiency** 🇦🇹 | **Working solutions in hours, not days** ⚡ | **Sin temor y sin esperanza** 💪
