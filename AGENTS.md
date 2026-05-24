# AGENTS.md

## Entry Points
- Package entry: `usos.core:main` — also mapped as `[project.scripts]` entry `server` and callable via `python -m usos`.
- `src/usos/__main__.py` is functional (imports from `core`); do not treat it as empty anymore.
- The old root `server.py` no longer exists.

## Runtime & Dependencies
- Python `>=3.14` (`.python-version` enforces 3.14).
- Uses **uv** for package management. Lockfile: `uv.lock`. Install: `uv sync` (or `uv sync --frozen --no-dev` for prod).
- Key deps from `pyproject.toml`: `fastmcp`, `pydantic`, `pydantic-settings`, `dotenv`, `requests`.

## Setup & Config
- `.env` is **required** locally (gitignored). Template shows `FAST_MCP_HOST`, `FAST_MCP_TRANSPORT` (`http`/`stdio`), `FAST_MCP_PORT`, and USOS OAuth credentials (`USOS_API_PUT_CONSUMER_KEY`, `USOS_API_PUT_CONSUMER_SECRET`).
- Run server: `uv run server` (uses `usos.core:main`) or `python -m usos`.
- Docker: `Dockerfile` builds with `uv sync --frozen --no-dev`, defaults `FAST_MCP_TRANSPORT=stdio`, entrypoint `python -m usos`.
- **Production (PyPI)**: Designed to be run by end-users via `uvx usos-mcp`.
- **Production (Docker)**: Can be run via `docker run -i --rm -e ... ghcr.io/<username>/usos-mcp:latest`.

## Architecture
- `src/usos/` — main package.
- **Modular Auto-Discovery**: The codebase uses a Registry Pattern. `usos.core:USOSMcp` automatically discovers and imports any `tools.py`, `prompts.py`, and `resources.py` across all submodules (e.g., `src/usos/auth/tools.py`).
  - To add a new tool, prompt, or resource, create a `tools.py`, `prompts.py`, or `resources.py` in the relevant package.
  - Use `@registry.tool(description="...")`, `@registry.prompt()`, or `@registry.resource()` from `usos.registry`. Do **not** import or initialize FastMCP manually in these files.
  - The registry validates definitions internally using `pydantic`.
- Project Structure:
  - `core.py`: Application entrypoint; initializes `FastMCP`, triggers module discovery, and binds registered tools/prompts/resources.
  - `registry.py`: Exposes `registry` with decorators `@registry.tool()`, `@registry.prompt()`, and `@registry.resource()`.
  - `discover.py` (or within `core.py`): Contains logic to recursively find and import `*.tools`, `*.prompts`, and `*.resources`.
  - `models.py`: Contains `ServerSettings` (loaded via `pydantic-settings` from `.env` with prefix `fast_mcp_`).
  - Submodules (`api/`, `auth/`, `mcp/`): Domain-specific logic. Each should independently contain its own `tools.py`, `prompts.py`, `resources.py`, `utils.py`, and `models.py` as needed.
- The file `exceptons.py` is intentionally named (missing "i") — do **not** import from `usos.exceptions`.
- `src/scripts/usos_versions.py` — standalone script that scans USOS API installations.
- `tests/` is empty.
- No CI, no lint/typecheck/test config yet.

## USOS API
- API reference: `https://apps.usos.edu.pl/developers/api/` (or university-specific like PUT).
- Auth: OAuth 1.0a. Token/authorize/access endpoints are university-specific.
