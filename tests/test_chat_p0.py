"""Regression tests for the P0 chatbot fixes (BUG-08 … BUG-11)."""

import asyncio

import pytest
from fastapi import HTTPException

import main
from db import LlmUsage


class _FakeResponse:
    def __init__(self, payload, status_code=200):
        self._payload = payload
        self.status_code = status_code

    def json(self):
        return self._payload


class _FakeAsyncClient:
    """Minimal httpx.AsyncClient stand-in that records the outgoing request."""

    payload = None
    headers = None
    responses = None

    def __init__(self, *args, **kwargs):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass

    async def post(self, url, headers, json):
        _FakeAsyncClient.payload = json
        _FakeAsyncClient.headers = headers
        responses = _FakeAsyncClient.responses or [
            {"choices": [{"message": {"content": "Bonjour"}}]}
        ]
        return _FakeResponse(responses.pop(0) if responses else responses)


@pytest.fixture(autouse=True)
def _reset_fake_client():
    _FakeAsyncClient.payload = None
    _FakeAsyncClient.headers = None
    _FakeAsyncClient.responses = None
    yield
    _FakeAsyncClient.responses = None


@pytest.fixture(autouse=True)
def _no_retry_sleep(monkeypatch):
    async def no_sleep(_seconds):
        return None

    monkeypatch.setattr(main.asyncio, "sleep", no_sleep)


def test_chat_payload_requests_json_and_larger_budget(monkeypatch):
    monkeypatch.setattr(main, "NVIDIA_API_KEY", "test-key")
    monkeypatch.setattr(main, "MODEL", "nvidia/test-model")
    monkeypatch.setattr(main.httpx, "AsyncClient", _FakeAsyncClient)

    result = asyncio.run(main.call_nvidia([{"role": "user", "content": "Bonjour"}]))

    assert result["choices"][0]["message"]["content"] == "Bonjour"
    assert _FakeAsyncClient.payload["stream"] is False
    assert _FakeAsyncClient.payload["max_tokens"] >= main.CHAT_MAX_TOKENS
    assert _FakeAsyncClient.headers.get("Accept") == "application/json"


@pytest.mark.parametrize("payload", [
    {"choices": [{"message": {"content": ""}, "finish_reason": "length"}]},
    {"choices": [{"message": {"content": None}, "finish_reason": "stop"}]},
    {"choices": [{"message": {"content": "   "}}]},
    {"choices": []},
])
def test_empty_or_truncated_provider_reply_is_a_failure(monkeypatch, payload):
    monkeypatch.setattr(main, "NVIDIA_API_KEY", "test-key")
    monkeypatch.setattr(main, "MODEL", "nvidia/test-model")
    monkeypatch.setattr(main.httpx, "AsyncClient", _FakeAsyncClient)
    _FakeAsyncClient.responses = [payload] * 3

    with pytest.raises(HTTPException) as exc:
        asyncio.run(main.call_nvidia([{"role": "user", "content": "Bonjour"}]))

    assert exc.value.status_code == 503


def test_lesson_vocabulary_and_grammar_reach_the_system_prompt():
    from engine import build_system_prompt

    prompt = build_system_prompt(level="A1", mode="lesson", lesson_context={
        "title": "First contacts",
        "titleFr": "Premiers contacts",
        "description": "Greeting people",
        "objectives": ["Greet someone"],
        "vocabulary": [{"fr": "bonjour", "en": "hello", "ipa": "/bɔ̃.ʒuʁ/"}],
        "grammar": [{"title": "être", "explanation": "Present tense of to be"}],
        "dialogue": [{"speaker": "A", "fr": "Bonjour", "en": "Hello"}],
        "culturalNote": "French greetings",
    })

    assert "AUTHORITATIVE LESSON DATA" in prompt
    assert "bonjour = hello" in prompt
    assert "être: Present tense of to be" in prompt
    assert "CULTURAL NOTE: French greetings" in prompt


def test_exercise_schema_is_only_attached_to_practice_modes():
    from engine import build_system_prompt

    conversation = build_system_prompt(level="B1", mode="conversation")
    lesson = build_system_prompt(level="A1", mode="lesson", lesson_context={"title": "Hi"})

    assert "EXERCISE FORMAT" not in conversation
    assert len(conversation) < 2500  # was ~4900+ with the always-on schema
    assert "EXERCISE FORMAT" in lesson
    assert len(lesson) > len(conversation) + 3000
    assert "LANGUAGE RATIO instruction" in lesson


def test_new_learner_is_not_treated_as_failing():
    from engine.adaptive import (
        analyze_weak_areas,
        get_difficulty_adjustments,
        build_adaptive_prompt_addition,
    )

    analysis = analyze_weak_areas([])
    assert analysis["has_data"] is False

    adjustments = get_difficulty_adjustments("A1", analysis)
    assert adjustments["french_ratio"] == 0.4
    assert adjustments["complexity"] == "normal"
    assert adjustments["practice_count"] == 3

    addition = build_adaptive_prompt_addition("A1", analysis, adjustments)
    assert "NEW LEARNER" in addition
    assert "30% French" not in addition


def test_llm_budget_is_durable_and_utc_keyed():
    user = {"id": "budget-user"}
    assert main.check_daily_llm_budget(user) == 1
    assert main.check_daily_llm_budget(user) == 2

    with main.storage.Session() as session:
        row = session.query(LlmUsage).filter_by(user_id="budget-user").one()
    assert row.count == 2
    assert row.day == main._utc_day()


def test_llm_budget_rejects_over_limit(monkeypatch):
    monkeypatch.setattr(main, "DAILY_LLM_BUDGET", 1)
    user = {"id": "limited-user"}
    main.check_daily_llm_budget(user)
    with pytest.raises(HTTPException) as exc:
        main.check_daily_llm_budget(user)
    assert exc.value.status_code == 429
    assert "midnight UTC" in exc.value.detail


class _FakeStreamResponse:
    status_code = 200

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass

    async def aiter_lines(self):
        lines = [
            'data: {"choices":[{"delta":{"content":"Bon"}}]}',
            'data: {"choices":[{"delta":{"content":"jour"}}]}',
            'data: [DONE]',
        ]
        for line in lines:
            yield line


class _FakeStreamClient:
    def __init__(self, *args, **kwargs):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass

    def stream(self, *args, **kwargs):
        return _FakeStreamResponse()


def test_streaming_provider_yields_text_deltas(monkeypatch):
    monkeypatch.setattr(main, "NVIDIA_API_KEY", "test-key")
    monkeypatch.setattr(main.httpx, "AsyncClient", _FakeStreamClient)

    async def collect():
        return [delta async for delta in main.call_ai_provider_stream(
            [{"role": "user", "content": "Bonjour"}], "nvidia", "nvidia/test-model", 2048
        )]

    assert asyncio.run(collect()) == ["Bon", "jour"]


def test_provider_failover_when_active_provider_fails(monkeypatch):
    monkeypatch.setattr(main, "NVIDIA_API_KEY", "test-key")
    monkeypatch.setenv("GEMINI_API_KEY", "fallback-key")
    main._provider_circuit.clear()
    calls = []

    async def fake_call(messages, provider, model, max_tokens=2048, operation="chat"):
        calls.append(provider)
        if provider == "nvidia":
            raise HTTPException(status_code=503, detail="down")
        return {"choices": [{"message": {"content": "Bonjour"}}]}

    monkeypatch.setattr(main, "call_ai_provider", fake_call)

    result = asyncio.run(main.call_nvidia([{"role": "user", "content": "Bonjour"}]))

    assert result["choices"][0]["message"]["content"] == "Bonjour"
    assert calls[0] == "nvidia"
    assert "gemini" in calls


def test_chat_stream_endpoint_emits_sse_events(auth_client, monkeypatch):
    async def fake_stream(messages, max_tokens=None):
        yield "Bon"
        yield "jour"

    monkeypatch.setattr(main, "stream_chat", fake_stream)

    r = auth_client.post("/api/chat/stream", json={"message": "Bonjour"})

    assert r.status_code == 200
    assert "text/event-stream" in r.headers["content-type"]
    assert '"delta": "Bon"' in r.text
    assert '"done": true' in r.text
    assert '"response": "Bonjour"' in r.text
    user = main.storage.get_user_by_username("testuser")
    assert user["progress"]["xp"] == 5


def test_chat_does_not_award_xp_for_empty_reply(auth_client, monkeypatch):
    async def fake_call(messages, max_tokens=None, operation="chat"):
        return {"choices": [{"message": {"content": ""}, "finish_reason": "length"}]}

    monkeypatch.setattr(main, "call_nvidia", fake_call)

    r = auth_client.post("/api/chat", json={"message": "Bonjour"})

    assert r.status_code == 502
    user = main.storage.get_user_by_username("testuser")
    assert user["progress"]["xp"] == 0
