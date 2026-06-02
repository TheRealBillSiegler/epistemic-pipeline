"""LLM-agent encoding: ranking a closed set of hypotheses with an LLM loop.

Expressiveness proof #5: an LLM agent reasoning over tool results as an
(O, E, B, R) tuple. The ontology holds a closed set of hypotheses and a
registry of named tools. Beliefs are a confidence distribution over the
hypotheses. Evidence is the full sequence of tool results and LLM
confidence reports. The revision policy parses the most recent LLM
confidence vector and renormalizes.

The LLM is non-deterministic, but R stays pure: each LLM response is
recorded as an Observation before R runs. R only ever reads from E,
never calls the LLM directly. Replay determinism is conditioned on the
recorded trace, matching the v1.0 conditional-determinism contract.
"""

from __future__ import annotations

import json
from collections.abc import Callable, Mapping
from dataclasses import dataclass, replace
from typing import TYPE_CHECKING

from epistemic_pipeline.meta import MetaController
from epistemic_pipeline.pipeline import PipelineResult, run_pipeline
from epistemic_pipeline.state import (
    EpistemicState,
    EvidenceType,
    Metadata,
    Observation,
)

if TYPE_CHECKING:
    from epistemic_pipeline.llm.llm_interfaces import RatingLLMInterface
    from epistemic_pipeline.tools.tool_interfaces import ToolInterface

_FLOAT_TOLERANCE = 1e-9
_OSCILLATION_WINDOW = 6
_OSCILLATION_MIN_TRANSITIONS = 3
_OSCILLATION_MIN_WINDOW = 2
_MIN_FOR_MARGIN = 2


@dataclass(frozen=True)
class LLMAgentOntology:
    """Hypotheses and tools the agent operates over.

    hypotheses: mutually exclusive hypothesis names. The agent must
        rank exactly these. If the LLM proposes a name outside this
        set, the Test stage flags the ontology as inadequate.
    tools: tool names the agent may call.
    inadequate: True if the agent has proposed a hypothesis outside
        the closed set. Set by the Test stage, not by R.
    """

    hypotheses: tuple[str, ...]
    tools: tuple[str, ...]
    inadequate: bool = False

    def adequate(self, evidence: tuple[Observation, ...]) -> bool:
        """Return False once the agent has proposed an unknown hypothesis.

        Args:
            evidence: observations to check (unused; the inadequate flag
                is set by the Test stage when it parses LLM responses).

        Returns:
            True if the ontology still covers every hypothesis the
            agent has proposed; False otherwise.
        """
        _ = evidence
        return not self.inadequate


@dataclass(frozen=True)
class LLMAgentBeliefs:
    """Confidence distribution over hypotheses.

    confidences: maps each hypothesis name to a confidence in [0, 1].
    Invariant: sum(confidences.values()) == 1.0 within float tolerance.
    """

    confidences: dict[str, float]


def llm_agent_argmax(beliefs: LLMAgentBeliefs) -> str:
    """Return the hypothesis with the highest confidence.

    Args:
        beliefs: a confidence distribution.

    Returns:
        The name of the hypothesis with the largest confidence value.
    """
    return max(beliefs.confidences, key=lambda h: beliefs.confidences[h])


def _parse_confidence_vector(text: str) -> dict[str, float]:
    """Parse a JSON object mapping hypothesis name to confidence.

    Args:
        text: a JSON string. Expected shape ``{name: float, ...}``.

    Returns:
        A dict from name to float. Empty dict if parsing fails or the
        payload is not a JSON object.
    """
    try:
        payload = json.loads(text)
    except (json.JSONDecodeError, ValueError):
        return {}
    if not isinstance(payload, dict):
        return {}
    result: dict[str, float] = {}
    for name, value in payload.items():
        if not isinstance(name, str):
            continue
        try:
            result[name] = float(value)
        except (TypeError, ValueError):
            continue
    return result


def llm_agent_update(
    beliefs: LLMAgentBeliefs,
    evidence: Observation,
    ontology: LLMAgentOntology,
) -> LLMAgentBeliefs:
    """Apply the LLM's revised confidence vector to current beliefs.

    R(B, e, O) -> B'. The LLM response is already captured in
    ``evidence.value`` as a JSON object. R parses it, drops entries
    whose name is not in ``ontology.hypotheses``, and renormalizes the
    remaining values so they sum to 1.0. If the parsed map is empty
    after filtering, beliefs are returned unchanged.

    Args:
        beliefs: current confidence distribution over hypotheses.
        evidence: the recorded LLM observation containing a JSON
            confidence vector in ``value``.
        ontology: the closed hypothesis set used for filtering.

    Returns:
        Updated LLMAgentBeliefs with normalized confidences.
    """
    parsed = _parse_confidence_vector(evidence.value)
    filtered = {
        name: max(0.0, value)
        for name, value in parsed.items()
        if name in ontology.hypotheses
    }
    total = sum(filtered.values())
    if total <= _FLOAT_TOLERANCE:
        return beliefs
    normalized = {name: value / total for name, value in filtered.items()}
    for hypothesis in ontology.hypotheses:
        normalized.setdefault(hypothesis, 0.0)
    return LLMAgentBeliefs(confidences=normalized)


def _detect_oscillation(map_history: list[str]) -> bool:
    """Return True if the top hypothesis flips at least three times.

    A flip is a change of the argmax between consecutive steps. Three
    flips inside a six-step window means the evidence is pushing
    beliefs back and forth instead of converging.

    Args:
        map_history: the argmax hypothesis recorded after each step.

    Returns:
        True if oscillation is detected; False otherwise.
    """
    window = map_history[-_OSCILLATION_WINDOW:]
    if len(window) < _OSCILLATION_MIN_WINDOW:
        return False
    transitions = sum(
        1 for i in range(len(window) - 1) if window[i] != window[i + 1]
    )
    return transitions >= _OSCILLATION_MIN_TRANSITIONS


def _summarize_evidence(evidence: tuple[Observation, ...]) -> str:
    """Build a short text summary of evidence for prompting the LLM.

    Args:
        evidence: the current evidence tuple.

    Returns:
        A newline-separated list of ``modality:variable=value`` lines.
    """
    return "\n".join(
        f"{obs.modality or 'obs'}:{obs.variable}={obs.value}"
        for obs in evidence
    )


@dataclass(frozen=True)
class LLMAgentProblem:
    """Full specification of an LLM-agent reasoning problem.

    question: the natural-language task to solve.
    hypotheses: closed set of candidate answers.
    tools: name -> ToolInterface registry.
    llm: an LLM that satisfies RatingLLMInterface.
    max_steps: outer-loop budget.
    confidence_threshold: stop when the top hypothesis exceeds this.
    priors: starting confidence distribution. Uniform if None.
    """

    question: str
    hypotheses: tuple[str, ...]
    tools: Mapping[str, ToolInterface]
    llm: RatingLLMInterface
    max_steps: int = 10
    confidence_threshold: float = 0.9
    priors: dict[str, float] | None = None


def llm_agent_frame(
    problem: LLMAgentProblem,
) -> EpistemicState[LLMAgentOntology, LLMAgentBeliefs]:
    """Frame stage: build the ontology and set initial beliefs.

    Constructs the LLMAgentOntology from the problem's hypotheses and
    tools. Uses uniform priors unless the problem provides custom ones.
    The LLM and tool registry are not part of the state; they are held
    by the closure that drives the Test stage.

    Args:
        problem: the full LLM-agent problem specification.

    Returns:
        Initial EpistemicState ready for the pipeline.
    """
    ontology = LLMAgentOntology(
        hypotheses=problem.hypotheses,
        tools=tuple(problem.tools.keys()),
    )
    if problem.priors is None:
        n = len(problem.hypotheses)
        prior_dist = dict.fromkeys(problem.hypotheses, 1.0 / n)
    else:
        prior_dist = dict(problem.priors)
    beliefs = LLMAgentBeliefs(confidences=prior_dist)
    metadata = Metadata(
        strategy="llm_agent",
        evidence_order=(),
        pending_observations=(),
    )
    return EpistemicState(
        ontology=ontology,
        evidence=(),
        beliefs=beliefs,
        revision_policy=llm_agent_update,
        metadata=metadata,
    )


def llm_agent_decompose(
    state: EpistemicState[LLMAgentOntology, LLMAgentBeliefs],
) -> EpistemicState[LLMAgentOntology, LLMAgentBeliefs]:
    """Decompose stage: no-op for v1.1."""
    return state


def llm_agent_model(
    state: EpistemicState[LLMAgentOntology, LLMAgentBeliefs],
) -> EpistemicState[LLMAgentOntology, LLMAgentBeliefs]:
    """Model stage: no-op. Priors and revision policy are set in Frame."""
    return state


def llm_agent_select(
    state: EpistemicState[LLMAgentOntology, LLMAgentBeliefs],
) -> EpistemicState[LLMAgentOntology, LLMAgentBeliefs]:
    """Select stage: no-op. Tool choice is made each iteration in Test."""
    return state


def _llm_agent_test_factory(
    problem: LLMAgentProblem,
) -> Callable[
    [EpistemicState[LLMAgentOntology, LLMAgentBeliefs]],
    EpistemicState[LLMAgentOntology, LLMAgentBeliefs],
]:
    """Build the Test stage closure for a specific problem.

    The Test stage needs the LLM and tool registry. Stages are pure
    functions of state, so we close over the problem here and return a
    stage function that the pipeline can call.

    Args:
        problem: the LLM-agent problem specification.

    Returns:
        A Test stage function bound to ``problem``.
    """

    def stage(
        state: EpistemicState[LLMAgentOntology, LLMAgentBeliefs],
    ) -> EpistemicState[LLMAgentOntology, LLMAgentBeliefs]:
        beliefs = state.beliefs
        evidence_list: list[Observation] = list(state.evidence)
        anomalies: list[str] = list(state.metadata.anomalies)
        map_history: list[str] = [llm_agent_argmax(beliefs)]
        ontology = state.ontology
        timestamp = 0.0

        for step in range(problem.max_steps):
            timestamp = float(step)
            evidence_summary = _summarize_evidence(tuple(evidence_list))

            # 1. Ask LLM which tool to call.
            tool_pick = problem.llm.pick_tool(
                problem.question, ontology.tools, evidence_summary,
            )
            evidence_list.append(
                Observation(
                    variable="tool_choice",
                    value=tool_pick.content,
                    source="llm",
                    timestamp=timestamp,
                    confidence=tool_pick.confidence,
                    etype=EvidenceType.REPORT,
                    modality="llm",
                ),
            )

            # 2. Parse the tool choice and call the tool.
            try:
                pick_payload = json.loads(tool_pick.content)
                tool_name = pick_payload.get("tool", "")
                tool_args = pick_payload.get("args", {})
            except (json.JSONDecodeError, ValueError, AttributeError):
                anomalies.append("tool_pick_unparseable")
                break

            if tool_name not in problem.tools:
                anomalies.append("tool_pick_unknown")
                break

            tool_result = problem.tools[tool_name].invoke(tool_name, tool_args)
            evidence_list.append(
                Observation(
                    variable=tool_name,
                    value=str(tool_result.output),
                    source=tool_name,
                    timestamp=timestamp,
                    confidence=1.0 if tool_result.success else 0.5,
                    etype=EvidenceType.MEASUREMENT,
                    modality="tool",
                ),
            )

            # 3. Ask LLM for a fresh confidence vector.
            evidence_summary = _summarize_evidence(tuple(evidence_list))
            rating = problem.llm.rate_confidence(
                problem.question, ontology.hypotheses, evidence_summary,
            )
            evidence_list.append(
                Observation(
                    variable="confidence_vector",
                    value=rating.content,
                    source="llm",
                    timestamp=timestamp,
                    confidence=rating.confidence,
                    etype=EvidenceType.REPORT,
                    modality="llm",
                ),
            )

            # 4. Detect unknown hypotheses before applying R.
            parsed = _parse_confidence_vector(rating.content)
            unknown = [
                name for name in parsed if name not in ontology.hypotheses
            ]
            if unknown:
                anomalies.append("ontology_inadequate")
                ontology = replace(ontology, inadequate=True)

            # 5. Apply R to the recorded LLM observation.
            beliefs = llm_agent_update(beliefs, evidence_list[-1], ontology)
            map_history.append(llm_agent_argmax(beliefs))

            # 6. Detect oscillation.
            if (
                _detect_oscillation(map_history)
                and "oscillation" not in anomalies
            ):
                anomalies.append("oscillation")

            # 7. Early stop on confidence threshold.
            top = beliefs.confidences[map_history[-1]]
            if top >= problem.confidence_threshold:
                break

        return replace(
            state,
            ontology=ontology,
            beliefs=beliefs,
            evidence=tuple(evidence_list),
            metadata=replace(
                state.metadata,
                anomalies=tuple(anomalies),
            ),
        )

    return stage


def llm_agent_integrate(
    state: EpistemicState[LLMAgentOntology, LLMAgentBeliefs],
) -> EpistemicState[LLMAgentOntology, LLMAgentBeliefs]:
    """Integrate stage: record the answer and confidence margin in metadata.

    The answer is the argmax hypothesis. The margin is top1 minus top2.
    Both are stored in the heuristics tuple of metadata so they are
    visible in trace dumps without changing the Metadata schema.

    Args:
        state: the state after the Test stage.

    Returns:
        State with ``answer`` and ``margin`` recorded in metadata.
    """
    sorted_pairs = sorted(
        state.beliefs.confidences.items(),
        key=lambda kv: kv[1],
        reverse=True,
    )
    answer = sorted_pairs[0][0] if sorted_pairs else ""
    margin = (
        sorted_pairs[0][1] - sorted_pairs[1][1]
        if len(sorted_pairs) >= _MIN_FOR_MARGIN
        else 0.0
    )
    return replace(
        state,
        metadata=replace(
            state.metadata,
            heuristics=(f"answer={answer}", f"margin={margin:.4f}"),
        ),
    )


def run_llm_agent_pipeline(
    problem: LLMAgentProblem,
    meta_controller: MetaController | None = None,
) -> PipelineResult[LLMAgentOntology, LLMAgentBeliefs]:
    """Run a complete LLM-agent pipeline.

    Composes all six stages: Frame -> Decompose -> Model -> Select ->
    Test -> Integrate. The Test stage closure carries the LLM and tool
    registry from the problem. Returns the result with full trace and
    meta-layer evaluation.

    Args:
        problem: the LLM-agent problem specification.
        meta_controller: meta-epistemic controller. Defaults to the
            built-in adaptive controller.

    Returns:
        PipelineResult with final state, trace, and meta decision.
    """
    initial_state = llm_agent_frame(problem)
    return run_pipeline(
        initial_state=initial_state,
        stages=[
            llm_agent_decompose,
            llm_agent_model,
            llm_agent_select,
            _llm_agent_test_factory(problem),
            llm_agent_integrate,
        ],
        meta_controller=meta_controller,
    )
