"""Shared parser for LLM confidence vectors.

Several encodings record the LLM's confidence as a JSON object that maps
a name (a hypothesis or a concept) to a number. They all parse it the
same way, so the parser lives here once instead of being copied per
encoding.

Example: ``'{"flu": 0.7, "cold": 0.3}'`` parses to
``{"flu": 0.7, "cold": 0.3}``.
"""

from __future__ import annotations

import json
import math


def parse_confidence_vector(text: str) -> dict[str, float]:
    """Parse a JSON object mapping name -> confidence.

    Keeps only string keys whose value is a finite number. Anything else
    is skipped: a non-finite value (``Infinity`` or ``NaN``, both of
    which ``json.loads`` accepts) would poison a later renormalize, so it
    is dropped here at the trust boundary rather than allowed to reach
    beliefs.

    Args:
        text: a JSON string. Expected shape ``{name: float, ...}``.

    Returns:
        A dict from name to finite float. Empty dict if parsing fails or
        the payload is not a JSON object.
    """
    try:
        payload = json.loads(text)
    except (json.JSONDecodeError, ValueError):
        return {}
    if not isinstance(payload, dict):
        return {}
    result: dict[str, float] = {}
    for name, value in payload.items():
        if not isinstance(name, str):
            continue
        try:
            number = float(value)
        except (TypeError, ValueError):
            continue
        if math.isfinite(number):
            result[name] = number
    return result
