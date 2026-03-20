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


class TestBayesOntologyAdequacy:
    """BayesOntology.adequate(E) returns True when every observation's
    (variable, value) pair has a likelihood entry for at least one hypothesis."""

    def test_adequate_when_all_evidence_covered(self):
        ontology = BayesOntology(
            hypotheses=("A", "B"),
            observables=("x",),
            likelihoods={("A", "x", "1"): 0.8, ("B", "x", "1"): 0.2},
        )
        evidence = (
            Observation(variable="x", value="1", source="test", timestamp=0.0),
        )
        assert ontology.adequate(evidence) is True

    def test_inadequate_when_unknown_variable(self):
        ontology = BayesOntology(
            hypotheses=("A",),
            observables=("x",),
            likelihoods={("A", "x", "1"): 0.8},
        )
        evidence = (
            Observation(variable="y", value="1", source="test", timestamp=0.0),
        )
        assert ontology.adequate(evidence) is False

    def test_inadequate_when_unknown_value(self):
        ontology = BayesOntology(
            hypotheses=("A",),
            observables=("x",),
            likelihoods={("A", "x", "1"): 0.8},
        )
        evidence = (
            Observation(variable="x", value="999", source="test", timestamp=0.0),
        )
        assert ontology.adequate(evidence) is False

    def test_adequate_with_empty_evidence(self):
        ontology = BayesOntology(
            hypotheses=("A",),
            observables=("x",),
            likelihoods={("A", "x", "1"): 0.8},
        )
        assert ontology.adequate(()) is True


class TestConfidenceWeightedUpdates:
    """Confidence-weighted Bayes: L_eff(e|h) = c*P(e|h) + (1-c)*P(e)."""

    def _simple_ontology(self) -> BayesOntology:
        return BayesOntology(
            hypotheses=("A", "B"),
            observables=("x",),
            likelihoods={("A", "x", "1"): 0.9, ("B", "x", "1"): 0.1},
        )

    def test_full_confidence_matches_standard_bayes(self):
        ontology = self._simple_ontology()
        beliefs = BayesBeliefs(probabilities={"A": 0.5, "B": 0.5})
        obs = Observation(variable="x", value="1", source="t", timestamp=0.0, confidence=1.0)
        updated = bayes_update(beliefs, obs, ontology)
        assert math.isclose(updated.probabilities["A"], 0.9, rel_tol=1e-9)

    def test_zero_confidence_is_noop(self):
        ontology = self._simple_ontology()
        beliefs = BayesBeliefs(probabilities={"A": 0.5, "B": 0.5})
        obs = Observation(variable="x", value="1", source="t", timestamp=0.0, confidence=0.0)
        updated = bayes_update(beliefs, obs, ontology)
        assert math.isclose(updated.probabilities["A"], 0.5, rel_tol=1e-9)
        assert math.isclose(updated.probabilities["B"], 0.5, rel_tol=1e-9)

    def test_half_confidence_dampens_update(self):
        ontology = self._simple_ontology()
        beliefs = BayesBeliefs(probabilities={"A": 0.5, "B": 0.5})
        obs = Observation(variable="x", value="1", source="t", timestamp=0.0, confidence=0.5)
        updated = bayes_update(beliefs, obs, ontology)
        assert 0.5 < updated.probabilities["A"] < 0.9

    def test_low_confidence_preserves_normalization(self):
        ontology = self._simple_ontology()
        beliefs = BayesBeliefs(probabilities={"A": 0.5, "B": 0.5})
        obs = Observation(variable="x", value="1", source="t", timestamp=0.0, confidence=0.3)
        updated = bayes_update(beliefs, obs, ontology)
        total = sum(updated.probabilities.values())
        assert math.isclose(total, 1.0, rel_tol=1e-9)


class TestAnomalyDetection:
    """Anomaly detection in bayes_test: oscillation and contradiction."""

    def _oscillation_problem(self) -> BayesProblem:
        """6 observations with alternating evidence that flips the MAP hypothesis.

        Uses different variables to avoid same-variable contradiction.
        Pro-B evidence (0.005/0.995) is slightly stronger than pro-A (0.99/0.01).
        This asymmetry ensures each counter-observation overwhelms the prior,
        genuinely flipping the MAP label back and forth.
        """
        return BayesProblem(
            hypotheses=("A", "B"),
            observables=("v1", "v2", "v3", "v4", "v5", "v6"),
            likelihoods={
                # Pro-A evidence: strong but not overwhelming
                ("A", "v1", "a"): 0.99, ("B", "v1", "a"): 0.01,
                ("A", "v3", "a"): 0.99, ("B", "v3", "a"): 0.01,
                ("A", "v5", "a"): 0.99, ("B", "v5", "a"): 0.01,
                # Pro-B evidence: slightly stronger, overwhelms accumulated pro-A
                ("A", "v2", "b"): 0.005, ("B", "v2", "b"): 0.995,
                ("A", "v4", "b"): 0.005, ("B", "v4", "b"): 0.995,
                ("A", "v6", "b"): 0.005, ("B", "v6", "b"): 0.995,
            },
            observations=(
                Observation(variable="v1", value="a", source="t", timestamp=1.0),
                Observation(variable="v2", value="b", source="t", timestamp=2.0),
                Observation(variable="v3", value="a", source="t", timestamp=3.0),
                Observation(variable="v4", value="b", source="t", timestamp=4.0),
                Observation(variable="v5", value="a", source="t", timestamp=5.0),
                Observation(variable="v6", value="b", source="t", timestamp=6.0),
            ),
        )

    def test_oscillation_detected(self):
        result = run_bayesian_pipeline(self._oscillation_problem())
        assert "oscillation" in result.final_state.metadata.anomalies

    def test_no_oscillation_on_normal_convergence(self):
        result = run_bayesian_pipeline(_medical_problem())
        assert "oscillation" not in result.final_state.metadata.anomalies

    def test_same_variable_contradiction(self):
        problem = BayesProblem(
            hypotheses=("A", "B"),
            observables=("x",),
            likelihoods={
                ("A", "x", "yes"): 0.9, ("B", "x", "yes"): 0.1,
                ("A", "x", "no"): 0.1, ("B", "x", "no"): 0.9,
            },
            observations=(
                Observation(variable="x", value="yes", source="t", timestamp=1.0),
                Observation(variable="x", value="no", source="t", timestamp=2.0),
            ),
        )
        result = run_bayesian_pipeline(problem)
        assert "contradiction" in result.final_state.metadata.anomalies

    def test_high_confidence_reversal(self):
        """MAP shift when prior MAP had probability > 0.8 flags contradiction.

        First observation strongly favors A (P(A)->0.99).
        Second observation must be much stronger to overwhelm the prior and flip MAP.
        """
        problem = BayesProblem(
            hypotheses=("A", "B"),
            observables=("x", "y"),
            likelihoods={
                ("A", "x", "1"): 0.99, ("B", "x", "1"): 0.01,
                ("A", "y", "1"): 0.0001, ("B", "y", "1"): 0.9999,
            },
            observations=(
                Observation(variable="x", value="1", source="t", timestamp=1.0),
                Observation(variable="y", value="1", source="t", timestamp=2.0),
            ),
        )
        result = run_bayesian_pipeline(problem)
        assert "contradiction" in result.final_state.metadata.anomalies


class TestExtendedNorms:
    """v0.2 norm extensions: calibration, heuristic cost, consistency, power."""

    def test_calibration_perfect(self):
        """calibration = log(B(h*)) = 0.0 when B(h*) = 1.0."""
        result = run_bayesian_pipeline(_medical_problem())

        scores = score_pipeline_run(
            result.trace,
            ground_truth="flu",
            belief_argmax=bayes_argmax,
            belief_probability=lambda b, h: b.probabilities[h],
        )

        # flu probability is high but not 1.0, so calibration < 0
        assert scores.calibration < 0.0

    def test_calibration_uses_log_scoring(self):
        """calibration = log(B_final(h*)) for the ground truth hypothesis."""
        result = run_bayesian_pipeline(_medical_problem())

        p_flu = result.final_state.beliefs.probabilities["flu"]
        expected_cal = math.log(p_flu)

        scores = score_pipeline_run(
            result.trace,
            ground_truth="flu",
            belief_argmax=bayes_argmax,
            belief_probability=lambda b, h: b.probabilities[h],
        )

        assert math.isclose(scores.calibration, expected_cal, rel_tol=1e-9)

    def test_v01_scoring_still_works(self):
        """Calling score_pipeline_run with only v0.1 args still works."""
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
        assert scores.calibration == 0.0  # default

    def test_power_with_adequate_ontology(self):
        """power = True when ontology covers all evidence."""
        result = run_bayesian_pipeline(_medical_problem())

        scores = score_pipeline_run(
            result.trace,
            ground_truth="flu",
            belief_argmax=bayes_argmax,
            ontology_adequate=lambda o, e: o.adequate(e),
        )

        assert scores.power is True

    def test_intermediate_consistency_checked(self):
        """Intermediate consistency calls the provided checker."""
        result = run_bayesian_pipeline(_medical_problem())

        def check_bayes_consistent(
            beliefs: BayesBeliefs, _ontology: BayesOntology,
        ) -> bool:
            total = sum(beliefs.probabilities.values())
            return math.isclose(total, 1.0, rel_tol=1e-6)

        scores = score_pipeline_run(
            result.trace,
            ground_truth="flu",
            belief_argmax=bayes_argmax,
            belief_consistent=check_bayes_consistent,
        )

        assert scores.justification_intermediate_consistent is True

    def test_strategy_switches_from_metadata(self):
        """Strategy switches are read from the final state metadata."""
        result = run_bayesian_pipeline(_medical_problem())

        scores = score_pipeline_run(
            result.trace,
            ground_truth="flu",
            belief_argmax=bayes_argmax,
        )

        assert scores.efficiency_strategy_switches == 0

    def test_calibration_neg_inf_when_zero_probability(self):
        """calibration = -inf when B(h*) = 0."""
        result = run_bayesian_pipeline(_medical_problem())

        scores = score_pipeline_run(
            result.trace,
            ground_truth="nonexistent_hypothesis",
            belief_argmax=bayes_argmax,
            belief_probability=lambda b, h: b.probabilities.get(h, 0.0),
        )

        assert scores.calibration == float("-inf")

    def test_power_false_through_scorer(self):
        """power = False when ontology doesn't cover all evidence."""
        result = run_bayesian_pipeline(_medical_problem())

        def always_inadequate(
            _ontology: BayesOntology, _evidence: tuple[Observation, ...],
        ) -> bool:
            return False

        scores = score_pipeline_run(
            result.trace,
            ground_truth="flu",
            belief_argmax=bayes_argmax,
            ontology_adequate=always_inadequate,
        )

        assert scores.power is False

    def test_heuristic_cost_passed_through(self):
        """Heuristic cost is passed as a parameter."""
        result = run_bayesian_pipeline(_medical_problem())

        scores = score_pipeline_run(
            result.trace,
            ground_truth="flu",
            belief_argmax=bayes_argmax,
            heuristic_cost=42,
        )

        assert scores.efficiency_heuristic_cost == 42

    def test_heuristic_cost_defaults_to_zero(self):
        """Heuristic cost defaults to 0 when not provided."""
        result = run_bayesian_pipeline(_medical_problem())

        scores = score_pipeline_run(
            result.trace,
            ground_truth="flu",
            belief_argmax=bayes_argmax,
        )

        assert scores.efficiency_heuristic_cost == 0


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
