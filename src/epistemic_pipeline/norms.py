"""Normative evaluation: reliability, efficiency, justification, power.

Scores a pipeline run on four dimensions.
v0.2 adds calibration (log scoring rule), heuristic cost, strategy switches,
intermediate consistency checks, and ontology adequacy (power).
"""

import math
from collections.abc import Callable
from dataclasses import dataclass
from types import MappingProxyType

from epistemic_pipeline.state import EpistemicState, Observation


@dataclass(frozen=True)
class NormScore:
    """Score for a pipeline run across four normative dimensions.

    v0.1 fields: reliability, efficiency, justification, power.
    v0.2 additions: calibration, heuristic cost, strategy switches,
    intermediate consistency. All v0.2 fields have defaults for
    backward compatibility.
    """

    reliability: float
    efficiency: int
    justification: bool
    power: bool | None = None
    calibration: float = 0.0
    efficiency_heuristic_cost: int = 0
    efficiency_strategy_switches: int = 0
    justification_intermediate_consistent: bool = True


_JUSTIFICATION_ATOL = 1e-9


def _beliefs_approx_equal(a: object, b: object) -> bool:  # noqa: PLR0911
    """Compare two belief objects with float tolerance.

    Walks dict and dataclass fields looking for float values.
    Two beliefs are approximately equal when all non-float fields match exactly
    and all float values are within _JUSTIFICATION_ATOL of each other.
    Falls back to == for types without dict-like or dataclass structure.
    """
    if type(a) is not type(b):
        return False
    # Handle dict comparison (e.g. BayesBeliefs.probabilities).
    if isinstance(a, dict) and isinstance(b, dict):
        if a.keys() != b.keys():
            return False
        for k in a:
            av, bv = a[k], b[k]
            if isinstance(av, float) and isinstance(bv, float):
                if abs(av - bv) > _JUSTIFICATION_ATOL:
                    return False
            elif av != bv:
                return False
        return True
    # Handle frozen dataclasses by comparing fields.
    dataclass_fields = getattr(a, "__dataclass_fields__", None)
    if dataclass_fields is not None:
        for field_name in dataclass_fields:
            fa = getattr(a, field_name)
            fb = getattr(b, field_name)
            if not _beliefs_approx_equal(fa, fb):
                return False
        return True
    # Handle MappingProxyType by comparing the underlying data.
    if isinstance(a, MappingProxyType) and isinstance(b, MappingProxyType):
        return _beliefs_approx_equal(dict(a), dict(b))
    # Scalar floats.
    if isinstance(a, float) and isinstance(b, float):
        return abs(a - b) <= _JUSTIFICATION_ATOL
    return a == b


def _replay_beliefs[O, B](
    initial_beliefs: B,
    evidence: tuple[Observation, ...],
    revision_policy: Callable[[B, Observation, O], B],
    ontology: O,
) -> B:
    """Replay R over every observation, starting from initial beliefs.

    Returns the beliefs after processing all evidence.
    """
    beliefs = initial_beliefs
    for obs in evidence:
        beliefs = revision_policy(beliefs, obs, ontology)
    return beliefs


def score_pipeline_run[O, B](  # noqa: PLR0913
    trace: tuple[EpistemicState[O, B], ...],
    ground_truth: str,
    belief_argmax: Callable[[B], str],
    *,
    belief_probability: Callable[[B, str], float] | None = None,
    belief_consistent: Callable[[B, O], bool] | None = None,
    ontology_adequate: Callable[[O, tuple[Observation, ...]], bool] | None = None,
    heuristic_cost: int | None = None,
) -> NormScore:
    """Score a completed pipeline run on all norms.

    Args:
        trace: sequence of EpistemicStates from the pipeline run.
        ground_truth: the correct answer (e.g. hypothesis name).
        belief_argmax: extracts the top belief from B.
        belief_probability: returns B(h) for a given hypothesis. None = skip calibration.
        belief_consistent: returns True if B is consistent with O. None = skip check.
        ontology_adequate: returns True if O covers E. None = skip power.
        heuristic_cost: number of search steps (frontier expansions). None = 0.

    Returns:
        NormScore with all computed dimensions.
    """
    if not trace:
        return NormScore(reliability=0.0, efficiency=0, justification=False)

    initial = trace[0]
    final = trace[-1]

    # Reliability: does the top belief match ground truth?
    top = belief_argmax(final.beliefs)
    reliability = 1.0 if top == ground_truth else 0.0

    # Efficiency: trace length + metadata fields
    efficiency = len(trace)
    strategy_switches = final.metadata.strategy_switches

    # Justification: replay check
    replayed = _replay_beliefs(
        initial.beliefs,
        final.evidence,
        final.revision_policy,
        final.ontology,
    )
    justification = _beliefs_approx_equal(replayed, final.beliefs)

    # Calibration: log(B_final(h*))
    calibration = 0.0
    if belief_probability is not None:
        p_truth = belief_probability(final.beliefs, ground_truth)
        calibration = math.log(p_truth) if p_truth > 0 else float("-inf")

    # Intermediate consistency
    intermediate_consistent = True
    if belief_consistent is not None:
        for state in trace:
            if not belief_consistent(state.beliefs, state.ontology):
                intermediate_consistent = False
                break

    # Power: ontology adequacy
    power: bool | None = None
    if ontology_adequate is not None:
        power = ontology_adequate(final.ontology, final.evidence)

    return NormScore(
        reliability=reliability,
        efficiency=efficiency,
        justification=justification,
        power=power,
        calibration=calibration,
        efficiency_heuristic_cost=heuristic_cost or 0,
        efficiency_strategy_switches=strategy_switches,
        justification_intermediate_consistent=intermediate_consistent,
    )
