# ImmichMCP User Guide

Welcome to ImmichMCP! This guide will help you manage your Immich photo library using natural language through Claude.

## 🚀 Getting Started

### Prerequisites
- Running Immich server (v1.90.0 or later)
- Claude Desktop with MCP support
- Immich API key

### Basic Setup
1. Clone this repository
2. Install dependencies: `pip install -r requirements.txt`
3. Create a `.env` file with your Immich credentials:
   ```
   IMMICH_URL=http://your-immich-server:2283
   IMMICH_API_KEY=your_api_key_here
   ```
4. Start the server: `python immich_mcp_server.py`

## 💬 Natural Language Examples

### Photo Management
- "Upload my vacation photos from the Tokyo trip"
- "Show me all photos from last summer"
- "Find all photos with mountains in them"
- "Create an album called 'Best of 2025' with my top 50 photos"
- "Archive all photos older than 2 years"

### Album Operations
- "Create a new album called 'Family Reunion' and add all photos with my family"
- "Show me what's in my 'Vacation' album"
- "Add these 10 photos to my 'Favorites' album"
- "Remove all blurry photos from my 'Portfolio' album"

### Advanced Search
- "Find all photos taken in Tokyo with good lighting"
- "Show me photos of dogs from last year"
- "Find duplicate photos in my library"
- "Show me all photos with more than 3 stars"

## 🖼️ Photo Viewing (Experimental)

While Claude's interface doesn't natively support image viewing, here are some workarounds:

### Option 1: Local Image Viewer
1. Download photos to a local directory
2. Use your system's default image viewer

Example command:
```
Download the last 10 photos I took to ./recent_photos
```

### Option 2: Web Server Mode
Start the server in web mode to view photos in a browser:
```bash
python immich_mcp_server.py --web
```
Then open `http://localhost:8000` in your browser.

## 🔄 Common Workflows

### Importing New Photos
1. Upload photos from a directory
2. Let ImmichMCP automatically organize them by date
3. Review and tag the new photos
4. Add selected photos to relevant albums

### Cleaning Up Your Library
1. Search for duplicates
2. Archive or delete unwanted photos
3. Update metadata and tags
4. Organize into albums

## 🛠️ Troubleshooting

- **Connection issues**: Verify your Immich server is running and accessible
- **Authentication errors**: Double-check your API key in the .env file
- **Photo not found**: Check if the photo exists in your Immich library

For more help, see the [Troubleshooting Guide](./Troubleshooting.md).

## 📚 Additional Resources

- [Immich Documentation](https://immich.app/docs)
- [API Reference](./API.md)
- [Configuration Options](./Configuration.md)

## 🤖 Advanced: Creating Custom Tools

You can extend ImmichMCP by adding new tools. See the developer documentation for more information.

## 📝 Tips & Tricks

- Use natural language to describe what you're looking for
- Combine multiple criteria in your searches
- Create smart albums with dynamic queries
- Use tags and metadata to improve search results
