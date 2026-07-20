from typing import Annotated, Awaitable, Callable

from fastapi import Depends, FastAPI, HTTPException, Query, status
from sqlmodel import Session, func, select

from app.db import get_session
from app.jenkins import get_build_status, trigger_build_and_wait
from app.models import (
    JenkinsBuildResponse,
    JenkinsBuildStatus,
    Todo,
    TodoCreate,
    TodoList,
    TodoUpdate,
    utcnow,
)

SessionDep = Annotated[Session, Depends(get_session)]


def get_jenkins_trigger() -> Callable[[], Awaitable[str]]:
    return trigger_build_and_wait


def get_jenkins_status_fetcher() -> Callable[[int], Awaitable[JenkinsBuildStatus]]:
    return get_build_status


JenkinsTriggerDep = Annotated[Callable[[], Awaitable[str]], Depends(get_jenkins_trigger)]
JenkinsStatusDep = Annotated[
    Callable[[int], Awaitable[JenkinsBuildStatus]], Depends(get_jenkins_status_fetcher)
]

app = FastAPI(title="Todo API")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/todos", response_model=Todo, status_code=status.HTTP_201_CREATED)
def create_todo(todo: TodoCreate, session: SessionDep) -> Todo:
    db_todo = Todo.model_validate(todo)
    session.add(db_todo)
    session.commit()
    session.refresh(db_todo)
    return db_todo


@app.get("/todos", response_model=TodoList)
def list_todos(
    session: SessionDep,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> TodoList:
    total = session.exec(select(func.count()).select_from(Todo)).one()
    items = session.exec(select(Todo).order_by(Todo.id).offset(offset).limit(limit)).all()
    return TodoList(items=list(items), total=total, limit=limit, offset=offset)


@app.get("/todos/{todo_id}", response_model=Todo)
def get_todo(todo_id: int, session: SessionDep) -> Todo:
    todo = session.get(Todo, todo_id)
    if todo is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found")
    return todo


@app.patch("/todos/{todo_id}", response_model=Todo)
def update_todo(todo_id: int, todo: TodoUpdate, session: SessionDep) -> Todo:
    db_todo = session.get(Todo, todo_id)
    if db_todo is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found")
    for key, value in todo.model_dump(exclude_unset=True).items():
        setattr(db_todo, key, value)
    db_todo.updated_at = utcnow()
    session.add(db_todo)
    session.commit()
    session.refresh(db_todo)
    return db_todo


@app.delete("/todos/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_todo(todo_id: int, session: SessionDep) -> None:
    todo = session.get(Todo, todo_id)
    if todo is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found")
    session.delete(todo)
    session.commit()


@app.post("/jenkins/builds", response_model=JenkinsBuildResponse, status_code=status.HTTP_201_CREATED)
async def trigger_jenkins_build(trigger: JenkinsTriggerDep) -> JenkinsBuildResponse:
    build_url = await trigger()
    return JenkinsBuildResponse(build_url=build_url)


@app.get("/jenkins/builds/{number}", response_model=JenkinsBuildStatus)
async def get_jenkins_build(number: int, fetch_status: JenkinsStatusDep) -> JenkinsBuildStatus:
    return await fetch_status(number)
