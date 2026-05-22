# AGENTS.md

## Scope and Entry Points
- Python package lives in `src/usos`; `src/usos/core.py` defines a minimal ASGI `server` callable used as the current entry point.
- `server.py` and `src/usos/__main__.py` are empty; do not expect a CLI or runnable module yet.

## Runtime and Dependencies
- Python requirement is `>=3.14` per `pyproject.toml` and `uv.lock`.
- No runtime dependencies are declared yet; expect to add them as features land.

## Documentation and API Reference
- USOS API reference lives at `https://apps.usos.edu.pl/developers/api/` and should be the source of truth for endpoint behavior.

## Tests and CI
- `tests/` is currently empty and there are no CI workflows or task runners.
