"""Boundary tests for the shared oscillation detector.

detect_oscillation is the one piece of real logic shared across encodings
(Bayes and the LLM agent). The encoding pipelines cover it transitively with
many flips; these pin the threshold itself so a future tweak to the constant
or the comparison can't slip through.
"""

from epistemic_pipeline.encodings._confidence import detect_oscillation


def test_two_transitions_is_not_oscillation():
    # A -> B -> C is 2 transitions; the threshold is 3.
    assert detect_oscillation(["A", "B", "C"]) is False


def test_three_transitions_is_oscillation():
    # A -> B -> A -> B is 3 transitions in a 4-step window.
    assert detect_oscillation(["A", "B", "A", "B"]) is True


def test_short_history_is_not_oscillation():
    assert detect_oscillation([]) is False
    assert detect_oscillation(["A"]) is False
