"""Tests for the meta-epistemic layer.

v0.1: the meta-controller always returns ACCEPT.
"""

from epistemic_pipeline.meta import MetaController, MetaDecision, MetaResult


class TestMetaController:
    def test_always_returns_accept(self):
        controller = MetaController()
        result = controller.monitor((), None, None, "bayesian", ())
        assert result.decision == MetaDecision.ACCEPT

    def test_returns_meta_result_type(self):
        controller = MetaController()
        result = controller.monitor((), None, None, "test", ("sub1", "sub2"))
        assert isinstance(result, MetaResult)
        assert result.details == {}

    def test_meta_decision_enum_values(self):
        assert MetaDecision.ACCEPT.value == "ACCEPT"
        assert MetaDecision.REFRAME.value == "REFRAME"
        assert MetaDecision.SWITCH_STRATEGY.value == "SWITCH_STRATEGY"
        assert MetaDecision.ESCALATE.value == "ESCALATE"

    def test_accept_regardless_of_inputs(self):
        controller = MetaController()
        result = controller.monitor(
            (object(), object(), object()),
            {"reliability": 0.0},
            {"symbols": []},
            "unknown",
            ("a", "b", "c"),
        )
        assert result.decision == MetaDecision.ACCEPT
