# USOS Model Context Protocol (MCP) Server

A standardized Model Context Protocol (MCP) server that bridges the official **USOS API** (Uniwersytecki System Obsługi Studiów) with generative AI clients (such as Claude Code, Claude Desktop, Cursor, and web-based assistants via tunnels).

This server allows students of Polish universities to query their schedules, track academic grades, monitor ECTS accumulation, search for lecturer contact data, and review study programs through natural language conversations.

---

## Usage with MCP Clients (e.g. Cursor, Claude desktop)

You can connect this server to any MCP-compatible client like Cursor.

### Authenticating with USOS

Use the `setup_user_authentication` prompt to guide the user through OAuth setup. It should be run one step at a time and wait for the user's response before continuing.

### Option A: Running via PyPI (Recommended)

If you have `uv` installed, you can use `uvx` to fetch and run the package dynamically without manual installation:

```json
"usos": {
  "command": "uvx",
  "args": ["--from", "usos-mcp", "server"],
  "env": {
    "USOS_API_BASE_URL": "...",
    "USOS_API_CONSUMER_KEY": "...",
    "USOS_API_CONSUMER_SECRET": "..."
  }
}
```

### Option B: Running via Docker

If you prefer not to install Python/uv locally, you can use the Docker image. The `-i` flag is required for MCP to communicate over standard input/output.

```json
"usos": {
  "command": "docker",
  "args": [
    "run", "-i", "--rm",
    "-e", "USOS_API_BASE_URL=...",
    "-e", "USOS_API_CONSUMER_KEY=...",
    "-e", "USOS_API_CONSUMER_SECRET=...",
    "ghcr.io/skalskidaniel/usos-mcp:latest"
  ]
}
```

## Contributing

Contributions are welcome! This server is built with a modular registry pattern that makes adding new USOS API integrations simple.

See [CONTRIBUTING.md](./CONTRIBUTING.md) for a guide on how to add your own tools, prompts, and resources.
