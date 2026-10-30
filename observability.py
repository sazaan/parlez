"""Structured logging, request correlation, local telemetry, and OpenTelemetry traces.

The admin dashboard keeps bounded, process-local samples for immediate diagnosis.
For durable, multi-instance monitoring, ship the JSON stdout logs, scrape the
Prometheus endpoint, and configure an OTLP collector.
"""
from __future__ import annotations

import json
import logging
import math
import os
import re
import threading
import time
import traceback
from collections import deque
from contextvars import ContextVar
from datetime import datetime, timezone
from typing import Any

from opentelemetry import propagate, trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import ReadableSpan, SpanProcessor, TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.trace.sampling import ParentBased, TraceIdRatioBased
from opentelemetry.trace import StatusCode
from prometheus_client import CONTENT_TYPE_LATEST, CollectorRegistry, Counter, Gauge, Histogram, generate_latest


SERVICE_NAME = os.getenv("OTEL_SERVICE_NAME", "parlez")[:100]
REQUEST_ID_RE = re.compile(r"^(?:[0-9a-fA-F]{32}|[0-9a-fA-F]{8}-(?:[0-9a-fA-F]{4}-){3}[0-9a-fA-F]{12})$")
METRICS_REGISTRY = CollectorRegistry(auto_describe=True)

HTTP_REQUESTS = Counter(
    "parlez_http_requests_total",
    "Completed HTTP requests, grouped by low-cardinality route and service class.",
    ("method", "route", "status_code", "service_class"),
    registry=METRICS_REGISTRY,
)
HTTP_REQUEST_DURATION = Histogram(
    "parlez_http_request_duration_seconds",
    "HTTP request duration in seconds.",
    ("method", "route", "service_class"),
    buckets=(0.05, 0.1, 0.25, 0.5, 1, 2, 5, 10, 20, 30, 60),
    registry=METRICS_REGISTRY,
)
AI_PROVIDER_CALLS = Counter(
    "parlez_ai_provider_calls_total",
    "AI provider calls by provider, operation, and result.",
    ("provider", "operation", "outcome"),
    registry=METRICS_REGISTRY,
)
AI_PROVIDER_DURATION = Histogram(
    "parlez_ai_provider_call_duration_seconds",
    "AI provider call duration in seconds, including retries.",
    ("provider", "operation", "outcome"),
    buckets=(0.1, 0.25, 0.5, 1, 2, 5, 10, 20, 30, 45, 60, 90),
    registry=METRICS_REGISTRY,
)
AI_TOKENS = Counter(
    "parlez_ai_tokens_total",
    "Provider-reported AI tokens, when the provider returns usage metadata.",
    ("provider", "direction"),
    registry=METRICS_REGISTRY,
)
AUTH_EVENTS = Counter(
    "parlez_auth_events_total",
    "Authentication and authorization events; no account identifiers are labels.",
    ("action", "outcome"),
    registry=METRICS_REGISTRY,
)
OPERATIONAL_EVENTS = Counter(
    "parlez_operational_events_total",
    "Allowlisted operational event counts by event name and severity.",
    ("event", "severity"),
    registry=METRICS_REGISTRY,
)
DATABASE_HEALTH = Gauge(
    "parlez_database_health",
    "Whether the most recent database health probe succeeded (1) or failed (0).",
    registry=METRICS_REGISTRY,
)
DATABASE_LAST_CHECK = Gauge(
    "parlez_database_last_check_timestamp_seconds",
    "Unix time of the most recent database health probe.",
    registry=METRICS_REGISTRY,
)
PROCESS_START_TIME = Gauge(
    "parlez_process_start_time_seconds",
    "Unix time when this Parlez worker initialized observability.",
    registry=METRICS_REGISTRY,
)
PROCESS_START_TIME.set(time.time())


_request_context: ContextVar[dict[str, str]] = ContextVar("parlez_request_context", default={})

# Keep log attributes explicit and small. Never include request bodies, prompts,
# auth material, email addresses, usernames, or learner/admin identity.
SAFE_LOG_FIELDS = {
    "route", "method", "status_code", "duration_ms", "slo_class", "provider",
    "model", "operation", "outcome", "attempt", "attempts", "error_type",
    "http_status", "mfa_enabled", "enabled", "alert_name", "reason_code",
    "count", "threshold", "latency_ms", "result", "database", "level",
    "sample_size", "error_rate", "p95_ms", "window_seconds", "input_tokens",
    "output_tokens", "token_count", "user_count", "limit", "offset",
    "review_status", "enabled_level_count", "actor_type", "action", "learner_level",
}
SAFE_SPAN_ATTRIBUTES = {
    "http.request.method", "http.route", "http.response.status_code",
    "parlez.slo_class", "parlez.provider", "parlez.model", "parlez.operation",
    "parlez.outcome", "parlez.attempt", "parlez.error_type",
    "parlez.request_id", "parlez.correlation_id",
}


def _current_trace_fields() -> dict[str, str]:
    fields = dict(_request_context.get())
    span_context = trace.get_current_span().get_span_context()
    if span_context and span_context.is_valid:
        fields["trace_id"] = f"{span_context.trace_id:032x}"
        fields["span_id"] = f"{span_context.span_id:016x}"
    return fields


def _safe_value(value: Any) -> str | int | float | bool | None:
    if isinstance(value, bool) or value is None:
        return value
    if isinstance(value, int):
        return value if abs(value) <= 2**53 else None
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    if isinstance(value, str):
        cleaned = "".join(ch for ch in value if ch >= " " and ch != "\x7f")
        return cleaned[:160]
    return None


def _safe_fields(fields: dict[str, Any]) -> dict[str, str | int | float | bool]:
    result: dict[str, str | int | float | bool] = {}
    for key, value in fields.items():
        if key not in SAFE_LOG_FIELDS:
            continue
        safe = _safe_value(value)
        if safe is not None:
            result[key] = safe
    return result


class JsonLogFormatter(logging.Formatter):
    """Emit one compact JSON object per log line for container log collectors."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z"),
            "severity": record.levelname.lower(),
            "logger": record.name[:100],
            "message": record.getMessage()[:500],
        }
        event = getattr(record, "event_name", None)
        if isinstance(event, str):
            payload["event"] = event[:80]
        payload.update(_current_trace_fields())
        payload.update(_safe_fields(getattr(record, "event_fields", {}) or {}))
        if record.exc_info:
            exc_type = record.exc_info[0]
            payload["error_type"] = getattr(exc_type, "__name__", "Exception")[:80]
            # Frame summaries aid diagnosis without source lines, exception text,
            # or request/provider response data.
            frames = traceback.extract_tb(record.exc_info[2])
            payload["stacktrace"] = "".join(
                f"{os.path.basename(frame.filename)}:{frame.lineno} in {frame.name}\n"
                for frame in frames
            )[-6000:]
        return json.dumps(payload, ensure_ascii=False, separators=(",", ":"), default=str)


def configure_json_logging(level: str | None = None) -> None:
    root = logging.getLogger()
    handler = logging.StreamHandler()
    handler.setFormatter(JsonLogFormatter())
    root.handlers[:] = [handler]
    root.setLevel(getattr(logging, (level or os.getenv("LOG_LEVEL", "INFO")).upper(), logging.INFO))
    # Dependency DEBUG/INFO logs can include full URLs, SQL parameters, or
    # request payload details. Our own safe operational events replace them.
    for logger_name in ("httpx", "httpcore", "sqlalchemy.engine", "uvicorn.access"):
        logging.getLogger(logger_name).setLevel(logging.WARNING)


class Observability:
    """Thread-safe, bounded in-process event, request, AI, and trace samples."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self.started_at = time.time()
        self._events: deque[dict[str, Any]] = deque(maxlen=500)
        self._requests: deque[dict[str, Any]] = deque(maxlen=10_000)
        self._ai_calls: deque[dict[str, Any]] = deque(maxlen=5_000)
        self._spans: deque[dict[str, Any]] = deque(maxlen=2_000)
        self._alert_states: dict[str, dict[str, Any]] = {}

    def _event_record(self, event: str, severity: str, fields: dict[str, Any]) -> dict[str, Any]:
        context_fields = _current_trace_fields()
        return {
            "timestamp": time.time(),
            "event": event,
            "severity": severity,
            "request_id": context_fields.get("request_id"),
            "correlation_id": context_fields.get("correlation_id"),
            "trace_id": context_fields.get("trace_id"),
            "span_id": context_fields.get("span_id"),
            "fields": _safe_fields(fields),
        }

    def record_event(self, event: str, severity: str, fields: dict[str, Any]) -> None:
        with self._lock:
            self._events.append(self._event_record(event, severity, fields))

    def record_request(
        self,
        *,
        method: str,
        route: str,
        status_code: int,
        duration_seconds: float,
        service_class: str,
        request_id: str | None,
        correlation_id: str | None,
        trace_id: str | None,
    ) -> None:
        method = _metric_label(method.upper(), 12)
        route = _metric_label(route, 100)
        service_class = _metric_label(service_class, 16)
        status = str(status_code) if 100 <= status_code <= 599 else "500"
        duration_seconds = max(0.0, min(float(duration_seconds), 600.0))
        HTTP_REQUESTS.labels(method, route, status, service_class).inc()
        HTTP_REQUEST_DURATION.labels(method, route, service_class).observe(duration_seconds)
        if service_class in {"core", "ai"}:
            with self._lock:
                self._requests.append({
                    "timestamp": time.time(),
                    "method": method,
                    "route": route,
                    "status_code": int(status),
                    "duration_seconds": duration_seconds,
                    "service_class": service_class,
                    "request_id": request_id,
                    "correlation_id": correlation_id,
                    "trace_id": trace_id,
                })

    def record_ai_call(
        self,
        *,
        provider: str,
        operation: str,
        outcome: str,
        duration_seconds: float,
        input_tokens: int | None = None,
        output_tokens: int | None = None,
    ) -> None:
        provider = _metric_label(provider, 40)
        operation = _metric_label(operation, 40)
        outcome = "success" if outcome == "success" else "failure"
        duration_seconds = max(0.0, min(float(duration_seconds), 600.0))
        AI_PROVIDER_CALLS.labels(provider, operation, outcome).inc()
        AI_PROVIDER_DURATION.labels(provider, operation, outcome).observe(duration_seconds)
        token_count = 0
        if isinstance(input_tokens, int) and 0 < input_tokens < 2**31:
            AI_TOKENS.labels(provider, "input").inc(input_tokens)
            token_count += input_tokens
        if isinstance(output_tokens, int) and 0 < output_tokens < 2**31:
            AI_TOKENS.labels(provider, "output").inc(output_tokens)
            token_count += output_tokens
        context_fields = _current_trace_fields()
        with self._lock:
            self._ai_calls.append({
                "timestamp": time.time(),
                "provider": provider,
                "operation": operation,
                "outcome": outcome,
                "duration_seconds": duration_seconds,
                "token_count": token_count,
                "trace_id": context_fields.get("trace_id"),
                "request_id": context_fields.get("request_id"),
            })

    def record_trace_span(self, span: dict[str, Any]) -> None:
        with self._lock:
            self._spans.append(span)

    def record_database_health(self, healthy: bool, duration_seconds: float) -> None:
        DATABASE_HEALTH.set(1 if healthy else 0)
        DATABASE_LAST_CHECK.set(time.time())
        log_event(
            "dependency.database.health_check",
            logging.INFO if healthy else logging.ERROR,
            outcome="success" if healthy else "failure",
            duration_ms=round(max(0.0, duration_seconds) * 1000, 2),
        )

    def reset_recent(self) -> None:
        """Clear bounded samples for tests; Prometheus counters remain monotonic."""
        with self._lock:
            self._events.clear()
            self._requests.clear()
            self._ai_calls.clear()
            self._spans.clear()
            self._alert_states.clear()

    def snapshot(self) -> dict[str, Any]:
        now = time.time()
        with self._lock:
            requests = list(self._requests)
            ai_calls = list(self._ai_calls)
            events = list(self._events)
            spans = list(self._spans)

        def within(items: list[dict[str, Any]], seconds: int) -> list[dict[str, Any]]:
            return [item for item in items if now - item.get("timestamp", 0) <= seconds]

        core_24h = [item for item in within(requests, 86_400) if item["service_class"] == "core"]
        core_1h = [item for item in within(requests, 3_600) if item["service_class"] == "core"]
        core_5m = [item for item in within(requests, 300) if item["service_class"] == "core"]
        ai_24h = [item for item in within(ai_calls, 86_400) if item["operation"] != "provider_test"]
        ai_1h = [item for item in within(ai_calls, 3_600) if item["operation"] != "provider_test"]
        ai_5m = [item for item in within(ai_calls, 300) if item["operation"] != "provider_test"]

        core_good = [item for item in core_24h if item["status_code"] < 500]
        core_availability = len(core_good) / len(core_24h) if core_24h else None
        core_p95 = _percentile([item["duration_seconds"] for item in core_1h], 0.95)
        ai_good = [item for item in ai_24h if item["outcome"] == "success"]
        ai_availability = len(ai_good) / len(ai_24h) if ai_24h else None
        ai_p95 = _percentile([item["duration_seconds"] for item in ai_1h], 0.95)

        slos = [
            _slo("core_api_availability", "Core API availability", core_availability, ">= 99.5%", 0.995, len(core_24h), 20, "ratio"),
            _slo("core_api_latency", "Core API p95 latency", core_p95, "p95 ≤ 2.0 s", 2.0, len(core_1h), 20, "max"),
            _slo("ai_provider_availability", "AI provider success", ai_availability, ">= 99.0%", 0.99, len(ai_24h), 5, "ratio"),
            _slo("ai_provider_latency", "AI provider p95 latency", ai_p95, "p95 ≤ 30 s", 30.0, len(ai_1h), 5, "max"),
        ]

        recent_5m_events = within(events, 300)
        server_errors = sum(1 for item in core_5m if item["status_code"] >= 500)
        server_error_rate = server_errors / len(core_5m) if core_5m else None
        core_5m_p95 = _percentile([item["duration_seconds"] for item in core_5m], 0.95)
        ai_failures = sum(1 for item in ai_5m if item["outcome"] == "failure")
        ai_failure_rate = ai_failures / len(ai_5m) if ai_5m else None
        auth_failures = sum(
            1 for item in recent_5m_events
            if item["event"] in {"auth.login.failure", "auth.admin_login.failure", "auth.admin_session.failure"}
        )
        db_probes = [item for item in recent_5m_events if item["event"] == "dependency.database.health_check"]
        database_down = bool(db_probes and db_probes[-1]["fields"].get("outcome") == "failure")

        alerts = []
        if len(core_5m) >= 20 and server_error_rate is not None and server_error_rate > 0.01:
            alerts.append(_alert("http_5xx_rate", "Elevated server error rate", "critical", f"{server_error_rate:.1%} of core API requests returned a server error in the last 5 minutes.", len(core_5m)))
        if len(core_5m) >= 20 and core_5m_p95 is not None and core_5m_p95 > 2.0:
            alerts.append(_alert("core_api_latency", "Core API latency is above SLO", "warning", f"Core API p95 latency is {core_5m_p95:.2f} seconds over the last 5 minutes.", len(core_5m)))
        if len(ai_5m) >= 5 and ai_failure_rate is not None and ai_failure_rate > 0.10:
            alerts.append(_alert("ai_provider_failures", "AI provider failures increased", "critical", f"{ai_failure_rate:.1%} of AI provider calls failed in the last 5 minutes.", len(ai_5m)))
        if auth_failures >= 10:
            alerts.append(_alert("auth_failure_burst", "Authentication failure burst", "warning", f"{auth_failures} authentication failures were recorded in the last 5 minutes.", auth_failures))
        if database_down:
            alerts.append(_alert("database_unavailable", "Database health check failed", "critical", "The most recent database health check in the last 5 minutes failed.", len(db_probes)))

        alerts = self._update_alert_states(alerts, now)
        with self._lock:
            events = list(self._events)
            spans = list(self._spans)
        event_payload = [_public_event(item) for item in reversed(events[-100:])]
        span_payload = [_public_span(item) for item in sorted(spans, key=lambda item: item.get("start_time", 0), reverse=True)[:100]]
        return {
            "generated_at": now,
            "service": SERVICE_NAME,
            "process_uptime_seconds": round(max(0.0, now - self.started_at), 2),
            "retention": {
                "scope": "process-local; samples reset on restart and are not shared across workers",
                "events": 500,
                "request_samples": 10_000,
                "provider_samples": 5_000,
                "trace_spans": 2_000,
                "otlp_export_configured": bool(os.getenv("OTEL_EXPORTER_OTLP_TRACES_ENDPOINT") or os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")),
                "prometheus_scrape_enabled": os.getenv("METRICS_ENABLED", "false").lower() in {"1", "true", "yes"},
            },
            "metrics": {
                "core_requests_24h": len(core_24h),
                "core_5xx_rate_5m": server_error_rate,
                "core_p95_ms_1h": round(core_p95 * 1000, 2) if core_p95 is not None else None,
                "ai_calls_24h": len(ai_24h),
                "ai_failures_5m": ai_failures,
                "ai_failure_rate_5m": ai_failure_rate,
                "ai_p95_ms_1h": round(ai_p95 * 1000, 2) if ai_p95 is not None else None,
            },
            "slos": slos,
            "alerts": alerts,
            "events": event_payload,
            "traces": span_payload,
        }

    def _update_alert_states(self, alerts: list[dict[str, Any]], now: float) -> list[dict[str, Any]]:
        active = {alert["id"]: alert for alert in alerts}
        transitions: list[tuple[str, dict[str, Any]]] = []
        with self._lock:
            for alert_id, alert in active.items():
                previous = self._alert_states.get(alert_id)
                since = previous.get("since", now) if previous else now
                alert["since"] = since
                alert["state"] = "firing"
                if not previous or not previous.get("active"):
                    self._alert_states[alert_id] = {"active": True, "since": since}
                    transitions.append(("alert.fired", alert))
            for alert_id, previous in list(self._alert_states.items()):
                if previous.get("active") and alert_id not in active:
                    self._alert_states[alert_id] = {"active": False, "since": previous.get("since"), "resolved_at": now}
                    transitions.append(("alert.resolved", {"id": alert_id, "severity": "info", "since": previous.get("since")}))
        for event, alert in transitions:
            log_event(
                event,
                logging.WARNING if event == "alert.fired" else logging.INFO,
                alert_name=alert.get("id", "unknown"),
                reason_code=alert.get("severity", "info"),
                sample_size=alert.get("sample_size", 0),
            )
        return list(active.values())


class AdminTraceProcessor(SpanProcessor):
    """Retain safe span summaries for the admin panel while the SDK exports OTLP."""

    def on_start(self, span: Any, parent_context: Any = None) -> None:
        return None

    def on_end(self, span: ReadableSpan) -> None:
        span_context = span.context
        if not span_context or not span_context.is_valid:
            return
        attributes: dict[str, Any] = {}
        for key, value in (span.attributes or {}).items():
            if key in SAFE_SPAN_ATTRIBUTES and isinstance(value, (str, int, float, bool)):
                safe = _safe_value(value)
                if safe is not None:
                    attributes[key] = safe
        parent_span_id = None
        if span.parent and span.parent.is_valid:
            parent_span_id = f"{span.parent.span_id:016x}"
        OBSERVABILITY.record_trace_span({
            "trace_id": f"{span_context.trace_id:032x}",
            "span_id": f"{span_context.span_id:016x}",
            "parent_span_id": parent_span_id,
            "name": str(span.name)[:100],
            "kind": getattr(span.kind, "name", "INTERNAL").lower(),
            "start_time": (span.start_time or 0) / 1_000_000_000,
            "duration_ms": max(0.0, ((span.end_time or span.start_time or 0) - (span.start_time or 0)) / 1_000_000),
            "status": "error" if span.status.status_code == StatusCode.ERROR else "ok",
            "attributes": attributes,
        })

    def shutdown(self) -> None:
        return None

    def force_flush(self, timeout_millis: int = 30_000) -> bool:
        return True


OBSERVABILITY = Observability()
_TRACER_PROVIDER: TracerProvider | None = None


def initialize_tracing() -> Any:
    global _TRACER_PROVIDER
    if _TRACER_PROVIDER is not None:
        return trace.get_tracer("parlez")
    ratio_text = os.getenv("OTEL_TRACE_SAMPLE_RATIO", "1.0")
    try:
        sample_ratio = min(1.0, max(0.0, float(ratio_text)))
    except ValueError:
        sample_ratio = 1.0
    provider = TracerProvider(
        resource=Resource.create({"service.name": SERVICE_NAME}),
        sampler=ParentBased(TraceIdRatioBased(sample_ratio)),
    )
    provider.add_span_processor(AdminTraceProcessor())
    endpoint = os.getenv("OTEL_EXPORTER_OTLP_TRACES_ENDPOINT") or os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
    if endpoint:
        try:
            provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=endpoint)))
        except Exception as exc:  # Collector setup must never prevent Parlez from starting.
            logging.getLogger("parlez.observability").warning(
                "OTLP trace exporter could not be initialized: %s", type(exc).__name__
            )
    trace.set_tracer_provider(provider)
    propagate.set_global_textmap(TraceContextTextMapPropagator())
    _TRACER_PROVIDER = provider
    return trace.get_tracer("parlez")


def shutdown_tracing() -> None:
    if _TRACER_PROVIDER is not None:
        try:
            _TRACER_PROVIDER.force_flush(timeout_millis=2_000)
            _TRACER_PROVIDER.shutdown()
        except Exception as exc:
            logging.getLogger("parlez.observability").warning(
                "Tracing shutdown encountered an error: %s", type(exc).__name__
            )


def set_request_context(request_id: str, correlation_id: str) -> Any:
    return _request_context.set({"request_id": request_id, "correlation_id": correlation_id})


def reset_request_context(token: Any) -> None:
    _request_context.reset(token)


def valid_correlation_id(value: str | None) -> bool:
    return bool(value and REQUEST_ID_RE.fullmatch(value))


def route_service_class(route: str) -> str:
    if route == "/metrics":
        return "telemetry"
    if route == "/health":
        return "health"
    if route.startswith("/api/admin"):
        return "admin"
    if route in {"/api/chat", "/api/writing/correct", "/api/tts"}:
        return "ai"
    if route.startswith("/api/"):
        return "core"
    if route.startswith("/static/"):
        return "static"
    return "web"


def safe_route(scope: dict[str, Any]) -> str:
    route = scope.get("route")
    template = getattr(route, "path", None)
    if isinstance(template, str) and template.startswith("/") and len(template) <= 100:
        return template
    path = str(scope.get("path", "/"))
    if path == "/":
        return "/"
    if path.startswith("/static/"):
        return "/static/{asset}"
    if path.startswith("/api/admin"):
        return "/api/admin/{unmatched}"
    if path.startswith("/api/"):
        return "/api/{unmatched}"
    return "/unmatched"


def log_event(event: str, level: int = logging.INFO, **fields: Any) -> None:
    event = event if re.fullmatch(r"[a-zA-Z0-9_.-]{1,80}", event or "") else "application.event"
    safe = _safe_fields(fields)
    severity = logging.getLevelName(level).lower()
    OPERATIONAL_EVENTS.labels(event, severity).inc()
    if event.startswith("auth."):
        parts = event.split(".")
        action = parts[1] if len(parts) > 1 else "other"
        outcome = "failure" if "failure" in event or safe.get("outcome") == "failure" else "success"
        AUTH_EVENTS.labels(_metric_label(action, 40), outcome).inc()
    OBSERVABILITY.record_event(event, severity, safe)
    logging.getLogger("parlez").log(
        level,
        event,
        extra={"event_name": event, "event_fields": safe},
    )


def observe_http_request(**kwargs: Any) -> None:
    OBSERVABILITY.record_request(**kwargs)


def observe_ai_call(**kwargs: Any) -> None:
    OBSERVABILITY.record_ai_call(**kwargs)


def record_database_health(healthy: bool, duration_seconds: float) -> None:
    OBSERVABILITY.record_database_health(healthy, duration_seconds)


def metrics_bytes() -> bytes:
    return generate_latest(METRICS_REGISTRY)


def metrics_content_type() -> str:
    return CONTENT_TYPE_LATEST


def get_tracer() -> Any:
    return trace.get_tracer("parlez")


def _metric_label(value: str, maximum: int) -> str:
    value = re.sub(r"[^A-Za-z0-9_./{}:-]+", "_", str(value))
    return value[:maximum] or "unknown"


def _percentile(values: list[float], percentile: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = max(0, min(len(ordered) - 1, math.ceil(percentile * len(ordered)) - 1))
    return ordered[index]


def _slo(
    slo_id: str,
    name: str,
    value: float | None,
    target: str,
    threshold: float,
    sample_size: int,
    minimum_samples: int,
    comparison: str,
) -> dict[str, Any]:
    if sample_size < minimum_samples or value is None:
        state = "insufficient_data"
        display_value: float | None = None
    else:
        breached = value < threshold if comparison == "ratio" else value > threshold
        state = "breached" if breached else "met"
        display_value = round(value * 100, 3) if comparison == "ratio" else round(value * 1000, 2)
    unit = "percent" if comparison == "ratio" else "milliseconds"
    return {
        "id": slo_id,
        "name": name,
        "target": target,
        "value": display_value,
        "unit": unit,
        "sample_size": sample_size,
        "minimum_samples": minimum_samples,
        "state": state,
    }


def _alert(alert_id: str, title: str, severity: str, summary: str, sample_size: int) -> dict[str, Any]:
    return {
        "id": alert_id,
        "title": title,
        "severity": severity,
        "summary": summary[:240],
        "sample_size": sample_size,
        "state": "firing",
    }


def _public_event(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "timestamp": item.get("timestamp"),
        "event": item.get("event"),
        "severity": item.get("severity"),
        "request_id": item.get("request_id"),
        "correlation_id": item.get("correlation_id"),
        "trace_id": item.get("trace_id"),
        "fields": item.get("fields", {}),
    }


def _public_span(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "trace_id": item.get("trace_id"),
        "span_id": item.get("span_id"),
        "parent_span_id": item.get("parent_span_id"),
        "name": item.get("name"),
        "kind": item.get("kind"),
        "start_time": item.get("start_time"),
        "duration_ms": item.get("duration_ms"),
        "status": item.get("status"),
        "attributes": item.get("attributes", {}),
    }
