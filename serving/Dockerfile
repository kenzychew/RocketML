# syntax=docker/dockerfile:1
# Multi-stage build for the RocketML serving image.
# Build context is the repo root, so uv can read pyproject.toml + uv.lock.

# --- build: resolve and install dependencies into a venv -------------------
FROM python:3.12-slim AS build

# uv binary, copied from the official distroless image.
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

# Install only third-party dependencies (no dev tools, not the project itself),
# pinned by uv.lock. The cache mount keeps rebuilds fast.
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev

# Application code (the only first-party source the runtime needs).
COPY serving/app ./app

# --- runtime: slim, non-root image that serves the app ---------------------
FROM python:3.12-slim AS runtime

RUN useradd --create-home --uid 1000 appuser
WORKDIR /app

# Bring over the venv and app code, owned by the non-root user.
COPY --from=build --chown=appuser:appuser /app /app
ENV PATH="/app/.venv/bin:$PATH"

USER appuser
EXPOSE 8000

# Liveness check using only the stdlib (no curl in the slim image).
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

ENTRYPOINT ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
