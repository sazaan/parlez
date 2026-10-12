"""NVIDIA NIM model configuration tests."""

import asyncio

import main


def test_model_config_uses_nemotron_35_lightning_by_default(monkeypatch):
    monkeypatch.delenv("NVIDIA_MODEL", raising=False)
    assert main.DEFAULT_NVIDIA_MODEL == "nvidia/nemotron-3.5-lightning-30b-a3b"
    assert main.resolve_nvidia_model() == main.DEFAULT_NVIDIA_MODEL
    assert main.resolve_nvidia_model("   ") == main.DEFAULT_NVIDIA_MODEL


def test_model_config_accepts_an_env_override(monkeypatch):
    monkeypatch.setenv("NVIDIA_MODEL", " nvidia/custom-chat-model ")
    assert main.resolve_nvidia_model() == "nvidia/custom-chat-model"


def test_configured_model_is_sent_to_nvidia(monkeypatch):
    class FakeResponse:
        status_code = 200

        @staticmethod
        def json():
            return {"choices": [{"message": {"content": "Bonjour"}}]}

    class FakeAsyncClient:
        payload = None

        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

        async def post(self, url, headers, json):
            self.payload = json
            FakeAsyncClient.payload = json
            return FakeResponse()

    monkeypatch.setattr(main, "NVIDIA_API_KEY", "test-key")
    monkeypatch.setattr(main, "MODEL", "nvidia/test-model")
    monkeypatch.setattr(main.httpx, "AsyncClient", FakeAsyncClient)

    result = asyncio.run(main.call_nvidia([{"role": "user", "content": "Bonjour"}]))

    assert result["choices"][0]["message"]["content"] == "Bonjour"
    assert FakeAsyncClient.payload["model"] == "nvidia/test-model"
