"""Meta-epistemic layer: monitors reasoning and decides how to proceed.

Evaluates the pipeline trace, norm scores, ontology adequacy, and
anomalies. Returns one of four decisions: ACCEPT, REFRAME,
SWITCH_STRATEGY, or ESCALATE. Priority order ensures safety:
budget exhaustion beats cycle detection beats escalation beats
reframing beats strategy switching.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from epistemic_pipeline.norms import NormScore


class MetaDecision(Enum):
    """What the meta-layer can decide about the current reasoning state.

    ACCEPT: reasoning is on track, continue.
    REFRAME: the ontology needs restructuring.
    SWITCH_STRATEGY: try a different reasoning strategy.
    ESCALATE: the problem is beyond current capabilities.
    """

    ACCEPT = "ACCEPT"
    REFRAME = "REFRAME"
    SWITCH_STRATEGY = "SWITCH_STRATEGY"
    ESCALATE = "ESCALATE"


@dataclass(frozen=True)
class MetaResult:
    """Result from the meta-epistemic monitor.

    decision: which action to take.
    details: additional context about why this decision was made.
    """

    decision: MetaDecision
    details: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class MetaThresholds:
    """Configuration for meta-layer decision boundaries.

    reliability_min: below this reliability, trigger REFRAME.
    efficiency_ratio_max: if efficiency > ratio * expected, trigger SWITCH.
    expected_efficiency: baseline expected trace length.
    value_divergence_threshold: minimum value divergence to trigger SWITCH.
    max_interventions: maximum non-ACCEPT decisions before forced ESCALATE.
        This is K_max in the spec.
    """

    reliability_min: float = 0.5
    efficiency_ratio_max: float = 2.0
    expected_efficiency: int = 10
    value_divergence_threshold: float = 0.01
    max_interventions: int = 5


_MIN_CONTRADICTIONS_FOR_ESCALATE = 2


class MetaController:
    """Meta-epistemic controller with functional decision logic.

    Evaluates triggers in priority order:
    1. Budget exhaustion — k >= K_max.
    2. Cycle detection — same (trigger, corrective_action) pair recurring.
    3. ESCALATE — repeated contradictions or causal_inconsistency.
    4. REFRAME — ontology inadequate, low reliability, or paradigm_mismatch.
    5. SWITCH_STRATEGY — high efficiency, oscillation, tool/llm disagreement,
       or value_divergence.
    6. ACCEPT — no triggers fired.

    Attributes:
        thresholds: decision boundaries for all triggers.
        intervention_count: number of non-ACCEPT decisions so far.
        last_trigger: the (trigger_type, corrective_action) pair from the
            most recent non-ACCEPT decision. None if no intervention yet.
    """

    def __init__(self, thresholds: MetaThresholds | None = None) -> None:
        """Initialize with optional thresholds.

        Args:
            thresholds: decision boundaries. Uses defaults if None.
        """
        self.thresholds = thresholds or MetaThresholds()
        self.intervention_count: int = 0
        self.last_trigger: tuple[str, str] | None = None

    def _collect_anomalies(
        self, trace: tuple[object, ...],
    ) -> tuple[str, ...]:
        """Collect anomalies from all states in the trace."""
        anomalies: list[str] = []
        for state in trace:
            meta = getattr(state, "metadata", None)
            if meta is not None:
                anomalies.extend(getattr(meta, "anomalies", ()))
        return tuple(anomalies)

    def _record_intervention(self, trigger_type: str, corrective_action: str) -> None:
        """Update mutable state after a non-ACCEPT decision.

        Args:
            trigger_type: the trigger key (e.g., "oscillation").
            corrective_action: the corrective action taken.
        """
        self.intervention_count += 1
        self.last_trigger = (trigger_type, corrective_action)

    def monitor(
        self,
        trace: tuple[object, ...],
        scores: NormScore | object | None,
        _ontology: object,
        _strategy: str,
        _decomposition: tuple[str, ...],
    ) -> MetaResult:
        """Evaluate the current pipeline state and decide how to proceed.

        Args:
            trace: sequence of EpistemicStates from the run.
            scores: norm scores. Can be NormScore, dict, or None.
            _ontology: the current ontology (reserved for future use).
            _strategy: the current reasoning strategy name (reserved).
            _decomposition: sub-problems from the Decompose stage (reserved).

        Returns:
            MetaResult with decision and details.
        """
        anomalies = self._collect_anomalies(trace)

        # Import NormScore at runtime to avoid circular import.
        from epistemic_pipeline.norms import NormScore as _NormScore  # noqa: PLC0415

        norm: _NormScore | None = None
        if isinstance(scores, _NormScore):
            norm = scores

        # 1. Budget exhaustion: unconditional ESCALATE when K_max reached.
        if self.intervention_count >= self.thresholds.max_interventions:
            return MetaResult(
                decision=MetaDecision.ESCALATE,
                details={
                    "trigger": "budget_exhausted",
                    "corrective_action": "escalate",
                    "intervention_count": self.intervention_count,
                },
            )

        # 2. Cycle detection: same (trigger, corrective_action) pair as last time.
        # We need to peek at what trigger would fire before committing.
        # We do this by computing the pending trigger first.
        pending = self._compute_trigger(anomalies, norm)
        if pending is not None:
            trigger_type, corrective_action = pending
            if self.last_trigger == (trigger_type, corrective_action):
                self._record_intervention("cycle_detected", "escalate")
                return MetaResult(
                    decision=MetaDecision.ESCALATE,
                    details={
                        "trigger": "cycle_detected",
                        "corrective_action": "escalate",
                        "repeated_trigger": trigger_type,
                    },
                )
            result = self._make_result(trigger_type, corrective_action, anomalies, norm)
            self._record_intervention(trigger_type, corrective_action)
            return result

        # 6. ACCEPT: default — no trigger fired, no state update.
        return MetaResult(decision=MetaDecision.ACCEPT)

    def _compute_trigger(
        self,
        anomalies: tuple[str, ...],
        norm: NormScore | None,
    ) -> tuple[str, str] | None:
        """Return (trigger_type, corrective_action) for the highest-priority trigger.

        Returns None if no trigger fires (ACCEPT case).

        Args:
            anomalies: all anomalies collected from the trace.
            norm: parsed NormScore, or None if scores were not a NormScore.

        Returns:
            A (trigger_type, corrective_action) pair, or None.
        """
        max_eff = (
            self.thresholds.efficiency_ratio_max * self.thresholds.expected_efficiency
        )
        # Each check is (condition, trigger_type, corrective_action).
        # Evaluated in priority order; first match wins.
        checks: list[tuple[bool, str, str]] = [
            # 3. ESCALATE
            (
                anomalies.count("contradiction") >= _MIN_CONTRADICTIONS_FOR_ESCALATE,
                "repeated_contradictions",
                "escalate",
            ),
            ("causal_inconsistency" in anomalies, "causal_inconsistency", "escalate"),
            # 4. REFRAME
            (norm is not None and norm.power is False, "ontology_inadequate", "reframe_ontology"),
            (
                norm is not None and norm.reliability < self.thresholds.reliability_min,
                "low_reliability",
                "reframe_ontology",
            ),
            ("paradigm_mismatch" in anomalies, "paradigm_mismatch", "switch_paradigm"),
            # 5. SWITCH_STRATEGY
            (norm is not None and norm.efficiency > max_eff, "high_efficiency", "switch_strategy"),
            ("oscillation" in anomalies, "oscillation", "switch_strategy"),
            ("tool_disagreement" in anomalies, "tool_disagreement", "request_tool_evidence"),
            ("llm_disagreement" in anomalies, "llm_disagreement", "request_llm_proposal"),
            ("value_divergence" in anomalies, "value_divergence", "switch_strategy"),
        ]
        for condition, trigger_type, corrective_action in checks:
            if condition:
                return (trigger_type, corrective_action)
        return None

    def _make_result(
        self,
        trigger_type: str,
        corrective_action: str,
        anomalies: tuple[str, ...],
        norm: NormScore | None,
    ) -> MetaResult:
        """Build a MetaResult for the given trigger.

        Args:
            trigger_type: the trigger key (e.g., "oscillation").
            corrective_action: the corrective action for this trigger.
            anomalies: all anomalies from the trace (for extra detail).
            norm: parsed NormScore, or None.

        Returns:
            A MetaResult with decision, trigger, and corrective_action.
        """
        base: dict[str, object] = {
            "trigger": trigger_type,
            "corrective_action": corrective_action,
        }

        # Add trigger-specific detail fields.
        if trigger_type == "repeated_contradictions":
            base["contradiction_count"] = anomalies.count("contradiction")
        elif trigger_type == "ontology_inadequate":
            base["power"] = norm.power if norm is not None else None
        elif trigger_type == "low_reliability":
            base["reliability"] = norm.reliability if norm is not None else None
            base["threshold"] = self.thresholds.reliability_min
        elif trigger_type == "high_efficiency":
            max_eff = (
                self.thresholds.efficiency_ratio_max * self.thresholds.expected_efficiency
            )
            base["efficiency"] = norm.efficiency if norm is not None else None
            base["threshold"] = max_eff

        # Map trigger to decision.
        _escalate = {"repeated_contradictions", "causal_inconsistency"}
        _reframe = {"ontology_inadequate", "low_reliability", "paradigm_mismatch"}
        if trigger_type in _escalate:
            decision = MetaDecision.ESCALATE
        elif trigger_type in _reframe:
            decision = MetaDecision.REFRAME
        else:
            decision = MetaDecision.SWITCH_STRATEGY

        return MetaResult(decision=decision, details=base)
