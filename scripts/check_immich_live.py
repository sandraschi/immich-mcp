#!/usr/bin/env python3
"""One-off script: load .env, create Immich client, fetch stats and timeline. No mocks."""
import asyncio
import os
from pathlib import Path

# Load .env from repo root
root = Path(__file__).resolve().parent.parent
env = root / ".env"
if env.exists():
    from dotenv import load_dotenv
    load_dotenv(env)
else:
    print("No .env found at", env)

from immich_mcp.config import get_config
from immich_mcp.immich_api import ImmichAPIClient, ImmichAPIError


async def main():
    try:
        config = get_config()
    except Exception as e:
        print("Config failed:", e)
        return
    print("IMMICH_SERVER_URL:", getattr(config, "server_url", os.getenv("IMMICH_SERVER_URL")))
    print("API key set:", bool(config.api_key or (config.users and config.active_user)))

    try:
        client = ImmichAPIClient(config=config)
    except Exception as e:
        print("Client init failed:", e)
        return

    # 1) Server stats (storage / asset count)
    print("\n--- get_server_stats ---")
    try:
        stats = await client.get_server_stats()
        print("photos:", stats.get("photos"))
        print("videos:", stats.get("videos"))
        print("albums:", stats.get("albums"))
        print("usage:", stats.get("usage"), "available:", stats.get("available"))
        if stats.get("error"):
            print("error in response:", stats.get("error"))
    except ImmichAPIError as e:
        print("ImmichAPIError:", e)
    except Exception as e:
        print("Error:", type(e).__name__, e)

    # 2) Timeline (POST /search/assets then fallback GET /search/metadata)
    print("\n--- get_timeline_assets(page=1, size=5) ---")
    try:
        items = await client.get_timeline_assets(page=1, size=5)
        print("items count:", len(items))
        for i, a in enumerate(items[:3]):
            print(f"  [{i}] id={a.get('id')} file={a.get('originalFileName', a.get('original_filename'))}")
    except ImmichAPIError as e:
        print("ImmichAPIError:", e)
    except Exception as e:
        print("Error:", type(e).__name__, e)

    # 3) Albums
    print("\n--- get_albums ---")
    try:
        albums = await client.get_albums()
        print("albums count:", len(albums) if isinstance(albums, list) else "not a list")
        if isinstance(albums, list) and albums:
            for a in albums[:3]:
                print("  ", a.get("albumName", a.get("album_name")), a.get("assetCount", a.get("asset_count")))
    except ImmichAPIError as e:
        print("ImmichAPIError:", e)
    except Exception as e:
        print("Error:", type(e).__name__, e)

    await client.close()
    print("\nDone.")


if __name__ == "__main__":
    asyncio.run(main())
