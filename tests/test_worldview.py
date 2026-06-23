"""Tests for the worldview encoding (#7)."""

import dataclasses
import math

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


class TestUpdate:
    def test_empty_prior_posterior_equals_normalized_likelihood(self):
        # No prior beliefs: posterior is just the renormalized vector.
        b0 = WorldviewBeliefs({})
        obs = _vector_obs({"c1": 0.6, "c2": 0.2})
        b1 = worldview_update(b0, obs, ONT)
        assert math.isclose(b1.confidences["c1"], 0.75)
        assert math.isclose(b1.confidences["c2"], 0.25)
        assert math.isclose(sum(b1.confidences.values()), 1.0)

    def test_already_normalized_vector_passes_through(self):
        b0 = WorldviewBeliefs({})
        obs = _vector_obs({"c1": 0.7, "c2": 0.3})
        b1 = worldview_update(b0, obs, ONT)
        assert math.isclose(b1.confidences["c1"], 0.7)
        assert math.isclose(b1.confidences["c2"], 0.3)

    def test_unknown_concepts_dropped(self):
        b0 = WorldviewBeliefs({})
        obs = _vector_obs({"c1": 0.5, "ghost": 0.5})
        b1 = worldview_update(b0, obs, ONT)
        assert set(b1.confidences) == {"c1"}
        assert math.isclose(b1.confidences["c1"], 1.0)

    def test_negative_values_clamped(self):
        b0 = WorldviewBeliefs({})
        obs = _vector_obs({"c1": 1.0, "c2": -0.5})
        b1 = worldview_update(b0, obs, ONT)
        assert math.isclose(b1.confidences["c1"], 1.0)
        assert math.isclose(b1.confidences["c2"], 0.0)

    def test_non_vector_observation_leaves_beliefs_unchanged(self):
        b0 = WorldviewBeliefs({"c1": 1.0})
        # a raw document chunk, not a confidence vector
        obs = dataclasses.replace(
            extraction_observation({"c1": 0.2}, 0.0, "m", "h", 1),
            variable="doc_chunk",
        )
        assert worldview_update(b0, obs, ONT) is b0

    def test_empty_after_filtering_leaves_beliefs_unchanged(self):
        b0 = WorldviewBeliefs({"c1": 1.0})
        obs = _vector_obs({"ghost": 0.9})
        assert worldview_update(b0, obs, ONT) is b0

    def test_non_finite_values_dropped(self):
        # +inf must not poison the distribution to NaN; it is dropped.
        b0 = WorldviewBeliefs({})
        b1 = worldview_update(b0, _vector_obs({"c1": float("inf"), "c2": 0.5}), ONT)
        assert b1.confidences == {"c2": 1.0}
        assert math.isfinite(sum(b1.confidences.values()))

    def test_nan_value_dropped(self):
        b0 = WorldviewBeliefs({})
        b1 = worldview_update(b0, _vector_obs({"c1": float("nan"), "c2": 0.5}), ONT)
        assert b1.confidences == {"c2": 1.0}

    def test_all_non_finite_leaves_beliefs_unchanged(self):
        b0 = WorldviewBeliefs({"c1": 1.0})
        assert worldview_update(b0, _vector_obs({"c1": float("inf")}), ONT) is b0

    def test_all_zero_vector_leaves_beliefs_unchanged(self):
        # Non-empty filtered map of zeros: must hit the guard, not divide by zero.
        b0 = WorldviewBeliefs({"c1": 1.0})
        assert worldview_update(b0, _vector_obs({"c1": 0.0, "c2": 0.0}), ONT) is b0

    def test_all_negative_vector_leaves_beliefs_unchanged(self):
        b0 = WorldviewBeliefs({"c1": 1.0})
        assert worldview_update(b0, _vector_obs({"c1": -0.5, "c2": -0.3}), ONT) is b0

    def test_malformed_or_non_object_json_leaves_beliefs_unchanged(self):
        b0 = WorldviewBeliefs({"c1": 1.0})
        for bad in ("{not json", "[1, 2, 3]", "5"):
            obs = dataclasses.replace(_vector_obs({"c1": 1.0}), value=bad)
            assert worldview_update(b0, obs, ONT) is b0

    def test_unrated_concepts_drop_across_documents(self):
        # Latest document wins: concepts it omits vanish, not retained or zeroed.
        b1 = worldview_update(
            WorldviewBeliefs({}), _vector_obs({"c1": 0.7, "c2": 0.3}), ONT,
        )
        b2 = worldview_update(b1, _vector_obs({"c3": 1.0}), ONT)
        assert set(b2.confidences) == {"c3"}
        assert "c1" not in b2.confidences


class TestArgmax:
    def test_picks_highest(self):
        assert worldview_argmax(WorldviewBeliefs({"c1": 0.2, "c2": 0.8})) == "c2"

    def test_empty_returns_empty_string(self):
        assert worldview_argmax(WorldviewBeliefs({})) == ""


class TestAdequacy:
    def test_adequate_when_all_concepts_known(self):
        ev = (_vector_obs({"c1": 0.5, "c2": 0.5}),)
        assert ONT.adequate(ev) is True

    def test_inadequate_when_evidence_names_unknown_concept(self):
        ev = (_vector_obs({"c1": 0.5, "newthing": 0.5}),)
        assert ONT.adequate(ev) is False

    def test_non_vector_evidence_ignored(self):
        obs = dataclasses.replace(_vector_obs({"ghost": 1.0}), variable="doc_chunk")
        assert ONT.adequate((obs,)) is True


class TestDeterminism:
    def test_extraction_observation_is_pure(self):
        a = extraction_observation({"c1": 0.7, "c2": 0.3}, 1.0, "m1", "h1", 9)
        b = extraction_observation({"c2": 0.3, "c1": 0.7}, 1.0, "m1", "h1", 9)
        # key order does not matter (sort_keys) -> identical observation
        assert a == b
        assert a.source == "m1@h1#9"

    def test_update_is_repeatable(self):
        b0 = WorldviewBeliefs({})
        obs = _vector_obs({"c1": 0.6, "c2": 0.4})
        assert worldview_update(b0, obs, ONT) == worldview_update(b0, obs, ONT)

    def test_extraction_observation_variable_and_provenance(self):
        obs = extraction_observation({"c1": 1.0}, 0.0, "m", "h", 1)
        # The magic string adequate()/worldview_update() branch on.
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
    controller = MetaController()
    decision = controller.monitor((s0, s1), None, ONT, "worldview", ())
    return PipelineResult(final_state=s1, trace=(s0, s1), meta_decision=decision)


class TestPowerNormWiring:
    def test_unknown_concept_triggers_reframe(self):
        # A document introduces a concept O does not know -> power False -> REFRAME.
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
        # Contrapositive: all-known concepts -> power True -> ACCEPT.
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
            assert back.beliefs == orig.beliefs
            assert back.evidence == orig.evidence
            assert back.metadata == orig.metadata

    def test_two_runs_produce_byte_identical_traces(self, tmp_path):
        # Determinism: rebuilding from the same inputs dumps identical bytes.
        a = tmp_path / "a.jsonl"
        b = tmp_path / "b.jsonl"
        dump_trace(_two_step_result(), a)
        dump_trace(_two_step_result(), b)
        assert a.read_bytes() == b.read_bytes()

    def test_dump_load_dump_is_byte_identical(self, tmp_path):
        # Determinism across the load path: re-dumping a loaded trace matches.
        a = tmp_path / "a.jsonl"
        b = tmp_path / "b.jsonl"
        dump_trace(_two_step_result(), a)
        dump_trace(load_trace(a), b)
        assert a.read_bytes() == b.read_bytes()

    def test_loaded_policy_still_revises(self, tmp_path):
        # The revision policy is reattached on load and still works.
        result = _two_step_result()
        path = tmp_path / "wv.jsonl"
        dump_trace(result, path)
        loaded = load_trace(path)
        obs = _vector_obs({"c3": 1.0}, ts=1.0)
        revised = loaded.final_state.revision_policy(
            loaded.final_state.beliefs, obs, loaded.final_state.ontology,
        )
        assert math.isclose(revised.confidences["c3"], 1.0)


def test_fresh_reader_first_document_is_complete():
    """Empty prior + one document yields a usable belief, no setup step."""
    b0 = WorldviewBeliefs({})
    b1 = worldview_update(b0, _vector_obs({"c1": 0.9, "c2": 0.1}), ONT)
    assert worldview_argmax(b1) == "c1"
    assert math.isclose(sum(b1.confidences.values()), 1.0)
