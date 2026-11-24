"""Sandbox payment flows for Khalti and eSewa with mocked HTTP.

No real network calls or credentials are used. These tests lock down the
sandbox URLs, paisa conversion, signature generation and the mandatory
authoritative status check.
"""

import asyncio
import base64
import json

import pytest

import payments


class _Response:
    def __init__(self, status_code=200, payload=None):
        self.status_code = status_code
        self._payload = payload or {}

    def json(self):
        return self._payload


class _Client:
    def __init__(self, post_response=None, get_response=None):
        self.post_response = post_response
        self.get_response = get_response
        self.post_calls = []
        self.get_calls = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass

    async def post(self, url, headers=None, json=None):
        self.post_calls.append({"url": url, "headers": headers or {}, "json": json or {}})
        return self.post_response or _Response()

    async def get(self, url, params=None, headers=None):
        self.get_calls.append({"url": url, "params": params or {}, "headers": headers or {}})
        return self.get_response or _Response()

    async def aclose(self):
        pass


@pytest.fixture
def sandbox_env(monkeypatch):
    monkeypatch.setenv("APP_BASE_URL", "http://localhost:8000")
    monkeypatch.setenv("KHALTI_SECRET_KEY", "test-khalti-key")
    monkeypatch.setenv("KHALTI_BASE_URL", "https://dev.khalti.com/api/v2/")
    monkeypatch.setenv("ESEWA_SECRET_KEY", "8gBm/:&EnhH.1/q")
    monkeypatch.setenv("ESEWA_PRODUCT_CODE", "EPAYTEST")
    monkeypatch.setenv("ESEWA_BASE_URL", "https://rc-epay.esewa.com.np/api/epay/main/v2/form")
    monkeypatch.setenv("ESEWA_STATUS_URL", "https://rc-epay.esewa.com.np/api/epay/transaction/status/")


def test_khalti_sandbox_initiate_uses_paisa_and_attempt_id(sandbox_env):
    client = _Client(post_response=_Response(200, {
        "pidx": "pidx-123", "payment_url": "https://dev.khalti.com/checkout/pidx-123",
    }))
    result = asyncio.run(payments.initiate("khalti", "pay_abc", "plus_monthly", client=client))

    call = client.post_calls[0]
    assert call["url"] == "https://dev.khalti.com/api/v2/epayment/initiate/"
    assert call["headers"]["Authorization"] == "Key test-khalti-key"
    assert call["json"]["amount"] == payments.PLANS["plus_monthly"]["price_npr"] * 100
    assert call["json"]["purchase_order_id"] == "pay_abc"
    assert result["checkout_url"].endswith("pidx-123")
    assert result["provider_ref"] == "pidx-123"


def test_khalti_sandbox_verify_checks_status_and_amount(sandbox_env):
    attempt = {"amount_npr": 499, "provider_ref": "pidx-123"}
    client = _Client(get_response=_Response(200, {
        "status": "Completed", "total_amount": 49900, "transaction_id": "txn-1",
    }))
    result = asyncio.run(payments.verify("khalti", attempt, {"pidx": "pidx-123"}, client=client))

    assert result.status == "paid"
    assert result.provider_ref == "txn-1"
    assert client.get_calls[0]["url"] == "https://dev.khalti.com/api/v2/epayment/lookup/"

    bad = _Client(get_response=_Response(200, {"status": "Completed", "total_amount": 100}))
    with pytest.raises(payments.PaymentVerificationFailed):
        asyncio.run(payments.verify("khalti", attempt, {"pidx": "pidx-123"}, client=bad))


def test_esewa_sandbox_initiate_signs_required_fields(sandbox_env):
    result = asyncio.run(payments.initiate("esewa", "pay_abc", "plus_yearly"))

    assert result["provider"] == "esewa"
    assert result["method"] == "form_post"
    fields = result["fields"]
    assert fields["product_code"] == "EPAYTEST"
    assert fields["transaction_uuid"] == "pay_abc"
    assert fields["total_amount"] == f"{payments.PLANS['plus_yearly']['price_npr']:.2f}"
    expected = payments._esewa_signature(fields["total_amount"], "pay_abc", "EPAYTEST")
    assert fields["signature"] == expected
    assert result["checkout_url"].startswith("https://rc-epay.esewa.com.np")


def test_esewa_sandbox_verify_decodes_callback_and_checks_status(sandbox_env):
    attempt = {"id": "pay_abc", "amount_npr": 499}
    payload = {
        "product_code": "EPAYTEST", "transaction_uuid": "pay_abc",
        "total_amount": "499.00", "status": "COMPLETE", "transaction_code": "esewa-txn",
    }
    encoded = base64.b64encode(json.dumps(payload).encode()).decode()
    client = _Client(get_response=_Response(200, {"status": "COMPLETE"}))
    result = asyncio.run(payments.verify("esewa", attempt, {"data": encoded}, client=client))

    assert result.status == "paid"
    assert result.provider_ref == "esewa-txn"
    assert client.get_calls[0]["url"] == "https://rc-epay.esewa.com.np/api/epay/transaction/status/"

    wrong = dict(payload, transaction_uuid="someone-else")
    with pytest.raises(payments.PaymentVerificationFailed):
        asyncio.run(payments.verify(
            "esewa", attempt,
            {"data": base64.b64encode(json.dumps(wrong).encode()).decode()},
            client=_Client(),
        ))


def test_checkout_endpoint_returns_sandbox_url(sandbox_env, auth_client, monkeypatch):
    async def fake_initiate(provider, attempt_id, plan_id, client=None):
        return {
            "provider": provider, "method": "redirect",
            "checkout_url": f"https://dev.khalti.com/checkout/{attempt_id}",
            "provider_ref": f"pidx-{attempt_id}",
        }

    monkeypatch.setattr(payments, "initiate", fake_initiate)
    r = auth_client.post("/api/payments/checkout", json={"plan_id": "plus_monthly", "provider": "khalti"})

    assert r.status_code == 200
    data = r.json()
    assert data["attempt_id"].startswith("pay_")
    assert "dev.khalti.com" in data["checkout_url"]
    status = auth_client.get(f"/api/payments/attempt/{data['attempt_id']}")
    assert status.json()["status"] == "pending"
