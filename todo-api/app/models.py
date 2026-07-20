from datetime import UTC, datetime

from sqlmodel import Field, SQLModel


def utcnow() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


class TodoBase(SQLModel):
    title: str
    description: str | None = None
    completed: bool = False


class Todo(TodoBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)


class TodoCreate(TodoBase):
    pass


class TodoUpdate(SQLModel):
    title: str | None = None
    description: str | None = None
    completed: bool | None = None


class TodoList(SQLModel):
    items: list[Todo]
    total: int
    limit: int
    offset: int


class JenkinsBuildResponse(SQLModel):
    build_url: str


class JenkinsBuildStatus(SQLModel):
    number: int
    url: str
    building: bool
    result: str | None = None
