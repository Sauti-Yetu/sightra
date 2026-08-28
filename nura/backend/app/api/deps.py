"""Shared FastAPI dependencies."""

from __future__ import annotations

from functools import lru_cache
from uuid import uuid4

from fastapi import Depends, Header, Request

from app.config import Settings, get_settings
from app.services.pipeline import VisualPipeline
from app.utils.errors import RATE_LIMITED, UserFacingError
from app.utils.rate_limit import RateLimiter


@lru_cache
def get_pipeline() -> VisualPipeline:
    return VisualPipeline(get_settings())


@lru_cache
def get_limiter() -> RateLimiter:
    return RateLimiter(max_calls=get_settings().rate_limit_per_minute)


def require_rate_limit(
    request: Request,
    limiter: RateLimiter = Depends(get_limiter),
) -> None:
    client = request.client.host if request.client else "unknown"
    if not limiter.allow(client):
        raise UserFacingError(RATE_LIMITED, status_code=429)


def session_id(
    x_nura_session: str | None = Header(default=None, alias="X-Nura-Session"),
) -> str:
    value = (x_nura_session or "").strip()
    return value or str(uuid4())
