FROM python:3.14-bookworm AS builder

RUN apt-get update && apt-get install --no-install-recommends -y \
        build-essential && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

ADD https://astral.sh/uv/install.sh /install.sh
RUN chmod -R 755 /install.sh && /install.sh && rm /install.sh

ENV PATH="/root/.local/bin:$PATH"

WORKDIR /app

COPY ./pyproject.toml .
COPY ./src src

RUN uv sync

FROM python:3.14-slim-bookworm AS production

ENV FAST_MCP_TRANSPORT=stdio
ENV FAST_MCP_HOST=0.0.0.0
ENV FAST_MCP_PORT=8000

RUN useradd --create-home appuser
USER appuser

WORKDIR /app

COPY ./src src
COPY --from=builder /app/.venv .venv

ENV PATH="/app/.venv/bin:$PATH"

ENTRYPOINT [ "python", "-m", "usos" ]
