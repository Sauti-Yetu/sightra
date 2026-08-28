"""Simple in-memory rate limiter for the MVP."""

from __future__ import annotations

import time
from collections import defaultdict


class RateLimiter:
    def __init__(self, max_calls: int, window_seconds: int = 60) -> None:
        self.max_calls = max_calls
        self.window_seconds = window_seconds
        self._hits: dict[str, list[float]] = defaultdict(list)

    def allow(self, key: str) -> bool:
        now = time.time()
        recent = [stamp for stamp in self._hits[key] if now - stamp < self.window_seconds]
        if len(recent) >= self.max_calls:
            self._hits[key] = recent
            return False
        recent.append(now)
        self._hits[key] = recent
        return True
