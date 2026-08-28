"""Short-term scan context. In-memory only — no image persistence."""

from __future__ import annotations

import time
from threading import Lock

from app.schemas.common import AnalysisResult


class MemoryContextProvider:
    def __init__(self, ttl_seconds: int = 1800) -> None:
        self.ttl_seconds = ttl_seconds
        self._lock = Lock()
        self._sessions: dict[str, dict] = {}

    def _expired(self, record: dict) -> bool:
        return time.time() - record["updated_at"] > self.ttl_seconds

    def get(self, session_id: str) -> dict | None:
        with self._lock:
            record = self._sessions.get(session_id)
            if not record:
                return None
            if self._expired(record):
                self._sessions.pop(session_id, None)
                return None
            return {
                "last_scan": record["last_scan"],
                "conversation_history": list(record["conversation_history"]),
            }

    def save_scan(self, session_id: str, result: AnalysisResult) -> None:
        with self._lock:
            self._sessions[session_id] = {
                "last_scan": result.model_dump(),
                "conversation_history": [],
                "updated_at": time.time(),
            }

    def add_turn(self, session_id: str, role: str, content: str) -> None:
        with self._lock:
            record = self._sessions.get(session_id)
            if not record or self._expired(record):
                return
            record["conversation_history"].append({"role": role, "content": content})
            record["conversation_history"] = record["conversation_history"][-12:]
            record["updated_at"] = time.time()

    def clear(self, session_id: str) -> None:
        with self._lock:
            self._sessions.pop(session_id, None)
