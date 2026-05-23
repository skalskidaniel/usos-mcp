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

## Architecture
- `src/usos/` — main package.
  - `core.py`: `USOSMcp` class wrapping a `FastMCP` instance; `ServerSettings` loaded via `pydantic-settings` from `.env` with prefix `fast_mcp_`.
  - `mcp/` — MCP prompt/tool definitions (only `prompts.py` exists, empty).
  - `api/` — USOS API wrappers (`controllers.py`, `routes.py` — both empty stubs).
  - `auth/` — OAuth 1.0a logic (`__init__.py` — empty stub).
  - `models.py`, `utils.py` — empty stubs.
- The file `exceptons.py` is intentionally named (missing "i") — do **not** import from `usos.exceptions`.
- `src/scripts/usos_versions.py` — standalone script that scans USOS API installations.
- `tests/` is empty.
- No CI, no lint/typecheck/test config yet.

## USOS API
- API reference: `https://apps.usos.edu.pl/developers/api/` (or university-specific like PUT).
- Auth: OAuth 1.0a. Token/authorize/access endpoints are university-specific.
