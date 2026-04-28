"""
HealthVault AI — Gemini Model Selector

Dynamically picks the best available Gemini model that supports
`generateContent` for the configured API key. Avoids hardcoding model names
which Google retires periodically (e.g. gemini-1.5-* → gone for new keys).

Usage:
    from ai.gemini_models import get_gemini_model_name
    model_name = get_gemini_model_name()  # cached after first call
"""
from __future__ import annotations

from typing import Optional

import structlog

from config import settings

log = structlog.get_logger(__name__)

# Preferred order — newer/faster first. The selector returns the first one
# from this list that the configured API key has access to. If none match,
# it falls back to whatever the API lists.
_PREFERENCE_ORDER = [
    "gemini-2.5-flash",
    "gemini-flash-latest",
    "gemini-2.0-flash-001",
    "gemini-2.5-pro",
    "gemini-pro-latest",
    "gemini-2.0-flash-lite-001",
]

# Module-level cache so we only call list_models() once per process.
_cached_model: Optional[str] = None


def _strip_prefix(name: str) -> str:
    """Normalize 'models/gemini-2.5-flash' → 'gemini-2.5-flash'."""
    return name.split("/", 1)[1] if name.startswith("models/") else name


def get_gemini_model_name(force_refresh: bool = False) -> str:
    """
    Return a model name string to pass to `genai.GenerativeModel(...)`.
    Cached after first call. Set `force_refresh=True` to re-query.
    """
    global _cached_model
    if _cached_model and not force_refresh:
        return _cached_model

    if not settings.GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY is not configured.")

    try:
        import google.generativeai as genai
        genai.configure(api_key=settings.GEMINI_API_KEY)

        available = []
        for m in genai.list_models():
            if "generateContent" in (m.supported_generation_methods or []):
                available.append(_strip_prefix(m.name))

        if not available:
            raise RuntimeError("No Gemini models with generateContent support are available for this API key.")

        # Prefer in our chosen order
        for preferred in _PREFERENCE_ORDER:
            if preferred in available:
                _cached_model = preferred
                log.info("gemini.model_selected", model=preferred, source="preferred")
                return preferred

        # Fallback: pick any non-preview, non-tts flash-class model
        flash_like = [n for n in available if "flash" in n and "preview" not in n and "tts" not in n]
        if flash_like:
            _cached_model = flash_like[0]
            log.info("gemini.model_selected", model=_cached_model, source="flash_fallback")
            return _cached_model

        # Last resort — first available
        _cached_model = available[0]
        log.info("gemini.model_selected", model=_cached_model, source="first_available")
        return _cached_model

    except Exception as exc:
        log.error("gemini.model_selection_failed", error=str(exc))
        # Hard fallback to a recent name; if this is also unavailable,
        # the actual generate_content call will surface the error.
        _cached_model = "gemini-2.5-flash"
        return _cached_model
