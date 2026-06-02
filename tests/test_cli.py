"""Tests for the epc CLI (v1.1)."""

import io
import json
from pathlib import Path

import pytest

from epistemic_pipeline.cli import (
    EXIT_BAD_INPUT,
    EXIT_OK,
    EXIT_SCORE_FAIL,
    main,
    print_diff,
    print_replay,
    print_score,
)
from epistemic_pipeline.encodings.bayes import BayesProblem, run_bayesian_pipeline
from epistemic_pipeline.encodings.llm_agent import (
    LLMAgentProblem,
    run_llm_agent_pipeline,
)
from epistemic_pipeline.llm.llm_interfaces import LLMResponse, MockRatingLLM
from epistemic_pipeline.state import EvidenceType, Observation
from epistemic_pipeline.tools.tool_interfaces import MockTool, ToolResult
from epistemic_pipeline.trace import dump_trace


def _bayes_trace(path: Path):
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
    result = run_bayesian_pipeline(problem)
    dump_trace(result, path)
    return result


def _llm_agent_trace(
    path: Path,
    *,
    confidence_values: tuple[float, float] = (0.95, 0.05),
):
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
                content=json.dumps(
                    {"a": confidence_values[0], "b": confidence_values[1]},
                ),
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
    dump_trace(result, path)
    return result


class TestReplay:
    def test_replay_bayes_prints_steps(self, tmp_path: Path):
        path = tmp_path / "b.jsonl"
        result = _bayes_trace(path)
        stream = io.StringIO()
        print_replay(result, stream)
        output = stream.getvalue()
        assert "Step 0" in output
        assert "flu" in output
        assert "cold" in output

    def test_replay_llm_agent_shows_evidence(self, tmp_path: Path):
        path = tmp_path / "l.jsonl"
        result = _llm_agent_trace(path)
        stream = io.StringIO()
        print_replay(result, stream)
        output = stream.getvalue()
        assert "a:" in output  # confidence for "a"
        assert "tool_choice" in output or "lookup" in output


class TestDiff:
    def test_diff_identical_traces(self, tmp_path: Path):
        path = tmp_path / "x.jsonl"
        result = _llm_agent_trace(path)
        stream = io.StringIO()
        print_diff(result, result, stream)
        assert "identical" in stream.getvalue()

    def test_diff_finds_divergence(self, tmp_path: Path):
        path_a = tmp_path / "a.jsonl"
        path_b = tmp_path / "b.jsonl"
        result_a = _llm_agent_trace(
            path_a, confidence_values=(0.95, 0.05),
        )
        result_b = _llm_agent_trace(
            path_b, confidence_values=(0.05, 0.95),
        )
        stream = io.StringIO()
        print_diff(result_a, result_b, stream)
        output = stream.getvalue()
        assert "divergence" in output
        assert "a beliefs" in output
        assert "b beliefs" in output


class TestScore:
    def test_score_without_truth(self, tmp_path: Path):
        path = tmp_path / "x.jsonl"
        result = _llm_agent_trace(path)
        stream = io.StringIO()
        code = print_score(result, truth=None, stream=stream)
        assert code == EXIT_OK
        assert "n/a" in stream.getvalue()

    def test_score_with_correct_truth(self, tmp_path: Path):
        path = tmp_path / "x.jsonl"
        result = _llm_agent_trace(path)
        stream = io.StringIO()
        code = print_score(result, truth="a", stream=stream)
        assert code == EXIT_OK
        assert "Reliability:  1.00" in stream.getvalue()

    def test_score_with_wrong_truth_fails(self, tmp_path: Path):
        path = tmp_path / "x.jsonl"
        result = _llm_agent_trace(path)
        stream = io.StringIO()
        code = print_score(result, truth="b", stream=stream)
        assert code == EXIT_SCORE_FAIL


class TestMain:
    def test_replay_via_main(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]):
        path = tmp_path / "x.jsonl"
        _bayes_trace(path)
        code = main(["replay", str(path)])
        assert code == EXIT_OK
        captured = capsys.readouterr()
        assert "Step 0" in captured.out

    def test_missing_file_exits(self):
        with pytest.raises(SystemExit) as exc:
            main(["replay", "does_not_exist.jsonl"])
        assert exc.value.code == EXIT_BAD_INPUT

    def test_score_via_main(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]):
        path = tmp_path / "x.jsonl"
        _llm_agent_trace(path)
        code = main(["score", str(path), "--truth", "a"])
        assert code == EXIT_OK
        out = capsys.readouterr().out
        assert "Reliability" in out
