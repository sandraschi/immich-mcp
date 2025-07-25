# Immich MCP Troubleshooting Guide

**Austrian Efficiency** | **Direct Communication** | **No Gaslighting**

## Quick Diagnostics

### 1. Test Basic Connection

```bash
python -c "
from immich.manager import ImmichManager
import os
from dotenv import load_dotenv

load_dotenv()
manager = ImmichManager(os.getenv('IMMICH_URL'), os.getenv('IMMICH_API_KEY'))
print('✅ Connection successful' if manager.test_connection() else '❌ Connection failed')
"
```

### 2. Check Server Health

Use the MCP tool:
```
Check if Immich server is responding properly
```

Expected response:
```json
{
  "status": "healthy",
  "server_version": "v1.x.x",
  "api_accessible": true
}
```

## Common Issues & Solutions

### Connection Problems

#### ❌ `Connection refused` / `Connection timeout`

**Symptoms:**
- Cannot connect to Immich server
- Timeout errors on all operations
- "Connection refused" messages

**Austrian diagnosis:** Your Immich server isn't running or accessible.

**Solutions:**
1. **Check Immich server status:**
   ```bash
   curl http://localhost:2283/api/server-info
   ```

2. **Verify URL format:**
   ```bash
   # Correct
   IMMICH_URL=http://localhost:2283
   
   # Incorrect
   IMMICH_URL=http://localhost:2283/  # No trailing slash
   IMMICH_URL=localhost:2283          # Missing protocol
   ```

3. **Check Docker/service status:**
   ```bash
   docker ps | grep immich
   # or
   systemctl status immich
   ```

#### ❌ `Unauthorized` / `Invalid API key`

**Symptoms:**
- 401 Unauthorized errors
- "Invalid API key" responses
- Authentication failures

**Austrian diagnosis:** Your API key is wrong, expired, or missing.

**Solutions:**
1. **Regenerate API key in Immich:**
   - Web UI → User Settings → API Keys
   - Delete old key, create new one
   - Update `.env` file

2. **Verify key format:**
   ```bash
   # API keys are typically 40+ characters
   echo $IMMICH_API_KEY | wc -c
   ```

3. **Test key manually:**
   ```bash
   curl -H "x-api-key: YOUR_KEY" http://localhost:2283/api/server-info
   ```

### Upload Issues

#### ❌ `File upload failed` / `413 Request Entity Too Large`

**Symptoms:**
- Large files fail to upload
- 413 HTTP status codes
- "File too large" errors

**Austrian diagnosis:** File exceeds size limits (server or MCP).

**Solutions:**
1. **Check file size:**
   ```bash
   ls -lh /path/to/your/file.jpg
   ```

2. **Adjust MCP limits in `config/settings.yaml`:**
   ```yaml
   immich:
     upload:
       max_file_size_mb: 1000  # Increase limit
   ```

3. **Check Immich server limits:**
   - Docker: Adjust `client_max_body_size` in nginx config
   - Standalone: Check reverse proxy settings

#### ❌ `Unsupported file format`

**Symptoms:**
- Specific file types rejected
- "Format not supported" errors

**Austrian diagnosis:** File type not in allowed list.

**Solutions:**
1. **Check supported formats in `config/settings.yaml`:**
   ```yaml
   immich:
     upload:
       supported_formats:
         images: [".jpg", ".jpeg", ".png", ".tiff", ".webp", ".heic", ".raw"]
         videos: [".mp4", ".mov", ".avi", ".mkv", ".webm"]
   ```

2. **Convert unsupported files:**
   ```bash
   # Example: Convert HEIC to JPEG
   magick convert photo.heic photo.jpg
   ```

### Search & Face Detection Issues

#### ❌ `Smart search not working` / `No CLIP results`

**Symptoms:**
- Search returns no results
- CLIP model errors
- "Search feature unavailable"

**Austrian diagnosis:** Immich's ML features aren't configured properly.

**Solutions:**
1. **Check Immich ML container:**
   ```bash
   docker logs immich_machine_learning
   ```

2. **Verify search is enabled:**
   ```yaml
   immich:
     features:
       smart_search: true
   ```

3. **Rebuild search index in Immich:**
   - Web UI → Administration → Jobs
   - Run "Smart Search" job

#### ❌ `Face detection failed`

**Symptoms:**
- No faces detected in photos
- Face detection errors
- People search returns empty

**Austrian diagnosis:** Face detection model not loaded or configured.

**Solutions:**
1. **Enable face detection:**
   ```yaml
   immich:
     features:
       face_detection: true
   ```

2. **Check ML container logs:**
   ```bash
   docker logs immich_machine_learning | grep face
   ```

3. **Manually trigger face detection:**
   ```
   Run face detection on all my new photos
   ```

### Performance Issues

#### ❌ `Slow responses` / `Operations timing out`

**Symptoms:**
- Long wait times for operations
- Timeout errors after delays
- Sluggish photo browsing

**Austrian diagnosis:** Server overloaded or inefficient settings.

**Solutions:**
1. **Reduce concurrent operations:**
   ```yaml
   server:
     concurrent_uploads: 2  # Lower value
     timeout: 60           # Longer timeout
   ```

2. **Enable bandwidth optimization:**
   ```yaml
   efficiency:
     optimize_bandwidth: true
     cache_duration: 600    # Cache longer
     batch_size: 25        # Smaller batches
   ```

3. **Check server resources:**
   ```bash
   # CPU and memory usage
   top
   # Disk space
   df -h
   ```

### Album & Organization Issues

#### ❌ `Album creation failed`

**Symptoms:**
- Cannot create new albums
- Album operations fail
- "Insufficient permissions" errors

**Austrian diagnosis:** User permissions or Immich configuration issue.

**Solutions:**
1. **Check user permissions in Immich:**
   - Ensure user can create albums
   - Verify not in read-only mode

2. **Test album creation manually:**
   ```
   Create album "Test Album" 
   ```

3. **Check Immich logs:**
   ```bash
   docker logs immich_server | grep album
   ```

## Debugging Tools

### Enable Debug Logging

In `.env`:
```bash
LOG_LEVEL=DEBUG
```

Restart server and check detailed logs for operation traces.

### Manual API Testing

Test Immich API directly:

```bash
# Server info
curl -H "x-api-key: YOUR_KEY" http://localhost:2283/api/server-info

# List albums  
curl -H "x-api-key: YOUR_KEY" http://localhost:2283/api/albums

# Search
curl -H "x-api-key: YOUR_KEY" "http://localhost:2283/api/search/smart?q=dog"
```

### Configuration Validation

```bash
python -c "
import yaml
with open('config/settings.yaml') as f:
    config = yaml.safe_load(f)
    print('✅ Config syntax valid')
    print(f'Server: {config[\"server\"][\"name\"]}')
    print(f'Features: {list(config[\"immich\"][\"features\"].keys())}')
"
```

## Austrian Context Solutions

### Vienna-Specific Issues

If using Austrian/European servers:

1. **Timezone settings:**
   ```yaml
   vienna_deployment:
     timezone: "Europe/Vienna"
     date_format: "DD.MM.YYYY"
   ```

2. **Character encoding:**
   - Ensure UTF-8 support for German characters (ä, ö, ü, ß)
   - Check file path encoding on Windows systems

### Budget-Conscious Performance

Optimizations for ~€100/month AI tools usage:

1. **Reduce API calls:**
   ```yaml
   efficiency:
     cache_duration: 900    # 15-minute cache
     batch_size: 100       # Fewer API requests
   ```

2. **Bandwidth optimization:**
   ```yaml
   efficiency:
     optimize_bandwidth: true
     compress_responses: true
   ```

## When to Report Issues

**Report bugs if:**
- Solutions above don't work after 15 minutes
- Error messages are unclear or misleading
- Performance is worse than expected

**Don't report if:**
- You didn't read this troubleshooting guide first
- Your Immich server itself isn't working
- Issue is clearly stated with solution above

## Emergency Recovery

### Complete Reset

If everything is broken:

1. **Stop server:**
   ```bash
   pkill -f "python server.py"
   ```

2. **Reset configuration:**
   ```bash
   cp config/settings.yaml.example config/settings.yaml
   cp .env.example .env
   ```

3. **Edit `.env` with correct values**

4. **Test connection:**
   ```bash
   python -c "from immich.manager import ImmichManager; print('✅ Works')"
   ```

5. **Restart server:**
   ```bash
   python server.py
   ```

**Austrian guarantee:** If this doesn't work, the problem is with Immich itself or your server setup, not the MCP implementation.

## Getting Help

1. **Check Immich server logs first**
2. **Verify issue isn't already documented above**
3. **Include specific error messages and configuration when asking for help**
4. **Direct communication**: We'll tell you exactly what's wrong, no gaslighting

Remember: Most issues take under 10 minutes to resolve with this guide. If you're stuck longer, something is genuinely broken.
