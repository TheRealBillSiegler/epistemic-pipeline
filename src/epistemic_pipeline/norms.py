"""Normative evaluation: reliability, efficiency, justification, power.

Scores a pipeline run on four dimensions. v0.2 adds calibration
(log scoring rule), heuristic cost, strategy switches, intermediate
consistency checks, and ontology adequacy (power).
"""

import math
from collections.abc import Callable
from dataclasses import dataclass

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
    power: str | bool | None = None
    calibration: float = 0.0
    efficiency_heuristic_cost: int = 0
    efficiency_strategy_switches: int = 0
    justification_intermediate_consistent: bool = True


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
    justification = replayed == final.beliefs

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
    power: str | bool | None = None
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
