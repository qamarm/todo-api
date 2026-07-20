# Todo API

[![CI](https://github.com/qamarm/todo-api/actions/workflows/ci.yml/badge.svg)](https://github.com/qamarm/todo-api/actions/workflows/ci.yml)

A basic FastAPI todo app with CRUD operations, backed by SQLite (via SQLModel).

## Requirements

- [Docker](https://docs.docker.com/get-docker/) (recommended), or
- Python 3.12+ and [uv](https://docs.astral.sh/uv/) for local development

## Run with Docker

```bash
cp .env.example .env   # fill in JENKINS_USER / JENKINS_API_TOKEN if you need the Jenkins endpoint
docker compose up --build
```

Database migrations run automatically on container start. The API is available
at `http://localhost:8000`, with interactive docs at `http://localhost:8000/docs`.

## Run locally

```bash
uv sync
uv run alembic upgrade head
set -a && source .env && set +a   # if you need the Jenkins endpoint
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
make test   # runs pytest with a coverage report (term-missing)
```

## Lint & format

```bash
make lint     # ruff check
make format   # ruff format
```

## API

| Method | Path          | Description       |
|--------|---------------|--------------------|
| GET    | `/health`        | Health check       |
| POST   | `/todos`         | Create a todo      |
| GET    | `/todos`         | List todos (paginated) |
| GET    | `/todos/{id}`    | Get a todo         |
| PATCH  | `/todos/{id}`    | Update a todo      |
| DELETE | `/todos/{id}`    | Delete a todo      |
| POST   | `/jenkins/builds` | Trigger the `my-cli` Jenkins job |
| GET    | `/jenkins/builds/{number}` | Get status/result of a build |

### Examples

```bash
curl -X POST http://localhost:8000/todos \
  -H "Content-Type: application/json" \
  -d '{"title": "Buy milk", "description": "2%"}'

curl "http://localhost:8000/todos?limit=10&offset=0"
```

`GET /todos` accepts `limit` (1-100, default 20) and `offset` (default 0), and
returns `{"items": [...], "total": <int>, "limit": <int>, "offset": <int>}`.

```bash
curl -X POST http://localhost:8000/jenkins/builds
```

`POST /jenkins/builds` triggers the `my-cli` Jenkins job (job name is fixed for
now), waits (up to 30s) for Jenkins to assign a build number, and returns
`{"build_url": "http://localhost:8080/job/my-cli/<n>/"}`. Requires
`JENKINS_URL`, `JENKINS_USER`, and `JENKINS_API_TOKEN` to be set (see
`.env.example`). Returns `502` if Jenkins can't be reached or rejects the
request, `504` (with the queue item URL in the error) if Jenkins doesn't
assign a build number within the timeout.

```bash
curl http://localhost:8000/jenkins/builds/3
```

`GET /jenkins/builds/{number}` returns
`{"number": <int>, "url": <str>, "building": <bool>, "result": <str|null>}` for
that build of `my-cli`. `result` is `null` while the build is still running.
Returns `404` if the build doesn't exist.

## Notes

Data is stored in a SQLite database file at `data/todos.db`, created by running
migrations (see above). When running with `docker compose`, this directory is
mounted as a volume so data persists across container restarts. When running
locally, it's created relative to the project root and is git-ignored.
