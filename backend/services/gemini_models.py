"""
Shared Gemini model selection with graceful fallback.

MedBhasha previously hardcoded `gemini-2.5-flash`, which is no longer
available to new users. Newer flash models also come and go, so we keep
an ordered candidate list and transparently fall back to the next model
when a model is unavailable or overloaded.
"""

from __future__ import annotations

import logging
import os
from typing import Any, List, Optional

from google import genai
from google.genai import errors
from google.genai import types

logger = logging.getLogger("medbhasha.gemini")

DEFAULT_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")
FALLBACK_MODELS = [
    m.strip()
    for m in os.getenv(
        "GEMINI_FALLBACK_MODELS",
        "gemini-3.5-flash-lite,gemini-3.1-flash-lite,gemini-3.5-flash,"
        "gemini-3.6-flash,gemini-3.8-flash,gemini-flash-latest,gemini-2.5-flash",
    ).split(",")
    if m.strip()
]


def model_candidates() -> List[str]:
    """Return an ordered, de-duplicated list of candidate model names."""
    seen: List[str] = []
    for model in [DEFAULT_MODEL, *FALLBACK_MODELS]:
        if model not in seen:
            seen.append(model)
    return seen


def _is_retryable(exc: Exception) -> bool:
    code = getattr(exc, "code", None)
    if code is None:
        code = getattr(exc, "status_code", None)
    if code is None:
        # Some google-genai errors expose status as a string.
        code = getattr(exc, "status", None)
    try:
        code_int = int(code)
    except (TypeError, ValueError):
        code_int = None
    if code_int in {404, 408, 429, 500, 502, 503, 504}:
        return True
    # Network / timeout failures are retryable.
    name = type(exc).__name__.lower()
    return any(token in name for token in ("timeout", "deadline", "connection", "unavailable"))


def generate_content(
    client: genai.Client,
    contents: Any,
    config: Optional[types.GenerateContentConfig] = None,
    *,
    operation: str = "Gemini request",
) -> Any:
    """Try each candidate model in order, returning the first successful response."""
    last_exc: Optional[Exception] = None
    for model in model_candidates():
        try:
            response = client.models.generate_content(
                model=model, contents=contents, config=config
            )
            logger.info("%s succeeded with model=%s", operation, model)
            return response
        except errors.APIError as exc:
            last_exc = exc
            if _is_retryable(exc):
                logger.warning(
                    "%s model=%s failed (%s), trying next model",
                    operation,
                    model,
                    getattr(exc, "code", getattr(exc, "status", exc)),
                )
                continue
            raise
        except Exception as exc:  # noqa: BLE001 - network/timeout fallback
            last_exc = exc
            if _is_retryable(exc):
                logger.warning(
                    "%s model=%s failed (%s), trying next model", operation, model, exc
                )
                continue
            raise
    if last_exc is not None:
        raise last_exc
    raise RuntimeError("No Gemini models configured")
