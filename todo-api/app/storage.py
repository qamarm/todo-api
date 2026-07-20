from datetime import datetime, timezone
from typing import Optional

from app.models import Todo, TodoCreate, TodoUpdate


class TodoStore:
    def __init__(self) -> None:
        self._todos: dict[int, Todo] = {}
        self._next_id = 1

    def list(self) -> list[Todo]:
        return list(self._todos.values())

    def get(self, todo_id: int) -> Optional[Todo]:
        return self._todos.get(todo_id)

    def create(self, data: TodoCreate) -> Todo:
        now = datetime.now(timezone.utc)
        todo = Todo(id=self._next_id, created_at=now, updated_at=now, **data.model_dump())
        self._todos[todo.id] = todo
        self._next_id += 1
        return todo

    def update(self, todo_id: int, data: TodoUpdate) -> Optional[Todo]:
        existing = self._todos.get(todo_id)
        if existing is None:
            return None
        updated = existing.model_copy(
            update={**data.model_dump(exclude_unset=True), "updated_at": datetime.now(timezone.utc)}
        )
        self._todos[todo_id] = updated
        return updated

    def delete(self, todo_id: int) -> bool:
        return self._todos.pop(todo_id, None) is not None


store = TodoStore()
