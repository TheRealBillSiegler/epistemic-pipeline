"""Six-stage pipeline: Frame, Decompose, Model, Select, Test, Integrate.

Each stage is a pure function: EpistemicState -> EpistemicState.
The pipeline composes them, collects a trace of every intermediate
state, and passes the result to the meta-epistemic controller.
"""

from collections.abc import Callable, Sequence
from dataclasses import dataclass

from epistemic_pipeline.meta import MetaController, MetaResult
from epistemic_pipeline.state import EpistemicState


@dataclass(frozen=True)
class PipelineResult[O, B]:
    """Result of a complete pipeline run.

    final_state: the state after all stages.
    trace: every intermediate state, starting from the frame output.
    meta_decision: the meta-layer's evaluation of the run.
    """

    final_state: EpistemicState[O, B]
    trace: tuple[EpistemicState[O, B], ...]
    meta_decision: MetaResult


def run_pipeline[O, B](
    initial_state: EpistemicState[O, B],
    stages: Sequence[Callable[[EpistemicState[O, B]], EpistemicState[O, B]]],
    meta_controller: MetaController | None = None,
) -> PipelineResult[O, B]:
    """Run the pipeline: compose stages, collect trace, evaluate meta-layer.

    Args:
        initial_state: output of the Frame stage.
        stages: pure functions for Decompose, Model, Select, Test, Integrate.
        meta_controller: meta-epistemic controller. Defaults to v0.1 stub.

    Returns:
        PipelineResult with final state, full trace, and meta decision.
    """
    trace: list[EpistemicState[O, B]] = [initial_state]
    state = initial_state

    for stage in stages:
        state = stage(state)
        trace.append(state)

    controller = meta_controller or MetaController()
    meta_result = controller.monitor(
        tuple(trace),
        None,
        state.ontology,
        state.metadata.strategy,
        state.metadata.decomposition,
    )

    return PipelineResult(
        final_state=state,
        trace=tuple(trace),
        meta_decision=meta_result,
    )
