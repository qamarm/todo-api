from fastapi import FastAPI, HTTPException, status

from app.models import Todo, TodoCreate, TodoUpdate
from app.storage import store

app = FastAPI(title="Todo API")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/todos", response_model=Todo, status_code=status.HTTP_201_CREATED)
def create_todo(todo: TodoCreate) -> Todo:
    return store.create(todo)


@app.get("/todos", response_model=list[Todo])
def list_todos() -> list[Todo]:
    return store.list()


@app.get("/todos/{todo_id}", response_model=Todo)
def get_todo(todo_id: int) -> Todo:
    todo = store.get(todo_id)
    if todo is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found")
    return todo


@app.patch("/todos/{todo_id}", response_model=Todo)
def update_todo(todo_id: int, todo: TodoUpdate) -> Todo:
    updated = store.update(todo_id, todo)
    if updated is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found")
    return updated


@app.delete("/todos/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_todo(todo_id: int) -> None:
    if not store.delete(todo_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found")
