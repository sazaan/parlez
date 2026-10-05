import os
import sys
import tempfile

# Ensure the project root is on the path so `import main` works.
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# CRITICAL: force an isolated DB before importing main, so tests never touch
# data/parlez.db (real users / bcrypt hashes / PII). This MUST happen before
# `import main` — `main.py` constructs the storage singleton at import time.
# We use a per-session tempdir (not :memory:) so all connections in the
# SQLAlchemy pool share one DB; :memory: is per-connection and would split
# test state across connections.
_TEST_DB_DIR = tempfile.mkdtemp(prefix="parlez-test-")
os.environ["DATABASE_URL"] = f"sqlite:///{_TEST_DB_DIR}/test.db"

import pytest
from fastapi.testclient import TestClient

# Import main *after* path manipulation AND env setup so the module-level
# storage singleton is built against the test DB.
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
        "email": "fixture@example.com",
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
