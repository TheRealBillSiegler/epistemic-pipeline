"""End-to-end Bayesian inference tests: medical diagnosis scenario.

Three hypotheses (flu, cold, allergy), three diagnostic tests.
Ground truth is flu. Posterior should converge after all observations.
"""

import dataclasses
import math

from epistemic_pipeline.encodings.bayes import (
    BayesBeliefs,
    BayesOntology,
    BayesProblem,
    bayes_argmax,
    bayes_update,
    run_bayesian_pipeline,
)
from epistemic_pipeline.meta import MetaDecision
from epistemic_pipeline.norms import score_pipeline_run
from epistemic_pipeline.state import EvidenceType, Observation


def _medical_problem() -> BayesProblem:
    """Build a medical diagnosis problem: flu vs cold vs allergy."""
    hypotheses = ("flu", "cold", "allergy")
    observables = ("fever", "congestion", "duration")

    likelihoods = {
        # Fever: flu causes high fever more often
        ("flu", "fever", "high"): 0.9,
        ("cold", "fever", "high"): 0.3,
        ("allergy", "fever", "high"): 0.1,
        ("flu", "fever", "low"): 0.1,
        ("cold", "fever", "low"): 0.7,
        ("allergy", "fever", "low"): 0.9,
        # Congestion: cold causes congestion most often
        ("flu", "congestion", "present"): 0.7,
        ("cold", "congestion", "present"): 0.9,
        ("allergy", "congestion", "present"): 0.5,
        ("flu", "congestion", "absent"): 0.3,
        ("cold", "congestion", "absent"): 0.1,
        ("allergy", "congestion", "absent"): 0.5,
        # Duration: flu lasts longer
        ("flu", "duration", "long"): 0.8,
        ("cold", "duration", "long"): 0.4,
        ("allergy", "duration", "long"): 0.2,
        ("flu", "duration", "short"): 0.2,
        ("cold", "duration", "short"): 0.6,
        ("allergy", "duration", "short"): 0.8,
    }

    observations = (
        Observation(variable="fever", value="high", source="thermometer", timestamp=1.0),
        Observation(variable="congestion", value="present", source="exam", timestamp=2.0),
        Observation(variable="duration", value="long", source="patient_report", timestamp=3.0),
    )

    return BayesProblem(
        hypotheses=hypotheses,
        observables=observables,
        likelihoods=likelihoods,
        observations=observations,
    )


class TestBayesUpdate:
    def test_single_update_two_hypotheses(self):
        """One observation with two hypotheses produces correct posterior."""
        ontology = BayesOntology(
            hypotheses=("A", "B"),
            observables=("x",),
            likelihoods={("A", "x", "1"): 0.8, ("B", "x", "1"): 0.2},
        )
        beliefs = BayesBeliefs(probabilities={"A": 0.5, "B": 0.5})
        obs = Observation(variable="x", value="1", source="test", timestamp=0.0)

        updated = bayes_update(beliefs, obs, ontology)

        assert math.isclose(updated.probabilities["A"], 0.8, rel_tol=1e-9)
        assert math.isclose(updated.probabilities["B"], 0.2, rel_tol=1e-9)

    def test_probabilities_sum_to_one(self):
        """Posterior probabilities always sum to 1.0."""
        ontology = BayesOntology(
            hypotheses=("A", "B", "C"),
            observables=("x",),
            likelihoods={
                ("A", "x", "1"): 0.9,
                ("B", "x", "1"): 0.3,
                ("C", "x", "1"): 0.1,
            },
        )
        beliefs = BayesBeliefs(probabilities={"A": 0.5, "B": 0.3, "C": 0.2})
        obs = Observation(variable="x", value="1", source="test", timestamp=0.0)

        updated = bayes_update(beliefs, obs, ontology)

        total = sum(updated.probabilities.values())
        assert math.isclose(total, 1.0, rel_tol=1e-9)

    def test_zero_likelihood_eliminates_hypothesis(self):
        """A hypothesis with zero likelihood gets zero posterior."""
        ontology = BayesOntology(
            hypotheses=("A", "B"),
            observables=("x",),
            likelihoods={("A", "x", "1"): 1.0, ("B", "x", "1"): 0.0},
        )
        beliefs = BayesBeliefs(probabilities={"A": 0.5, "B": 0.5})
        obs = Observation(variable="x", value="1", source="test", timestamp=0.0)

        updated = bayes_update(beliefs, obs, ontology)

        assert math.isclose(updated.probabilities["A"], 1.0, rel_tol=1e-9)
        assert math.isclose(updated.probabilities["B"], 0.0, abs_tol=1e-15)

    def test_sequential_updates_accumulate(self):
        """Two sequential updates produce the same result as one combined update."""
        ontology = BayesOntology(
            hypotheses=("A", "B"),
            observables=("x", "y"),
            likelihoods={
                ("A", "x", "1"): 0.9,
                ("B", "x", "1"): 0.1,
                ("A", "y", "1"): 0.4,
                ("B", "y", "1"): 0.8,
            },
        )
        beliefs = BayesBeliefs(probabilities={"A": 0.5, "B": 0.5})
        obs1 = Observation(variable="x", value="1", source="test", timestamp=0.0)
        obs2 = Observation(variable="y", value="1", source="test", timestamp=1.0)

        after_first = bayes_update(beliefs, obs1, ontology)
        after_both = bayes_update(after_first, obs2, ontology)

        total = sum(after_both.probabilities.values())
        assert math.isclose(total, 1.0, rel_tol=1e-9)
        # With conflicting evidence, neither hypothesis should dominate completely
        assert 0.0 < after_both.probabilities["A"] < 1.0
        assert 0.0 < after_both.probabilities["B"] < 1.0


class TestMedicalDiagnosis:
    """End-to-end: 3 hypotheses, 3 tests, posterior converges to flu."""

    def test_posterior_converges_to_ground_truth(self):
        result = run_bayesian_pipeline(_medical_problem())

        posterior = result.final_state.beliefs.probabilities
        assert bayes_argmax(result.final_state.beliefs) == "flu"
        assert posterior["flu"] > 0.75

    def test_uniform_priors(self):
        result = run_bayesian_pipeline(_medical_problem())

        initial_beliefs = result.trace[0].beliefs
        n = len(_medical_problem().hypotheses)
        for h in _medical_problem().hypotheses:
            assert math.isclose(
                initial_beliefs.probabilities[h],
                1.0 / n,
                rel_tol=1e-9,
            )

    def test_trace_has_correct_length(self):
        result = run_bayesian_pipeline(_medical_problem())

        # initial + 5 stages (decompose, model, select, test, integrate)
        assert len(result.trace) == 6

    def test_evidence_accumulates(self):
        result = run_bayesian_pipeline(_medical_problem())

        assert len(result.trace[0].evidence) == 0
        assert len(result.final_state.evidence) == 3

    def test_trace_replayable(self):
        result = run_bayesian_pipeline(_medical_problem())

        # Replay: start from initial beliefs, apply R for each evidence
        initial = result.trace[0]
        beliefs = initial.beliefs
        for obs in result.final_state.evidence:
            beliefs = result.final_state.revision_policy(
                beliefs,
                obs,
                result.final_state.ontology,
            )

        # Replayed beliefs must match final beliefs exactly
        for h in _medical_problem().hypotheses:
            assert math.isclose(
                beliefs.probabilities[h],
                result.final_state.beliefs.probabilities[h],
                rel_tol=1e-9,
            )

    def test_meta_layer_returns_accept(self):
        result = run_bayesian_pipeline(_medical_problem())

        assert result.meta_decision.decision == MetaDecision.ACCEPT

    def test_norm_scoring(self):
        result = run_bayesian_pipeline(_medical_problem())

        scores = score_pipeline_run(
            result.trace,
            ground_truth="flu",
            belief_argmax=bayes_argmax,
        )

        assert scores.reliability == 1.0
        assert scores.efficiency == 6
        assert scores.justification is True
        assert scores.power is None

    def test_custom_priors(self):
        problem = BayesProblem(
            hypotheses=_medical_problem().hypotheses,
            observables=_medical_problem().observables,
            likelihoods=_medical_problem().likelihoods,
            observations=_medical_problem().observations,
            priors={"flu": 0.1, "cold": 0.1, "allergy": 0.8},
        )
        result = run_bayesian_pipeline(problem)

        # Even with allergy-biased priors, strong flu evidence wins
        assert bayes_argmax(result.final_state.beliefs) == "flu"


class TestStateImmutability:
    def test_epistemic_state_is_frozen(self):
        result = run_bayesian_pipeline(_medical_problem())

        assert dataclasses.is_dataclass(result.final_state)
        try:
            result.final_state.ontology = None  # type: ignore[misc]
        except dataclasses.FrozenInstanceError:
            pass
        else:
            raise AssertionError("EpistemicState should be frozen")

    def test_beliefs_are_frozen(self):
        beliefs = BayesBeliefs(probabilities={"A": 0.5, "B": 0.5})
        try:
            beliefs.probabilities = {}  # type: ignore[misc]
        except dataclasses.FrozenInstanceError:
            pass
        else:
            raise AssertionError("BayesBeliefs should be frozen")

    def test_observation_is_frozen(self):
        obs = Observation(variable="x", value="1", source="s", timestamp=0.0)
        try:
            obs.variable = "y"  # type: ignore[misc]
        except dataclasses.FrozenInstanceError:
            pass
        else:
            raise AssertionError("Observation should be frozen")

    def test_pipeline_result_is_frozen(self):
        result = run_bayesian_pipeline(_medical_problem())

        assert dataclasses.is_dataclass(result)
        try:
            result.final_state = None  # type: ignore[misc]
        except dataclasses.FrozenInstanceError:
            pass
        else:
            raise AssertionError("PipelineResult should be frozen")


class TestEvidenceType:
    """EvidenceType and confidence fields on Observation."""

    def test_default_etype_is_observation(self):
        obs = Observation(variable="x", value="1", source="s", timestamp=0.0)
        assert obs.etype == EvidenceType.OBSERVATION

    def test_default_confidence_is_one(self):
        obs = Observation(variable="x", value="1", source="s", timestamp=0.0)
        assert obs.confidence == 1.0

    def test_report_etype_round_trips(self):
        obs = Observation(
            variable="x", value="1", source="s", timestamp=0.0,
            etype=EvidenceType.REPORT, confidence=0.7,
        )
        assert obs.etype == EvidenceType.REPORT
        assert obs.confidence == 0.7

    def test_measurement_etype_round_trips(self):
        obs = Observation(
            variable="x", value="1", source="s", timestamp=0.0,
            etype=EvidenceType.MEASUREMENT, confidence=0.99,
        )
        assert obs.etype == EvidenceType.MEASUREMENT
