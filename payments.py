"""Payment gateway abstraction — Nepal first, international later.

Amounts are resolved server-side from PLANS; the browser never supplies a
price. Every provider requires an authoritative server-side status check after
the redirect. No gateway secret is ever sent to the client.

Prices below are PLACEHOLDERS for design/development only and must be confirmed
and disclosed to users before charging anyone.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import time
import uuid
from dataclasses import dataclass
import httpx


PLANS = {
    "free": {
        "name": "Free", "price_npr": 0, "duration_days": None,
        "features": ["A1–B2 practice paths", "AI tutor", "Flashcards", "Exam-style practice"],
    },
    "plus_monthly": {
        "name": "Parlez Plus (monthly)", "price_npr": 499, "duration_days": 30,
        "features": ["More speaking practice", "Higher AI allowance", "Supports the platform"],
    },
    "plus_yearly": {
        "name": "Parlez Plus (yearly)", "price_npr": 3999, "duration_days": 365,
        "features": ["Everything in monthly", "Better value", "Supports the platform"],
    },
}


class PaymentNotConfigured(RuntimeError):
    pass


class PaymentVerificationFailed(RuntimeError):
    pass


@dataclass
class Verification:
    status: str  # paid | pending | failed
    provider_ref: str
    amount_npr: int


def new_attempt_id() -> str:
    return f"pay_{uuid.uuid4().hex[:20]}"


def _env(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


def provider_configured(provider: str) -> bool:
    if provider == "khalti":
        return bool(_env("KHALTI_SECRET_KEY"))
    if provider == "esewa":
        return bool(_env("ESEWA_SECRET_KEY") and _env("ESEWA_PRODUCT_CODE"))
    if provider == "paddle":
        return bool(_env("PADDLE_API_KEY") and (
            _env("PADDLE_PRICE_MONTHLY") or _env("PADDLE_PRICE_YEARLY")
        ))
    return False


_PADDLE_PRICE_ENVS = {
    "plus_monthly": "PADDLE_PRICE_MONTHLY",
    "plus_yearly": "PADDLE_PRICE_YEARLY",
}


async def initiate(provider: str, attempt_id: str, plan_id: str, *, client=None) -> dict:
    """Return a checkout description for the static frontend."""
    plan = PLANS.get(plan_id)
    if not plan or plan["price_npr"] <= 0:
        raise ValueError("Unknown or free plan")
    if not provider_configured(provider):
        raise PaymentNotConfigured(f"{provider} is not configured on this deployment")

    owns_client = client is None
    client = client or httpx.AsyncClient(timeout=20.0)
    try:
        if provider == "khalti":
            return await _khalti_initiate(client, attempt_id, plan)
        if provider == "esewa":
            return _esewa_initiate(attempt_id, plan)
        if provider == "paddle":
            return await _paddle_initiate(client, attempt_id, plan_id)
        raise ValueError(f"Unsupported provider: {provider}")
    finally:
        if owns_client:
            await client.aclose()


async def _paddle_initiate(client, attempt_id, plan_id):
    """International Merchant-of-Record checkout (Paddle Billing).

    Paddle returns a hosted checkout URL; the webhook is handled by the same
    event-inbox pattern as the Nepal providers. Enable only with a sandbox key.
    """
    price_id = _env(_PADDLE_PRICE_ENVS.get(plan_id, ""))
    if not price_id:
        raise PaymentNotConfigured(f"No Paddle price configured for {plan_id}")
    base = _env("PADDLE_BASE_URL", "https://sandbox-api.paddle.com").rstrip("/")
    response = await client.post(
        f"{base}/transactions",
        headers={
            "Authorization": f"Bearer {_env('PADDLE_API_KEY')}",
            "Content-Type": "application/json",
        },
        json={
            "items": [{"priceId": price_id, "quantity": 1}],
            "successUrl": f"{_env('APP_BASE_URL', 'http://localhost:8000')}/payment-result?attempt={attempt_id}",
            "customData": {"attempt_id": attempt_id},
        },
    )
    if response.status_code not in (200, 201):
        raise PaymentVerificationFailed(f"Paddle initiation failed ({response.status_code})")
    data = response.json().get("data") or {}
    url = data.get("checkoutUrl") or data.get("checkout_url")
    if not url:
        raise PaymentVerificationFailed("Paddle returned no checkout URL")
    return {
        "provider": "paddle", "method": "redirect",
        "checkout_url": url, "provider_ref": data.get("id", attempt_id),
    }


async def _khalti_initiate(client, attempt_id, plan):
    base = _env("KHALTI_BASE_URL", "https://dev.khalti.com/api/v2/").rstrip("/")
    response = await client.post(
        f"{base}/epayment/initiate/",
        headers={"Authorization": f"Key {_env('KHALTI_SECRET_KEY')}", "Content-Type": "application/json"},
        json={
            "return_url": f"{_env('APP_BASE_URL', 'http://localhost:8000')}/api/payments/return/khalti",
            "website_url": _env("APP_BASE_URL", "http://localhost:8000"),
            "amount": plan["price_npr"] * 100,  # paisa
            "purchase_order_id": attempt_id,
            "purchase_order_name": plan["name"],
        },
    )
    if response.status_code != 200:
        raise PaymentVerificationFailed(f"Khalti initiation failed ({response.status_code})")
    data = response.json()
    return {
        "provider": "khalti",
        "method": "redirect",
        "checkout_url": data["payment_url"],
        "provider_ref": data.get("pidx"),
    }


def _esewa_signature(total_amount: str, transaction_uuid: str, product_code: str) -> str:
    message = f"total_amount={total_amount},transaction_uuid={transaction_uuid},product_code={product_code}"
    digest = hmac.new(_env("ESEWA_SECRET_KEY").encode(), message.encode(), hashlib.sha256).digest()
    return base64.b64encode(digest).decode()


def _esewa_initiate(attempt_id, plan):
    base = _env("ESEWA_BASE_URL", "https://rc-epay.esewa.com.np/api/epay/main/v2/form").rstrip("/")
    amount = f"{plan['price_npr']:.2f}"
    product_code = _env("ESEWA_PRODUCT_CODE", "EPAYTEST")
    fields = {
        "amount": amount, "tax_amount": "0", "total_amount": amount,
        "transaction_uuid": attempt_id, "product_code": product_code,
        "product_service_charge": "0", "product_delivery_charge": "0",
        "success_url": f"{_env('APP_BASE_URL', 'http://localhost:8000')}/api/payments/return/esewa",
        "failure_url": f"{_env('APP_BASE_URL', 'http://localhost:8000')}/payment-result?ok=0",
        "signed_field_names": "total_amount,transaction_uuid,product_code",
    }
    fields["signature"] = _esewa_signature(amount, attempt_id, product_code)
    return {"provider": "esewa", "method": "form_post", "checkout_url": base, "fields": fields,
            "provider_ref": attempt_id}


async def verify(provider: str, attempt, params: dict, *, client=None) -> Verification:
    """Authoritative server-side verification. Browser callbacks are untrusted."""
    owns_client = client is None
    client = client or httpx.AsyncClient(timeout=20.0)
    try:
        if provider == "khalti":
            return await _khalti_verify(client, attempt, params)
        if provider == "esewa":
            return await _esewa_verify(client, attempt, params)
        raise ValueError(f"Unsupported provider: {provider}")
    finally:
        if owns_client:
            await client.aclose()


async def _khalti_verify(client, attempt, params):
    pidx = str(params.get("pidx") or attempt.get("provider_ref") or "")
    if not pidx:
        raise PaymentVerificationFailed("Missing pidx")
    base = _env("KHALTI_BASE_URL", "https://dev.khalti.com/api/v2/").rstrip("/")
    response = await client.get(
        f"{base}/epayment/lookup/",
        headers={"Authorization": f"Key {_env('KHALTI_SECRET_KEY')}"},
        params={"pidx": pidx},
    )
    if response.status_code != 200:
        raise PaymentVerificationFailed("Khalti lookup failed")
    data = response.json()
    if data.get("status") != "Completed" or int(data.get("total_amount", 0)) != attempt["amount_npr"] * 100:
        raise PaymentVerificationFailed("Khalti payment not completed or amount mismatch")
    return Verification("paid", data.get("transaction_id", pidx), attempt["amount_npr"])


async def _esewa_verify(client, attempt, params):
    raw = params.get("data")
    if not raw:
        raise PaymentVerificationFailed("Missing eSewa data")
    try:
        data = json.loads(base64.b64decode(raw).decode())
    except (ValueError, UnicodeDecodeError):
        raise PaymentVerificationFailed("Invalid eSewa callback data")
    if data.get("product_code") != _env("ESEWA_PRODUCT_CODE", "EPAYTEST"):
        raise PaymentVerificationFailed("Product code mismatch")
    if data.get("transaction_uuid") != attempt["id"]:
        raise PaymentVerificationFailed("Transaction mismatch")
    if str(data.get("status", "")).upper() != "COMPLETE":
        raise PaymentVerificationFailed("eSewa payment not complete")
    if abs(float(data.get("total_amount", 0)) - attempt["amount_npr"]) > 0.01:
        raise PaymentVerificationFailed("Amount mismatch")
    status_url = _env("ESEWA_STATUS_URL", "https://rc-epay.esewa.com.np/api/epay/transaction/status/")
    response = await client.get(status_url, params={
        "product_code": data["product_code"], "total_amount": data["total_amount"],
        "transaction_uuid": data["transaction_uuid"],
    })
    if response.status_code != 200:
        raise PaymentVerificationFailed("eSewa status check failed")
    return Verification("paid", data.get("transaction_code", attempt["id"]), attempt["amount_npr"])


def grant_from_attempt(storage, attempt, verification: Verification) -> dict:
    """Idempotently settle an attempt and update the entitlement."""
    event_id = f"{attempt['provider']}:{verification.provider_ref}"
    if not storage.claim_payment_event(event_id, attempt["provider"], "payment_completed", {
        "attempt_id": attempt["id"], "amount_npr": verification.amount_npr,
    }):
        return {"settled": False}
    if not storage.mark_attempt_paid(attempt["id"]):
        return {"settled": False}
    plan = PLANS[attempt["plan_id"]]
    duration = plan.get("duration_days") or 30
    storage.set_entitlement(
        attempt["user_id"], attempt["plan_id"], "active",
        time.time() + duration * 86400, attempt["provider"], verification.provider_ref,
    )
    return {"settled": True, "plan": attempt["plan_id"], "valid_until": time.time() + duration * 86400}


def has_entitlement(entitlement: dict, feature: str) -> bool:
    """Single place for feature gating; free always includes the core lessons."""
    if entitlement.get("plan") == "free":
        return feature in {"lessons", "chat", "flashcards", "exam_style"}
    if entitlement.get("status") != "active":
        return False
    until = entitlement.get("valid_until")
    if until is not None and until < time.time():
        return False
    return True
