"""Meta-epistemic layer: monitors reasoning and decides how to proceed.

Evaluates the pipeline trace, norm scores, ontology adequacy, and
anomalies. Returns one of four decisions: ACCEPT, REFRAME,
SWITCH_STRATEGY, or ESCALATE. Priority order ensures safety:
escalation beats reframing beats strategy switching.
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
    """

    reliability_min: float = 0.5
    efficiency_ratio_max: float = 2.0
    expected_efficiency: int = 10


class MetaController:
    """Meta-epistemic controller with functional decision logic.

    Evaluates triggers in priority order:
    1. ESCALATE — repeated contradictions.
    2. REFRAME — ontology inadequate or reliability too low.
    3. SWITCH_STRATEGY — efficiency too high or oscillation.
    4. ACCEPT — no triggers fired.
    """

    def __init__(self, thresholds: MetaThresholds | None = None) -> None:
        """Initialize with optional thresholds.

        Args:
            thresholds: decision boundaries. Uses defaults if None.
        """
        self.thresholds = thresholds or MetaThresholds()

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

    def monitor(
        self,
        trace: tuple[object, ...],
        scores: NormScore | object | None,
        ontology: object,
        strategy: str,
        decomposition: tuple[str, ...],
    ) -> MetaResult:
        """Evaluate the current pipeline state and decide how to proceed.

        Args:
            trace: sequence of EpistemicStates from the run.
            scores: norm scores. Can be NormScore, dict, or None.
            ontology: the current ontology.
            strategy: the current reasoning strategy name.
            decomposition: sub-problems from the Decompose stage.

        Returns:
            MetaResult with decision and details.
        """
        anomalies = self._collect_anomalies(trace)

        # Import NormScore at runtime to avoid circular import.
        from epistemic_pipeline.norms import NormScore as _NormScore

        norm: _NormScore | None = None
        if isinstance(scores, _NormScore):
            norm = scores

        # 1. ESCALATE: repeated contradictions
        contradiction_count = anomalies.count("contradiction")
        if contradiction_count >= 2:
            return MetaResult(
                decision=MetaDecision.ESCALATE,
                details={
                    "trigger": "repeated_contradictions",
                    "contradiction_count": contradiction_count,
                },
            )

        # 2. REFRAME: ontology inadequate or low reliability
        if norm is not None:
            if norm.power is False:
                return MetaResult(
                    decision=MetaDecision.REFRAME,
                    details={
                        "trigger": "ontology_inadequate",
                        "power": norm.power,
                    },
                )
            if norm.reliability < self.thresholds.reliability_min:
                return MetaResult(
                    decision=MetaDecision.REFRAME,
                    details={
                        "trigger": "low_reliability",
                        "reliability": norm.reliability,
                        "threshold": self.thresholds.reliability_min,
                    },
                )

        # 3. SWITCH_STRATEGY: high efficiency cost or oscillation
        if norm is not None:
            max_eff = (
                self.thresholds.efficiency_ratio_max
                * self.thresholds.expected_efficiency
            )
            if norm.efficiency > max_eff:
                return MetaResult(
                    decision=MetaDecision.SWITCH_STRATEGY,
                    details={
                        "trigger": "high_efficiency",
                        "efficiency": norm.efficiency,
                        "threshold": max_eff,
                    },
                )

        if "oscillation" in anomalies:
            return MetaResult(
                decision=MetaDecision.SWITCH_STRATEGY,
                details={"trigger": "oscillation"},
            )

        # 4. ACCEPT: default
        return MetaResult(decision=MetaDecision.ACCEPT)
