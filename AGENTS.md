# AGENTS.md

## Entry Points

- `usos.core:main` — CLI entry (`uv run server`, `uvx usos-mcp`, `python -m usos`).
- `usos.core:get_mcp` — factory used by `fastmcp.json` for FastMCP tooling.
- `src/usos/__main__.py` imports from `core` and works (not a stub).

## Dependencies & Setup

- Python `>=3.14`. Uses **uv** (`uv sync`, `uv sync --frozen --no-dev`).
- Runtime deps: `fastmcp`, `pydantic`, `pydantic-settings`, `dotenv`, `requests`, `requests-oauthlib`.
- `.env` required locally. Two independent env-prefix groups:
    - `FAST_MCP_*` — transport (`stdio`/`http`/`sse`/`streamable-http`), host, port.
    - `USOS_API_*` — `CONSUMER_KEY`, `CONSUMER_SECRET`, `BASE_URL`, `OAUTH_TOKEN`, `OAUTH_TOKEN_SECRET`.
- Runs tests via **pytest** under `tests/` (`test_auth.py`, `test_schedule.py`, `test_utils.py`, `test_groups.py`).

## Architecture

- `src/usos/` main package. Modular registry pattern.
- `core.py`: Bootstraps `FastMCP` with a `FileSystemProvider` that scans `src/usos` for `@tool`, `@prompt`, and
  `@resource` decorators.
- `models.py`: `ServerSettings` (pydantic-settings, `FAST_MCP_` prefix).
- Domain packages (`auth/`, `schedule/`, `grades/`, `groups/`) each own their `tools.py`, `prompts.py`, `resources.py`,
  `models.py`, `utils.py`.
- `auth/` — OAuth 1.0a setup (`login`, `check_login`, `logout`), `authenticate_me` prompt,
  `usos://universities/supported` resource.
- `schedule/` — Timetable and calendar tools (`get_schedule`, `get_faculties`, `get_days_off`,
  `get_exam_session_dates`).
- `grades/` — Fetch student grades (`get_grades`) and calculate ECTS-weighted GPA (`get_gpa`).
- `groups/` — Fetch student class groups (`get_student_groups`) and group participants (`get_group_participants`).
- Auth utils (`get_authenticated_session`) provides the signed OAuth1Session reused by other packages. Uses
  `USOSAuthSettings` (env prefix `USOS_API_`).
- Old root `server.py` removed.

## API Constraints

- `services/tt/student`: max **7 days** per request.
- `services/calendar/search`: max **30 days** per request (batching built into `fetch_calendar_events`).
- `calendar/search` is marked BETA in USOS docs.
- Faculty auto-resolution (`resolve_faculty_id`) works only when exactly one faculty is found; otherwise raises
  `MultipleFacultiesError`.
- Term auto-resolution picks the first active term from `services/terms/terms_index`.
- `get_gpa` excludes non-numeric grade symbols (e.g., `ZAL`, `NZAL`, `NK`) and requires ECTS details fetched from
  `services/courses/user_ects_points`.
- All grade retrieval tools require the user token to have the `grades` OAuth scope.

## Build & CI

- PyPI: `uv build && uv publish` (triggered on main branch push). Token via `UV_PUBLISH_TOKEN`.
- Docker: GHCR `ghcr.io/skalskidaniel/usos-mcp` (triggered on main + semver tags). Stdio transport default.
- Docker entrypoint: `python -m usos` with `FAST_MCP_TRANSPORT=stdio`.
- Production end-user install: `uvx usos-mcp`.

## Documentation references

- [FastMCP](https://gofastmcp.com/llms.txt)
