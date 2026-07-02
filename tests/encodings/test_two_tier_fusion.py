import math

from epistemic_pipeline.encodings._subjective_logic import Opinion
from epistemic_pipeline.encodings.worldview import (
    WorldviewOntology,
    aggregate_beliefs,
    two_tier_fuse,
)


def test_within_root_averages_then_across_roots_accumulates():
    inc = Opinion(2.0, 0.0)  # one fully-confident increment
    one_root = two_tier_fuse({"A": [inc, inc, inc]})        # 3 restatements of A
    assert math.isclose(one_root.uncertainty, 0.5)          # counted once
    two_roots = two_tier_fuse({"A": [inc], "B": [inc]})     # 2 distinct roots
    assert math.isclose(two_roots.uncertainty, 2 / 6)       # accumulated


def test_aggregate_collapses_one_root_but_distinct_roots_settle_more():
    onto = WorldviewOntology(concepts=frozenset({"c"}))
    same = aggregate_beliefs([("A", {"c": 1.0}), ("A", {"c": 1.0}), ("A", {"c": 1.0})], onto)
    distinct = aggregate_beliefs([("A", {"c": 1.0}), ("B", {"c": 1.0}), ("C", {"c": 1.0})], onto)
    assert math.isclose(same.opinions["c"].uncertainty, 0.5)       # one root's worth
    assert distinct.opinions["c"].uncertainty < same.opinions["c"].uncertainty


def test_aggregate_skips_concepts_outside_the_ontology():
    onto = WorldviewOntology(concepts=frozenset({"known"}))
    beliefs = aggregate_beliefs([("A", {"known": 1.0, "unknown": 1.0})], onto)
    assert set(beliefs.opinions) == {"known"}
