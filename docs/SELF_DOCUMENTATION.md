# Self-Documenting FastMCP Tools and DXT Integration

## 🌟 Overview

This guide covers best practices for creating self-documenting FastMCP tools that provide an excellent user experience in Claude's DXT interface. We'll cover tool documentation, help systems, and discoverability patterns.

## 📝 FastMCP Tool Documentation

### Basic Documentation

```python
@mcp.tool(
    name="search_photos",
    description="Search for photos using natural language queries",
    tags=["photos", "search"]
)
async def search_photos(
    query: str,
    limit: int = 10,
    start_date: str | None = None,
    end_date: str | None = None
) -> List[Photo]:
    """Search for photos using natural language queries.
    
    This tool allows you to find photos using natural language descriptions,
    date ranges, and other filters.
    
    Args:
        query: Natural language search query (e.g., 'photos of my dog at the park')
        limit: Maximum number of results to return (default: 10, max: 100)
        start_date: Optional start date (YYYY-MM-DD) for filtering
        end_date: Optional end date (YYYY-MM-DD) for filtering
        
    Returns:
        List of matching Photo objects with metadata
        
    Examples:
        # Find beach photos from last summer
        results = await search_photos(
            query="beach vacation",
            start_date="2024-06-01",
            end_date="2024-08-31"
        )
    """
    # Implementation...
```

### Advanced Documentation with Examples

```python
@mcp.tool(
    name="enhance_photo",
    description=(
        "Enhance photo quality using AI. "
        "Supports color correction, noise reduction, and detail enhancement."
    ),
    tags=["photos", "editing", "ai"],
    output_schema={
        "type": "object",
        "properties": {
            "success": {"type": "boolean"},
            "before_hash": {"type": "string"},
            "after_hash": {"type": "string"},
            "enhancements_applied": {"type": "array", "items": {"type": "string"}}
        }
    }
)
async def enhance_photo(
    photo_id: str,
    enhancement_type: Literal["auto", "portrait", "landscape", "low_light"],
    strength: float = 0.7,
    save_copy: bool = True
) -> dict:
    """Enhance photo quality using AI-powered algorithms.
    
    This tool applies various enhancements to improve photo quality, including:
    - Automatic color correction
    - Noise reduction
    - Detail enhancement
    - Face enhancement (for portraits)
    
    Args:
        photo_id: ID of the photo to enhance
        enhancement_type: Type of enhancement to apply
        strength: Enhancement strength (0.1 to 1.0)
        save_copy: Whether to save as a new copy (default: True)
        
    Returns:
        Dictionary with enhancement results
        
    Examples:
        # Basic enhancement
        result = await enhance_photo("photo123", "auto")
        
        # Strong portrait enhancement
        result = await enhance_photo(
            photo_id="portrait456",
            enhancement_type="portrait",
            strength=0.9
        )
    """
    # Implementation...
```

## 🔍 DXT Integration

### Tool Discovery

In Claude's DXT interface, tools are automatically discovered and displayed with:

1. **Name and Description**: From the `@mcp.tool` decorator
2. **Parameters**: Inferred from the function signature
3. **Documentation**: From the function's docstring

### Best Practices for DXT

1. **Keep Descriptions Concise but Informative**
   ```python
   # Good
   description="Search photos using natural language queries"
   
   # Too vague
   description="Search photos"
   ```

2. **Use Tags for Organization**
   ```python
   tags=["photos", "search", "discovery"]
   ```

3. **Document Parameters Thoroughly**
   - Use type hints
   - Document valid values for enums
   - Include examples in docstrings

## 🆘 Adding a Help System

Since FastMCP doesn't include a built-in help command, we can add one:

```python
@mcp.tool(
    name="help",
    description="Show help for available tools"
)
async def show_help(tool_name: str | None = None) -> str:
    """Show help for available tools.
    
    Args:
        tool_name: Optional name of a specific tool to get help for
        
    Returns:
        Formatted help text
    """
    if tool_name:
        return _get_tool_help(tool_name)
    return _list_all_tools()

def _get_tool_help(tool_name: str) -> str:
    """Get detailed help for a specific tool."""
    # Implementation that returns formatted help text
    return f"Help for {tool_name}"

def _list_all_tools() -> str:
    """List all available tools with descriptions."""
    # Implementation that lists all tools
    return "Available tools: ..."
```

## 🎨 Example: ImmichMCP Tool Documentation

### Photo Upload Tool

```python
@mcp.tool(
    name="upload_photos",
    description=(
        "Upload photos to Immich with automatic metadata extraction. "
        "Supports batch processing and album organization."
    ),
    tags=["photos", "upload", "batch"]
)
async def upload_photos(
    file_paths: List[Union[str, Path]],
    album_name: str | None = None,
    privacy_level: Literal["private", "shared", "public"] = "private",
    extract_metadata: bool = True,
    skip_duplicates: bool = True
) -> Dict[str, Any]:
    """Upload one or more photos to Immich with advanced options.
    
    This tool handles uploading photos with the following features:
    - Batch processing of multiple files
    - Automatic metadata extraction (EXIF, IPTC, XMP)
    - Duplicate detection
    - Album organization
    
    Args:
        file_paths: List of file paths to upload (supports str or Path objects)
        album_name: Optional album name to add photos to (will be created if needed)
        privacy_level: Privacy setting for the uploaded photos
        extract_metadata: Whether to extract and save metadata (default: True)
        skip_duplicates: Skip files that already exist in the library (default: True)
        
    Returns:
        Dictionary with upload results including:
        - success_count: Number of successfully uploaded files
        - skipped_count: Number of skipped duplicates
        - errors: List of error messages for failed uploads
        - asset_ids: List of created asset IDs
        
    Examples:
        # Basic upload
        result = await upload_photos(["photo1.jpg", "photo2.jpg"])
        
        # Upload to an album with metadata
        result = await upload_photos(
            file_paths=["vacation/*.jpg"],
            album_name="Summer Vacation 2024",
            privacy_level="shared"
        )
    """
    # Implementation...
```

## 🔄 Interactive Help in Claude

Users can interact with the help system using natural language:

```
User: @immich help
Claude: Here are the available commands:
        • upload_photos - Upload photos with metadata
        • search_photos - Search using natural language
        • enhance_photo - Improve photo quality
        Type '@immich help <command>' for more details

User: @immich help upload_photos
Claude: 📤 upload_photos - Upload photos to Immich
        
        Usage: @immich upload_photos [files...] [options]
        
        Options:
        --album, -a <name>    Add to album (creates if needed)
        --privacy <level>     Set privacy (private|shared|public)
        --no-metadata         Skip metadata extraction
        --force               Overwrite duplicates
        
        Examples:
        @immich upload_photos *.jpg
        @immich upload_photos --album "Vacation" ~/photos/*.jpg
```

## 📦 DXT Manifest Example

```json
{
  "name": "immich-mcp",
  "version": "1.0.0",
  "description": "Immich integration for Claude - Manage and edit your photo library",
  "tools": [
    {
      "name": "upload_photos",
      "description": "Upload photos with metadata extraction and album support",
      "parameters": {
        "type": "object",
        "properties": {
          "file_paths": {
            "type": "array",
            "items": {"type": "string"},
            "description": "List of file paths to upload"
          },
          "album_name": {
            "type": "string",
            "description": "Optional album name"
          },
          "privacy_level": {
            "type": "string",
            "enum": ["private", "shared", "public"],
            "default": "private"
          }
        },
        "required": ["file_paths"]
      }
    }
  ]
}
```

## 🎯 Best Practices Summary

1. **Be Descriptive but Concise**
   - Use clear, action-oriented descriptions
   - Keep parameter descriptions brief but informative

2. **Provide Examples**
   - Include common usage patterns
   - Show both simple and complex examples

3. **Use Type Hints**
   - Helps with validation and documentation
   - Makes the API more discoverable

4. **Document Error Cases**
   - List common errors and how to handle them
   - Document retry behavior

5. **Keep Documentation in Sync**
   - Update docs when behavior changes
   - Use the same terminology consistently

6. **Add a Help Command**
   - Implement a `help` tool
   - Support both listing all tools and detailed help

7. **Test Your Documentation**
   - Verify examples work as written
   - Check that all parameters are documented
