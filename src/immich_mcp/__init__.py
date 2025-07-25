"""
ImmichMCP - FastMCP 2.10 Server for Immich Photo Management

Austrian efficiency for Sandra's 2000+ photo library management.
Provides 15 tools: 5 core photo operations + 4 album management + 3 people/faces + 3 administration
"""
from typing import List

from .immich_api import ImmichAPIClient, ImmichAPIError
from .config import ImmichConfig, get_config
from .settings import Settings, get_settings
from .server import ImmichMCP, mcp

__version__ = "1.0.0"

__all__: List[str] = [
    # Core classes
    'ImmichMCP',
    'ImmichAPIClient',
    'ImmichAPIError',
    'ImmichConfig',
    'Settings',
    
    # Functions
    'get_config',
    'get_settings',
    
    # Instance
    'mcp',
    'ImmichAPIError', 
    'ImmichConfig',
    'get_config'
]

__version__ = "1.0.0"
