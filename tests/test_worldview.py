"""Tests for the worldview encoding on Subjective Logic (#18)."""

import dataclasses
import math

import pytest

from epistemic_pipeline.encodings._subjective_logic import Opinion
from epistemic_pipeline.encodings.worldview import (
    WorldviewBeliefs,
    WorldviewOntology,
    extraction_observation,
    worldview_argmax,
    worldview_update,
)
from epistemic_pipeline.meta import MetaController, MetaDecision
from epistemic_pipeline.norms import score_pipeline_run
from epistemic_pipeline.pipeline import PipelineResult
from epistemic_pipeline.state import EpistemicState, EvidenceType, Metadata
from epistemic_pipeline.trace import dump_trace, load_trace

ONT = WorldviewOntology(concepts=frozenset({"c1", "c2", "c3"}))


def _vector_obs(confidences, ts=0.0):
    return extraction_observation(
        confidences, timestamp=ts, model_id="m1", prompt_hash="deadbeef", seed=7,
    )


def _update(beliefs, confidences, ts=0.0):
    return worldview_update(beliefs, _vector_obs(confidences, ts), ONT)


class TestUpdateBuildsOpinions:
    def test_confidence_splits_evidence_for_and_against(self):
        # p=0.6 over E=2 units -> Opinion(1.2, 0.8).
        op = _update(WorldviewBeliefs({}), {"c1": 0.6}).opinions["c1"]
        assert op.r == pytest.approx(1.2)
        assert op.s == pytest.approx(0.8)
        assert op.projected == pytest.approx(0.55)  # 0.3 + 0.5*0.5

    def test_full_confidence_is_believed_but_uncertain(self):
        # One fully-confident source: b = u = 0.5, P = 0.75.
        op = _update(WorldviewBeliefs({}), {"c1": 1.0}).opinions["c1"]
        assert op.belief == pytest.approx(0.5)
        assert op.uncertainty == pytest.approx(0.5)
        assert op.projected == pytest.approx(0.75)

    def test_zero_confidence_is_disconfirmation(self):
        # p=0 is evidence AGAINST, not a no-op: Opinion(0, 2), P below base rate.
        op = _update(WorldviewBeliefs({}), {"c1": 0.0}).opinions["c1"]
        assert op.disbelief == pytest.approx(0.5)
        assert op.projected == pytest.approx(0.25)

    def test_confidence_clamped_to_unit_interval(self):
        hi = _update(WorldviewBeliefs({}), {"c1": 1.5}).opinions["c1"]
        lo = _update(WorldviewBeliefs({}), {"c2": -0.5}).opinions["c2"]
        assert (hi.r, hi.s) == pytest.approx((2.0, 0.0))
        assert (lo.r, lo.s) == pytest.approx((0.0, 2.0))


class TestAccumulationAndCarryForward:
    def test_repeated_evidence_accumulates(self):
        b1 = _update(WorldviewBeliefs({}), {"c1": 1.0})
        b2 = _update(b1, {"c1": 1.0})
        op = b2.opinions["c1"]
        assert (op.r, op.s) == pytest.approx((4.0, 0.0))  # counts added
        assert op.projected > b1.opinions["c1"].projected  # firmer
        assert op.uncertainty < b1.opinions["c1"].uncertainty  # less ignorant

    def test_unmentioned_concept_is_carried_forward(self):
        # The amnesia regression: a document silent on c1 must not erase it.
        b1 = _update(WorldviewBeliefs({}), {"c1": 1.0})
        b2 = _update(b1, {"c2": 1.0})
        assert "c1" in b2.opinions
        assert b2.opinions["c1"] == b1.opinions["c1"]  # untouched
        assert "c2" in b2.opinions

    def test_existing_concepts_preserved_when_new_one_arrives(self):
        b = _update(WorldviewBeliefs({}), {"c1": 0.8, "c2": 0.2})
        b = _update(b, {"c3": 0.9})
        assert set(b.opinions) == {"c1", "c2", "c3"}


class TestUnverifiedVersusBalanced:
    def test_vacuous_concept_projects_to_base_rate_with_full_uncertainty(self):
        # No evidence: u=1, P=base_rate. "I don't know", not a fabricated 0.5.
        op = Opinion(0.0, 0.0)
        assert op.uncertainty == 1.0
        assert op.projected == 0.5

    def test_balanced_evidence_differs_from_ignorance(self):
        # Balanced but evidenced: P=0.5 like ignorance, but u is lower.
        balanced = _update(WorldviewBeliefs({}), {"c1": 0.5}).opinions["c1"]
        assert balanced.projected == pytest.approx(0.5)
        assert balanced.uncertainty < 1.0  # distinct from the vacuous state


class TestUpdateNoOps:
    def test_non_vector_observation_unchanged(self):
        b0 = WorldviewBeliefs({"c1": Opinion(2, 0)})
        obs = dataclasses.replace(_vector_obs({"c1": 0.2}), variable="doc_chunk")
        assert worldview_update(b0, obs, ONT) is b0

    def test_unknown_only_vector_unchanged(self):
        b0 = WorldviewBeliefs({"c1": Opinion(2, 0)})
        assert _update(b0, {"ghost": 0.9}) is b0

    def test_non_finite_values_dropped(self):
        b1 = _update(WorldviewBeliefs({}), {"c1": float("inf"), "c2": 0.5})
        assert set(b1.opinions) == {"c2"}

    def test_all_non_finite_unchanged(self):
        b0 = WorldviewBeliefs({"c1": Opinion(2, 0)})
        assert _update(b0, {"c1": float("nan")}) is b0

    def test_malformed_json_unchanged(self):
        b0 = WorldviewBeliefs({"c1": Opinion(2, 0)})
        for bad in ("{not json", "[1, 2, 3]", "5"):
            obs = dataclasses.replace(_vector_obs({"c1": 1.0}), value=bad)
            assert worldview_update(b0, obs, ONT) is b0

    def test_unknown_concept_in_mixed_vector_dropped(self):
        b1 = _update(WorldviewBeliefs({}), {"c1": 0.5, "ghost": 0.5})
        assert set(b1.opinions) == {"c1"}


class TestArgmax:
    def test_picks_highest_projected(self):
        b = WorldviewBeliefs({"c1": Opinion(0, 2), "c2": Opinion(2, 0)})
        assert worldview_argmax(b) == "c2"

    def test_empty_returns_empty_string(self):
        assert worldview_argmax(WorldviewBeliefs({})) == ""


class TestAdequacy:
    def test_adequate_when_all_concepts_known(self):
        assert ONT.adequate((_vector_obs({"c1": 0.5, "c2": 0.5}),)) is True

    def test_inadequate_when_evidence_names_unknown_concept(self):
        assert ONT.adequate((_vector_obs({"c1": 0.5, "newthing": 0.5}),)) is False

    def test_non_vector_evidence_ignored(self):
        obs = dataclasses.replace(_vector_obs({"ghost": 1.0}), variable="doc_chunk")
        assert ONT.adequate((obs,)) is True


class TestDeterminism:
    def test_extraction_observation_is_pure(self):
        a = extraction_observation({"c1": 0.7, "c2": 0.3}, 1.0, "m1", "h1", 9)
        b = extraction_observation({"c2": 0.3, "c1": 0.7}, 1.0, "m1", "h1", 9)
        assert a == b  # sort_keys -> order-independent
        assert a.source == "m1@h1#9"

    def test_update_is_repeatable(self):
        b0 = WorldviewBeliefs({})
        obs = _vector_obs({"c1": 0.6, "c2": 0.4})
        assert worldview_update(b0, obs, ONT) == worldview_update(b0, obs, ONT)

    def test_accumulation_is_order_independent(self):
        # Cumulative fusion is count addition, so document order does not matter.
        forward = _update(_update(WorldviewBeliefs({}), {"c1": 0.8}), {"c1": 0.3})
        backward = _update(_update(WorldviewBeliefs({}), {"c1": 0.3}), {"c1": 0.8})
        assert forward.opinions["c1"] == backward.opinions["c1"]

    def test_extraction_observation_provenance(self):
        obs = extraction_observation({"c1": 1.0}, 0.0, "m", "h", 1)
        assert obs.variable == "confidence_vector"
        assert obs.etype == EvidenceType.REPORT
        assert obs.modality == "llm"


def _two_step_result():
    """Build a PipelineResult by hand: empty prior, one document."""
    b0 = WorldviewBeliefs({})
    obs = _vector_obs({"c1": 0.7, "c2": 0.3})
    b1 = worldview_update(b0, obs, ONT)
    meta = Metadata(strategy="worldview")
    s0 = EpistemicState(ONT, (), b0, worldview_update, meta)
    s1 = EpistemicState(ONT, (obs,), b1, worldview_update, meta)
    decision = MetaController().monitor((s0, s1), None, ONT, "worldview", ())
    return PipelineResult(final_state=s1, trace=(s0, s1), meta_decision=decision)


class TestPowerNormWiring:
    def test_unknown_concept_triggers_reframe(self):
        b0 = WorldviewBeliefs({})
        obs = _vector_obs({"c1": 0.5, "unmapped": 0.5})
        b1 = worldview_update(b0, obs, ONT)
        meta = Metadata(strategy="worldview")
        trace = (
            EpistemicState(ONT, (), b0, worldview_update, meta),
            EpistemicState(ONT, (obs,), b1, worldview_update, meta),
        )
        score = score_pipeline_run(
            trace,
            ground_truth="c1",
            belief_argmax=worldview_argmax,
            ontology_adequate=lambda o, e: o.adequate(e),
        )
        assert score.power is False
        result = MetaController().monitor(trace, score, ONT, "worldview", ())
        assert result.decision == MetaDecision.REFRAME
        assert result.details["trigger"] == "ontology_inadequate"

    def test_all_known_concepts_accept(self):
        b0 = WorldviewBeliefs({})
        obs = _vector_obs({"c1": 0.7, "c2": 0.3})
        b1 = worldview_update(b0, obs, ONT)
        meta = Metadata(strategy="worldview")
        trace = (
            EpistemicState(ONT, (), b0, worldview_update, meta),
            EpistemicState(ONT, (obs,), b1, worldview_update, meta),
        )
        score = score_pipeline_run(
            trace,
            ground_truth="c1",
            belief_argmax=worldview_argmax,
            ontology_adequate=lambda o, e: o.adequate(e),
        )
        assert score.power is True
        result = MetaController().monitor(trace, score, ONT, "worldview", ())
        assert result.decision == MetaDecision.ACCEPT


class TestTraceRoundTrip:
    def test_dump_load_round_trip(self, tmp_path):
        result = _two_step_result()
        path = tmp_path / "wv.jsonl"
        dump_trace(result, path)
        loaded = load_trace(path)
        assert len(loaded.trace) == len(result.trace)
        for orig, back in zip(result.trace, loaded.trace, strict=True):
            assert back.ontology == orig.ontology
            assert back.beliefs == orig.beliefs  # opinions compare by value
            assert back.evidence == orig.evidence
            assert back.metadata == orig.metadata

    def test_two_runs_produce_byte_identical_traces(self, tmp_path):
        a = tmp_path / "a.jsonl"
        b = tmp_path / "b.jsonl"
        dump_trace(_two_step_result(), a)
        dump_trace(_two_step_result(), b)
        assert a.read_bytes() == b.read_bytes()

    def test_dump_load_dump_is_byte_identical(self, tmp_path):
        a = tmp_path / "a.jsonl"
        b = tmp_path / "b.jsonl"
        dump_trace(_two_step_result(), a)
        dump_trace(load_trace(a), b)
        assert a.read_bytes() == b.read_bytes()

    def test_loaded_policy_still_revises(self, tmp_path):
        result = _two_step_result()
        path = tmp_path / "wv.jsonl"
        dump_trace(result, path)
        loaded = load_trace(path)
        obs = _vector_obs({"c3": 1.0}, ts=1.0)
        revised = loaded.final_state.revision_policy(
            loaded.final_state.beliefs, obs, loaded.final_state.ontology,
        )
        assert revised.opinions["c3"].projected == pytest.approx(0.75)


def test_fresh_reader_first_document_is_complete():
    """Empty prior + one document yields a usable belief, no setup step."""
    b1 = _update(WorldviewBeliefs({}), {"c1": 0.9, "c2": 0.1})
    assert worldview_argmax(b1) == "c1"
    assert math.isfinite(b1.opinions["c1"].projected)
