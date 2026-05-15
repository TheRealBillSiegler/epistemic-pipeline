"""Tests for the LLM-agent encoding (v1.1)."""

import json

import pytest

from epistemic_pipeline.encodings.llm_agent import (
    LLMAgentBeliefs,
    LLMAgentOntology,
    LLMAgentProblem,
    llm_agent_argmax,
    llm_agent_update,
    run_llm_agent_pipeline,
)
from epistemic_pipeline.llm.llm_interfaces import LLMResponse, MockRatingLLM
from epistemic_pipeline.state import EvidenceType, Observation
from epistemic_pipeline.tools.tool_interfaces import MockTool, ToolResult


def _obs(value: str, confidence: float = 1.0) -> Observation:
    return Observation(
        variable="confidence_vector",
        value=value,
        source="llm",
        timestamp=0.0,
        confidence=confidence,
        etype=EvidenceType.REPORT,
        modality="llm",
    )


class TestRevisionPolicy:
    def test_full_coverage_normalizes(self):
        ont = LLMAgentOntology(hypotheses=("a", "b"), tools=())
        beliefs = LLMAgentBeliefs(confidences={"a": 0.5, "b": 0.5})
        evidence = _obs(json.dumps({"a": 0.8, "b": 0.2}))
        out = llm_agent_update(beliefs, evidence, ont)
        assert out.confidences["a"] == pytest.approx(0.8)
        assert out.confidences["b"] == pytest.approx(0.2)

    def test_partial_coverage_renormalizes(self):
        ont = LLMAgentOntology(hypotheses=("a", "b"), tools=())
        beliefs = LLMAgentBeliefs(confidences={"a": 0.5, "b": 0.5})
        evidence = _obs(json.dumps({"a": 0.3, "b": 0.3}))
        out = llm_agent_update(beliefs, evidence, ont)
        assert out.confidences["a"] == pytest.approx(0.5)
        assert out.confidences["b"] == pytest.approx(0.5)
        total = sum(out.confidences.values())
        assert total == pytest.approx(1.0)

    def test_unknown_hypothesis_dropped(self):
        ont = LLMAgentOntology(hypotheses=("a", "b"), tools=())
        beliefs = LLMAgentBeliefs(confidences={"a": 0.5, "b": 0.5})
        evidence = _obs(json.dumps({"a": 0.6, "b": 0.3, "c": 0.1}))
        out = llm_agent_update(beliefs, evidence, ont)
        total = sum(out.confidences.values())
        assert total == pytest.approx(1.0)
        assert "c" not in out.confidences
        assert out.confidences["a"] == pytest.approx(0.6 / 0.9)
        assert out.confidences["b"] == pytest.approx(0.3 / 0.9)

    def test_empty_filter_returns_prior(self):
        ont = LLMAgentOntology(hypotheses=("a", "b"), tools=())
        beliefs = LLMAgentBeliefs(confidences={"a": 0.7, "b": 0.3})
        evidence = _obs(json.dumps({"c": 0.9, "d": 0.1}))
        out = llm_agent_update(beliefs, evidence, ont)
        assert out is beliefs

    def test_malformed_json_returns_prior(self):
        ont = LLMAgentOntology(hypotheses=("a", "b"), tools=())
        beliefs = LLMAgentBeliefs(confidences={"a": 0.7, "b": 0.3})
        evidence = _obs("not json")
        out = llm_agent_update(beliefs, evidence, ont)
        assert out is beliefs

    def test_negative_values_clamped_to_zero(self):
        ont = LLMAgentOntology(hypotheses=("a", "b"), tools=())
        beliefs = LLMAgentBeliefs(confidences={"a": 0.5, "b": 0.5})
        evidence = _obs(json.dumps({"a": -0.5, "b": 0.5}))
        out = llm_agent_update(beliefs, evidence, ont)
        assert out.confidences["a"] == pytest.approx(0.0)
        assert out.confidences["b"] == pytest.approx(1.0)


class TestPipelineEndToEnd:
    def test_confidence_threshold_early_stop(self):
        tools = {
            "lookup": MockTool({
                "lookup": ToolResult(
                    name="lookup", output={"answer": "a"}, success=True,
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
            question="pick a",
            hypotheses=("a", "b"),
            tools=tools,
            llm=llm,
            max_steps=10,
            confidence_threshold=0.9,
        )
        result = run_llm_agent_pipeline(problem)
        assert llm_agent_argmax(result.final_state.beliefs) == "a"
        assert result.final_state.beliefs.confidences["a"] >= 0.9

    def test_step_budget_exhaustion(self):
        tool_picks = [
            LLMResponse(
                content=json.dumps({"tool": "lookup", "args": {}}),
                confidence=1.0,
            )
            for _ in range(3)
        ]
        ratings = [
            LLMResponse(
                content=json.dumps({"a": 0.55, "b": 0.45}),
                confidence=1.0,
            )
            for _ in range(3)
        ]
        tools = {
            "lookup": MockTool({
                "lookup": ToolResult(
                    name="lookup", output={"x": "y"}, success=True,
                ),
            }),
        }
        llm = MockRatingLLM(
            responses={},
            tool_picks=tool_picks,
            confidence_ratings=ratings,
        )
        problem = LLMAgentProblem(
            question="q",
            hypotheses=("a", "b"),
            tools=tools,
            llm=llm,
            max_steps=3,
            confidence_threshold=0.99,
        )
        result = run_llm_agent_pipeline(problem)
        assert result.final_state.beliefs.confidences["a"] == pytest.approx(
            0.55,
        )

    def test_ontology_inadequate_flag_set(self):
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
                    content=json.dumps({"a": 0.4, "b": 0.4, "novel": 0.2}),
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
        result = run_llm_agent_pipeline(problem)
        assert result.final_state.ontology.inadequate is True
        assert "ontology_inadequate" in result.final_state.metadata.anomalies

    def test_fiscal_vs_calendar_oscillation(self):
        tools = {
            "lookup_financials": MockTool({
                "lookup_financials": ToolResult(
                    name="lookup_financials",
                    output={"period": "Q4 FY2024", "revenue": "$2.1B"},
                    success=True,
                ),
            }),
            "lookup_recent_news": MockTool({
                "lookup_recent_news": ToolResult(
                    name="lookup_recent_news",
                    output={"headline": "FakeCo reports $2.4B Q4"},
                    success=True,
                ),
            }),
        }
        tool_picks = [
            LLMResponse(
                content=json.dumps(
                    {"tool": "lookup_financials", "args": {"company": "FakeCo"}},
                ),
                confidence=1.0,
            ),
            LLMResponse(
                content=json.dumps(
                    {"tool": "lookup_recent_news", "args": {"q": "FakeCo Q4"}},
                ),
                confidence=1.0,
            ),
            LLMResponse(
                content=json.dumps(
                    {"tool": "lookup_financials", "args": {"company": "FakeCo"}},
                ),
                confidence=1.0,
            ),
            LLMResponse(
                content=json.dumps(
                    {"tool": "lookup_recent_news", "args": {"q": "FakeCo Q4"}},
                ),
                confidence=1.0,
            ),
        ]
        ratings = [
            LLMResponse(
                content=json.dumps({"$2.1B": 0.85, "$2.4B": 0.15}),
                confidence=1.0,
            ),
            LLMResponse(
                content=json.dumps({"$2.1B": 0.30, "$2.4B": 0.70}),
                confidence=1.0,
            ),
            LLMResponse(
                content=json.dumps({"$2.1B": 0.80, "$2.4B": 0.20}),
                confidence=1.0,
            ),
            LLMResponse(
                content=json.dumps({"$2.1B": 0.25, "$2.4B": 0.75}),
                confidence=1.0,
            ),
        ]
        llm = MockRatingLLM(
            responses={},
            tool_picks=tool_picks,
            confidence_ratings=ratings,
        )
        problem = LLMAgentProblem(
            question="What was Q4 2024 revenue for FakeCo?",
            hypotheses=("$2.1B", "$2.4B"),
            tools=tools,
            llm=llm,
            max_steps=4,
            confidence_threshold=0.99,
        )
        result = run_llm_agent_pipeline(problem)
        assert "oscillation" in result.final_state.metadata.anomalies

    def test_trace_records_every_step(self):
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
        result = run_llm_agent_pipeline(problem)
        # Six pipeline stages -> seven trace entries (Frame + 5 stages + 1 for final)
        # Actually run_pipeline trace = initial + len(stages). Frame produces initial,
        # then five stages are applied, giving 1 + 5 = 6 entries.
        assert len(result.trace) == 6
        # Evidence in final state: 1 tool_choice obs + 1 tool obs + 1 confidence obs.
        assert len(result.final_state.evidence) == 3
