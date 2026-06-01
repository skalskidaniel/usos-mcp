"""
USOS MCP server — Model Context Protocol bridge to the USOS API.

Exposes USOS (Uniwersytecki System Obsługi Studiów) data to MCP clients such as
Cursor and Claude Desktop. Students authenticate once via OAuth 1.0a, then query
timetables, calendars, and related academic information through natural language.

Public API:
- USOSMcp: Application wrapper around FastMCP (discovery, registration, run).

Entry points:
- usos.core:main — primary CLI entry (`uv run server`, `uvx usos-mcp`).
- python -m usos — same runtime via __main__.

Architecture:
- core.py bootstraps FastMCP and auto-imports every `tools.py`, `prompts.py`, and
  `resources.py` under domain subpackages.
- FastMCP FileSystemProvider discovers `@tool`, `@prompt`, and `@resource`
  definitions and binds them to the FastMCP app at startup.
- models.py holds ServerSettings for transport/host/port (`FAST_MCP_*` env prefix).

Domain subpackages (see each package's __init__.py for tools and API details):
- usos.auth — OAuth 1.0a setup, credential checks, supported universities resource.
- usos.schedule — Personal timetable, faculties, days off, exam session dates.

USOS credentials are configured separately under the `USOS_API_*` prefix (see usos.auth).
"""

from .core import USOSMcp

__all__ = ["USOSMcp"]
