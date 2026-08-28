from app.api.deps import get_pipeline
from app.config import get_settings


def pytest_sessionfinish() -> None:
    get_settings.cache_clear()
    get_pipeline.cache_clear()
