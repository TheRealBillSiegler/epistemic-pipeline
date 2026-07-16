"""Boundary tests for the shared confidence parser and oscillation detector.

detect_oscillation is the one piece of real logic shared across encodings
(Bayes and the LLM agent). The encoding pipelines cover it transitively with
many flips; these pin the threshold itself so a future tweak to the constant
or the comparison can't slip through.
"""

import pytest

from epistemic_pipeline.encodings._confidence import (
    detect_oscillation,
    parse_confidence_vector,
)


class TestStrictMode:
    """Strict mode separates 'garbage' from 'rated nothing' (#22)."""

    @pytest.mark.parametrize("garbage", ["not json", "[1, 2, 3]", "3.5", "null"])
    def test_garbage_raises_in_strict_mode(self, garbage):
        with pytest.raises(ValueError, match="confidence vector"):
            parse_confidence_vector(garbage, strict=True)

    @pytest.mark.parametrize("garbage", ["not json", "[1, 2, 3]", "3.5", "null"])
    def test_garbage_is_empty_in_lenient_mode(self, garbage):
        assert parse_confidence_vector(garbage) == {}

    def test_valid_empty_object_is_fine_in_both_modes(self):
        assert parse_confidence_vector("{}") == {}
        assert parse_confidence_vector("{}", strict=True) == {}

    def test_strict_mode_still_skips_bad_entries(self):
        # Partial drops are fine: non-finite and non-numeric values are
        # removed either way, as long as something usable survives.
        text = '{"a": 0.7, "b": "high", "c": NaN}'
        assert parse_confidence_vector(text, strict=True) == {"a": 0.7}

    @pytest.mark.parametrize("text", ['{"c": "high"}', '{"c": null}', '{"c": NaN}'])
    def test_object_with_no_usable_entries_raises_in_strict_mode(self, text):
        # A valid envelope around all-garbage entries is still garbage:
        # returning {} here would re-open the #22 silent skip.
        with pytest.raises(ValueError, match="no usable entries"):
            parse_confidence_vector(text, strict=True)


def test_two_transitions_is_not_oscillation():
    # A -> B -> C is 2 transitions; the threshold is 3.
    assert detect_oscillation(["A", "B", "C"]) is False


def test_three_transitions_is_oscillation():
    # A -> B -> A -> B is 3 transitions in a 4-step window.
    assert detect_oscillation(["A", "B", "A", "B"]) is True


def test_short_history_is_not_oscillation():
    assert detect_oscillation([]) is False
    assert detect_oscillation(["A"]) is False
