# Agent Context: Litestar Starter Template

This document provides essential context for AI agents working on this project.

## Project Overview
A modern, lightweight starter template for Python web applications using **Litestar**, focused on developer experience, type safety, and efficient containerized deployment.

## Core Tech Stack
- **Framework**: [Litestar](https://litestar.dev/) (ASGI)
- **Language**: Python 3.11+ (managed by `uv`)
- **Database**: SQLite (Async via `aiosqlite`)
- **Migrations**: `yoyo-migrations` (Raw SQL)
- **Frontend**: Tailwind CSS 4 (CLI-based)
- **Templating**: Jinja2
- **Tooling**:
    - `uv`: Dependency management and execution.
    - `just`: Project-level task runner (see `Justfile`).
    - `ruff`: Fast linting and formatting.
    - `ty`: Type checking wrapper (Astral's `ty`).
    - `pytest`: Testing framework.

## Infrastructure & Deployment
- **Local Dev**: Docker Compose orchestrating the app and a Tailwind watcher.
- **Production Target**: [Dokploy](https://dokploy.com/).
- **Containerization**: Multi-stage `Dockerfile` (uv-based).

## Project Structure
- `src/`: Core Python application logic.
    - `app.py`: Application factory, routes, and middleware.
    - `repository.py`: Data access layer (UserRepository).
    - `cli.py`: Custom CLI commands (e.g., `create-user`).
    - `helpers.py`: Utility functions.
- `static/`: Static assets. `input.css` is the Tailwind source; `style.css` is the compiled output.
- `templates/`: Jinja2 templates (base, auth, error pages).
- `migrations/`: Raw SQL migration files managed by `yoyo`.

## Key Commands (via `just`)
- `just dev`: Start the full stack via Docker Compose (App + Tailwind Watcher).
- `just check`: Run linting (`ruff`), formatting, and type checking (`ty`).
- `just test`: Run the test suite in parallel.
- `just migrate`: Apply pending SQL migrations.
- `just new-migration <name>`: Scaffold a new migration file.

## Implementation Details for Agents
- **Async Database**: The project uses `aiosqlite`. All database operations in `repository.py` must be `async`.
- **Dependency Injection**: Litestar's DI is used for database connections and repositories (see `create_app` in `src/app.py`).
- **Tailwind 4**: The project uses Tailwind CSS 4. During development, the CLI runs in a separate Docker container (`tailwind` service) and watches `./static/input.css` to build `./static/style.css`.
- **Pre-built Assets**: For production, the project relies on the pre-built `static/style.css`. Ensure this file is committed to the repository before deployment.
- **Environment Variables**: Managed via `.env` (loaded automatically by `Justfile` and `python-dotenv`).

## Known Discrepancies
- `docker-compose.yml` currently contains placeholder paths for Tailwind CLI (e.g., `./tailwind/input.css`). When updating the Tailwind config, ensure paths align with the actual `./static/` directory.
