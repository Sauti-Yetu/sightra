"""Backend tests. No live API keys required."""

from __future__ import annotations

import io

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app.config import get_settings
from app.main import app
from app.providers.currency import CurrencyService, spoken_for_kes
from app.providers.ocr import StaticOCRProvider
from app.providers.speech import ElevenLabsSpeechProvider
from app.schemas.common import AnalysisResult
from app.services.image import preprocess_image
from app.utils.errors import TTS_UNAVAILABLE, UserFacingError
from app.utils.rate_limit import RateLimiter


@pytest.fixture
def client():
    get_settings.cache_clear()
    return TestClient(app)


def jpeg_bytes(size: tuple[int, int] = (64, 64), color: tuple[int, int, int] = (20, 20, 20)) -> bytes:
    image = Image.new("RGB", size, color)
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG")
    return buffer.getvalue()


def test_health(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "nura-api"}


def test_invalid_upload_rejected(client: TestClient) -> None:
    response = client.post(
        "/api/read",
        files={"image": ("note.txt", b"not an image", "text/plain")},
    )
    assert response.status_code == 400
    body = response.json()
    assert body["success"] is False
    assert "Axios" not in body["error"]
    assert "traceback" not in body["error"].lower()


def test_empty_upload_rejected(client: TestClient) -> None:
    response = client.post(
        "/api/analyze",
        files={"image": ("blank.jpg", b"", "image/jpeg")},
    )
    assert response.status_code == 400


def test_ocr_static_provider() -> None:
    provider = StaticOCRProvider(text="KENYATTA AVENUE\n\nNairobi", confidence=0.93)
    result = provider.extract_text(b"unused")
    assert result["text"].startswith("KENYATTA")
    assert len(result["paragraphs"]) == 2
    assert result["confidence"] == 0.93


def test_currency_spoken_standard() -> None:
    assert spoken_for_kes(1000, "standard", True) == "This is a one thousand Kenyan shilling note."
    assert spoken_for_kes(1000, "concise", True) == "One thousand Kenyan shillings."
    assert spoken_for_kes(500, "detailed", True) == "This appears to be a Kenyan five hundred shilling banknote."
    uncertain = spoken_for_kes(500, "standard", False)
    assert "not completely certain" in uncertain


def test_currency_service_from_text() -> None:
    service = CurrencyService()
    result = service.identify_from_analysis(None, 0.8, "standard", "KES 200")
    assert result["denomination"] == 200
    assert result["currency"] == "KES"


def test_tts_missing_api_key() -> None:
    provider = ElevenLabsSpeechProvider(api_key="", voice_id="x", tts_model_id="y")
    with pytest.raises(UserFacingError) as exc:
        provider.synthesize("Hello")
    assert exc.value.message == TTS_UNAVAILABLE
    assert exc.value.status_code == 503


def test_image_preprocess_resizes() -> None:
    data = jpeg_bytes((2400, 1200))
    processed = preprocess_image(data, max_dimension=800)
    image = Image.open(io.BytesIO(processed))
    assert max(image.size) <= 800
    assert image.format == "JPEG"


def test_rate_limiter() -> None:
    limiter = RateLimiter(max_calls=2, window_seconds=60)
    assert limiter.allow("a")
    assert limiter.allow("a")
    assert not limiter.allow("a")
    assert limiter.allow("b")


def test_settings_work_without_secrets(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ELEVENLABS_API_KEY", "")
    monkeypatch.setenv("AI_API_KEY", "")
    get_settings.cache_clear()
    settings = get_settings()
    assert settings.has_elevenlabs is False
    assert settings.has_ai is False


def test_valid_image_without_ai_returns_user_error(client: TestClient) -> None:
    response = client.post(
        "/api/read",
        files={"image": ("page.jpg", jpeg_bytes(), "image/jpeg")},
    )
    assert response.status_code == 503
    body = response.json()
    assert body["success"] is False
    assert "key" in body["error"].lower() or "configured" in body["error"].lower()
    assert "traceback" not in body["error"].lower()


def test_analysis_result_schema() -> None:
    result = AnalysisResult(
        type="document",
        confidence=0.94,
        text="Admission confirmed",
        title="University Admission Letter",
        important_information=["Admission confirmed", "Reporting date: 14 September 2026"],
        summary="This is a university admission letter.",
        spoken="This appears to be a university admission letter.",
    )
    payload = result.model_dump()
    assert payload["title"] == "University Admission Letter"
    assert payload["confidence"] == 0.94


def test_gemini_uses_header_auth() -> None:
    from unittest.mock import MagicMock, patch

    from app.providers.gemini import generate_content

    response = MagicMock()
    response.status_code = 200
    response.is_success = True
    response.json.return_value = {"candidates": [{"content": {"parts": [{"text": "{}"}]}}]}
    with patch("app.providers.gemini.httpx.post", return_value=response) as post:
        generate_content("test-placeholder", "gemini-2.5-flash", {"contents": []})
    url = post.call_args.args[0]
    headers = post.call_args.kwargs["headers"]
    assert "generativelanguage.googleapis.com" in url
    assert "gemini-2.5-flash" in url
    assert "generateContent" in url
    assert "x-goog-api-key" in headers
    assert "params" not in post.call_args.kwargs or "key" not in (post.call_args.kwargs.get("params") or {})


def test_gemini_falls_back_on_missing_model() -> None:
    from unittest.mock import MagicMock, patch

    from app.providers.gemini import generate_content

    missing = MagicMock()
    missing.status_code = 404
    missing.is_success = False
    ok = MagicMock()
    ok.status_code = 200
    ok.is_success = True
    ok.json.return_value = {"candidates": [{"content": {"parts": [{"text": "ok"}]}}]}
    with patch("app.providers.gemini.httpx.post", side_effect=[missing, ok]) as post:
        payload = generate_content("test-placeholder", "not-a-real-model", {"contents": []})
    assert payload["candidates"]
    assert post.call_count == 2
    assert "gemini-3.5-flash" in post.call_args.args[0]
