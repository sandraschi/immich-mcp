# Immich MCP Configuration Guide

**FastMCP 2.0 Setup** | **Austrian Efficiency** | **Working in Hours**

## Quick Start (5 Minutes)

### 1. Environment Setup

Create `.env` file in project root:

```bash
# Required - Your Immich server connection
IMMICH_URL=http://localhost:2283
IMMICH_API_KEY=your_api_key_here

# Optional - Customize server behavior
MCP_SERVER_NAME="Immich Photo Management MCP 📸"
LOG_LEVEL=INFO
```

### 2. Get Immich API Key

1. Open Immich web interface
2. Navigate to **User Settings** → **API Keys**
3. Click **"Create API Key"**
4. Copy the generated key to your `.env` file

### 3. Test Connection

```bash
python server.py
```

Look for: `✅ Immich MCP Server ready!`

## Configuration Files

### `config/settings.yaml`

Main server configuration with Austrian efficiency settings:

```yaml
server:
  name: "Immich Photo Management MCP 📸"
  timeout: 30
  max_retries: 3
  
immich:
  api_timeout: 30
  features:
    face_detection: true
    smart_search: true
    auto_tagging: true
  
efficiency:
  verbose_errors: true
  optimize_bandwidth: true
```

### `config/immich_config.yaml`

Environment-specific templates:

```yaml
development:
  url: "http://localhost:2283"
  concurrent_uploads: 3
  
production:
  url: "${IMMICH_URL}"
  concurrent_uploads: 5
  verify_ssl: true
  
vienna_deployment:
  timezone: "Europe/Vienna"
  date_format: "DD.MM.YYYY"
  language: "de"
```

## Environment Variables

### Required

| Variable | Description | Example |
|----------|-------------|---------|
| `IMMICH_URL` | Immich server URL | `http://localhost:2283` |
| `IMMICH_API_KEY` | API key from Immich | `abc123...` |

### Optional

| Variable | Description | Default |
|----------|-------------|---------|
| `MCP_SERVER_NAME` | Server display name | `"Immich Photo Management MCP 📸"` |
| `LOG_LEVEL` | Logging verbosity | `INFO` |
| `IMMICH_TIMEOUT` | API request timeout | `30` |
| `MAX_UPLOAD_SIZE_MB` | Upload size limit | `500` |

## Deployment Scenarios

### Local Development

```bash
# .env
IMMICH_URL=http://localhost:2283
IMMICH_API_KEY=dev_key_12345
LOG_LEVEL=DEBUG
```

### Docker Deployment

```bash
# .env
IMMICH_URL=http://immich-server:3001
IMMICH_API_KEY=${IMMICH_API_KEY}
LOG_LEVEL=INFO
```

### Production (Vienna Context)

```bash
# .env
IMMICH_URL=https://photos.yourdomain.com
IMMICH_API_KEY=${IMMICH_API_KEY}
LOG_LEVEL=WARNING
MCP_SERVER_NAME="Vienna Photos MCP 📸"
```

## Advanced Configuration

### Upload Settings

Customize in `config/settings.yaml`:

```yaml
immich:
  upload:
    max_file_size_mb: 500
    supported_formats:
      images: [".jpg", ".jpeg", ".png", ".tiff", ".webp", ".heic"]
      videos: [".mp4", ".mov", ".avi", ".mkv"]
    preserve_metadata: true
    auto_organize: false
```

### Performance Tuning

```yaml
server:
  concurrent_uploads: 5  # Adjust based on server capacity
  timeout: 30           # API timeout in seconds
  max_retries: 3        # Retry failed operations

efficiency:
  cache_duration: 300   # Cache API responses (seconds)
  batch_size: 50       # Bulk operation size
  parallel_processing: true
  optimize_bandwidth: true  # Austrian budget awareness
```

### Face Detection Settings

```yaml
immich:
  features:
    face_detection: true
    smart_search: true
    auto_tagging: true    # Auto-assign names
    bulk_operations: true
```

## Security Configuration

### SSL/TLS Setup

For production deployments:

```yaml
production:
  url: "https://your-immich-server.com"
  security:
    verify_ssl: true
    timeout_extensions: false
```

### API Key Security

**Never commit API keys to version control!**

Use environment variables or secure key management:

```bash
# Good - Environment variable
export IMMICH_API_KEY="your_key_here"

# Good - .env file (add to .gitignore)
echo "IMMICH_API_KEY=your_key_here" >> .env

# Bad - Hard-coded in source
IMMICH_API_KEY = "your_key_here"  # DON'T DO THIS
```

## Troubleshooting Configuration

### Connection Issues

1. **Check Immich URL format:**
   ```bash
   # Correct
   IMMICH_URL=http://localhost:2283
   
   # Incorrect (no trailing slash)
   IMMICH_URL=http://localhost:2283/
   ```

2. **Verify API key validity:**
   ```bash
   curl -H "x-api-key: YOUR_KEY" http://localhost:2283/api/server-info
   ```

3. **Test server availability:**
   ```bash
   curl http://localhost:2283/api/server-info
   ```

### Performance Issues

1. **Reduce concurrent uploads:**
   ```yaml
   server:
     concurrent_uploads: 2  # Lower for slower servers
   ```

2. **Increase timeouts:**
   ```yaml
   immich:
     api_timeout: 60  # For slower connections
   ```

3. **Enable bandwidth optimization:**
   ```yaml
   efficiency:
     optimize_bandwidth: true
     compress_responses: true
   ```

## Austrian Context Notes

- **Direct communication**: Configuration errors will be clearly stated
- **Budget awareness**: Optimized for ~€100/month AI tools usage
- **Vienna timezone**: Automatically configured for Europe/Vienna
- **Rapid setup**: Complete configuration in under 10 minutes
- **No gaslighting**: If something doesn't work, we'll tell you exactly why

## Migration from Other Versions

### From FastMCP 1.x

1. Update `requirements.txt`:
   ```
   fastmcp>=2.10.0
   ```

2. Add new config files:
   ```bash
   cp config/settings.yaml.example config/settings.yaml
   ```

3. Update environment variables per this guide

### From Custom Implementations

1. Export your current settings to `.env`
2. Run configuration validator:
   ```bash
   python -c "from immich.manager import ImmichManager; print('✅ Config valid')"
   ```
3. Test all tools work as expected

**Austrian efficiency note**: Migration should take 15 minutes maximum. If it takes longer, something is wrong with the documentation (not you).
