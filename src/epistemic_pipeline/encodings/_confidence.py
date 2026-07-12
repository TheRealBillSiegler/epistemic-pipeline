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


def parse_confidence_vector(text: str, *, strict: bool = False) -> dict[str, float]:
    """Parse a JSON object mapping name -> confidence.

    Keeps only string keys whose value is a finite number. Anything else
    is skipped: a non-finite value (``Infinity`` or ``NaN``, both of
    which ``json.loads`` accepts) would poison a later renormalize, so it
    is dropped here at the trust boundary rather than allowed to reach
    beliefs.

    Two callers, two failure needs. Replaying persisted values must
    tolerate anything (default: garbage becomes ``{}``). Parsing a fresh
    LLM response must fail loudly, or a garbage response is
    indistinguishable from "the model rated nothing" and the caller
    wrongly records success (#22). ``strict=True`` raises in that case;
    a valid empty object ``{}`` is still a valid rating in both modes.

    Args:
        text: a JSON string. Expected shape ``{name: float, ...}``.
        strict: raise instead of returning ``{}`` when ``text`` is not a
            JSON object, or when it is a non-empty object with no usable
            entries (``{"c": "high"}`` is garbage; ``{}`` is a rating).

    Returns:
        A dict from name to finite float. Empty dict if parsing fails or
        the payload is not a JSON object (non-strict mode).

    Raises:
        ValueError: in strict mode, when ``text`` does not parse to a
            JSON object or no entry survives.
    """
    try:
        payload = json.loads(text)
    except (json.JSONDecodeError, ValueError):
        if strict:
            msg = f"confidence vector is not valid JSON: {text[:80]!r}"
            raise ValueError(msg) from None
        return {}
    if not isinstance(payload, dict):
        if strict:
            msg = f"confidence vector is not a JSON object: {text[:80]!r}"
            raise ValueError(msg)
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
    # A non-empty object where every entry was dropped is garbage wearing
    # a valid envelope, not "the model rated nothing" -- strict mode must
    # treat it like malformed JSON or the #22 silent skip re-enters.
    if strict and payload and not result:
        msg = f"confidence vector has no usable entries: {text[:80]!r}"
        raise ValueError(msg)
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
