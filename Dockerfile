FROM node:20-alpine AS css-builder
WORKDIR /app
COPY tailwind.config.js ./
COPY static/input.css ./static/
COPY templates/ ./templates/
COPY src/ ./src/
RUN npx tailwindcss -i ./static/input.css -o ./static/style.css --minify

FROM python:3.12-slim AS base
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv
WORKDIR /app
COPY pyproject.toml .
RUN uv sync --no-dev
COPY . .
ENV PYTHONPATH="/app/src"

FROM base AS dev
EXPOSE 8000

FROM base AS prod
COPY --from=css-builder /app/static/style.css ./static/style.css
EXPOSE 8000

CMD ["uv", "run", "uvicorn", "src.app:app", "--host", "0.0.0.0", "--port", "8000"]
