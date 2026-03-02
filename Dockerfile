# --- Stage 1: Base Image ---
FROM python:3.13-slim AS base
WORKDIR /app
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Install minimal system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

# Set the virtual environment location outside the app directory
ENV UV_PROJECT_ENVIRONMENT=/opt/venv

# --- Stage 2: Dev Builder ---
FROM base AS dev-builder
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project

# --- Stage 3: Prod Builder ---
FROM base AS prod-builder
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project --no-dev

# --- Stage 4: Runtime Config ---
FROM base AS runtime
ENV PYTHONPATH="/app/src"
COPY . .

# --- Stage 5: Dev Stage ---
FROM runtime AS dev
COPY --from=dev-builder /opt/venv /opt/venv
EXPOSE 8000
CMD ["uv", "run", "uvicorn", "src.app:app", "--host", "0.0.0.0", "--port", "8000"]

# --- Stage 6: Production Stage ---
FROM runtime AS prod
COPY --from=prod-builder /opt/venv /opt/venv
EXPOSE 8000
CMD ["uv", "run", "uvicorn", "src.app:app", "--host", "0.0.0.0", "--port", "8000"]
