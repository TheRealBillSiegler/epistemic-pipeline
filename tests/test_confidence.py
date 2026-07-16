"""Boundary tests for the shared oscillation detector.

detect_oscillation is the one piece of real logic shared across encodings
(Bayes and the LLM agent). The encoding pipelines cover it transitively with
many flips; these pin the threshold itself so a future tweak to the constant
or the comparison can't slip through.
"""

import pytest

from epistemic_pipeline.encodings._confidence import (
    detect_oscillation,
    parse_confidence_object,
)


def test_two_transitions_is_not_oscillation():
    # A -> B -> C is 2 transitions; the threshold is 3.
    assert detect_oscillation(["A", "B", "C"]) is False


def test_three_transitions_is_oscillation():
    # A -> B -> A -> B is 3 transitions in a 4-step window.
    assert detect_oscillation(["A", "B", "A", "B"]) is True


def test_short_history_is_not_oscillation():
    assert detect_oscillation([]) is False
    assert detect_oscillation(["A"]) is False


class TestParseConfidenceObjectIsStrict:
    # parse_confidence_object is the ingest-boundary parser. It must tell a
    # valid-but-empty answer apart from garbage, where the lenient parser
    # collapses both to {} (issue #22).

    def test_empty_object_is_an_answer_not_an_error(self):
        assert parse_confidence_object("{}") == {}

    def test_filters_non_finite_like_the_lenient_parser(self):
        assert parse_confidence_object('{"a": 0.5, "b": Infinity}') == {"a": 0.5}

    @pytest.mark.parametrize("garbage", ["not json", "[1, 2, 3]", "0.5", "null", '"x"'])
    def test_non_object_raises(self, garbage):
        with pytest.raises(ValueError, match="confidence vector"):
            parse_confidence_object(garbage)
