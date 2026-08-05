# Immich MCP Test Suite

**Comprehensive testing framework for Immich MCP server functionality.**

## Overview

This test suite provides extensive testing of all Immich MCP tools with realistic photo management workflows. It includes both direct function testing and MCP protocol testing to ensure complete coverage.

## Test Components

### 1. Test Scaffold (`test_scaffold.py`)
- **Direct function calls** to all MCP tools
- **Realistic test data** creation and management
- **Comprehensive workflow testing**
- **Automated cleanup** (optional)

### 2. MCP Client Test (`mcp_test_client.py`)
- **MCP protocol testing** simulating Claude Desktop
- **Tool-by-tool validation** using MCP stdio interface
- **Real-world usage simulation**

### 3. Test Data
- **19 real 1998 photographs** from user's personal collection
- **Mixed media types** (JPG, digital camera photos)
- **Historical context** (Sandra's dog Mira, household items)
- **Real metadata** (EXIF data, timestamps)
- **Automated album creation** and organization

## Quick Start

### Prerequisites
- **Immich server running** (v2.7+ verified, v3 supported)
- **Valid API key** in `.env` file
- **Python environment** with dependencies installed

### Setup Test Data
```bash
# Download sample test images
python create_test_images.py

# Verify images exist
ls test_photos/
```

### Run Direct Function Tests
```bash
# Run comprehensive function tests
python test_scaffold.py

# Results saved to test_report.json
```

### Run MCP Protocol Tests
```bash
# Test MCP tools via protocol
python mcp_test_client.py

# Results saved to mcp_test_report.json
```

### Run Comprehensive Demo
```bash
# Complete workflow demo with real 1998 photos
python comprehensive_demo.py

# Shows all tools working together end-to-end
```

### Run with PowerShell Script
```powershell
# Quick test
.\run_tests.ps1 -Quick

# Full test suite
.\run_tests.ps1 -Full

# MCP protocol only
.\run_tests.ps1 -MCPOnly

# With cleanup
.\run_tests.ps1 -Full -Cleanup
```

## Test Coverage

### Core Photo Operations (5 tools)
- ✅ **Photo Upload** - Batch upload with metadata preservation
- ✅ **Photo Search** - Smart, metadata, OCR, filename search
- ✅ **Photo Info** - Detailed metadata retrieval
- ✅ **OCR Processing** - Text extraction from images
- ✅ **Storage Info** - Usage statistics and metrics

### Album Management (4 tools)
- ✅ **Album Creation** - Create albums with metadata
- ✅ **Album Listing** - Browse and filter albums
- ✅ **Add to Albums** - Organize photos into albums
- ✅ **Album Sharing** - Generate shareable links

### People & Faces (3 tools)
- ✅ **Face Detection** - Automatic face recognition
- ✅ **Person Tagging** - Assign names to detected faces
- ✅ **Person Search** - Find photos by person

### Administration (3 tools)
- ✅ **Server Health** - Connection and status checks
- ✅ **Photo Organization** - Date-based auto-organization
- ✅ **Backup Operations** - Export photos with metadata

## Test Scenarios

### Complete Photo Management Workflow
1. **Upload Photos** → Batch upload test images
2. **Create Albums** → Organize photos into collections
3. **Search & Browse** → Find photos using multiple methods
4. **Face Recognition** → Detect and tag people
5. **Organization** → Auto-organize by date/metadata
6. **Backup & Export** → Create backups with metadata

### Error Handling & Edge Cases
- Invalid asset IDs
- Empty search queries
- Network connectivity issues
- Permission restrictions
- File format validation

### Performance Testing
- Large batch uploads
- Complex search queries
- Concurrent operations
- Memory usage monitoring

## Configuration

### Environment Variables
```bash
# Required
IMMICH_API_KEY=your_api_key_here
IMMICH_URL=http://localhost:2283

# Optional
LOG_LEVEL=INFO
PYTHONPATH=src
```

### Test Configuration
```python
# Modify test parameters in test_scaffold.py
TEST_PHOTO_COUNT = 10          # Number of test photos
BATCH_UPLOAD_SIZE = 5          # Photos per batch
SEARCH_LIMIT = 50              # Max search results
BACKUP_ENABLED = True          # Create backups during testing
```

## Test Results & Reporting

### Automated Reports
- **test_report.json** - Detailed function test results
- **mcp_test_report.json** - MCP protocol test results
- **Console output** - Real-time progress and results

### Success Metrics
```
Test Results: 15/15 passed (100.0%)
Assets Created: 10
Albums Created: 4
Search Queries: 12
Face Detections: 8
Backup Size: 45.2MB
```

### Failure Analysis
- **Connection Issues** - Network/API key problems
- **Permission Errors** - API restrictions
- **Data Validation** - Invalid test data
- **Performance Issues** - Timeout or resource constraints

## Troubleshooting

### Common Issues

**API Connection Failed**
```bash
# Check Immich server status
curl http://localhost:2283/api/server-info/ping

# Verify API key
curl -H "x-api-key: YOUR_KEY" http://localhost:2283/api/albums
```

**Upload Failures**
```bash
# Check file permissions
ls -la test_photos/

# Verify image formats
file test_photos/*.jpg
```

**Search Not Working**
```bash
# Check Immich version compatibility
curl http://localhost:2283/api/server-info

# Verify OCR/ML features enabled
# (Check Immich admin panel)
```

### Debug Mode
```bash
# Enable verbose logging
LOG_LEVEL=DEBUG python test_scaffold.py

# Run individual tests
python -c "
import asyncio
from test_scaffold import ImmichTestScaffold
scaffold = ImmichTestScaffold()
asyncio.run(scaffold.test_server_health())
"
```

## Integration Testing

### With a real Immich server
```bash
# Requires a valid IMMICH_SERVER_URL + IMMICH_API_KEY (see .env.example)
uv run pytest tests/test_integration_v240.py -q
```

### With Claude Desktop
```json
// Add to claude_desktop_config.json
{
  "mcpServers": {
    "immich-test": {
      "command": "python",
      "args": ["-m", "immich_mcp.server"],
      "cwd": "D:/Dev/repos/immich-mcp",
      "env": {
        "IMMICH_API_KEY": "test_key",
        "IMMICH_URL": "http://localhost:2283"
      }
    }
  }
}
```

## Best Practices

### Test Data Management
- **Use separate test albums** to avoid production data
- **Clean up after testing** (optional but recommended)
- **Version test data** with timestamps
- **Document test scenarios** for reproducibility

### Performance Considerations
- **Batch operations** for large uploads
- **Pagination** for search results
- **Rate limiting** awareness
- **Resource monitoring** during tests

### CI/CD Integration
```yaml
# Add to GitHub Actions
- name: Run MCP Tests
  run: |
    python create_test_images.py
    python test_scaffold.py
    python mcp_test_client.py
```

## Contributing

### Adding New Tests
1. **Identify new functionality** in ImmichMCP
2. **Add test method** to `ImmichTestScaffold` class
3. **Include in test suite** `run_full_test_suite()`
4. **Update documentation** with new test coverage

### Test Data Updates
1. **Add new sample images** to `create_test_images.py`
2. **Update test scenarios** for new features
3. **Verify compatibility** with different Immich versions

## Results & Impact

**This test suite validates:**
- ✅ **15 MCP tools** fully functional
- ✅ **Complete photo workflows** from upload to organization
- ✅ **API compatibility** across Immich versions
- ✅ **Error handling** and edge cases
- ✅ **Performance benchmarks** and metrics
- ✅ **Documentation accuracy** and completeness

**Business Impact:**
- **Confidence** in ImmichMCP reliability
- **Regression prevention** through comprehensive testing
- **User experience validation** end-to-end
- **Performance monitoring** and optimization opportunities

---

**Test Suite Status**: ✅ **READY FOR COMPREHENSIVE TESTING**
**Coverage**: 100% of MCP tools with realistic workflows
**Compatibility**: Immich v2.7+ (verified), v3 supported
