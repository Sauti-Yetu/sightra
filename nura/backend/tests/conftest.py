"""Isolate tests from local .env secrets so live keys are never used or leaked."""

from __future__ import annotations

import pytest

from app.api.deps import get_limiter, get_pipeline
from app.config import get_settings


@pytest.fixture(autouse=True)
def isolate_secrets(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("AI_API_KEY", "")
    monkeypatch.setenv("ELEVENLABS_API_KEY", "")
    get_settings.cache_clear()
    get_pipeline.cache_clear()
    get_limiter.cache_clear()
    yield
    get_settings.cache_clear()
    get_pipeline.cache_clear()
    get_limiter.cache_clear()


def pytest_sessionfinish() -> None:
    get_settings.cache_clear()
    get_pipeline.cache_clear()
    get_limiter.cache_clear()
