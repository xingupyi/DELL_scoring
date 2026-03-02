from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from app.db import Base, engine, init_db
from app.main import app


@pytest.fixture(autouse=True)
def clean_database():
    """Reset database schema for each test."""

    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture()
def client() -> TestClient:
    init_db()
    return TestClient(app)


@pytest.fixture()
def fixed_timestamp() -> datetime:
    return datetime(2025, 1, 8, 12, 0, 0, tzinfo=timezone.utc)

