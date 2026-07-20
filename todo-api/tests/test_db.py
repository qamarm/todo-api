import pytest
from sqlmodel import Session

from app.db import get_session


def test_get_session_yields_and_closes_session():
    gen = get_session()
    session = next(gen)

    assert isinstance(session, Session)

    with pytest.raises(StopIteration):
        next(gen)
