"""
FastMCP 2.10 API routes for ImmichMCP.

This module defines the FastAPI router with all v1 API endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException
from fastmcp import FastMCP

from ...config import get_settings
from ...immich_api import ImmichAPIClient

router = APIRouter(prefix="/api/v1", tags=["v1"])

# Health check endpoint required by FastMCP 2.10
@router.get("/health")
async def health_check():
    """Health check endpoint for FastMCP 2.10 compatibility."""
    return {"status": "ok", "version": "1.0.0"}

# Example endpoint - will be expanded with all 15 tools
@router.get("/photos/search")
async def search_photos(
    query: str,
    search_type: str = "smart",
    limit: int = 50,
    client: ImmichAPIClient = Depends(ImmichAPIClient)
):
    """Search photos using CLIP smart search or metadata queries."""
    try:
        return await client.search_photos(query, search_type, limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
