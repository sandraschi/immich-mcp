# immich-mcp (MCPB Bundle)

Industrialized FastMCP 3.1 server for Immich photo management with conversational AI, sampling, and SOTA 2026 fleet standards.

## Usage

Add to \claude_desktop_config.json\:
\\\json
{
  "mcpServers": {
    "immich-mcp": {
      "command": "uv",
      "args": ["run", "--directory", "\D:\Dev\repos", "python", "-m", "immich_mcp"],
      "env": { "PYTHONPATH": "\D:\Dev\repos/src" }
    }
  }
}
\\\

## Tools

- **immich_help**: immich_help
- **upload_photos**: upload_photos
- **get_logs**: Retrieve system logs for the dashboard.     For now, returns a combination of memory logs and rec...

## Requirements

- Python 3.12+
- uv
