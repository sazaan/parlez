"""Tests for Redis-backed rate limiting configuration."""

import sys

sys.path.insert(0, ".")

from main import build_limiter


def test_limiter_uses_redis_when_redis_url_set():
    """When a Redis URL is provided, the limiter storage should be Redis-backed."""
    limiter = build_limiter("redis://localhost:6379/0")
    storage_cls = type(limiter._storage)
    assert "Redis" in storage_cls.__name__ or "redis" in storage_cls.__module__


def test_limiter_uses_memory_by_default():
    """When no Redis URL is provided, the limiter storage should be in-memory."""
    limiter = build_limiter(None)
    storage_cls = type(limiter._storage)
    assert "Memory" in storage_cls.__name__
