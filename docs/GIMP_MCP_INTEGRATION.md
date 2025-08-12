# GIMP MCP Integration for ImmichMCP

## 🎯 Purpose
Create a dedicated GIMP MCP server that works alongside ImmichMCP to provide advanced photo editing capabilities through natural language commands, leveraging GIMP's powerful scripting capabilities.

## 📋 Core Features

### 1. GIMP MCP Server
- **Python-based MCP server** using GIMP's Python-Fu
- **Bidirectional communication** with ImmichMCP
- **Plugin architecture** for extending functionality

### 2. Key Capabilities
- Open images directly from Immich in GIMP
- Apply edits and save back to Immich
- Batch processing of multiple images
- Non-destructive editing with layers
- Support for GIMP filters and plugins

## 🛠 Technical Implementation

### GIMP MCP Server (gimp_mcp_server.py)
```python
#!/usr/bin/env python3
"""
GIMP MCP Server - Provides GIMP editing capabilities to ImmichMCP
"""
import os
import json
from pathlib import Path
from typing import Dict, List, Optional, Any

from fastmcp import FastMCP
import gi
gi.require_version('Gimp', '3.0')
from gi.repository import Gimp

# Initialize FastMCP server
mcp = FastMCP(
    name="gimp-mcp",
    version="1.0.0",
    description="GIMP integration for ImmichMCP"
)

class GimpEditor:
    def __init__(self):
        self.gimp = Gimp.get_pdb()
        
    async def open_image(self, image_path: str) -> Dict[str, Any]:
        """Open an image in GIMP"""
        try:
            image = self.gimp.file_load(
                Gimp.RunMode.NONINTERACTIVE,
                Gimp.file_new_for_path(image_path),
                Gimp.file_new_for_path(image_path)
            )
            return {"success": True, "image_id": image.get_id()}
        except Exception as e:
            return {"success": False, "error": str(e)}

# Register MCP tools
@mcp.tool()
async def edit_in_gimp(image_url: str) -> Dict[str, Any]:
    """
    Open an image from Immich in GIMP for editing
    
    Args:
        image_url: URL of the image in Immich
        
    Returns:
        Dict with operation status and GIMP image ID
    """
    editor = GimpEditor()
    # 1. Download image from Immich to temp location
    # 2. Open in GIMP
    # 3. Return status
    return await editor.open_image("/path/to/temp/image.jpg")

if __name__ == "__main__":
    mcp.run()
```

## 🔄 Workflow Integration

### Basic Flow
1. User requests edit via ImmichMCP
2. ImmichMCP calls GIMP MCP with image reference
3. GIMP MCP:
   - Downloads image from Immich
   - Opens in GIMP
   - Applies requested edits
   - Saves back to Immich
   - Returns updated image

### Example Commands
```
"Open this photo in GIMP and enhance the colors"
"Remove the background from this image using GIMP"
"Apply vintage filter to these 5 photos"
"Crop and straighten this image, then adjust levels"
```

## 📦 Dependencies
- Python 3.8+
- GIMP 2.10+ with Python-Fu
- `python-gobject` for GIMP Python bindings
- `fastmcp` for MCP server
- `httpx` for HTTP requests

## 🚀 Getting Started

### 1. Install GIMP with Python Support
```bash
# On Ubuntu/Debian
sudo apt install gimp python3-gi python3-gi-cairo gir1.2-gtk-3.0

# On macOS
brew install gimp --with-python

# On Windows
# Install GIMP with Python support from gimp.org
```

### 2. Set Up Python Environment
```bash
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install fastmcp httpx python-dotenv
```

### 3. Configure
Create `.env`:
```
IMMICH_URL=http://your-immich-server:2283
IMMICH_API_KEY=your_api_key
TEMP_DIR=./temp_images
```

## 🔌 Available Tools

### 1. Basic Editing
- `edit_in_gimp(image_url: str)`: Open image in GIMP
- `apply_filter(image_id: str, filter_name: str, **params)`: Apply GIMP filter
- `adjust_levels(image_id: str, **adjustments)`: Adjust image levels

### 2. Batch Processing
- `batch_edit(images: List[str], script: str)`: Apply script to multiple images
- `create_contact_sheet(images: List[str], output_path: str)`: Create contact sheet

### 3. Advanced Features
- `remove_background(image_id: str)`: AI-powered background removal
- `enhance_portrait(image_id: str)`: Portrait-specific enhancements
- `color_grade(image_id: str, style: str)`: Apply color grading

## 📝 Example Scripts

### Vintage Filter
```python
# vintage_effect.py
def run(image_id):
    # Apply vintage effect
    pdb.gimp_desaturate_full(image_id, DESATURATE_LUMINOSITY)
    pdb.plug_in_softglow(image_id, 0.5, 0.8, 0.5)
    pdb.plug_in_colors_channel_mixer(image_id, True, 0.7, 0.3, 0.0, 0.0, 0.8, 0.2, 0.0, 0.2, 0.8)
```

### Background Removal
```python
# remove_bg.py
def run(image_id):
    # Use GIMP's foreground select
    pdb.plug_in_foreground_select(image_id, 0, 0, 0, 0, 0, 0, 0, 0)
    # Add alpha channel and remove background
    pdb.gimp_layer_add_alpha(image_id)
    pdb.gimp_edit_clear(image_id)
```

## 🔄 Integration with Claude

### Example Interaction
```
User: Can you remove the background from this product photo?
Claude: [Calls GIMP MCP's remove_background]
        I've removed the background. Would you like to:
        1. Save it back to Immich
        2. Make additional edits
        3. Try a different approach
```

## 📅 Next Steps
1. Implement core GIMP MCP server
2. Create basic editing tools
3. Add batch processing capabilities
4. Develop AI-powered editing features
5. Create documentation and examples
