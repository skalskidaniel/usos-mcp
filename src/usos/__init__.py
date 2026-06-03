"""
USOS MCP server — Model Context Protocol bridge to the USOS API.

Exposes USOS (Uniwersytecki System Obsługi Studiów) data to MCP clients such as
Cursor and Claude Desktop. Students authenticate once via OAuth 1.0a, then query
timetables, calendars, and related academic information through natural language.

Public API:
- create_server: Factory function that builds and returns the FastMCP application.

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
- usos.auth — Interactive OAuth 1.0a login/logout, credentials verification, supported universities resource.
- usos.schedule — Student timetable, faculties, days off, exam session dates.
- usos.grades — Student grades and ECTS-weighted GPA average calculations.
- usos.groups — Student class groups and participant lists.

USOS credentials are saved in local file storage after interactive authentication, or can be configured via environment variables under the `USOS_API_*` prefix.
"""

from .core import create_server

__all__ = ["create_server"]
