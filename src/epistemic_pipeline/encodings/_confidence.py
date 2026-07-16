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
    return _finite_confidences(payload)


def parse_confidence_object(text: str) -> dict[str, float]:
    """Strict parse for the live ingest boundary: raise on a non-object.

    Same value filtering as ``parse_confidence_vector``, but it tells two
    failure modes apart instead of collapsing both to an empty dict:

    - text that is not a JSON object (garbage, a JSON array, a bare value)
      raises ``ValueError`` -- the model did not answer in the expected shape.
    - a valid empty object ``"{}"`` returns ``{}`` -- the model answered, and
      rated nothing.

    The ingest boundary needs that distinction: a note must be marked seen
    only when the model actually answered. Garbage must leave it un-seen so
    the next attempt retries instead of silently dropping it (issue #22).
    Replay over recorded evidence uses the lenient parser instead, because a
    replay must never raise on data already accepted.

    Args:
        text: a JSON string. Expected shape ``{name: float, ...}``.

    Returns:
        A dict from name to finite float (possibly empty).

    Raises:
        ValueError: if ``text`` does not parse to a JSON object.
    """
    try:
        payload = json.loads(text)
    except (json.JSONDecodeError, ValueError) as exc:
        raise ValueError("confidence vector is not valid JSON") from exc
    if not isinstance(payload, dict):
        raise ValueError(
            f"confidence vector must be a JSON object, got {type(payload).__name__}"
        )
    return _finite_confidences(payload)


def _finite_confidences(payload: dict[str, object]) -> dict[str, float]:
    """Keep only values that are a finite number (the trust filter).

    Shared by both parsers. JSON object keys are always strings, so only
    values are checked. A non-finite value (``Infinity`` or ``NaN``, which
    ``json.loads`` accepts) would poison a later update, so it is dropped
    here rather than allowed to reach beliefs.
    """
    result: dict[str, float] = {}
    for name, value in payload.items():
        try:
            number = float(value)  # pyright: ignore[reportArgumentType]
        except (TypeError, ValueError):
            continue
        if math.isfinite(number):
            result[name] = number
    return result


_OSCILLATION_WINDOW = 6
_OSCILLATION_MIN_TRANSITIONS = 3


def detect_oscillation(map_history: list[str]) -> bool:
    """Return True if the top hypothesis flips at least three times.

    ``map_history`` holds the argmax (the MAP, or most-probable) hypothesis
    after each step. A flip is a change between consecutive entries. One flip
    is normal belief evolution; three flips inside a six-step window means the
    evidence is pushing beliefs back and forth instead of converging.

    Shared by the encodings that track a top hypothesis over time (Bayes and
    the LLM agent), so the check lives here once instead of being copied.

    Args:
        map_history: the argmax hypothesis recorded after each step.

    Returns:
        True if oscillation is detected; False otherwise.
    """
    window = map_history[-_OSCILLATION_WINDOW:]
    transitions = sum(
        1 for i in range(len(window) - 1) if window[i] != window[i + 1]
    )
    return transitions >= _OSCILLATION_MIN_TRANSITIONS
