"""
FastMCP 2.10 compatible settings for ImmichMCP.

This module provides Pydantic settings management with environment variable overrides.
"""

import os
from pathlib import Path
from typing import Optional, List, Dict, Any

from pydantic import Field, AnyHttpUrl, field_validator, PostgresDsn, ConfigDict
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable overrides."""
    
    # Application settings
    app_name: str = "ImmichMCP"
    app_version: str = "1.0.0"
    app_description: str = "FastMCP 2.10 server for Immich photo management"
    
    # Server settings
    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = False
    log_level: str = "info"
    
    # Immich API settings
    immich_url: AnyHttpUrl = "http://localhost:2283"
    immich_api_key: str = Field(..., validation_alias="IMMICH_API_KEY")
    immich_timeout: int = 30
    immich_max_retries: int = 3
    immich_default_limit: int = 50
    immich_max_limit: int = 200
    
    # Security
    cors_origins: List[str] = ["*"]
    
    # Database settings (if needed in the future)
    database_url: Optional[PostgresDsn] = None
    
    # File storage
    upload_dir: Path = Path("uploads")
    
    # Pydantic v2 config
    model_config = SettingsConfigDict(
        env_prefix="IMMICH_MCP_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Validation
    @field_validator("immich_url", mode="before")
    @classmethod
    def validate_immich_url(cls, v: Any) -> AnyHttpUrl:
        """Ensure the Immich URL doesn't end with /api."""
        if isinstance(v, str):
            if v.endswith("/api"):
                v = v[:-4]
        elif hasattr(v, "__str__"):
            v_str = str(v)
            if v_str.endswith("/api"):
                v = v_str[:-4]
        return v


# Create settings instance
settings = Settings()

# Convenience function for dependency injection
def get_settings() -> Settings:
    """Get the settings instance for dependency injection."""
    return settings
