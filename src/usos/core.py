async def server(scope, receive, send):
    """Minimal ASGI app so the package can be run with an ASGI server.

    Example: PYTHONPATH=src uvicorn usosMCP:server --reload

    This keeps the implementation tiny and dependency-free. Replace with
    a FastAPI/Starlette app or an app factory when you add real routes.
    """
    # Only handle HTTP connections here; other scope types can be ignored
    if scope.get("type") != "http":
        return

    # Simple response: 200 OK with plain text body
    await send({"type": "http.response.start", "status": 200, "headers": [[b"content-type", b"text/plain; charset=utf-8"]]})
    await send({"type": "http.response.body", "body": b"OK"})
