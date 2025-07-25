# Immich MCP Server API Documentation

**FastMCP 2.0 Implementation** | **Austrian Dev Efficiency** | **Complete Photo Management**

## Overview

The Immich MCP Server provides comprehensive photo library management through natural language commands via the MCP (Model Context Protocol). Built with Austrian efficiency principles: working solutions in hours, not days.

## Available Tools

### 📸 Core Photo Operations

#### `upload_photos`
Upload multiple photos/videos to Immich with metadata preservation.

**Parameters:**
- `file_paths` (List[str]): Paths to photos/videos to upload
- `album_name` (Optional[str]): Album to add photos to
- `preserve_metadata` (bool, default=True): Keep EXIF data

**Example:**
```
Upload my vacation photos from /photos/vacation/ to a new album called "Vienna Trip 2025"
```

#### `search_photos`
CLIP-based intelligent photo search using natural language.

**Parameters:**
- `query` (str): Natural language search query
- `limit` (int, default=20): Maximum results to return

**Example:**
```
Find photos of Benny (my dog) playing in the park
```

#### `get_photo_info`
Get detailed metadata and information about specific photos.

**Parameters:**
- `asset_id` (str): Immich asset identifier

**Example:**
```
Show me details about photo ID abc123
```

#### `organize_photos_by_date`
Automatically organize photos into date-based folder structure.

**Parameters:**
- `start_date` (Optional[str]): Start date for organization (YYYY-MM-DD)
- `end_date` (Optional[str]): End date for organization
- `folder_pattern` (str, default="YYYY/MM"): Date folder structure

**Example:**
```
Organize all photos from 2025 by month
```

#### `delete_photos`
Safely delete photos with optional trash/permanent deletion.

**Parameters:**
- `asset_ids` (List[str]): Photo IDs to delete
- `permanent` (bool, default=False): Skip trash, delete permanently

**Example:**
```
Delete photo ID xyz789 permanently
```

### 📂 Album Management

#### `create_album`
Create new photo albums with optional initial photos.

**Parameters:**
- `album_name` (str): Name for the new album
- `description` (Optional[str]): Album description
- `asset_ids` (Optional[List[str]]): Initial photos to add

**Example:**
```
Create album "Vienna Winter 2025" with photos abc123, def456
```

#### `add_to_album`
Add photos to existing albums.

**Parameters:**
- `album_id` (str): Target album identifier
- `asset_ids` (List[str]): Photos to add

**Example:**
```
Add photos xyz789, abc456 to my Vienna album
```

#### `list_albums`
Browse all albums with statistics and recent photos.

**Parameters:**
- `limit` (int, default=50): Maximum albums to return
- `include_stats` (bool, default=True): Include photo counts and dates

**Example:**
```
Show me all my photo albums with statistics
```

#### `share_album`
Create public sharing links for albums.

**Parameters:**
- `album_id` (str): Album to share
- `expires_days` (Optional[int]): Link expiration in days

**Example:**
```
Create a public link for my Vienna album that expires in 30 days
```

### 👥 People & Face Detection

#### `detect_people`
Process photos for face detection and people recognition.

**Parameters:**
- `asset_ids` (Optional[List[str]]): Specific photos to process
- `force_reprocess` (bool, default=False): Reprocess already detected faces

**Example:**
```
Run face detection on all my new photos
```

#### `tag_person`
Assign names to detected faces for future recognition.

**Parameters:**
- `person_id` (str): Detected person identifier
- `name` (str): Name to assign

**Example:**
```
Tag person ID per123 as "Sandra"
```

#### `search_by_person`
Find all photos containing a specific person.

**Parameters:**
- `person_name` (str): Name of person to search for
- `limit` (int, default=50): Maximum results

**Example:**
```
Find all photos with Marion in them
```

#### `list_people`
Browse all detected people with photo counts.

**Parameters:**
- `limit` (int, default=100): Maximum people to return

**Example:**
```
Show me all detected people in my photo library
```

### 🔧 Administration & Monitoring

#### `get_storage_info`
Monitor Immich storage usage and statistics.

**Parameters:** None

**Example:**
```
Show me my photo library storage statistics
```

#### `backup_photos`
Export photos with metadata for backup purposes.

**Parameters:**
- `destination_path` (str): Where to save backup
- `include_metadata` (bool, default=True): Export metadata files
- `date_range` (Optional[Dict]): Specific date range to backup

**Example:**
```
Backup all photos from 2025 to /backup/photos/ with metadata
```

#### `server_health`
Check Immich server connection and health status.

**Parameters:** None

**Example:**
```
Check if Immich server is responding properly
```

## Error Handling

All tools include comprehensive error handling with Austrian efficiency principles:

- **Direct communication**: Clear, actionable error messages
- **No gaslighting**: Honest about failures and limitations  
- **Detailed context**: Specific information about what went wrong
- **Recovery suggestions**: Practical next steps when possible

## Response Formats

All responses follow structured Pydantic models for consistency:

- **Success responses**: Include requested data plus operation metadata
- **Error responses**: Detailed error info with suggested actions
- **Progress updates**: Real-time feedback for long operations
- **Statistics**: Counts, sizes, and performance metrics where relevant

## Austrian Context Features

- **Budget awareness**: Efficient operations, ~€100/month AI tools consideration
- **Direct communication**: No rah-rah, straight answers
- **Vienna-specific**: Timezone, date formats, localization support
- **Rapid development**: Hours not weeks, practical timelines
