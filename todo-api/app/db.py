from collections.abc import Iterator
from pathlib import Path

from sqlmodel import Session, create_engine

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

DATABASE_URL = f"sqlite:///{DATA_DIR / 'todos.db'}"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})


def get_session() -> Iterator[Session]:
    with Session(engine) as session:
        yield session
