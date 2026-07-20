# Todo API

A basic FastAPI todo app with CRUD operations, backed by SQLite (via SQLModel).

## Requirements

- [Docker](https://docs.docker.com/get-docker/) (recommended), or
- Python 3.12+ and [uv](https://docs.astral.sh/uv/) for local development

## Run with Docker

```bash
docker compose up --build
```

Database migrations run automatically on container start. The API is available
at `http://localhost:8000`, with interactive docs at `http://localhost:8000/docs`.

## Run locally

```bash
uv sync
uv run alembic upgrade head
uv run uvicorn app.main:app --reload
```

## Database migrations

Schema changes are managed with [Alembic](https://alembic.sqlalchemy.org/).

```bash
uv run alembic upgrade head                          # apply migrations
uv run alembic revision --autogenerate -m "message"   # create a new migration after changing app/models.py
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
| GET    | `/todos`      | List todos (paginated) |
| GET    | `/todos/{id}` | Get a todo         |
| PATCH  | `/todos/{id}` | Update a todo      |
| DELETE | `/todos/{id}` | Delete a todo      |

### Examples

```bash
curl -X POST http://localhost:8000/todos \
  -H "Content-Type: application/json" \
  -d '{"title": "Buy milk", "description": "2%"}'

curl "http://localhost:8000/todos?limit=10&offset=0"
```

`GET /todos` accepts `limit` (1-100, default 20) and `offset` (default 0), and
returns `{"items": [...], "total": <int>, "limit": <int>, "offset": <int>}`.

## Notes

Data is stored in a SQLite database file at `data/todos.db`, created by running
migrations (see above). When running with `docker compose`, this directory is
mounted as a volume so data persists across container restarts. When running
locally, it's created relative to the project root and is git-ignored.
