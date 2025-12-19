#!/usr/bin/env python3
"""
Run ImmichMCP Server in HTTP Mode

This script runs the ImmichMCP server as an HTTP REST API server,
enabling Immich++ to use the MCP tools via HTTP calls.

Usage:
    python run_http_server.py [--host HOST] [--port PORT]
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from immich_mcp.server import main

if __name__ == "__main__":
    # Set default arguments for HTTP mode
    if len(sys.argv) == 1:
        sys.argv.extend(['--transport', 'http'])

    main()
