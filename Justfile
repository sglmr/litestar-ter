set dotenv-load := true

# Variables
compose := "docker compose"

# Default
default:
    just --list

# Run local development via docker-compose (Litestar + Tailwind)
dev:
	{{compose}} up

# Run raw SQL migrations on SQLite
migrate:
	uv run yoyo apply --database sqlite:///$DATABASE_URL ./migrations --batch

# Generate a new migration file
new-migration name:
	uv run yoyo new ./migrations -m {{name}}

# Run tests in parallel
test:
	uv run pytest src/ -n auto

# Run Astral's ty type checker
check:
	uv run ty check

# Create a database user via CLI
create-user name:
	uv run python src/cli.py create-user {{name}}
