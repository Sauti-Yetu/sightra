"""Nura API — visual information accessibility engine."""

from __future__ import annotations

import logging
import os

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import analyze, ask, health, speech
from app.config import get_settings
from app.utils.errors import GENERIC, UserFacingError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("nura")

settings = get_settings()

app = FastAPI(
    title="Nura API",
    description="AI visual screen reader. Hardware-ready REST interface.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(analyze.router, prefix="/api")
app.include_router(ask.router, prefix="/api")
app.include_router(speech.router, prefix="/api")


@app.exception_handler(UserFacingError)
async def user_facing_error_handler(_: Request, exc: UserFacingError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": exc.message,
            "result": None,
            "audio": None,
        },
    )


@app.exception_handler(Exception)
async def unhandled_error_handler(_: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled error: %s", exc)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": GENERIC,
            "result": None,
            "audio": None,
        },
    )


def run() -> None:
    import uvicorn

    port = int(os.environ.get("PORT", "8000"))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=False)


if __name__ == "__main__":
    run()
