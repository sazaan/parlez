"""Original, licence-aware exam practice (never reproduced past papers)."""

from mock_tests.original_items import ITEMS


def test_original_items_have_provenance():
    assert ITEMS
    for item in ITEMS:
        assert item.item_origin == "original"
        assert item.spec_source.startswith("https://")
        assert 0 <= item.answer_index < len(item.options)
        assert item.verified_on


def test_practice_endpoint_does_not_leak_answers(client):
    r = client.get("/api/exam/practice/TEF/reading")
    assert r.status_code == 200
    data = r.json()
    assert data["items"]
    assert "answer_index" not in data["items"][0]
    assert data["items"][0]["itemOrigin"] == "original"
    assert "Not real or past exam questions" in data["notice"]


def test_grade_returns_practice_accuracy_only(client):
    answers = {item.id: item.answer_index for item in ITEMS if item.exam == "TCF" and item.skill == "reading"}
    r = client.post("/api/exam/practice/grade", json={"exam": "TCF", "skill": "reading", "answers": answers})
    assert r.status_code == 200
    data = r.json()
    assert data["correct"] == data["total"]
    assert data["accuracyPercent"] == 100
    assert "not an official" in data["notice"]
    assert all(result["correct"] for result in data["results"])


def test_grade_with_wrong_answers_still_honest(client):
    r = client.post("/api/exam/practice/grade", json={
        "exam": "TEF", "skill": "listening", "answers": {"TEF-CO-O-001": 3},
    })
    data = r.json()
    assert data["correct"] == 0
    assert data["results"][0]["correctIndex"] == 0


def test_writing_and_speaking_tasks_are_available(client):
    for exam, skill in (("TEF", "writing"), ("TEF", "speaking"), ("TCF", "writing"), ("TCF", "speaking")):
        r = client.get(f"/api/exam/tasks/{exam}/{skill}")
        assert r.status_code == 200
        assert r.json()["tasks"]


def test_task_word_count_check(client):
    task_id = "TCF-EE-1"
    short = client.post("/api/exam/tasks/check", json={"task_id": task_id, "response": "Bonjour."}).json()
    assert short["withinRange"] is False
    good = client.post("/api/exam/tasks/check", json={"task_id": task_id, "response": " ".join(["mot"] * 90)}).json()
    assert good["withinRange"] is True


def test_task_attempt_saved(auth_client):
    r = auth_client.post("/api/exam/tasks/attempt", json={
        "exam": "TEF", "skill": "writing", "task_id": "TEF-EE-A-1",
        "response": " ".join(["mot"] * 100), "self_rating": 4,
    })
    assert r.status_code == 200
    assert r.json()["wordCount"] == 100


def test_resources_registry_is_licence_aware(client):
    r = client.get("/api/practice/resources")
    assert r.status_code == 200
    resources = r.json()["resources"]
    assert any(x["id"] == "official-tef-prep" and x["mode"] == "link_only" for x in resources)
    assert any(x["id"] == "open-tex-grammar" and x["commercial_use"] for x in resources)
    assert all(x["url"].startswith("https://") for x in resources)
