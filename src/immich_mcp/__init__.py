"""
ImmichMCP - FastMCP 3.2.0 Server for Immich Photo Management

Austrian efficiency for Sandra's 2000+ photo library management.
Provides 25+ tools: 5 core photo operations + 4 album management + 3 people/faces
+ 7 library management + 3 multi-user support + 3 administration
"""

from .config import ImmichConfig, get_config
from .immich_api import ImmichAPIClient, ImmichAPIError
from .server import ImmichMCP, mcp
from .settings import Settings, get_settings

__version__ = "1.5.0"

__all__: list[str] = [
    "ImmichAPIClient",
    "ImmichAPIError",
    "ImmichConfig",
    "ImmichMCP",
    "Settings",
    "get_config",
    "get_settings",
    "mcp",
]
