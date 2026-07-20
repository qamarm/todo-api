.PHONY: help install migrate migration run test build up down logs clean

.DEFAULT_GOAL := help

help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-12s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies
	uv sync

migrate: ## Apply database migrations
	uv run alembic upgrade head

migration: ## Create a new migration (usage: make migration MSG="add x")
	uv run alembic revision --autogenerate -m "$(MSG)"

run: ## Run the dev server locally
	uv run uvicorn app.main:app --reload

test: ## Run the test suite
	uv run pytest -v

build: ## Build the Docker image
	docker compose build

up: ## Start the app with Docker Compose
	docker compose up --build

down: ## Stop the Docker Compose services
	docker compose down

logs: ## Follow container logs
	docker compose logs -f

clean: ## Remove caches and local data
	find . -path ./.venv -prune -o -type d -name '__pycache__' -exec rm -rf {} +
	rm -rf .pytest_cache data
