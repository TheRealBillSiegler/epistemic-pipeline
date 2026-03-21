"""Tests for v1.0 adaptive meta-layer.

Intervention budget, cycle detection, and new triggers.
"""

from epistemic_pipeline.meta import MetaController, MetaDecision, MetaThresholds
from epistemic_pipeline.norms import NormScore
from epistemic_pipeline.state import EpistemicState, Metadata


def _state_with_anomalies(*anomalies: str) -> EpistemicState[None, None]:
    """Helper: create a minimal state with given anomalies."""
    return EpistemicState(
        ontology=None,
        evidence=(),
        beliefs=None,
        revision_policy=lambda b, _e, _o: b,
        metadata=Metadata(anomalies=anomalies),
    )


class TestBudget:
    """Intervention budget: unconditional ESCALATE at K_max."""

    def test_budget_exhaustion_escalates(self):
        controller = MetaController(thresholds=MetaThresholds(max_interventions=2))
        # Use up budget with 2 SWITCH_STRATEGY triggers
        s = _state_with_anomalies("oscillation")
        controller.monitor((s,), None, None, "b", ())
        controller.monitor((s,), None, None, "b", ())
        # 3rd call should hit budget
        result = controller.monitor((s,), None, None, "b", ())
        assert result.decision == MetaDecision.ESCALATE
        assert result.details["trigger"] == "budget_exhausted"

    def test_accept_does_not_increment_budget(self):
        controller = MetaController(thresholds=MetaThresholds(max_interventions=2))
        # ACCEPT decisions don't count
        controller.monitor((), None, None, "b", ())
        controller.monitor((), None, None, "b", ())
        controller.monitor((), None, None, "b", ())
        # Still at 0 interventions, next non-ACCEPT should work
        s = _state_with_anomalies("oscillation")
        result = controller.monitor((s,), None, None, "b", ())
        assert result.decision == MetaDecision.SWITCH_STRATEGY

    def test_budget_beats_everything(self):
        controller = MetaController(thresholds=MetaThresholds(max_interventions=1))
        s = _state_with_anomalies("oscillation")
        controller.monitor((s,), None, None, "b", ())  # uses budget
        # Even with causal_inconsistency (normally ESCALATE), budget wins
        s2 = _state_with_anomalies("causal_inconsistency")
        result = controller.monitor((s2,), None, None, "b", ())
        assert result.decision == MetaDecision.ESCALATE
        assert result.details["trigger"] == "budget_exhausted"


class TestCycleDetection:
    """Cycle: same (trigger, corrective_action) pair recurring."""

    def test_cycle_detected(self):
        controller = MetaController(thresholds=MetaThresholds(max_interventions=10))
        s = _state_with_anomalies("oscillation")
        # First oscillation -> SWITCH_STRATEGY
        r1 = controller.monitor((s,), None, None, "b", ())
        assert r1.decision == MetaDecision.SWITCH_STRATEGY
        # Same trigger again -> cycle detected -> ESCALATE
        r2 = controller.monitor((s,), None, None, "b", ())
        assert r2.decision == MetaDecision.ESCALATE
        assert r2.details["trigger"] == "cycle_detected"

    def test_no_cycle_different_triggers(self):
        """Two different triggers are NOT a cycle."""
        controller = MetaController(thresholds=MetaThresholds(max_interventions=10))
        # First: oscillation -> SWITCH with corrective "switch_strategy"
        s1 = _state_with_anomalies("oscillation")
        controller.monitor((s1,), None, None, "b", ())
        # Second: tool_disagreement -> SWITCH with corrective "request_tool_evidence"
        s2 = _state_with_anomalies("tool_disagreement")
        r2 = controller.monitor((s2,), None, None, "b", ())
        # Different corrective action -> not a cycle
        assert r2.decision == MetaDecision.SWITCH_STRATEGY

    def test_no_cycle_different_reasons_same_decision(self):
        """Two REFRAMEs for different reasons are NOT a cycle."""
        controller = MetaController(thresholds=MetaThresholds(max_interventions=10))
        # First: inadequate ontology -> REFRAME with corrective "reframe_ontology"
        r1 = controller.monitor(
            (), NormScore(reliability=0.9, efficiency=5, justification=True, power=False),
            None, "b", ()
        )
        assert r1.decision == MetaDecision.REFRAME
        # Second: paradigm_mismatch -> REFRAME with corrective "switch_paradigm"
        s2 = _state_with_anomalies("paradigm_mismatch")
        r2 = controller.monitor(
            (s2,), NormScore(reliability=0.9, efficiency=5, justification=True, power=True),
            None, "b", ()
        )
        assert r2.decision == MetaDecision.REFRAME  # not ESCALATE


class TestNewTriggers:
    """v1.0 triggers: paradigm_mismatch, tool/llm disagreement, causal, value_divergence."""

    def test_causal_inconsistency_escalates(self):
        controller = MetaController(thresholds=MetaThresholds(max_interventions=10))
        s = _state_with_anomalies("causal_inconsistency")
        result = controller.monitor((s,), None, None, "b", ())
        assert result.decision == MetaDecision.ESCALATE

    def test_paradigm_mismatch_reframes(self):
        controller = MetaController(thresholds=MetaThresholds(max_interventions=10))
        s = _state_with_anomalies("paradigm_mismatch")
        result = controller.monitor((s,), None, None, "b", ())
        assert result.decision == MetaDecision.REFRAME
        assert result.details["corrective_action"] == "switch_paradigm"

    def test_tool_disagreement_switches(self):
        controller = MetaController(thresholds=MetaThresholds(max_interventions=10))
        s = _state_with_anomalies("tool_disagreement")
        result = controller.monitor((s,), None, None, "b", ())
        assert result.decision == MetaDecision.SWITCH_STRATEGY
        assert result.details["corrective_action"] == "request_tool_evidence"

    def test_llm_disagreement_switches(self):
        controller = MetaController(thresholds=MetaThresholds(max_interventions=10))
        s = _state_with_anomalies("llm_disagreement")
        result = controller.monitor((s,), None, None, "b", ())
        assert result.decision == MetaDecision.SWITCH_STRATEGY
        assert result.details["corrective_action"] == "request_llm_proposal"

    def test_value_divergence_switches(self):
        controller = MetaController(thresholds=MetaThresholds(max_interventions=10))
        s = _state_with_anomalies("value_divergence")
        result = controller.monitor((s,), None, None, "b", ())
        assert result.decision == MetaDecision.SWITCH_STRATEGY

    def test_causal_beats_reframe(self):
        """ESCALATE from causal_inconsistency beats REFRAME from inadequacy."""
        controller = MetaController(thresholds=MetaThresholds(max_interventions=10))
        s = _state_with_anomalies("causal_inconsistency", "paradigm_mismatch")
        result = controller.monitor(
            (s,), NormScore(reliability=0.9, efficiency=5, justification=True, power=False),
            None, "b", ()
        )
        assert result.decision == MetaDecision.ESCALATE


class TestCorrectiveActions:
    """Every non-ACCEPT result includes corrective_action in details."""

    def test_reframe_has_corrective_action(self):
        controller = MetaController(thresholds=MetaThresholds(max_interventions=10))
        result = controller.monitor(
            (), NormScore(reliability=0.9, efficiency=5, justification=True, power=False),
            None, "b", ()
        )
        assert "corrective_action" in result.details

    def test_switch_has_corrective_action(self):
        controller = MetaController(thresholds=MetaThresholds(max_interventions=10))
        s = _state_with_anomalies("oscillation")
        result = controller.monitor((s,), None, None, "b", ())
        assert "corrective_action" in result.details
