# syntax=docker/dockerfile:1
FROM python:3.12-slim AS base

ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml /app/
COPY app/ /app/app/
COPY templates/ /app/templates/

RUN pip install uv && \
    uv venv .venv --python 3.12

RUN --mount=type=secret,id=github_token \
    . .venv/bin/activate && \
    GIT_AUTH="$(cat /run/secrets/github_token)" && \
    uv pip install "burns-logger @ git+https://${GIT_AUTH}@github.com/bradcburns-home/burns-logger@main" && \
    uv pip install --requirement /app/pyproject.toml

# ── Test gate ─────────────────────────────────────────────────────────────
FROM base AS test

COPY tests/ /app/tests/
RUN . .venv/bin/activate && uv pip install --extra dev --requirement /app/pyproject.toml
RUN . .venv/bin/activate && python -m pytest tests/ -x -q
RUN touch /test-passed

# ── Final image ───────────────────────────────────────────────────────────
FROM base AS final

COPY --from=test /test-passed /test-passed

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD [".venv/bin/uvicorn", "app.server:app", "--host", "0.0.0.0", "--port", "8000"]
