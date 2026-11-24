"""Informal placement and privacy-safe funnel measurement."""

import main
from courses.assessment import ITEMS, evaluate, public_items


def test_placement_items_hide_answers():
    items = public_items()
    assert len(items) == 12
    assert all("answer_index" not in item for item in items)


def test_placement_evaluation_is_honest():
    perfect = {item.id: item.answer_index for item in ITEMS}
    result = evaluate(perfect)
    assert result["levelEstimate"] == "B2"
    assert result["unassessedSkills"] == ["listening", "speaking", "writing"]
    assert "not a CEFR or NCLC" in result["notice"]
    assert evaluate({})["levelEstimate"] == "A1"


def test_placement_endpoints(client):
    r = client.get("/api/assessment/placement")
    assert r.status_code == 200 and len(r.json()["items"]) == 12
    answers = {item.id: item.answer_index for item in ITEMS[:3]}
    submitted = client.post("/api/assessment/placement/submit", json={"answers": answers})
    assert submitted.status_code == 200
    assert submitted.json()["levelEstimate"] in {"A1", "A2", "B1", "B2"}


def test_learning_events_are_coarse_and_funnel_counts_aggregate(auth_client):
    r = auth_client.post("/api/events", json={
        "name": "lesson_start", "props": {"level": "A1", "user_answer": "secret text"},
    })
    assert r.status_code == 200
    counts = main.storage.funnel_counts()
    assert counts.get("lesson_start") == 1
    with main.storage.Session() as session:
        from db import LearningEvent
        row = session.query(LearningEvent).first()
    assert row.props == {"level": "A1"}  # free-text key was dropped


def test_events_reject_unknown_names(auth_client):
    assert auth_client.post("/api/events", json={"name": "drop_all_tables"}).status_code == 400


def test_chat_fact_memory_and_mid_turn_guidance(auth_client, monkeypatch):
    added = auth_client.post("/api/chat/facts", json={"fact": "I am preparing for TEF Canada in 2027."})
    assert added.status_code == 200
    listed = auth_client.get("/api/chat/facts").json()["facts"]
    assert "TEF Canada" in listed[0]

    captured = {}

    async def fake_call(messages, max_tokens=None, operation="chat"):
        captured["messages"] = messages
        return {"choices": [{"message": {"content": "Bonjour !"}}]}

    monkeypatch.setattr(main, "call_nvidia", fake_call)
    r = auth_client.post("/api/chat", json={"message": "Je ne comprends pas, can you repeat?"})
    assert r.status_code == 200
    system = captured["messages"][0]["content"]
    assert "SESSION CHECK" in system
    assert "TEF Canada" in system


def test_experiment_assignment_is_stable(auth_client):
    first = auth_client.get("/api/experiments/onboarding-copy").json()["variant"]
    second = auth_client.get("/api/experiments/onboarding-copy").json()["variant"]
    assert first == second
    assert first in {"control", "variant"}
