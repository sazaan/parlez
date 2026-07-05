import os
import sys

# Ensure the project root is on the path so `import main` works.
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest
from fastapi.testclient import TestClient

# Import main *after* path manipulation so the module-level storage singleton
# is created from the same working directory the tests run in.
import main


@pytest.fixture(autouse=True)
def reset_storage_and_limits():
    """Clear storage and slowapi rate-limit counters before each test."""
    from db import User, SharedLink, CommentGroup
    with main.storage.Session() as session:
        with session.begin():
            session.query(User).delete()
            session.query(SharedLink).delete()
            session.query(CommentGroup).delete()
    # Reset in-memory rate limit counters so tests don't trip each other.
    if hasattr(main.app.state, "limiter"):
        main.app.state.limiter.reset()
    yield


@pytest.fixture
def client():
    return TestClient(main.app)


@pytest.fixture
def auth_client(client):
    """Return a client logged in as a test user."""
    client.post("/api/auth/signup", json={
        "username": "testuser",
        "password": "password123",
        "name": "Test User"
    })
    r = client.post("/api/auth/login", json={
        "username": "testuser",
        "password": "password123"
    })
    token = r.json()["token"]
    client.headers["Authorization"] = f"Bearer {token}"
    return client
