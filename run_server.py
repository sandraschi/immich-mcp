"""PyInstaller entry point - dual transport.

MCP_PORT set (Tauri spawn) -> HTTP/uvicorn mode on 127.0.0.1:<port>.
No MCP_PORT (Claude Desktop) -> stdio mode.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

from immich_mcp.server import main

port = os.environ.get("MCP_PORT") or os.environ.get("PORT")
if port:
    host = os.environ.get("MCP_HOST", "127.0.0.1")
    sys.argv = ["run_server.py", "--http", "--host", host, "--port", str(port)]
else:
    sys.argv = ["run_server.py", "--stdio"]

main()
