"""Tests for trace persistence (v1.1)."""

import json
from pathlib import Path

import pytest

from epistemic_pipeline.encodings.bayes import BayesProblem, run_bayesian_pipeline
from epistemic_pipeline.encodings.llm_agent import (
    LLMAgentProblem,
    run_llm_agent_pipeline,
)
from epistemic_pipeline.encodings.mdp import MDPProblem, run_mdp_pipeline
from epistemic_pipeline.encodings.strips import (
    STRIPSAction,
    STRIPSProblem,
    run_strips_pipeline,
)
from epistemic_pipeline.llm.llm_interfaces import LLMResponse, MockRatingLLM
from epistemic_pipeline.state import EvidenceType, Observation
from epistemic_pipeline.tools.tool_interfaces import MockTool, ToolResult
from epistemic_pipeline.trace import dump_trace, load_trace


def _bayes_result():
    problem = BayesProblem(
        hypotheses=("flu", "cold"),
        observables=("fever",),
        likelihoods={
            ("flu", "fever", "true"): 0.8,
            ("cold", "fever", "true"): 0.3,
        },
        observations=(
            Observation(
                variable="fever",
                value="true",
                source="thermometer",
                timestamp=0.0,
                etype=EvidenceType.MEASUREMENT,
            ),
        ),
    )
    return run_bayesian_pipeline(problem)


def _strips_result():
    actions = (
        STRIPSAction(
            name="pickup_A",
            preconditions=frozenset({"clear_A", "ontable_A", "handempty"}),
            add_effects=frozenset({"holding_A"}),
            delete_effects=frozenset({"clear_A", "ontable_A", "handempty"}),
        ),
    )
    problem = STRIPSProblem(
        predicates=frozenset({
            "clear_A", "ontable_A", "handempty", "holding_A",
        }),
        actions=actions,
        initial_state=frozenset({"clear_A", "ontable_A", "handempty"}),
        goal=frozenset({"holding_A"}),
        max_search_steps=10,
    )
    return run_strips_pipeline(problem)


def _mdp_result():
    states = frozenset({"s0", "s1"})
    actions = ("a",)
    transitions = {("s0", "a", "s1"): 1.0, ("s1", "a", "s1"): 1.0}
    rewards = {("s0", "a"): 0.0, ("s1", "a"): 1.0}
    problem = MDPProblem(
        states=states,
        actions=actions,
        transitions=transitions,
        rewards=rewards,
        discount=0.9,
        terminal_states=frozenset(),
        max_iterations=20,
    )
    return run_mdp_pipeline(problem)


def _llm_agent_result():
    tools = {
        "lookup": MockTool({
            "lookup": ToolResult(
                name="lookup", output={"x": "y"}, success=True,
            ),
        }),
    }
    llm = MockRatingLLM(
        responses={},
        tool_picks=[
            LLMResponse(
                content=json.dumps({"tool": "lookup", "args": {}}),
                confidence=1.0,
            ),
        ],
        confidence_ratings=[
            LLMResponse(
                content=json.dumps({"a": 0.95, "b": 0.05}),
                confidence=1.0,
            ),
        ],
    )
    problem = LLMAgentProblem(
        question="q",
        hypotheses=("a", "b"),
        tools=tools,
        llm=llm,
        max_steps=1,
    )
    return run_llm_agent_pipeline(problem)


class TestRoundTrip:
    def test_bayes_round_trip(self, tmp_path: Path):
        result = _bayes_result()
        path = tmp_path / "bayes.jsonl"
        dump_trace(result, path)
        loaded = load_trace(path)
        assert len(loaded.trace) == len(result.trace)
        for original, restored in zip(result.trace, loaded.trace, strict=True):
            assert (
                restored.beliefs.probabilities
                == original.beliefs.probabilities
            )
            assert (
                restored.ontology.hypotheses
                == original.ontology.hypotheses
            )
            assert restored.evidence == original.evidence
            assert restored.metadata.strategy == original.metadata.strategy

    def test_strips_round_trip(self, tmp_path: Path):
        result = _strips_result()
        path = tmp_path / "strips.jsonl"
        dump_trace(result, path)
        loaded = load_trace(path)
        assert len(loaded.trace) == len(result.trace)
        final_original = result.final_state
        final_loaded = loaded.final_state
        assert final_loaded.beliefs.plan == final_original.beliefs.plan
        assert (
            final_loaded.beliefs.current_state
            == final_original.beliefs.current_state
        )
        assert final_loaded.ontology.goal == final_original.ontology.goal

    def test_mdp_round_trip(self, tmp_path: Path):
        result = _mdp_result()
        path = tmp_path / "mdp.jsonl"
        dump_trace(result, path)
        loaded = load_trace(path)
        assert len(loaded.trace) == len(result.trace)
        original_vf = dict(result.final_state.beliefs.value_function)
        loaded_vf = dict(loaded.final_state.beliefs.value_function)
        assert loaded_vf == original_vf
        assert (
            loaded.final_state.beliefs.converged
            == result.final_state.beliefs.converged
        )

    def test_llm_agent_round_trip(self, tmp_path: Path):
        result = _llm_agent_result()
        path = tmp_path / "llm.jsonl"
        dump_trace(result, path)
        loaded = load_trace(path)
        assert len(loaded.trace) == len(result.trace)
        assert (
            loaded.final_state.beliefs.confidences
            == result.final_state.beliefs.confidences
        )
        assert (
            loaded.final_state.ontology.hypotheses
            == result.final_state.ontology.hypotheses
        )
        assert (
            loaded.final_state.ontology.inadequate
            == result.final_state.ontology.inadequate
        )
        assert loaded.final_state.evidence == result.final_state.evidence


class TestErrors:
    def test_empty_file_raises(self, tmp_path: Path):
        path = tmp_path / "empty.jsonl"
        path.write_text("")
        with pytest.raises(ValueError, match="empty"):
            load_trace(path)

    def test_missing_header_raises(self, tmp_path: Path):
        path = tmp_path / "no_header.jsonl"
        path.write_text(json.dumps({"kind": "state"}) + "\n")
        with pytest.raises(ValueError, match="not a header"):
            load_trace(path)

    def test_unknown_encoding_raises(self, tmp_path: Path):
        path = tmp_path / "unknown.jsonl"
        path.write_text(
            json.dumps({
                "kind": "header",
                "encoding": "made_up",
                "version": "1.1",
                "meta_decision": {"decision": "accept", "details": {}},
            }) + "\n",
        )
        with pytest.raises(ValueError, match="not registered"):
            load_trace(path)

    def test_search_encoding_rejected(self):
        from collections.abc import Callable

        from epistemic_pipeline.encodings.search import (
            SearchOperator,
            SearchProblem,
            run_search_pipeline,
        )

        def applicable(_state: str) -> bool:
            return True

        def apply_op(state: str) -> str:
            return state

        def cost(_state: str) -> float:
            return 1.0

        def heuristic(_state: str) -> float:
            return 0.0

        def goal_test(state: str) -> bool:
            return state == "B"

        op: Callable[..., SearchOperator] = SearchOperator
        problem = SearchProblem(
            states=frozenset({"A", "B"}),
            operators=(
                op(
                    name="move",
                    applicable=applicable,
                    apply=apply_op,
                    cost=cost,
                ),
            ),
            initial_state="A",
            goal_test=goal_test,
            heuristic=heuristic,
            max_search_steps=2,
        )
        result = run_search_pipeline(problem)
        with pytest.raises(ValueError, match="astar_search"):
            dump_trace(result, "/tmp/should_not_write.jsonl")  # noqa: S108
