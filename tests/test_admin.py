"""Authentication, provider configuration, and publication tests for the admin console."""

import asyncio
import base64
import copy
import json
import time

import bcrypt
import pyotp
import pytest

import main


ADMIN_TEST_USERNAME = "root-admin"
ADMIN_TEST_PASSWORD = "a-very-long-admin-password-2026"


@pytest.fixture
def signed_admin(client, monkeypatch):
    monkeypatch.setattr(main, "ADMIN_USERNAME", ADMIN_TEST_USERNAME)
    monkeypatch.setattr(
        main,
        "ADMIN_PASSWORD_HASH",
        bcrypt.hashpw(ADMIN_TEST_PASSWORD.encode(), bcrypt.gensalt(rounds=4)).decode(),
    )
    monkeypatch.setattr(main, "ADMIN_SESSION_SECRET", "test-admin-session-secret-0123456789abcdef")
    monkeypatch.setattr(main, "ADMIN_SESSION_TTL_MINUTES", 15)
    monkeypatch.setattr(main, "ADMIN_AUTH_CONFIGURED", True)
    monkeypatch.setattr(main, "COOKIE_SECURE", False)

    response = client.post(
        "/api/admin/login",
        json={"username": ADMIN_TEST_USERNAME, "password": ADMIN_TEST_PASSWORD},
    )
    assert response.status_code == 200, response.text
    session = client.get("/api/admin/session")
    assert session.status_code == 200
    return client, session.json()["csrf_token"]


def test_admin_shell_is_same_origin_and_not_indexed(client):
    response = client.get(main.ADMIN_PATH)
    assert response.status_code == 200
    assert "Parlez Admin" in response.text
    assert response.headers.get("x-robots-tag") == "noindex, nofollow, noarchive"
    assert response.headers.get("cache-control", "").startswith("no-cache")
    assert 'data-section="users"' in response.text
    assert 'data-section="observability"' in response.text
    assert 'id="section-observability"' in response.text
    assert 'id="statusUsers"' in response.text
    assert 'id="usersTotalCount"' in response.text
    openapi = client.get("/openapi.json").json()
    assert "/api/admin/config" not in openapi.get("paths", {})
    assert "/api/admin/users" not in openapi.get("paths", {})
    assert "/api/admin/users/count" not in openapi.get("paths", {})


def test_admin_endpoints_fail_closed_when_admin_is_not_configured(client, monkeypatch):
    monkeypatch.setattr(main, "ADMIN_AUTH_CONFIGURED", False)
    response = client.get("/api/admin/config")
    assert response.status_code == 503
    assert client.get("/api/admin/users").status_code == 503
    assert client.get("/api/admin/users/count").status_code == 503
    assert client.get("/api/admin/observability").status_code == 503
    assert client.post("/api/admin/login", json={"username": "x", "password": "x", "totp": "abcdef"}).status_code == 503


def test_observability_panel_is_admin_only_and_shows_slos_alerts_and_traces(signed_admin):
    client, _ = signed_admin
    main.OBSERVABILITY.reset_recent()
    for _ in range(20):
        main.OBSERVABILITY.record_request(
            method="GET",
            route="/api/progress",
            status_code=500,
            duration_seconds=0.15,
            service_class="core",
            request_id=None,
            correlation_id=None,
            trace_id=None,
        )
    with main.tracer.start_as_current_span("admin.observability.test"):
        pass

    response = client.get("/api/admin/observability")
    assert response.status_code == 200, response.text
    assert response.headers.get("x-request-id")
    payload = response.json()
    assert payload["metrics"]["core_requests_24h"] == 20
    assert any(item["id"] == "core_api_availability" and item["state"] == "breached" for item in payload["slos"])
    assert any(item["id"] == "http_5xx_rate" for item in payload["alerts"])
    assert any(item["name"] == "admin.observability.test" for item in payload["traces"])


def test_admin_login_starts_with_username_password_only_and_rejects_cross_origin(client, monkeypatch):
    monkeypatch.setattr(main, "ADMIN_USERNAME", ADMIN_TEST_USERNAME)
    monkeypatch.setattr(
        main,
        "ADMIN_PASSWORD_HASH",
        bcrypt.hashpw(ADMIN_TEST_PASSWORD.encode(), bcrypt.gensalt(rounds=4)).decode(),
    )
    monkeypatch.setattr(main, "ADMIN_SESSION_SECRET", "test-admin-session-secret-0123456789abcdef")
    monkeypatch.setattr(main, "ADMIN_AUTH_CONFIGURED", True)

    password_only = client.post(
        "/api/admin/login",
        json={"username": ADMIN_TEST_USERNAME, "password": ADMIN_TEST_PASSWORD},
    )
    assert password_only.status_code == 200, password_only.text

    wrong_password = client.post(
        "/api/admin/login",
        json={"username": ADMIN_TEST_USERNAME, "password": "incorrect-password"},
    )
    assert wrong_password.status_code == 401

    cross_origin = client.post(
        "/api/admin/login",
        headers={"Origin": "https://attacker.invalid"},
        json={"username": ADMIN_TEST_USERNAME, "password": ADMIN_TEST_PASSWORD},
    )
    assert cross_origin.status_code == 403


def test_admin_users_directory_requires_an_authenticated_admin(client, monkeypatch):
    monkeypatch.setattr(main, "ADMIN_AUTH_CONFIGURED", True)
    response = client.get("/api/admin/users")
    assert response.status_code == 401
    assert client.get("/api/admin/users/count").status_code == 401


def test_admin_users_directory_counts_and_paginates_without_private_fields(signed_admin):
    client, _csrf = signed_admin
    empty = client.get("/api/admin/users").json()
    assert empty["total"] == 0
    assert client.get("/api/admin/users/count").json() == {"total": 0}
    assert empty["users"] == []
    password_hash = bcrypt.hashpw(b"test-user-password", bcrypt.gensalt(rounds=4)).decode()
    learners = [
        ("zoeexample", "Zoe Example", "zoe@example.test", "B2", "2026-10-24"),
        ("alexexample", "Alex Example", "alex@example.test", "A2", "2026-10-23"),
        ("miraexample", "Mira Example", "mira@example.test", "B1", None),
    ]
    for index, (username, name, email, level, last_active) in enumerate(learners):
        user = main.storage.create_user(username, password_hash, name, email)
        user["created_at"] = time.time() - (index + 1) * 86400
        user["level"] = level
        user["progress"]["level"] = level
        user["progress"]["last_active"] = last_active
        main.storage.save_user(user)

    assert client.get("/api/admin/users/count").json() == {"total": 3}
    first_page_response = client.get("/api/admin/users?limit=2&offset=0")
    assert first_page_response.status_code == 200, first_page_response.text
    first_page = first_page_response.json()
    assert first_page["total"] == 3
    assert first_page["limit"] == 2
    assert first_page["offset"] == 0
    assert [user["username"] for user in first_page["users"]] == ["alexexample", "miraexample"]
    assert first_page["users"][0]["level"] == "A2"
    assert first_page["users"][0]["email"] == "alex@example.test"
    assert first_page["users"][0]["last_active"] == "2026-10-23"
    assert first_page["users"][1]["last_active"] is None
    assert all(
        set(user) == {"name", "username", "email", "level", "registered_at", "last_active"}
        for user in first_page["users"]
    )
    assert "test-user-password" not in first_page_response.text
    assert "password_hash" not in first_page_response.text
    assert "conversations" not in first_page_response.text

    second_page = client.get("/api/admin/users?limit=2&offset=2").json()
    assert second_page["total"] == 3
    assert [user["username"] for user in second_page["users"]] == ["zoeexample"]
    assert client.get("/api/admin/users?limit=101").status_code == 400
    assert client.get("/api/admin/users?offset=-1").status_code == 400


def test_admin_can_enroll_and_toggle_authenticator_mfa_from_panel(signed_admin):
    client, csrf = signed_admin

    status = client.get("/api/admin/mfa")
    assert status.status_code == 200
    assert status.json() == {"enabled": False, "setup_pending": False}
    other_session_id = "other-active-admin-session"
    main.storage.create_admin_session(other_session_id, ADMIN_TEST_USERNAME, time.time() + 900)

    no_csrf = client.post(
        "/api/admin/mfa/setup",
        json={"password": ADMIN_TEST_PASSWORD},
    )
    assert no_csrf.status_code == 403

    setup = client.post(
        "/api/admin/mfa/setup",
        headers={"X-CSRF-Token": csrf},
        json={"password": ADMIN_TEST_PASSWORD},
    )
    assert setup.status_code == 200, setup.text
    assert "no-store" in setup.headers.get("cache-control", "")
    setup_data = setup.json()
    secret = setup_data["secret"]
    qr_svg = base64.b64decode(setup_data["qr_data_uri"].split(",", 1)[1])
    assert qr_svg.lstrip().startswith(b"<?xml") or b"<svg" in qr_svg.lower()
    assert secret not in qr_svg.decode("utf-8", errors="ignore")

    pending_secret = main.storage.get_setting(main.ADMIN_MFA_PENDING_SETTING_KEY)
    assert isinstance(pending_secret, str)
    assert secret not in pending_secret
    assert main._decrypt_admin_mfa_secret(pending_secret) == secret
    assert client.get("/api/admin/mfa").json() == {"enabled": False, "setup_pending": True}

    invalid_code = client.post(
        "/api/admin/mfa/enable",
        headers={"X-CSRF-Token": csrf},
        json={"code": "not-a-code"},
    )
    assert invalid_code.status_code == 400

    enabled = client.post(
        "/api/admin/mfa/enable",
        headers={"X-CSRF-Token": csrf},
        json={"code": pyotp.TOTP(secret).now()},
    )
    assert enabled.status_code == 200, enabled.text
    assert enabled.json()["sign_in_again"] is True
    assert client.get("/api/admin/session").status_code == 401
    assert not main.storage.admin_session_is_active(other_session_id, ADMIN_TEST_USERNAME)

    encrypted_state = main.storage.get_setting(main.ADMIN_MFA_SETTING_KEY)
    assert secret not in json.dumps(encrypted_state)
    assert main._get_admin_mfa_state()["secret"] == secret

    password_only = client.post(
        "/api/admin/login",
        json={"username": ADMIN_TEST_USERNAME, "password": ADMIN_TEST_PASSWORD},
    )
    assert password_only.status_code == 428
    wrong_code = client.post(
        "/api/admin/login",
        json={"username": ADMIN_TEST_USERNAME, "password": ADMIN_TEST_PASSWORD, "totp": "not-a-code"},
    )
    assert wrong_code.status_code == 401
    mfa_login = client.post(
        "/api/admin/login",
        json={
            "username": ADMIN_TEST_USERNAME,
            "password": ADMIN_TEST_PASSWORD,
            "totp": pyotp.TOTP(secret).now(),
        },
    )
    assert mfa_login.status_code == 200, mfa_login.text
    signed_in = client.get("/api/admin/session")
    assert signed_in.status_code == 200
    csrf_after_login = signed_in.json()["csrf_token"]
    assert client.get("/api/admin/mfa").json() == {"enabled": True, "setup_pending": False}
    config_response = client.get("/api/admin/config")
    assert config_response.status_code == 200
    assert secret not in json.dumps(signed_in.json())
    assert secret not in json.dumps(config_response.json())

    bad_disable = client.post(
        "/api/admin/mfa/disable",
        headers={"X-CSRF-Token": csrf_after_login},
        json={"password": "incorrect-password", "totp": pyotp.TOTP(secret).now()},
    )
    assert bad_disable.status_code == 403
    assert client.get("/api/admin/mfa").json()["enabled"] is True

    disabled = client.post(
        "/api/admin/mfa/disable",
        headers={"X-CSRF-Token": csrf_after_login},
        json={"password": ADMIN_TEST_PASSWORD, "totp": pyotp.TOTP(secret).now()},
    )
    assert disabled.status_code == 200, disabled.text
    assert disabled.json()["enabled"] is False
    assert client.get("/api/admin/session").status_code == 401
    assert client.get("/api/admin/mfa").status_code == 401

    password_login = client.post(
        "/api/admin/login",
        json={"username": ADMIN_TEST_USERNAME, "password": ADMIN_TEST_PASSWORD},
    )
    assert password_login.status_code == 200, password_login.text


def test_regular_user_session_does_not_authorize_admin_api(client, monkeypatch):
    monkeypatch.setattr(main, "ADMIN_AUTH_CONFIGURED", True)
    client.post("/api/auth/signup", json={
        "email": "learner@example.com",
        "username": "learner",
        "password": "password123",
        "name": "Learner",
    })
    login = client.post("/api/auth/login", json={"username": "learner", "password": "password123"})
    client.headers["Authorization"] = f"Bearer {login.json()['token']}"
    response = client.get("/api/admin/config")
    assert response.status_code == 401
    assert client.get("/api/admin/users").status_code == 401
    assert client.get("/api/admin/users/count").status_code == 401


def test_admin_writes_require_csrf_and_publish_level_updates_are_enforced(signed_admin):
    client, csrf = signed_admin
    no_csrf = client.put("/api/admin/courses", json={"enabled_levels": ["A1", "A2"], "enabled_units": {}})
    assert no_csrf.status_code == 403

    admin_courses = client.get("/api/admin/courses")
    assert admin_courses.status_code == 200
    a2 = next(level for level in admin_courses.json()["levels"] if level["level"] == "A2")
    assert a2["lesson_count"] == 24
    assert len(a2["units"]) == 8
    assert a2["content_status"] == "published_unattested"
    assert a2["review_status"] == "unattested"
    assert a2["reviewer_name"] is None
    assert a2["reviewer_qualification"] is None
    assert main.storage.get_setting("course_reviews", {}) == {}
    assert a2["enabled"] is True
    assert "without a recorded reviewer attestation" in a2["release_warning"]
    assert all(unit["capstone"] for unit in a2["units"])

    payload = {
        "enabled_levels": ["A1", "A2"],
        "enabled_units": {
            "A1": [unit["id"] for unit in next(item for item in admin_courses.json()["levels"] if item["level"] == "A1")["units"]],
            "A2": [unit["id"] for unit in a2["units"]],
            "B1": [],
            "B2": [],
        },
    }
    response = client.put("/api/admin/courses", headers={"X-CSRF-Token": csrf}, json=payload)
    assert response.status_code == 200, response.text
    assert response.json()["enabled_levels"] == ["A1", "A2"]
    assert client.get("/api/courses/A2").status_code == 200

    review = client.post(
        "/api/admin/courses/A2/review",
        headers={"X-CSRF-Token": csrf},
        json={"reviewer_name": "French educator", "qualification": "Graduate diploma in French-language teaching", "confirm_review": True},
    )
    assert review.status_code == 200, review.text
    updated_a2 = next(level for level in review.json()["levels"] if level["level"] == "A2")
    assert updated_a2["review_status"] == "reviewed"

    levels = client.get("/api/courses").json()
    assert [item["level"] for item in levels] == ["A1", "A2"]
    assert client.get("/api/courses/A2").status_code == 200
    assert client.get("/api/courses/B1").status_code == 404


def test_admin_rejects_disabling_a1_and_empty_published_level(signed_admin):
    client, csrf = signed_admin
    no_a1 = client.put(
        "/api/admin/courses",
        headers={"X-CSRF-Token": csrf},
        json={"enabled_levels": ["A2"], "enabled_units": {"A2": ["a2-u1"]}},
    )
    assert no_a1.status_code == 400

    empty_level = client.put(
        "/api/admin/courses",
        headers={"X-CSRF-Token": csrf},
        json={"enabled_levels": ["A1", "A2"], "enabled_units": {"A1": ["a1-m1"], "A2": []}},
    )
    assert empty_level.status_code == 400


def test_admin_can_select_provider_without_returning_api_key(signed_admin, monkeypatch):
    client, csrf = signed_admin
    monkeypatch.setenv("GEMINI_API_KEY", "test-secret-gemini-key")

    class FakeResponse:
        status_code = 200

        @staticmethod
        def json():
            return {"choices": [{"message": {"content": "Bonjour"}}]}

    class FakeAsyncClient:
        url = None
        headers = None
        payload = None

        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return None

        async def post(self, url, headers, json):
            FakeAsyncClient.url = url
            FakeAsyncClient.headers = headers
            FakeAsyncClient.payload = json
            return FakeResponse()

    monkeypatch.setattr(main.httpx, "AsyncClient", FakeAsyncClient)
    test_response = client.post(
        "/api/admin/ai/test",
        headers={"X-CSRF-Token": csrf},
        json={"provider": "gemini", "model": "gemini-test-model"},
    )
    assert test_response.status_code == 200, test_response.text
    assert test_response.json()["ok"] is True
    assert FakeAsyncClient.payload["messages"][0]["content"] == "Reply with exactly: Parlez connection test passed."

    response = client.put(
        "/api/admin/ai",
        headers={"X-CSRF-Token": csrf},
        json={"provider": "gemini", "model": "gemini-test-model"},
    )
    assert response.status_code == 200, response.text
    assert response.json()["provider"] == "gemini"
    assert response.json()["model"] == "gemini-test-model"
    assert "test-secret-gemini-key" not in json.dumps(client.get("/api/admin/config").json())

    result = asyncio.run(main.call_nvidia([{"role": "user", "content": "Bonjour"}]))
    assert result["choices"][0]["message"]["content"] == "Bonjour"
    assert FakeAsyncClient.url == main.AI_PROVIDER_SPECS["gemini"]["base_url"]
    assert FakeAsyncClient.payload["model"] == "gemini-test-model"
    assert FakeAsyncClient.headers["Authorization"] == "Bearer test-secret-gemini-key"


def test_model_change_requires_a_successful_test(signed_admin, monkeypatch):
    client, csrf = signed_admin
    monkeypatch.setenv("GEMINI_API_KEY", "test-secret-gemini-key")
    response = client.put(
        "/api/admin/ai",
        headers={"X-CSRF-Token": csrf},
        json={"provider": "gemini", "model": "gemini-test-model"},
    )
    assert response.status_code == 400
    assert "connection test" in response.json()["detail"]


def test_admin_can_rollback_to_last_known_ai_model(signed_admin, monkeypatch):
    client, csrf = signed_admin
    monkeypatch.setattr(main, "NVIDIA_API_KEY", "test-nvidia-key")
    monkeypatch.setenv("GEMINI_API_KEY", "test-secret-gemini-key")

    async def fake_call(messages, provider, model, max_tokens=2048, operation="chat"):
        return {"choices": [{"message": {"content": "test ok"}}]}

    monkeypatch.setattr(main, "call_ai_provider", fake_call)
    tested = client.post(
        "/api/admin/ai/test",
        headers={"X-CSRF-Token": csrf},
        json={"provider": "gemini", "model": "gemini-test-model"},
    )
    assert tested.status_code == 200
    saved = client.put(
        "/api/admin/ai",
        headers={"X-CSRF-Token": csrf},
        json={"provider": "gemini", "model": "gemini-test-model"},
    )
    assert saved.status_code == 200
    assert saved.json()["can_rollback"] is True

    rolled_back = client.post("/api/admin/ai/rollback", headers={"X-CSRF-Token": csrf})
    assert rolled_back.status_code == 200
    assert rolled_back.json()["provider"] == "nvidia"
    assert rolled_back.json()["can_rollback"] is False


def test_admin_model_config_rejects_missing_keys_and_arbitrary_provider(signed_admin, monkeypatch):
    client, csrf = signed_admin
    monkeypatch.setenv("OPENROUTER_API_KEY", "")
    missing_key = client.put(
        "/api/admin/ai",
        headers={"X-CSRF-Token": csrf},
        json={"provider": "openrouter", "model": "openrouter/free"},
    )
    assert missing_key.status_code == 400

    arbitrary_provider = client.put(
        "/api/admin/ai",
        headers={"X-CSRF-Token": csrf},
        json={"provider": "http://127.0.0.1:1234", "model": "x"},
    )
    assert arbitrary_provider.status_code == 400


def test_admin_audit_log_records_setting_changes(signed_admin):
    client, csrf = signed_admin
    before = client.get("/api/admin/audit").json()
    assert before[0]["action"] == "admin_login"
    response = client.put(
        "/api/admin/courses",
        headers={"X-CSRF-Token": csrf},
        json={"enabled_levels": ["A1"], "enabled_units": {"A1": ["a1-m1"]}},
    )
    assert response.status_code == 200
    after = client.get("/api/admin/audit").json()
    assert after[0]["action"] == "course_publication_updated"


def test_admin_unit_publication_gates_direct_lesson_requests(signed_admin):
    client, csrf = signed_admin
    catalog = client.get("/api/admin/courses").json()
    a1 = next(level for level in catalog["levels"] if level["level"] == "A1")
    a2 = next(level for level in catalog["levels"] if level["level"] == "A2")
    first_a2_unit = a2["units"][0]
    hidden_a2_unit = a2["units"][1]
    payload = {
        "enabled_levels": ["A1", "A2"],
        "enabled_units": {
            "A1": [unit["id"] for unit in a1["units"]],
            "A2": [first_a2_unit["id"]],
            "B1": [],
            "B2": [],
        },
    }
    review = client.post(
        "/api/admin/courses/A2/review",
        headers={"X-CSRF-Token": csrf},
        json={"reviewer_name": "French educator", "qualification": "Graduate diploma in French-language teaching", "confirm_review": True},
    )
    assert review.status_code == 200
    saved = client.put("/api/admin/courses", headers={"X-CSRF-Token": csrf}, json=payload)
    assert saved.status_code == 200, saved.text

    public_course = client.get("/api/courses/A2")
    assert public_course.status_code == 200
    assert [unit["id"] for unit in public_course.json()["units"]] == [first_a2_unit["id"]]

    hidden_lesson_id = next(
        lesson_id
        for course in main.COURSE_CATALOG.values()
        for unit in course.units
        if unit.id == hidden_a2_unit["id"]
        for lesson_id in [unit.lessons[0].id]
    )
    denied = client.get(f"/api/courses/A2/lessons/{hidden_lesson_id}")
    assert denied.status_code == 404


def test_admin_logout_revokes_server_side_session(signed_admin):
    client, csrf = signed_admin
    response = client.post("/api/admin/logout", headers={"X-CSRF-Token": csrf})
    assert response.status_code == 200
    assert client.get("/api/admin/session").status_code == 401


def test_admin_cannot_publish_malformed_course_content(signed_admin, monkeypatch):
    client, csrf = signed_admin
    broken_course = copy.deepcopy(main.COURSE_CATALOG["A2"])
    broken_course.units[0].lessons[0].vocabulary[0].fr += "\\"
    monkeypatch.setitem(main.COURSE_CATALOG, "A2", broken_course)

    review = client.post(
        "/api/admin/courses/A2/review",
        headers={"X-CSRF-Token": csrf},
        json={"reviewer_name": "French educator", "qualification": "Graduate diploma in French-language teaching", "confirm_review": True},
    )
    assert review.status_code == 409
    assert "integrity checks" in review.json()["detail"]

    current = client.get("/api/admin/courses").json()
    payload = {
        "enabled_levels": ["A1", "A2"],
        "enabled_units": {
            level["level"]: [unit["id"] for unit in level["units"]]
            for level in current["levels"]
        },
    }
    response = client.put("/api/admin/courses", headers={"X-CSRF-Token": csrf}, json=payload)
    assert response.status_code == 409
    assert client.get("/api/courses/A2").status_code == 404


def test_course_review_attestation_is_bound_to_course_version(signed_admin, monkeypatch):
    client, csrf = signed_admin
    current = client.get("/api/admin/courses").json()
    a1 = next(level for level in current["levels"] if level["level"] == "A1")
    a2 = next(level for level in current["levels"] if level["level"] == "A2")
    review = client.post(
        "/api/admin/courses/A2/review",
        headers={"X-CSRF-Token": csrf},
        json={"reviewer_name": "French educator", "qualification": "Graduate diploma in French-language teaching", "confirm_review": True},
    )
    assert review.status_code == 200

    changed_course = copy.deepcopy(main.COURSE_CATALOG["A2"])
    changed_course.version = "2026.3"
    monkeypatch.setitem(main.COURSE_CATALOG, "A2", changed_course)
    payload = {
        "enabled_levels": ["A1", "A2"],
        "enabled_units": {
            "A1": [unit["id"] for unit in a1["units"]],
            "A2": [unit["id"] for unit in a2["units"]],
        },
    }
    response = client.put("/api/admin/courses", headers={"X-CSRF-Token": csrf}, json=payload)
    assert response.status_code == 200
    assert client.get("/api/courses/A2").status_code == 200
    assert client.get("/api/courses/A2").json()["contentStatus"] == "published_unattested"


def test_legacy_course_access_setting_migrates_to_owner_release(signed_admin):
    client, _ = signed_admin
    main.storage.set_setting("course_access", {
        "enabled_levels": ["A1"],
        "enabled_units": {},
    })

    assert client.get("/api/courses/A2").status_code == 200
    assert client.get("/api/courses/B1").status_code == 200
    migrated = main.storage.get_setting("course_access")
    assert migrated["release_revision"] == main.COURSE_ACCESS_RELEASE_REVISION
    assert migrated["enabled_levels"] == ["A1", "A2", "B1", "B2"]
    assert all(migrated["enabled_units"][level] for level in ("A2", "B1", "B2"))


def test_course_review_attestation_is_invalidated_by_content_edit(signed_admin, monkeypatch):
    client, csrf = signed_admin
    original = copy.deepcopy(main.COURSE_CATALOG["B1"])
    review = client.post(
        "/api/admin/courses/B1/review",
        headers={"X-CSRF-Token": csrf},
        json={"reviewer_name": "French educator", "qualification": "Graduate diploma in French-language teaching", "confirm_review": True},
    )
    assert review.status_code == 200

    changed_course = copy.deepcopy(original)
    changed_course.units[0].lessons[0].description += " Additional content added after review."
    monkeypatch.setitem(main.COURSE_CATALOG, "B1", changed_course)
    response = client.put(
        "/api/admin/courses",
        headers={"X-CSRF-Token": csrf},
        json={
            "enabled_levels": ["A1", "B1"],
            "enabled_units": {"B1": [unit.id for unit in changed_course.units]},
        },
    )
    assert response.status_code == 200
    public_b1 = client.get("/api/courses/B1")
    assert public_b1.status_code == 200
    assert public_b1.json()["contentStatus"] == "published_unattested"
    admin_b1 = next(level for level in response.json()["levels"] if level["level"] == "B1")
    assert admin_b1["review_status"] == "unattested"
    assert admin_b1["reviewer_name"] is None
