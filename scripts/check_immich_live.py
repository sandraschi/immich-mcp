#!/usr/bin/env python3
"""One-off script: load .env, create Immich client, fetch stats and timeline. No mocks."""

import asyncio
from pathlib import Path

# Load .env from repo root
root = Path(__file__).resolve().parent.parent
env = root / ".env"
if env.exists():
    from dotenv import load_dotenv

    load_dotenv(env)
else:
    pass

from immich_mcp.config import get_config
from immich_mcp.immich_api import ImmichAPIClient, ImmichAPIError


async def main():
    try:
        config = get_config()
    except Exception:
        return

    try:
        client = ImmichAPIClient(config=config)
    except Exception:
        return

    # 1) Server stats (storage / asset count)
    try:
        stats = await client.get_server_stats()
        if stats.get("error"):
            pass
    except ImmichAPIError:
        pass
    except Exception:
        pass

    # 2) Timeline (POST /search/assets then fallback GET /search/metadata)
    try:
        items = await client.get_timeline_assets(page=1, size=5)
        for _i, _a in enumerate(items[:3]):
            pass
    except ImmichAPIError:
        pass
    except Exception:
        pass

    # 3) Albums
    try:
        albums = await client.get_albums()
        if isinstance(albums, list) and albums:
            for _a in albums[:3]:
                pass
    except ImmichAPIError:
        pass
    except Exception:
        pass

    await client.close()


if __name__ == "__main__":
    asyncio.run(main())
