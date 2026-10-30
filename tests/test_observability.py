"""Structured logs, correlation IDs, Prometheus access, SLOs, alerts, and traces."""

import logging
import re

import main
from fastapi.testclient import TestClient
from observability import OBSERVABILITY, get_tracer, log_event


def test_request_correlation_id_is_validated_and_returned(client):
    OBSERVABILITY.reset_recent()
    response = client.get("/health", headers={"X-Correlation-ID": "0123456789abcdef0123456789abcdef"})

    assert response.status_code == 200
    assert response.headers["x-request-id"] == "0123456789abcdef0123456789abcdef"
    assert response.headers["x-correlation-id"] == "0123456789abcdef0123456789abcdef"
    assert re.fullmatch(r"[0-9a-f]{32}", response.headers["x-trace-id"])
    event = next(item for item in OBSERVABILITY.snapshot()["events"] if item["event"] == "http.request.completed")
    assert event["correlation_id"] == "0123456789abcdef0123456789abcdef"
    assert event["trace_id"] == response.headers["x-trace-id"]


def test_invalid_correlation_id_is_replaced(client):
    response = client.get("/health", headers={"X-Correlation-ID": "not valid/contains spaces"})

    assert response.status_code == 200
    assert response.headers["x-request-id"] != "not valid/contains spaces"
    assert re.fullmatch(r"[0-9a-f]{32}", response.headers["x-request-id"])


def test_internal_error_responses_keep_correlation_and_redact_exception_text(monkeypatch, capfd):
    private_message = "PRIVATE_EXCEPTION_TEXT_MUST_NOT_BE_LOGGED"

    def fail_health_record(healthy, duration_seconds):
        raise RuntimeError(private_message)

    monkeypatch.setattr(main, "record_database_health", fail_health_record)
    error_client = TestClient(main.app, raise_server_exceptions=False)
    response = error_client.get("/health", headers={"X-Correlation-ID": "abcdef0123456789abcdef0123456789"})

    assert response.status_code == 500
    assert response.headers["x-request-id"] == "abcdef0123456789abcdef0123456789"
    assert response.headers["x-correlation-id"] == "abcdef0123456789abcdef0123456789"
    assert re.fullmatch(r"[0-9a-f]{32}", response.headers["x-trace-id"])
    assert private_message not in response.text
    assert private_message not in capfd.readouterr().err


def test_prometheus_endpoint_is_disabled_and_requires_a_strong_bearer_token(client, monkeypatch):
    monkeypatch.setattr(main, "METRICS_ENABLED", False)
    assert client.get("/metrics").status_code == 404

    monkeypatch.setattr(main, "METRICS_ENABLED", True)
    monkeypatch.setattr(main, "METRICS_TOKEN", "s" * 40)
    assert client.get("/metrics").status_code == 401
    response = client.get("/metrics", headers={"Authorization": f"Bearer {'s' * 40}"})
    assert response.status_code == 200
    assert "parlez_http_requests_total" in response.text
    assert "parlez_ai_provider_calls_total" in response.text
    assert "s" * 40 not in response.text


def test_observability_redacts_sensitive_log_fields():
    OBSERVABILITY.reset_recent()
    log_event(
        "test.redaction",
        action="probe",
        password="never-record-this",
        prompt="learner private text",
        email="learner@example.com",
    )

    event = OBSERVABILITY.snapshot()["events"][0]
    assert event["fields"] == {"action": "probe"}
    assert "password" not in repr(event)
    assert "learner private text" not in repr(event)
    assert "learner@example.com" not in repr(event)


def test_dependency_logs_that_may_include_payloads_are_not_verbose():
    for name in ("httpx", "httpcore", "sqlalchemy.engine", "uvicorn.access"):
        assert logging.getLogger(name).getEffectiveLevel() >= logging.WARNING


def test_slo_snapshot_computes_alerts_and_keeps_trace_spans_local():
    OBSERVABILITY.reset_recent()
    for _ in range(20):
        OBSERVABILITY.record_request(
            method="GET",
            route="/api/progress",
            status_code=500,
            duration_seconds=0.2,
            service_class="core",
            request_id=None,
            correlation_id=None,
            trace_id=None,
        )
    with get_tracer().start_as_current_span("observability.test.child"):
        pass

    snapshot = OBSERVABILITY.snapshot()
    assert snapshot["metrics"]["core_requests_24h"] == 20
    availability = next(item for item in snapshot["slos"] if item["id"] == "core_api_availability")
    assert availability["state"] == "breached"
    assert any(item["id"] == "http_5xx_rate" for item in snapshot["alerts"])
    assert any(item["name"] == "observability.test.child" for item in snapshot["traces"])
    assert "process-local" in snapshot["retention"]["scope"]
