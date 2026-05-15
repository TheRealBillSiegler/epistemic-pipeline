"""Command-line interface: ``epc replay | diff | score``.

The CLI reads JSONL trace files written by ``epistemic_pipeline.trace``
and renders them in three ways:

- ``epc replay`` walks the trace step by step.
- ``epc diff`` finds the first step where two traces disagree.
- ``epc score`` scores a trace against the four epistemic norms.

The ``epc run`` command is not in v1.1 because portable serialization of
LLM and tool callables is out of scope. Use the Python API to produce a
trace, then run ``epc replay`` on the result.
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import TYPE_CHECKING, Any, TextIO

from epistemic_pipeline.encodings.bayes import BayesBeliefs, bayes_argmax
from epistemic_pipeline.encodings.llm_agent import (
    LLMAgentBeliefs,
    llm_agent_argmax,
)
from epistemic_pipeline.norms import score_pipeline_run
from epistemic_pipeline.trace import load_trace

if TYPE_CHECKING:
    from epistemic_pipeline.pipeline import PipelineResult
    from epistemic_pipeline.state import EpistemicState

EXIT_OK = 0
EXIT_BAD_INPUT = 1
EXIT_SCORE_FAIL = 2


def _format_beliefs(beliefs: Any) -> str:  # noqa: ANN401
    """Render a beliefs object as a one-line summary.

    Args:
        beliefs: a belief object from any encoding.

    Returns:
        A short ``{name:value, ...}`` string.
    """
    if isinstance(beliefs, LLMAgentBeliefs):
        pairs = sorted(
            beliefs.confidences.items(), key=lambda kv: kv[1], reverse=True,
        )
        return "{" + ", ".join(f"{k}:{v:.2f}" for k, v in pairs) + "}"
    if isinstance(beliefs, BayesBeliefs):
        pairs = sorted(
            beliefs.probabilities.items(), key=lambda kv: kv[1], reverse=True,
        )
        return "{" + ", ".join(f"{k}:{v:.2f}" for k, v in pairs) + "}"
    return str(beliefs)


def _describe_new_evidence(
    prev_evidence: tuple[Any, ...], next_evidence: tuple[Any, ...],
) -> str:
    """Return a short string describing evidence added between two steps.

    Args:
        prev_evidence: evidence tuple in the earlier state.
        next_evidence: evidence tuple in the later state.

    Returns:
        Empty string if no new evidence. Otherwise a comma-separated
        list of new ``modality:variable=value`` entries.
    """
    new_items = next_evidence[len(prev_evidence):]
    if not new_items:
        return ""
    parts = []
    for obs in new_items:
        mod = obs.modality or "obs"
        parts.append(f"{mod}({obs.variable}={obs.value})")
    return ", ".join(parts)


def print_replay(
    result: PipelineResult[Any, Any], stream: TextIO | None = None,
) -> None:
    """Print one line per evidence observation in a trace.

    Walks the evidence list on the final state and re-applies the
    revision policy after each observation. This produces a per-step
    view of how beliefs evolved, which is more useful than the per-
    pipeline-stage view (most stages do not change beliefs).

    Args:
        result: the loaded PipelineResult.
        stream: where to write output. Defaults to stdout.
    """
    out: TextIO = stream if stream is not None else sys.stdout
    initial = result.trace[0]
    beliefs = initial.beliefs
    out.write(f"Step 0   B: {_format_beliefs(beliefs)}\n")
    final = result.final_state
    for i, obs in enumerate(final.evidence, start=1):
        beliefs = final.revision_policy(beliefs, obs, final.ontology)
        mod = obs.modality or "obs"
        out.write(
            f"Step {i}   B: {_format_beliefs(beliefs)}   "
            f"<- {mod}({obs.variable}={obs.value})\n",
        )
    if final.metadata.anomalies:
        out.write(
            f"Anomalies: {','.join(final.metadata.anomalies)}\n",
        )


def _states_disagree(
    a: EpistemicState[Any, Any], b: EpistemicState[Any, Any],
) -> bool:
    return a.evidence != b.evidence or a.beliefs != b.beliefs


def print_diff(
    left: PipelineResult[Any, Any],
    right: PipelineResult[Any, Any],
    stream: TextIO | None = None,
) -> None:
    """Print the first step where two traces disagree.

    Args:
        left: the first loaded result.
        right: the second loaded result.
        stream: where to write output. Defaults to stdout.
    """
    out: TextIO = stream if stream is not None else sys.stdout
    n = min(len(left.trace), len(right.trace))
    for i in range(n):
        if _states_disagree(left.trace[i], right.trace[i]):
            out.write(f"First divergence at step {i}.\n\n")
            out.write("  a evidence:\n")
            out.writelines(f"    {obs.modality}:{obs.variable}={obs.value}\n" for obs in left.trace[i].evidence)
            out.write("  b evidence:\n")
            out.writelines(f"    {obs.modality}:{obs.variable}={obs.value}\n" for obs in right.trace[i].evidence)
            out.write(f"\n  a beliefs: {_format_beliefs(left.trace[i].beliefs)}\n")
            out.write(f"  b beliefs: {_format_beliefs(right.trace[i].beliefs)}\n")
            return
    if len(left.trace) != len(right.trace):
        out.write(
            f"Traces agree for {n} steps; lengths differ "
            f"(a={len(left.trace)}, b={len(right.trace)}).\n",
        )
        return
    out.write("Traces are identical.\n")


def _argmax_for(beliefs: Any) -> str | None:  # noqa: ANN401
    """Return the argmax hypothesis name, or None if unsupported.

    Args:
        beliefs: a belief object from any encoding.

    Returns:
        The argmax hypothesis name, or None if the encoding does not
        support classification-style argmax.
    """
    if isinstance(beliefs, LLMAgentBeliefs):
        return llm_agent_argmax(beliefs)
    if isinstance(beliefs, BayesBeliefs):
        return bayes_argmax(beliefs)
    return None


def _belief_probability(
    beliefs: Any,  # noqa: ANN401
    hypothesis: str,
) -> float | None:
    """Return the probability/confidence of a hypothesis, if defined.

    Args:
        beliefs: a belief object from any encoding.
        hypothesis: the hypothesis name.

    Returns:
        The probability/confidence value, or None if undefined.
    """
    if isinstance(beliefs, LLMAgentBeliefs):
        return beliefs.confidences.get(hypothesis, 0.0)
    if isinstance(beliefs, BayesBeliefs):
        return beliefs.probabilities.get(hypothesis, 0.0)
    return None


def print_score(
    result: PipelineResult[Any, Any],
    truth: str | None,
    stream: TextIO | None = None,
) -> int:
    """Print the NormScore for a loaded trace.

    Args:
        result: the loaded PipelineResult.
        truth: ground-truth hypothesis name. If None, reliability and
            calibration are reported as unavailable.
        stream: where to write output. Defaults to stdout.

    Returns:
        EXIT_SCORE_FAIL if reliability is 0 or contradictions are
        present in metadata; EXIT_OK otherwise.
    """
    out: TextIO = stream if stream is not None else sys.stdout
    final = result.final_state
    argmax_value = _argmax_for(final.beliefs)
    if truth is None or argmax_value is None:
        out.write("Reliability: n/a (no --truth or non-classification encoding)\n")
        out.write(f"Efficiency:  {len(result.trace)} steps\n")
        adequate = final.ontology.adequate(final.evidence)
        out.write(f"Power:       {adequate}\n")
        out.write(
            f"Anomalies:   {','.join(final.metadata.anomalies) or 'none'}\n",
        )
        return (
            EXIT_SCORE_FAIL
            if "contradiction" in final.metadata.anomalies
            else EXIT_OK
        )

    score = score_pipeline_run(
        trace=result.trace,
        ground_truth=truth,
        belief_argmax=lambda b: _argmax_for(b) or "",
        belief_probability=lambda b, h: _belief_probability(b, h) or 0.0,
        ontology_adequate=lambda o, e: o.adequate(e),
    )
    out.write(f"Reliability:  {score.reliability:.2f}\n")
    out.write(f"Calibration:  {score.calibration:.4f}\n")
    out.write(f"Efficiency:   {score.efficiency} steps\n")
    out.write(f"Justification: {score.justification}\n")
    out.write(f"Power:        {score.power}\n")
    out.write(
        f"Anomalies:    {','.join(final.metadata.anomalies) or 'none'}\n",
    )
    if score.reliability < 1.0 or "contradiction" in final.metadata.anomalies:
        return EXIT_SCORE_FAIL
    return EXIT_OK


def _load_or_die(path: str) -> PipelineResult[Any, Any]:
    """Load a trace file, exit with code 1 on failure.

    Args:
        path: filesystem path to a JSONL trace.

    Returns:
        The loaded PipelineResult.
    """
    p = Path(path)
    if not p.exists():
        sys.stderr.write(f"epc: file not found: {path}\n")
        sys.exit(EXIT_BAD_INPUT)
    try:
        return load_trace(p)
    except (OSError, ValueError) as exc:
        sys.stderr.write(f"epc: failed to load {path}: {exc}\n")
        sys.exit(EXIT_BAD_INPUT)


def _build_parser() -> argparse.ArgumentParser:
    """Build the top-level argument parser.

    Returns:
        An argparse parser with the four subcommands attached.
    """
    parser = argparse.ArgumentParser(
        prog="epc",
        description="Epistemic Pipeline CLI: replay, diff, and score traces.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_replay = sub.add_parser("replay", help="Walk a trace step by step.")
    p_replay.add_argument("trace", help="Path to a JSONL trace file.")

    p_diff = sub.add_parser(
        "diff",
        help="Find the first divergence between two traces.",
    )
    p_diff.add_argument("a", help="Path to the first JSONL trace file.")
    p_diff.add_argument("b", help="Path to the second JSONL trace file.")

    p_score = sub.add_parser(
        "score", help="Score a trace against the epistemic norms.",
    )
    p_score.add_argument("trace", help="Path to a JSONL trace file.")
    p_score.add_argument(
        "--truth",
        help=(
            "Ground-truth hypothesis name. Required for reliability "
            "and calibration."
        ),
    )

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the CLI.

    Args:
        argv: argument list. ``None`` uses ``sys.argv[1:]``.

    Returns:
        Exit code: 0 on success, 1 on bad input, 2 on score failure.
    """
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == "replay":
        result = _load_or_die(args.trace)
        print_replay(result)
        return EXIT_OK
    if args.command == "diff":
        left = _load_or_die(args.a)
        right = _load_or_die(args.b)
        print_diff(left, right)
        return EXIT_OK
    if args.command == "score":
        result = _load_or_die(args.trace)
        return print_score(result, args.truth)

    parser.print_help()
    return EXIT_BAD_INPUT
