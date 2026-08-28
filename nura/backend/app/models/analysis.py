"""Domain shapes used by the visual engine.

API serialization lives in app.schemas; this module is the stable import path
for future hardware clients and provider implementations.
"""

from app.schemas.common import AnalysisResult, CurrencyResult, DocumentFields

__all__ = ["AnalysisResult", "CurrencyResult", "DocumentFields"]
