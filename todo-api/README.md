# Todo API

A basic FastAPI todo app with CRUD operations, backed by SQLite (via SQLModel).

## Requirements

- [Docker](https://docs.docker.com/get-docker/) (recommended), or
- Python 3.12+ and [uv](https://docs.astral.sh/uv/) for local development

## Run with Docker

```bash
docker compose up --build
```

The API is available at `http://localhost:8000`, with interactive docs at
`http://localhost:8000/docs`.

## Run locally

```bash
uv sync
uv run uvicorn app.main:app --reload
```

## Run tests

```bash
uv run pytest
```

## API

| Method | Path          | Description       |
|--------|---------------|--------------------|
| GET    | `/health`     | Health check       |
| POST   | `/todos`      | Create a todo      |
| GET    | `/todos`      | List all todos     |
| GET    | `/todos/{id}` | Get a todo         |
| PATCH  | `/todos/{id}` | Update a todo      |
| DELETE | `/todos/{id}` | Delete a todo      |

### Example

```bash
curl -X POST http://localhost:8000/todos \
  -H "Content-Type: application/json" \
  -d '{"title": "Buy milk", "description": "2%"}'
```

## Notes

Data is stored in a SQLite database file at `data/todos.db` (created automatically
on first run). When running with `docker compose`, this directory is mounted as a
volume so data persists across container restarts. When running locally, it's
created relative to the project root and is git-ignored.
