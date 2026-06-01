# Contribution Guide

This project is designed to be easily extendable through FastMCP's FileSystemProvider. You can add new capabilities (Tools, Prompts, and Resources) by creating new modules within the `src/usos/` directory.

## Architecture

The server uses `FastMCP` with a `FileSystemProvider`. This allows for:

- **Auto-Discovery**: Any `.py` file under `src/usos/` containing `@tool`, `@prompt`, or `@resource` is automatically discovered and registered.
- **Decoupling**: Modules don't need to know about the `FastMCP` app instance.

## Adding a New Module

1.  **Create a Directory**: Create a new package under `src/usos/`, for example `src/usos/grades/`.
2.  **Initialize**: Add an `__init__.py` file. Write a documentation inside.
3.  **Add Components**: Create one or more of the following files:
    - `tools.py`: For MCP Tools (executable functions).
    - `prompts.py`: For MCP Prompts (templates for conversations).
    - `resources.py`: For MCP Resources (static or dynamic data).

## Defining Tools

In your `tools.py`, import `tool` and use the `@tool()` decorator. Type hints are used by MCP to generate the tool's schema.

```python
from fastmcp.tools import tool

@tool(
    name="get_my_grades", # Optional: defaults to function name
    description="Fetches the current student's grades from USOS."
)
def get_my_grades(semester: str) -> dict:
    # Your implementation calling USOS API
    return {"grades": [...]}
```

## Defining Prompts & Resources

Similarly, use `@prompt()` and `@resource()`:

```python
from fastmcp.prompts import prompt
from fastmcp.resources import resource

@prompt(name="explain_ects", description="Explains how ECTS points work")
def explain_ects():
    return "ECTS points represent the workload of a course..."

@resource("usos://grades/latest", name="Latest Grades")
def latest_grades():
    return "Course: Math, Grade: 5.0"
```

## Development Workflow

1.  **Install Dependencies**:
    ```bash
    uv sync
    ```
2.  **Run Locally**:
    ```bash
    uv run server
    ```
3.  **Verify**:
    Use an MCP inspector or a client like Cursor to verify your new tools appear in the list.
