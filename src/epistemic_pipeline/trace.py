"""Trace persistence: dump a PipelineResult to JSONL and load it back.

A trace file is a stream of JSON objects, one per line. The first line
is a header that names the encoding and the schema version. Every line
after the header is one state from the pipeline trace. The revision
policy is not serialized; it is reconstructed at load time by looking
up the encoding name in the registry.

Supported encodings: bayes, strips, mdp, llm_agent, worldview. The search
encoding is excluded because SearchOperator carries Python callables
that cannot be serialized without naming a global symbol; v1.2 may add
this through importlib-based callable resolution.
"""

from __future__ import annotations

import json
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any

from epistemic_pipeline.encodings.bayes import (
    BayesBeliefs,
    BayesOntology,
    bayes_update,
)
from epistemic_pipeline.encodings.llm_agent import (
    LLMAgentBeliefs,
    LLMAgentOntology,
    llm_agent_update,
)
from epistemic_pipeline.encodings.mdp import (
    MDPBeliefs,
    MDPOntology,
    mdp_update,
)
from epistemic_pipeline.encodings.strips import (
    STRIPSAction,
    STRIPSBeliefs,
    STRIPSOntology,
    strips_update,
)
from epistemic_pipeline.encodings.worldview import (
    WorldviewBeliefs,
    WorldviewOntology,
    worldview_update,
)
from epistemic_pipeline.meta import MetaDecision, MetaResult
from epistemic_pipeline.pipeline import PipelineResult
from epistemic_pipeline.state import (
    EpistemicState,
    EvidenceType,
    Metadata,
    Observation,
)

_SCHEMA_VERSION = "1.1"


@dataclass(frozen=True)
class _Encoding:
    """Serializer triple for one encoding.

    name: the encoding name written in the header.
    serialize_ontology: turn an ontology into a JSON-safe dict.
    deserialize_ontology: turn a JSON dict back into an ontology.
    serialize_beliefs: turn beliefs into a JSON-safe dict.
    deserialize_beliefs: turn a JSON dict back into beliefs.
    revision_policy: the R function reattached on load.
    """

    name: str
    serialize_ontology: Callable[[Any], dict[str, Any]]
    deserialize_ontology: Callable[[dict[str, Any]], Any]
    serialize_beliefs: Callable[[Any], dict[str, Any]]
    deserialize_beliefs: Callable[[dict[str, Any]], Any]
    revision_policy: Callable[..., Any]


_REGISTRY: dict[str, _Encoding] = {}


def register_encoding(encoding: _Encoding) -> None:
    """Add an encoding to the global registry.

    Args:
        encoding: the encoding triple to register.
    """
    _REGISTRY[encoding.name] = encoding


# --- Observation / Metadata serializers (shared by all encodings) ---


def _serialize_observation(obs: Observation) -> dict[str, Any]:
    return {
        "variable": obs.variable,
        "value": obs.value,
        "source": obs.source,
        "timestamp": obs.timestamp,
        "confidence": obs.confidence,
        "etype": obs.etype.value,
        "modality": obs.modality,
    }


def _deserialize_observation(payload: dict[str, Any]) -> Observation:
    return Observation(
        variable=payload["variable"],
        value=payload["value"],
        source=payload["source"],
        timestamp=payload["timestamp"],
        confidence=payload["confidence"],
        etype=EvidenceType(payload["etype"]),
        modality=payload["modality"],
    )


def _serialize_metadata(meta: Metadata) -> dict[str, Any]:
    return {
        "decomposition": list(meta.decomposition),
        "strategy": meta.strategy,
        "evidence_order": list(meta.evidence_order),
        "anomalies": list(meta.anomalies),
        "pending_observations": [
            _serialize_observation(obs) for obs in meta.pending_observations
        ],
        "anomaly_checks": list(meta.anomaly_checks),
        "heuristics": list(meta.heuristics),
        "strategy_switches": meta.strategy_switches,
    }


def _deserialize_metadata(payload: dict[str, Any]) -> Metadata:
    return Metadata(
        decomposition=tuple(payload["decomposition"]),
        strategy=payload["strategy"],
        evidence_order=tuple(payload["evidence_order"]),
        anomalies=tuple(payload["anomalies"]),
        pending_observations=tuple(
            _deserialize_observation(p)
            for p in payload["pending_observations"]
        ),
        anomaly_checks=tuple(payload["anomaly_checks"]),
        heuristics=tuple(payload["heuristics"]),
        strategy_switches=payload["strategy_switches"],
    )


# --- Tuple-keyed dict serializers (used by Bayes and MDP) ---


def _serialize_tuple_keyed(
    data: Mapping[tuple[Any, ...], float],
) -> list[dict[str, Any]]:
    return [{"key": list(k), "value": v} for k, v in data.items()]


def _deserialize_tuple_keyed(
    payload: list[dict[str, Any]],
) -> dict[tuple[Any, ...], float]:
    return {tuple(entry["key"]): entry["value"] for entry in payload}


# --- Bayes ---


def _serialize_bayes_ontology(ont: BayesOntology) -> dict[str, Any]:
    return {
        "hypotheses": list(ont.hypotheses),
        "observables": list(ont.observables),
        "likelihoods": _serialize_tuple_keyed(ont.likelihoods),
    }


def _deserialize_bayes_ontology(payload: dict[str, Any]) -> BayesOntology:
    return BayesOntology(
        hypotheses=tuple(payload["hypotheses"]),
        observables=tuple(payload["observables"]),
        likelihoods=_deserialize_tuple_keyed(payload["likelihoods"]),
    )


def _serialize_bayes_beliefs(beliefs: BayesBeliefs) -> dict[str, Any]:
    return {"probabilities": dict(beliefs.probabilities)}


def _deserialize_bayes_beliefs(payload: dict[str, Any]) -> BayesBeliefs:
    return BayesBeliefs(probabilities=dict(payload["probabilities"]))


# --- STRIPS ---


def _serialize_strips_action(action: STRIPSAction) -> dict[str, Any]:
    return {
        "name": action.name,
        "preconditions": sorted(action.preconditions),
        "add_effects": sorted(action.add_effects),
        "delete_effects": sorted(action.delete_effects),
    }


def _deserialize_strips_action(payload: dict[str, Any]) -> STRIPSAction:
    return STRIPSAction(
        name=payload["name"],
        preconditions=frozenset(payload["preconditions"]),
        add_effects=frozenset(payload["add_effects"]),
        delete_effects=frozenset(payload["delete_effects"]),
    )


def _serialize_strips_ontology(ont: STRIPSOntology) -> dict[str, Any]:
    return {
        "predicates": sorted(ont.predicates),
        "actions": [_serialize_strips_action(a) for a in ont.actions],
        "goal": sorted(ont.goal),
    }


def _deserialize_strips_ontology(payload: dict[str, Any]) -> STRIPSOntology:
    return STRIPSOntology(
        predicates=frozenset(payload["predicates"]),
        actions=tuple(
            _deserialize_strips_action(a) for a in payload["actions"]
        ),
        goal=frozenset(payload["goal"]),
    )


def _serialize_strips_beliefs(beliefs: STRIPSBeliefs) -> dict[str, Any]:
    return {
        "current_state": sorted(beliefs.current_state),
        "plan": list(beliefs.plan),
        "frontier": [
            {"state": sorted(state), "plan": list(plan)}
            for state, plan in beliefs.frontier
        ],
        "explored": [sorted(s) for s in beliefs.explored],
    }


def _deserialize_strips_beliefs(payload: dict[str, Any]) -> STRIPSBeliefs:
    return STRIPSBeliefs(
        current_state=frozenset(payload["current_state"]),
        plan=tuple(payload["plan"]),
        frontier=tuple(
            (frozenset(entry["state"]), tuple(entry["plan"]))
            for entry in payload["frontier"]
        ),
        explored=frozenset(
            frozenset(s) for s in payload["explored"]
        ),
    )


# --- MDP ---


def _serialize_mdp_ontology(ont: MDPOntology) -> dict[str, Any]:
    return {
        "states": sorted(ont.states),
        "actions": list(ont.actions),
        "transitions": _serialize_tuple_keyed(ont.transitions),
        "rewards": _serialize_tuple_keyed(ont.rewards),
        "discount": ont.discount,
        "terminal_states": sorted(ont.terminal_states),
        "epsilon": ont.epsilon,
    }


def _deserialize_mdp_ontology(payload: dict[str, Any]) -> MDPOntology:
    return MDPOntology(
        states=frozenset(payload["states"]),
        actions=tuple(payload["actions"]),
        transitions=MappingProxyType(
            _deserialize_tuple_keyed(payload["transitions"]),
        ),
        rewards=MappingProxyType(
            _deserialize_tuple_keyed(payload["rewards"]),
        ),
        discount=payload["discount"],
        terminal_states=frozenset(payload["terminal_states"]),
        epsilon=payload["epsilon"],
    )


def _serialize_mdp_beliefs(beliefs: MDPBeliefs) -> dict[str, Any]:
    return {
        "value_function": dict(beliefs.value_function),
        "policy": dict(beliefs.policy),
        "iteration": beliefs.iteration,
        "converged": beliefs.converged,
    }


def _deserialize_mdp_beliefs(payload: dict[str, Any]) -> MDPBeliefs:
    return MDPBeliefs(
        value_function=MappingProxyType(dict(payload["value_function"])),
        policy=MappingProxyType(dict(payload["policy"])),
        iteration=payload["iteration"],
        converged=payload["converged"],
    )


# --- LLM-agent ---


def _serialize_llm_agent_ontology(ont: LLMAgentOntology) -> dict[str, Any]:
    return {
        "hypotheses": list(ont.hypotheses),
        "tools": list(ont.tools),
        "inadequate": ont.inadequate,
    }


def _deserialize_llm_agent_ontology(
    payload: dict[str, Any],
) -> LLMAgentOntology:
    return LLMAgentOntology(
        hypotheses=tuple(payload["hypotheses"]),
        tools=tuple(payload["tools"]),
        inadequate=payload["inadequate"],
    )


def _serialize_llm_agent_beliefs(
    beliefs: LLMAgentBeliefs,
) -> dict[str, Any]:
    return {"confidences": dict(beliefs.confidences)}


def _deserialize_llm_agent_beliefs(
    payload: dict[str, Any],
) -> LLMAgentBeliefs:
    return LLMAgentBeliefs(confidences=dict(payload["confidences"]))


# --- Worldview ---


def _serialize_worldview_ontology(ont: WorldviewOntology) -> dict[str, Any]:
    return {"concepts": sorted(ont.concepts)}


def _deserialize_worldview_ontology(payload: dict[str, Any]) -> WorldviewOntology:
    return WorldviewOntology(concepts=frozenset(payload["concepts"]))


def _serialize_worldview_beliefs(beliefs: WorldviewBeliefs) -> dict[str, Any]:
    return {"confidences": dict(beliefs.confidences)}


def _deserialize_worldview_beliefs(payload: dict[str, Any]) -> WorldviewBeliefs:
    return WorldviewBeliefs(confidences=dict(payload["confidences"]))


# --- Registry population ---

register_encoding(_Encoding(
    name="bayes",
    serialize_ontology=_serialize_bayes_ontology,
    deserialize_ontology=_deserialize_bayes_ontology,
    serialize_beliefs=_serialize_bayes_beliefs,
    deserialize_beliefs=_deserialize_bayes_beliefs,
    revision_policy=bayes_update,
))
register_encoding(_Encoding(
    name="strips",
    serialize_ontology=_serialize_strips_ontology,
    deserialize_ontology=_deserialize_strips_ontology,
    serialize_beliefs=_serialize_strips_beliefs,
    deserialize_beliefs=_deserialize_strips_beliefs,
    revision_policy=strips_update,
))
register_encoding(_Encoding(
    name="mdp",
    serialize_ontology=_serialize_mdp_ontology,
    deserialize_ontology=_deserialize_mdp_ontology,
    serialize_beliefs=_serialize_mdp_beliefs,
    deserialize_beliefs=_deserialize_mdp_beliefs,
    revision_policy=mdp_update,
))
register_encoding(_Encoding(
    name="llm_agent",
    serialize_ontology=_serialize_llm_agent_ontology,
    deserialize_ontology=_deserialize_llm_agent_ontology,
    serialize_beliefs=_serialize_llm_agent_beliefs,
    deserialize_beliefs=_deserialize_llm_agent_beliefs,
    revision_policy=llm_agent_update,
))
register_encoding(_Encoding(
    name="worldview",
    serialize_ontology=_serialize_worldview_ontology,
    deserialize_ontology=_deserialize_worldview_ontology,
    serialize_beliefs=_serialize_worldview_beliefs,
    deserialize_beliefs=_deserialize_worldview_beliefs,
    revision_policy=worldview_update,
))


# --- Public API ---


def _detect_encoding(strategy: str) -> str:
    """Map a strategy string to a registered encoding name.

    Args:
        strategy: the metadata.strategy value from an EpistemicState.

    Returns:
        The encoding name to write to the header.

    Raises:
        ValueError: if the strategy is not associated with any encoding.
    """
    mapping = {
        "bayesian": "bayes",
        "strips_forward_search": "strips",
        "astar_search": "search",
        "mdp_value_iteration": "mdp",
        "llm_agent": "llm_agent",
        "worldview": "worldview",
    }
    if strategy not in mapping:
        msg = (
            f"Unknown strategy {strategy!r}. "
            f"Trace persistence supports: {sorted(mapping)}"
        )
        raise ValueError(msg)
    name = mapping[strategy]
    if name not in _REGISTRY:
        msg = (
            f"Strategy {strategy!r} maps to encoding {name!r}, "
            f"but no serializer is registered. Search is excluded in v1.1."
        )
        raise ValueError(msg)
    return name


def _serialize_state(
    state: EpistemicState[Any, Any], encoding: _Encoding,
) -> dict[str, Any]:
    return {
        "kind": "state",
        "ontology": encoding.serialize_ontology(state.ontology),
        "evidence": [_serialize_observation(o) for o in state.evidence],
        "beliefs": encoding.serialize_beliefs(state.beliefs),
        "metadata": _serialize_metadata(state.metadata),
    }


def _deserialize_state(
    payload: dict[str, Any], encoding: _Encoding,
) -> EpistemicState[Any, Any]:
    return EpistemicState(
        ontology=encoding.deserialize_ontology(payload["ontology"]),
        evidence=tuple(
            _deserialize_observation(o) for o in payload["evidence"]
        ),
        beliefs=encoding.deserialize_beliefs(payload["beliefs"]),
        revision_policy=encoding.revision_policy,
        metadata=_deserialize_metadata(payload["metadata"]),
    )


def _serialize_meta_decision(meta: MetaResult) -> dict[str, Any]:
    return {"decision": meta.decision.value, "details": dict(meta.details)}


def _deserialize_meta_decision(payload: dict[str, Any]) -> MetaResult:
    return MetaResult(
        decision=MetaDecision(payload["decision"]),
        details=dict(payload["details"]),
    )


def dump_trace(
    result: PipelineResult[Any, Any], path: str | Path,
) -> None:
    """Write a pipeline result to a JSONL file.

    The first line is a header containing the encoding name, schema
    version, and meta decision. Each subsequent line is one state from
    ``result.trace``. The revision policy is not written; it is
    reconstructed at load time from the encoding registry.

    Args:
        result: the pipeline result to serialize.
        path: filesystem path to write to.

    Raises:
        ValueError: if the encoding is not supported.
    """
    if not result.trace:
        msg = "Cannot dump an empty trace."
        raise ValueError(msg)
    first_state = result.trace[0]
    encoding_name = _detect_encoding(first_state.metadata.strategy)
    encoding = _REGISTRY[encoding_name]
    output_path = Path(path)
    with output_path.open("w", encoding="utf-8") as f:
        header = {
            "kind": "header",
            "encoding": encoding_name,
            "version": _SCHEMA_VERSION,
            "meta_decision": _serialize_meta_decision(result.meta_decision),
        }
        f.write(json.dumps(header) + "\n")
        for state in result.trace:
            f.write(json.dumps(_serialize_state(state, encoding)) + "\n")


def load_trace(path: str | Path) -> PipelineResult[Any, Any]:
    """Read a pipeline result from a JSONL file.

    Reads the header to determine the encoding, then deserializes each
    state line. The revision policy is reattached from the registry.

    Args:
        path: filesystem path to read from.

    Returns:
        A PipelineResult equivalent to the one that was dumped.

    Raises:
        ValueError: if the file is empty, the header is missing or
            malformed, or the encoding is unknown.
    """
    input_path = Path(path)
    with input_path.open(encoding="utf-8") as f:
        lines = [line for line in f if line.strip()]
    if not lines:
        msg = f"Trace file is empty: {input_path}"
        raise ValueError(msg)
    header = json.loads(lines[0])
    if header.get("kind") != "header":
        msg = f"First line of {input_path} is not a header."
        raise ValueError(msg)
    encoding_name = header["encoding"]
    if encoding_name not in _REGISTRY:
        msg = (
            f"Encoding {encoding_name!r} is not registered. "
            f"Known encodings: {sorted(_REGISTRY)}"
        )
        raise ValueError(msg)
    encoding = _REGISTRY[encoding_name]
    state_payloads = [json.loads(line) for line in lines[1:]]
    trace = tuple(
        _deserialize_state(payload, encoding) for payload in state_payloads
    )
    if not trace:
        msg = f"Trace file has header but no state lines: {input_path}"
        raise ValueError(msg)
    meta_decision = _deserialize_meta_decision(header["meta_decision"])
    return PipelineResult(
        final_state=trace[-1],
        trace=trace,
        meta_decision=meta_decision,
    )


