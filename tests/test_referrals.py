"""Referral codes and one-time referrer reward."""


import main


def _signup(client, username, ref=None):
    payload = {
        "email": f"{username}@example.com", "username": username,
        "password": "password123", "name": username, "accept_terms": True,
    }
    if ref:
        payload["ref"] = ref
    r = client.post("/api/auth/signup", json=payload)
    assert r.status_code == 200, r.text
    return r.json()


def _login(client, username):
    r = client.post("/api/auth/login", json={"username": username, "password": "password123"})
    assert r.status_code == 200
    client.headers["Authorization"] = f"Bearer {r.json()['token']}"


def test_referral_link_endpoint(client):
    _signup(client, "referrer1")
    _login(client, "referrer1")

    r = client.get("/api/referrals/me")
    assert r.status_code == 200
    data = r.json()
    assert len(data["code"]) >= 6
    assert data["link"].startswith("/login?mode=signup&ref=")
    assert data["referredCount"] == 0


def test_referred_learner_completes_first_lesson_and_rewards_referrer(client):
    _signup(client, "referrer2")
    referrer = main.storage.get_user_by_username("referrer2")
    code = referrer["referral_code"]
    client.headers.clear()

    _signup(client, "newlearner", ref=code)
    _login(client, "newlearner")
    r = client.post("/api/progress/complete-lesson", json={"lesson_id": "a1-test"})
    assert r.status_code == 200

    referrer_after = main.storage.get_user_by_username("referrer2")
    learner_after = main.storage.get_user_by_username("newlearner")
    assert learner_after.get("referral_rewarded") is True
    assert referrer_after["progress"]["xp"] >= 50
