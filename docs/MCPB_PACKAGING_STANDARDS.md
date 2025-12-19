# MCPB Packaging Standards

**Version:** 1.0  
**Date:** 2025-10-24  
**Status:** Official Standard  
**Applies to:** All MCP projects using MCPB packaging

---

## 🎯 **Overview**

**MCPB (Model Context Protocol Bundle) is the packaging format used EXCLUSIVELY for Claude Desktop installations.** This document defines the complete standards for MCPB packaging.

### ⚠️ **Critical MCPB Requirements**

1. **NO Dependencies**: MCPB packages must NOT include any Python dependencies or libraries. Claude Desktop provides its own Python runtime and dependencies must be installed separately by the user.

2. **Extensive Prompt Templates**: MCPB packages MUST include comprehensive prompt templates in the `prompts/` directory. These templates are read by Claude Desktop to understand how to interact with your MCP server.

3. **Claude Desktop Only**: MCPB format is ONLY used for Claude Desktop. For other MCP clients (Cursor, Windsurf, etc.), use standard MCP server installation methods (npm/npx or local installation).

4. **Weird Installation**: MCPB packages are installed by dragging the `.mcpb` file into Claude Desktop settings. There is no command-line installer.

---

## 📦 **MCPB Package Structure**

### **Required Files**

```
mcp-server/
├── manifest.json          # MCPB manifest configuration
├── assets/                # Package assets
│   ├── icon.png          # Package icon
│   ├── screenshots/      # Screenshots for documentation
│   └── prompts/          # EXTENSIVE prompt templates (REQUIRED)
│       ├── system.md     # System prompt for Claude Desktop
│       ├── user.md       # User interaction templates
│       └── examples.json # Usage examples
├── src/                  # Source code ONLY (no dependencies)
│   └── package_name/
│       ├── __init__.py
│       ├── mcp_server.py
│       └── tools/
└── README.md            # Package documentation
```

### ⚠️ **What MCPB Packages MUST NOT Include**

- ❌ **NO `requirements.txt`** - Dependencies are NOT bundled
- ❌ **NO `pyproject.toml`** - Not used by Claude Desktop
- ❌ **NO `lib/` or `dependencies/` directories** - No bundled libraries
- ❌ **NO virtual environments** - Claude Desktop provides Python runtime

### ✅ **What MCPB Packages MUST Include**

- ✅ **Extensive `prompts/` directory** - Comprehensive prompt templates for Claude Desktop
- ✅ **Source code only** - Just your Python server code
- ✅ **Clear documentation** - README explaining installation and configuration

---

## 📋 **Manifest Configuration**

### **Required Manifest Structure**

```json
{
  "manifest_version": "0.2",
  "server": {
    "type": "python",
    "entry_point": "src/package_name/mcp_server.py",
    "mcp_config": {
      "command": "python",
      "args": ["-m", "package_name.mcp_server"],
      "env": {
        "PYTHONPATH": "${PWD}",
        "PYTHONUNBUFFERED": "1"
      }
    }
  },
  "user_config": {
    "api_key": {
      "type": "string",
      "title": "API Key",
      "required": true,
      "default": ""
    },
    "timeout": {
      "type": "string",
      "title": "Operation Timeout (seconds)",
      "default": "30"
    }
  },
  "tools": [
    {
      "name": "tool_name_1",
      "description": "Brief description of what this tool does"
    },
    {
      "name": "tool_name_2",
      "description": "Brief description of what this tool does"
    }
  ],
  "compatibility": {
    "platforms": ["win32", "darwin", "linux"],
    "python": ">=3.10"
  }
}
```

### **Manifest Requirements**

#### **Server Configuration**
- **type**: Must be "python"
- **entry_point**: Path to main server file
- **mcp_config**: Python execution configuration
- **env**: Environment variables for runtime

#### **User Configuration**
- **api_key**: API key for external services
- **timeout**: Operation timeout settings
- **Custom settings**: Application-specific configuration

#### **Tools Array**
- **Format**: Array of objects with `name` and `description` fields
- **Required fields**: Each tool must have `name` (string) and `description` (string)
- **Complete list**: Must match actual tool registrations in the server code
- **Example**:
  ```json
  "tools": [
    {
      "name": "upload_photos",
      "description": "Upload photos to Immich with batch processing"
    },
    {
      "name": "search_photos",
      "description": "Search photos using CLIP smart search"
    }
  ]
  ```

#### **Compatibility**
- **platforms**: Supported operating systems
- **python**: Minimum Python version requirement

---

## 🔧 **Build Process**

### **MCPB CLI Installation**

```bash
# Install MCPB CLI
npm install -g @anthropic-ai/mcpb

# Verify installation
mcpb --version
```

### **Package Building**

```bash
# Build MCPB package
mcpb pack . dist/package-name-v{version}.mcpb

# Build with validation
mcpb pack . dist/package-name-v{version}.mcpb --validate

# Build with signing (if configured)
mcpb pack . dist/package-name-v{version}.mcpb --sign
```

### **Package Validation**

```bash
# Validate manifest
mcpb validate manifest.json

# Validate package
mcpb validate dist/package-name-v{version}.mcpb
```

---

## 📁 **Assets Directory**

### **Required Assets**

```
assets/
├── icon.png              # Package icon (256x256px)
├── screenshots/          # Screenshots for documentation
│   ├── dashboard.png
│   ├── configuration.png
│   └── usage.png
└── prompts/             # EXTENSIVE prompt templates (REQUIRED)
    ├── system.md        # System prompt (REQUIRED)
    ├── user.md          # User interaction templates (REQUIRED)
    ├── examples.json    # Usage examples (REQUIRED)
    ├── quick-start.md   # Quick start guide
    ├── configuration.md # Configuration guide
    └── troubleshooting.md # Troubleshooting guide
```

### **Asset Requirements**

#### **Icon**
- **Size**: 256x256 pixels
- **Format**: PNG
- **Style**: Clear, recognizable, professional
- **Purpose**: Package identification in Claude Desktop

#### **Screenshots**
- **Purpose**: Documentation and marketing
- **Quality**: High resolution, clear text
- **Content**: Key features, configuration, usage

#### **Prompts (CRITICAL - REQUIRED)**
- **Purpose**: Claude Desktop reads these to understand your MCP server
- **Format**: Markdown for text, JSON for structured data
- **Content**: MUST be extensive and comprehensive
  - **system.md**: System-level instructions for Claude Desktop
  - **user.md**: User interaction templates and examples
  - **examples.json**: Structured examples of tool usage
  - **Additional guides**: Quick start, configuration, troubleshooting
- **Why Required**: Claude Desktop uses these prompts to generate appropriate tool calls and responses

---

## 🐍 **Python Configuration**

### **pyproject.toml Requirements**

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "package-name"
version = "1.0.0"
description = "MCP server description"
readme = "README.md"
requires-python = ">=3.10"
dependencies = [
    "fastmcp>=2.12",
    "httpx>=0.24.0",
    "structlog>=23.0.0"
]

[project.optional-dependencies]
dev = [
    "ruff>=0.1.0",
    "pytest>=7.0.0",
    "pytest-cov>=4.0.0",
    "pytest-asyncio>=0.21.0"
]

[tool.ruff]
select = ["E", "F", "W", "C90", "I", "N", "UP", "YTT", "S", "BLE", "FBT", "B", "A", "COM", "C4", "DTZ", "T10", "EM", "EXE", "ISC", "ICN", "G", "INP", "PIE", "T20", "PYI", "PT", "Q", "RSE", "RET", "SLF", "SLOT", "SIM", "TID", "TCH", "INT", "ARG", "PTH", "TD", "FIX", "ERA", "PD", "PGH", "PL", "TRY", "FLY", "NPY", "AIR", "PERF"]
ignore = ["E501", "W503"]
target-version = "py310"

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
```

### **requirements.txt Requirements**

```
# Core dependencies
fastmcp>=2.12
httpx>=0.24.0
structlog>=23.0.0
prometheus-client>=0.19.0

# Optional dependencies
aiohttp>=3.8.0
pydantic>=2.0.0
```

---

## 🚀 **CI/CD Integration**

### **GitHub Actions Workflow**

```yaml
name: Build and Package

on:
  push:
    tags:
      - 'v*'
  pull_request:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
          
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          npm install -g @anthropic-ai/mcpb
          
      - name: Run tests
        run: |
          pytest tests/
          
      - name: Build MCPB package
        run: |
          mcpb pack . dist/package-name-v${{ github.ref_name }}.mcpb
          
      - name: Upload artifacts
        uses: actions/upload-artifact@v3
        with:
          name: mcpb-package
          path: dist/
```

---

## 📚 **Documentation Requirements**

### **README.md Requirements**

```markdown
# Package Name

Brief description of the MCP server.

## Features

- Feature 1
- Feature 2
- Feature 3

## Installation

### Prerequisites

- Python 3.10+
- Required dependencies

### Install via MCPB

1. Download the .mcpb package
2. Drag to Claude Desktop
3. Configure settings

## Configuration

### Environment Variables

- `API_KEY`: Required API key
- `TIMEOUT`: Operation timeout (default: 30)

### User Configuration

Configure via Claude Desktop settings panel.

## Usage

### Basic Usage

```python
# Example usage
```

### Advanced Usage

```python
# Advanced examples
```

## Troubleshooting

### Common Issues

- Issue 1: Solution
- Issue 2: Solution

## License

MIT License
```

---

## 🔍 **Quality Standards**

### **Package Validation**

- **Manifest validation**: All required fields present
- **Tool registration**: All tools properly registered
- **Asset validation**: All required assets present
- **Python validation**: Code quality and testing

### **Testing Requirements**

- **Unit tests**: All tools and functions tested
- **Integration tests**: End-to-end workflows tested
- **Coverage**: 80%+ code coverage
- **Quality gates**: Ruff linting, security scanning

### **Security Standards**

- **Input validation**: All inputs validated
- **Error handling**: Secure error handling
- **Dependencies**: Security scanning of dependencies
- **Secrets**: Proper handling of API keys and secrets

---

## 📦 **Distribution**

### **Package Distribution**

- **GitHub Releases**: Automated package releases (`.mcpb` files)
- **Claude Desktop Only**: MCPB packages are ONLY for Claude Desktop
  - Installation: Drag-and-drop `.mcpb` file into Claude Desktop settings
  - No command-line installer available
  - No npm/npx installation method
- **Other MCP Clients**: Use standard installation methods (npm/npx or local clone)
- **Documentation**: Complete usage documentation
- **Support**: Issue tracking and support

### **Version Management**

- **Semantic versioning**: Major.Minor.Patch
- **Changelog**: Complete change documentation
- **Migration guides**: Breaking change documentation
- **Compatibility**: Version compatibility matrix

---

## 🎯 **Best Practices**

### **Package Design**

- **Single responsibility**: One package, one purpose
- **Clear naming**: Descriptive package and tool names
- **Comprehensive documentation**: Complete API documentation
- **User experience**: Intuitive configuration and usage

### **Development Process**

- **Version control**: Proper Git workflow
- **Testing**: Comprehensive test coverage
- **Documentation**: Up-to-date documentation
- **Quality assurance**: Automated quality checks

### **Maintenance**

- **Regular updates**: Keep dependencies current
- **Security patches**: Prompt security updates
- **Bug fixes**: Quick bug fix releases
- **Feature updates**: Regular feature releases

---

## 📞 **Support & Resources**

- **MCPB Documentation**: Official MCPB documentation
- **Claude Desktop**: Installation and usage guide
- **GitHub Issues**: Bug reports and feature requests
- **Community**: MCP community support

---

*Document created: October 24, 2025*  
*Status: Official Standard*  
*Next Review: As needed for standards updates*
