"""Payment abstraction, entitlements and idempotent settlement."""

import time

import main
import payments


def test_plans_endpoint(client):
    r = client.get("/api/plans")
    assert r.status_code == 200
    ids = [plan["id"] for plan in r.json()["plans"]]
    assert ids == ["free", "plus_monthly", "plus_yearly"]
    assert "placeholders" in r.json()["notice"]


def test_checkout_fails_closed_without_gateway_keys(auth_client, monkeypatch):
    monkeypatch.delenv("KHALTI_SECRET_KEY", raising=False)
    r = auth_client.post("/api/payments/checkout", json={"plan_id": "plus_monthly", "provider": "khalti"})
    assert r.status_code == 503


def test_free_entitlement_includes_core_features(auth_client):
    r = auth_client.get("/api/me/entitlements")
    assert r.status_code == 200
    data = r.json()
    assert data["plan"] == "free"
    assert data["features"]["lessons"] is True
    assert data["features"]["extended_speaking"] is False


def test_paid_entitlement_expires():
    storage = main.storage
    storage.set_entitlement("paid-user", "plus_monthly", "active", time.time() - 1, "khalti", "ref")
    expired = storage.get_entitlement("paid-user")
    assert payments.has_entitlement(expired, "extended_speaking") is False

    storage.set_entitlement("paid-user", "plus_yearly", "active", time.time() + 3600, "khalti", "ref")
    active = storage.get_entitlement("paid-user")
    assert payments.has_entitlement(active, "extended_speaking") is True


def test_settlement_is_idempotent():
    storage = main.storage
    attempt_id = payments.new_attempt_id()
    storage.create_payment_attempt(attempt_id, "settle-user", "plus_monthly", "khalti", 499)
    storage.set_attempt_provider_ref(attempt_id, "pidx-1")
    attempt = storage.get_payment_attempt(attempt_id)

    first = payments.grant_from_attempt(storage, attempt, payments.Verification("paid", "txn-1", 499))
    second = payments.grant_from_attempt(storage, attempt, payments.Verification("paid", "txn-1", 499))

    assert first["settled"] is True
    assert second["settled"] is False
    assert storage.get_payment_attempt(attempt_id)["status"] == "paid"
    assert storage.get_entitlement("settle-user")["plan"] == "plus_monthly"
