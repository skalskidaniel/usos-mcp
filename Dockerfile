FROM python:3.14-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

COPY . /app

RUN uv sync --frozen --no-dev

ENV PATH="/app/.venv/bin:$PATH"

ENV FAST_MCP_TRANSPORT=stdio
ENV FAST_MCP_HOST=0.0.0.0
ENV FAST_MCP_PORT=8000

ENTRYPOINT ["python", "-m", "usos"]