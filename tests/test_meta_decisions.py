"""Tests for functional meta-layer decisions.

Each MetaDecision has specific triggers. Tests verify the priority
order: ESCALATE > REFRAME > SWITCH_STRATEGY > ACCEPT.
"""

from epistemic_pipeline.meta import (
    MetaController,
    MetaDecision,
    MetaThresholds,
)
from epistemic_pipeline.norms import NormScore


class TestMetaAccept:
    """ACCEPT is the default when no triggers fire."""

    def test_accept_when_everything_normal(self):
        controller = MetaController()
        result = controller.monitor(
            trace=(),
            scores=NormScore(reliability=0.9, efficiency=5, justification=True, power=True),
            ontology=None,
            strategy="bayesian",
            decomposition=(),
        )
        assert result.decision == MetaDecision.ACCEPT

    def test_accept_when_no_scores(self):
        controller = MetaController()
        result = controller.monitor(
            trace=(),
            scores=None,
            ontology=None,
            strategy="bayesian",
            decomposition=(),
        )
        assert result.decision == MetaDecision.ACCEPT


class TestMetaEscalate:
    """ESCALATE: repeated contradictions (highest priority)."""

    def test_escalate_on_repeated_contradictions(self):
        from epistemic_pipeline.state import EpistemicState, Metadata

        meta = Metadata(anomalies=("contradiction", "contradiction"))
        state = EpistemicState(
            ontology=None,
            evidence=(),
            beliefs=None,
            revision_policy=lambda b, e, o: b,
            metadata=meta,
        )

        controller = MetaController()
        result = controller.monitor(
            trace=(state,),
            scores=NormScore(reliability=0.9, efficiency=5, justification=True, power=True),
            ontology=None,
            strategy="bayesian",
            decomposition=(),
        )
        assert result.decision == MetaDecision.ESCALATE
        assert "contradiction" in str(result.details)

    def test_escalate_beats_reframe(self):
        from epistemic_pipeline.state import EpistemicState, Metadata

        meta = Metadata(anomalies=("contradiction", "contradiction"))
        state = EpistemicState(
            ontology=None, evidence=(), beliefs=None,
            revision_policy=lambda b, e, o: b, metadata=meta,
        )

        controller = MetaController()
        result = controller.monitor(
            trace=(state,),
            scores=NormScore(
                reliability=0.1, efficiency=5, justification=True, power=False,
            ),
            ontology=None,
            strategy="bayesian",
            decomposition=(),
        )
        assert result.decision == MetaDecision.ESCALATE


class TestMetaReframe:
    """REFRAME: ontology inadequate or reliability too low."""

    def test_reframe_when_ontology_inadequate(self):
        controller = MetaController()
        result = controller.monitor(
            trace=(),
            scores=NormScore(
                reliability=0.9, efficiency=5, justification=True, power=False,
            ),
            ontology=None,
            strategy="bayesian",
            decomposition=(),
        )
        assert result.decision == MetaDecision.REFRAME

    def test_reframe_when_reliability_below_threshold(self):
        controller = MetaController(thresholds=MetaThresholds(reliability_min=0.5))
        result = controller.monitor(
            trace=(),
            scores=NormScore(
                reliability=0.3, efficiency=5, justification=True, power=True,
            ),
            ontology=None,
            strategy="bayesian",
            decomposition=(),
        )
        assert result.decision == MetaDecision.REFRAME

    def test_reframe_beats_switch_strategy(self):
        from epistemic_pipeline.state import EpistemicState, Metadata

        meta = Metadata(anomalies=("oscillation",))
        state = EpistemicState(
            ontology=None, evidence=(), beliefs=None,
            revision_policy=lambda b, e, o: b, metadata=meta,
        )

        controller = MetaController()
        result = controller.monitor(
            trace=(state,),
            scores=NormScore(
                reliability=0.9, efficiency=5, justification=True, power=False,
            ),
            ontology=None,
            strategy="bayesian",
            decomposition=(),
        )
        assert result.decision == MetaDecision.REFRAME


class TestMetaSwitchStrategy:
    """SWITCH_STRATEGY: efficiency too high or oscillation detected."""

    def test_switch_on_high_efficiency(self):
        controller = MetaController(
            thresholds=MetaThresholds(
                efficiency_ratio_max=2.0, expected_efficiency=5,
            ),
        )
        result = controller.monitor(
            trace=(),
            scores=NormScore(
                reliability=0.9, efficiency=11, justification=True, power=True,
            ),
            ontology=None,
            strategy="bayesian",
            decomposition=(),
        )
        assert result.decision == MetaDecision.SWITCH_STRATEGY

    def test_switch_on_oscillation(self):
        from epistemic_pipeline.state import EpistemicState, Metadata

        meta = Metadata(anomalies=("oscillation",))
        state = EpistemicState(
            ontology=None, evidence=(), beliefs=None,
            revision_policy=lambda b, e, o: b, metadata=meta,
        )

        controller = MetaController()
        result = controller.monitor(
            trace=(state,),
            scores=NormScore(
                reliability=0.9, efficiency=5, justification=True, power=True,
            ),
            ontology=None,
            strategy="bayesian",
            decomposition=(),
        )
        assert result.decision == MetaDecision.SWITCH_STRATEGY

    def test_switch_on_oscillation_without_scores(self):
        from epistemic_pipeline.state import EpistemicState, Metadata

        meta = Metadata(anomalies=("oscillation",))
        state = EpistemicState(
            ontology=None, evidence=(), beliefs=None,
            revision_policy=lambda b, e, o: b, metadata=meta,
        )

        controller = MetaController()
        result = controller.monitor(
            trace=(state,),
            scores=None,
            ontology=None,
            strategy="bayesian",
            decomposition=(),
        )
        assert result.decision == MetaDecision.SWITCH_STRATEGY


class TestMetaThresholds:
    """MetaThresholds configures decision boundaries."""

    def test_custom_reliability_threshold(self):
        controller = MetaController(
            thresholds=MetaThresholds(reliability_min=0.9),
        )
        result = controller.monitor(
            trace=(),
            scores=NormScore(
                reliability=0.85, efficiency=5, justification=True, power=True,
            ),
            ontology=None,
            strategy="bayesian",
            decomposition=(),
        )
        assert result.decision == MetaDecision.REFRAME

    def test_default_thresholds(self):
        t = MetaThresholds()
        assert t.reliability_min == 0.5
        assert t.efficiency_ratio_max == 2.0
        assert t.expected_efficiency == 10
