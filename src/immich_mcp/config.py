"""
Configuration management for ImmichMCP
Austrian efficiency for environment and settings management
"""

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

# Load .env file if it exists
env_path = Path(__file__).parent.parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)
else:
    # Also try loading from current directory
    load_dotenv()


@dataclass
class ImmichUser:
    """Configuration for a single Immich user"""

    name: str
    api_key: str
    role: str = "user"  # admin, user, shared
    description: str = ""

    def __post_init__(self):
        """Validate user configuration"""
        if not self.name:
            raise ValueError("User name is required")
        if not self.api_key:
            raise ValueError(f"API key is required for user {self.name}")


@dataclass
class ImmichConfig:
    """Immich server configuration with multi-user support"""

    server_url: str
    # Legacy single-user support (will be deprecated)
    api_key: str = ""
    # Multi-user configuration
    users: dict[str, ImmichUser] = None  # type: ignore
    active_user: str = ""

    # Common settings
    timeout: int = 30
    max_retries: int = 3
    default_limit: int = 50
    max_limit: int = 200
    debug: bool = False

    def __post_init__(self):
        """Validate configuration after initialization"""
        if not self.server_url:
            raise ValueError("IMMICH_SERVER_URL is required")

        # Ensure server URL doesn't end with /api
        if self.server_url.endswith("/api"):
            self.server_url = self.server_url[:-4]

        # Initialize users dict if not provided
        if self.users is None:
            self.users = {}

        # For backward compatibility, create default user if api_key is provided
        if self.api_key and not self.users:
            self.users["default"] = ImmichUser(
                name="default", api_key=self.api_key, role="admin", description="Default user (legacy configuration)"
            )
            self.active_user = "default"

        # Set active user if not specified and we have users
        if not self.active_user and self.users:
            self.active_user = next(iter(self.users.keys()))

        # Only validate active user if we have users configured
        if self.active_user and self.users and self.active_user not in self.users:
            raise ValueError(f"Active user '{self.active_user}' not found in users configuration")

        # If no users and no api_key, we'll handle this in ImmichAPIClient with better error message

    def get_active_user(self) -> ImmichUser:
        """Get the currently active user configuration"""
        if not self.active_user:
            raise ValueError("No active user configured")
        if self.active_user not in self.users:
            raise ValueError(f"Active user '{self.active_user}' not found")
        return self.users[self.active_user]

    def switch_user(self, username: str) -> ImmichUser:
        """Switch to a different user"""
        if username not in self.users:
            raise ValueError(f"User '{username}' not found")
        self.active_user = username
        return self.users[username]

    @classmethod
    def from_env(cls) -> "ImmichConfig":
        """Create configuration from environment variables"""
        server_url = os.getenv("IMMICH_SERVER_URL", "http://localhost:2283")
        active_user = os.getenv("IMMICH_ACTIVE_USER", "")

        # Parse users configuration
        users = {}
        users_env = os.getenv("IMMICH_USERS", "")

        if users_env:
            # Format: user1:key1:role1,user2:key2:role2
            for user_spec in users_env.split(","):
                if ":" in user_spec:
                    parts = user_spec.split(":")
                    if len(parts) >= 2:
                        name, api_key = parts[0], parts[1]
                        role = parts[2] if len(parts) > 2 else "user"
                        description = parts[3] if len(parts) > 3 else ""
                        users[name] = ImmichUser(name=name, api_key=api_key, role=role, description=description)

        # Legacy single-user support
        api_key = os.getenv("IMMICH_API_KEY", "")

        return cls(
            server_url=server_url,
            api_key=api_key,  # Keep for backward compatibility
            users=users if users else None,
            active_user=active_user,
            timeout=int(os.getenv("IMMICH_TIMEOUT", "30")),
            max_retries=int(os.getenv("IMMICH_MAX_RETRIES", "3")),
            default_limit=int(os.getenv("IMMICH_DEFAULT_LIMIT", "50")),
            max_limit=int(os.getenv("IMMICH_MAX_LIMIT", "200")),
            debug=os.getenv("IMMICH_DEBUG", "0").lower() in ("1", "true", "yes"),
        )


# Create default config instance
def get_config() -> ImmichConfig:
    """Get configuration instance from environment"""
    return ImmichConfig.from_env()
