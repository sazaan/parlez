"""API tests for Parlez."""

from unittest.mock import patch


def test_signup_and_login(client):
    # Signup
    r = client.post("/api/auth/signup", json={
        "email": "person@example.com",
        "username": "alice",
        "password": "password123",
        "name": "Alice"
    })
    assert r.status_code == 200
    data = r.json()
    assert data["user"]["username"] == "alice"
    assert data["token"]

    # Login
    r = client.post("/api/auth/login", json={
        "username": "alice",
        "password": "password123"
    })
    assert r.status_code == 200
    assert r.json()["user"]["name"] == "Alice"


def test_signup_password_too_short(client):
    r = client.post("/api/auth/signup", json={
        "email": "person@example.com",
        "username": "bob",
        "password": "short",
        "name": "Bob"
    })
    assert r.status_code == 400
    assert "8" in r.json()["detail"]


def test_login_invalid_credentials(client):
    client.post("/api/auth/signup", json={
        "email": "person@example.com",
        "username": "carol",
        "password": "password123",
        "name": "Carol"
    })
    r = client.post("/api/auth/login", json={
        "username": "carol",
        "password": "wrongpassword"
    })
    assert r.status_code == 401


def test_me_requires_auth(client):
    r = client.get("/api/auth/me")
    assert r.status_code == 401


def test_me_with_auth(auth_client):
    r = auth_client.get("/api/auth/me")
    assert r.status_code == 200
    assert r.json()["username"] == "testuser"


def test_user_settings(auth_client):
    r = auth_client.post("/api/user", json={"level": "B1", "name": "Updated"})
    assert r.status_code == 200
    assert r.json()["level"] == "B1"
    assert r.json()["name"] == "Updated"


def test_conversations_crud(auth_client):
    # Create
    r = auth_client.post("/api/conversations", json={"title": "Test Chat", "level": "A1"})
    assert r.status_code == 200
    conv = r.json()
    assert conv["title"] == "Test Chat"
    conv_id = conv["id"]

    # List
    r = auth_client.get("/api/conversations")
    assert r.status_code == 200
    assert any(c["id"] == conv_id for c in r.json())

    # Get
    r = auth_client.get(f"/api/conversations/{conv_id}")
    assert r.status_code == 200
    assert r.json()["id"] == conv_id

    # Delete
    r = auth_client.delete(f"/api/conversations/{conv_id}")
    assert r.status_code == 200

    r = auth_client.get("/api/conversations")
    assert not any(c["id"] == conv_id for c in r.json())


def test_chat_mocked(auth_client):
    with patch("main.call_nvidia") as mock_call:
        mock_call.return_value = {
            "choices": [{"message": {"content": "Bonjour!"}}]
        }
        r = auth_client.post("/api/chat", json={"message": "Hello"})
        assert r.status_code == 200
        data = r.json()
        assert data["response"] == "Bonjour!"
        assert data["xp_earned"] == 5


def test_exercise_check(auth_client):
    r = auth_client.post("/api/check-exercise", json={
        "exercise_id": "ex-1",
        "answer": "bonjour",
        "exercise_data": {
            "type": "short_answer",
            "answer": "bonjour",
            "acceptable": []
        }
    })
    assert r.status_code == 200
    data = r.json()
    assert data["correct"] is True
    assert data["total_xp"] >= 10


def test_comments_and_sharing(auth_client):
    # Create a conversation to share and comment on
    r = auth_client.post("/api/conversations", json={"title": "Share Me", "level": "A1"})
    conv_id = r.json()["id"]

    # Add comment
    r = auth_client.post("/api/comments", json={
        "conv_id": conv_id,
        "message": "A note"
    })
    assert r.status_code == 200
    comment_id = r.json()["id"]

    # List comments
    r = auth_client.get(f"/api/comments/{conv_id}")
    assert r.status_code == 200
    assert any(c["id"] == comment_id for c in r.json())

    # Share conversation
    r = auth_client.post("/api/share", json={"conv_id": conv_id})
    assert r.status_code == 200
    share_id = r.json()["share_id"]

    # Fetch shared conversation (no auth required)
    r = auth_client.get(f"/api/share/{share_id}")
    assert r.status_code == 200
    assert r.json()["conv_id"] == conv_id


def test_export(auth_client):
    r = auth_client.post("/api/conversations", json={"title": "Export Me", "level": "A1"})
    conv_id = r.json()["id"]

    r = auth_client.post("/api/export", json={"conv_id": conv_id, "format": "markdown"})
    assert r.status_code == 200
    data = r.json()
    assert data["format"] == "markdown"
    assert "Export Me" in data["content"]


def test_flashcards(auth_client):
    r = auth_client.post("/api/flashcards", json={
        "front": "chat",
        "back": "cat",
        "card_type": "vocab",
        "level": "A1"
    })
    assert r.status_code == 200
    card_id = r.json()["id"]

    r = auth_client.get("/api/flashcards")
    assert r.status_code == 200
    assert any(c["id"] == card_id for c in r.json())


def test_progress_and_streaks(auth_client):
    r = auth_client.get("/api/progress")
    assert r.status_code == 200
    assert "xp" in r.json()

    r = auth_client.get("/api/streaks")
    assert r.status_code == 200
    assert "current" in r.json()


def test_health_does_not_leak_database_url(client):
    r = client.get("/health")
    assert r.status_code == 200
    data = r.json()
    assert "database_url" not in data


def test_tts_requires_auth(client):
    r = client.post("/api/tts", json={"text": "bonjour", "lang": "fr"})
    assert r.status_code == 401


def test_comments_require_auth(client):
    r = client.get("/api/comments/conv-123")
    assert r.status_code == 401


def test_export_get_requires_auth(client):
    r = client.get("/api/export/conv-123")
    assert r.status_code == 401


def test_chat_message_too_long(auth_client):
    r = auth_client.post("/api/chat", json={"message": "a" * 5001})
    assert r.status_code == 400


def test_writing_correction_text_too_long(auth_client):
    r = auth_client.post("/api/writing/correct", json={"text": "a" * 5001})
    assert r.status_code == 400


def test_system_prompt_has_guardrails():
    from engine import build_system_prompt
    prompt = build_system_prompt(level="A1", mode="general")
    assert "refuse" in prompt.lower()
    assert "off-topic" in prompt.lower() or "french" in prompt.lower()
