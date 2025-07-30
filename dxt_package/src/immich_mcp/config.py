"""
Configuration management for ImmichMCP
Austrian efficiency for environment and settings management
"""

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class ImmichConfig:
    """Immich server configuration"""
    server_url: str
    api_key: str
    timeout: int = 30
    max_retries: int = 3
    default_limit: int = 50
    max_limit: int = 200
    debug: bool = False
    
    def __post_init__(self):
        """Validate configuration after initialization"""
        if not self.server_url:
            raise ValueError("IMMICH_SERVER_URL is required")
        if not self.api_key:
            raise ValueError("IMMICH_API_KEY is required")
        
        # Ensure server URL doesn't end with /api
        if self.server_url.endswith('/api'):
            self.server_url = self.server_url[:-4]
    
    @classmethod
    def from_env(cls) -> 'ImmichConfig':
        """Create configuration from environment variables"""
        return cls(
            server_url=os.getenv('IMMICH_SERVER_URL', 'http://localhost:2283'),
            api_key=os.getenv('IMMICH_API_KEY', ''),
            timeout=int(os.getenv('IMMICH_TIMEOUT', '30')),
            max_retries=int(os.getenv('IMMICH_MAX_RETRIES', '3')),
            default_limit=int(os.getenv('IMMICH_DEFAULT_LIMIT', '50')),
            max_limit=int(os.getenv('IMMICH_MAX_LIMIT', '200')),
            debug=os.getenv('IMMICH_DEBUG', '0').lower() in ('1', 'true', 'yes')
        )


# Create default config instance
def get_config() -> ImmichConfig:
    """Get configuration instance from environment"""
    return ImmichConfig.from_env()
