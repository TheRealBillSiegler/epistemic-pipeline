"""STRIPS encoding: classical planning as forward-state search.

Expressiveness proof #2: planning as an (O, E, B, R) tuple.
STRIPS (Stanford Research Institute Problem Solver) is a classical
planning formalism. The ontology holds predicates, actions, and the
goal. Beliefs track the current state, plan, and search frontier.
The revision policy expands one frontier state per call.
"""

from dataclasses import dataclass, replace

from epistemic_pipeline.meta import MetaController
from epistemic_pipeline.pipeline import PipelineResult, identity_stage, run_pipeline
from epistemic_pipeline.state import EpistemicState, Metadata, Observation


@dataclass(frozen=True)
class STRIPSAction:
    """One planning action with preconditions and effects.

    name: action identifier (e.g. "pickup_A").
    preconditions: predicates that must be true to apply this action.
    add_effects: predicates made true by this action.
    delete_effects: predicates made false by this action.
    """

    name: str
    preconditions: frozenset[str]
    add_effects: frozenset[str]
    delete_effects: frozenset[str]


@dataclass(frozen=True)
class STRIPSOntology:
    """STRIPS ontology: predicates, actions, and goal.

    The goal is an ontological commitment, not a belief.
    predicates: all predicate names in this domain.
    actions: available planning actions.
    goal: predicates that must be true in the goal state.
    """

    predicates: frozenset[str]
    actions: tuple[STRIPSAction, ...]
    goal: frozenset[str]

    def adequate(self, evidence: tuple[Observation, ...]) -> bool:
        """Check if this ontology covers all evidence.

        Returns True when every predicate mentioned in evidence
        appears in the ontology's predicate set. Skips synthetic
        search_step observations — those are planner signals, not
        real predicates.

        Args:
            evidence: observations to check against this ontology.

        Returns:
            True if every non-search-step observation is covered; False otherwise.
        """
        for obs in evidence:
            if obs.variable == "search_step":
                continue
            if obs.variable not in self.predicates:
                return False
        return True


@dataclass(frozen=True)
class STRIPSBeliefs:
    """Search state for STRIPS planning.

    current_state: predicates currently true.
    plan: action names chosen so far (the solution being built).
    frontier: states to explore. Each entry is (state, plan_so_far).
    explored: states already visited (for cycle detection).
    """

    current_state: frozenset[str]
    plan: tuple[str, ...]
    frontier: tuple[tuple[frozenset[str], tuple[str, ...]], ...] = ()
    explored: frozenset[frozenset[str]] = frozenset()


def _apply_action(
    state: frozenset[str], action: STRIPSAction,
) -> frozenset[str]:
    """Apply a STRIPS action to a state. Returns the new state.

    Args:
        state: predicates currently true.
        action: the action to apply.

    Returns:
        New state after deleting and adding predicates.
    """
    return (state - action.delete_effects) | action.add_effects


def strips_update(
    beliefs: STRIPSBeliefs,
    _evidence: Observation,
    ontology: STRIPSOntology,
) -> STRIPSBeliefs:
    """One search expansion step: R(B, e, O) -> B'.

    Pops the first frontier entry. If it satisfies the goal,
    returns beliefs with the completed plan. Otherwise, generates
    successor states from applicable actions and adds them to
    the frontier. Skips already-explored states.

    Args:
        beliefs: current search state with frontier and explored set.
        evidence: a search_step observation triggering one expansion.
        ontology: holds the actions and goal.

    Returns:
        Updated STRIPSBeliefs after one frontier expansion.
    """
    if not beliefs.frontier:
        return beliefs

    (current, plan_so_far), *rest = beliefs.frontier

    # Goal check
    if ontology.goal.issubset(current):
        return STRIPSBeliefs(
            current_state=current,
            plan=plan_so_far,
            frontier=tuple(rest),
            explored=beliefs.explored | {current},
        )

    # Expand: find applicable actions
    new_explored = beliefs.explored | {current}
    successors: list[tuple[frozenset[str], tuple[str, ...]]] = []

    for action in ontology.actions:
        if action.preconditions.issubset(current):
            new_state = _apply_action(current, action)
            if new_state not in new_explored:
                successors.append((new_state, (*plan_so_far, action.name)))

    new_frontier = tuple(rest) + tuple(successors)

    return STRIPSBeliefs(
        current_state=current,
        plan=plan_so_far,
        frontier=new_frontier,
        explored=new_explored,
    )


@dataclass(frozen=True)
class STRIPSProblem:
    """Full specification of a STRIPS planning problem.

    predicates: all predicate names in the domain.
    actions: available planning actions.
    goal: predicates that must be true in the goal state.
    initial_state: predicates true at the start.
    max_search_steps: maximum frontier expansions before giving up.
    """

    predicates: frozenset[str]
    actions: tuple[STRIPSAction, ...]
    goal: frozenset[str]
    initial_state: frozenset[str]
    max_search_steps: int = 100


def strips_frame(
    problem: STRIPSProblem,
) -> EpistemicState[STRIPSOntology, STRIPSBeliefs]:
    """Frame stage: build ontology and set initial search state.

    Creates the STRIPSOntology from the problem. Sets the initial
    state in beliefs with the frontier containing just the start state.
    Generates synthetic search-step observations for the Test stage.

    Args:
        problem: the full STRIPS planning problem specification.

    Returns:
        Initial EpistemicState ready for the pipeline.
    """
    ontology = STRIPSOntology(
        predicates=problem.predicates,
        actions=problem.actions,
        goal=problem.goal,
    )

    beliefs = STRIPSBeliefs(
        current_state=problem.initial_state,
        plan=(),
        frontier=((problem.initial_state, ()),),
        explored=frozenset(),
    )

    search_steps = tuple(
        Observation(
            variable="search_step",
            value="expand",
            source="planner",
            timestamp=float(i),
        )
        for i in range(problem.max_search_steps)
    )

    metadata = Metadata(
        strategy="strips_forward_search",
        pending_observations=search_steps,
    )

    return EpistemicState(
        ontology=ontology,
        evidence=(),
        beliefs=beliefs,
        revision_policy=strips_update,
        metadata=metadata,
    )


def strips_decompose(
    state: EpistemicState[STRIPSOntology, STRIPSBeliefs],
) -> EpistemicState[STRIPSOntology, STRIPSBeliefs]:
    """Decompose stage: identify subgoals not yet satisfied.

    Args:
        state: current epistemic state.

    Returns:
        State with unsatisfied goal predicates recorded in metadata.
    """
    unsatisfied = tuple(
        p for p in state.ontology.goal
        if p not in state.beliefs.current_state
    )
    return replace(
        state,
        metadata=replace(state.metadata, decomposition=unsatisfied),
    )


def strips_select(
    state: EpistemicState[STRIPSOntology, STRIPSBeliefs],
) -> EpistemicState[STRIPSOntology, STRIPSBeliefs]:
    """Select stage: record heuristic choice in metadata.

    Args:
        state: current epistemic state.

    Returns:
        State with heuristic and anomaly check names recorded.
    """
    return replace(
        state,
        metadata=replace(
            state.metadata,
            heuristics=("goal_count",),
            anomaly_checks=("empty_frontier",),
        ),
    )


def strips_test(
    state: EpistemicState[STRIPSOntology, STRIPSBeliefs],
) -> EpistemicState[STRIPSOntology, STRIPSBeliefs]:
    """Test stage: run search iterations until goal or frontier empty.

    Each pending observation triggers one frontier expansion.
    Stops early if the goal is reached or the frontier is empty.
    Records search-step observations as evidence.

    Args:
        state: current epistemic state with pending search-step observations.

    Returns:
        Updated state with final beliefs, accumulated evidence, and anomalies.
    """
    beliefs = state.beliefs
    evidence_list = list(state.evidence)
    anomalies = list(state.metadata.anomalies)

    for obs in state.metadata.pending_observations:
        if state.ontology.goal.issubset(beliefs.current_state):
            break

        if not beliefs.frontier:
            anomalies.append("empty_frontier")
            break

        beliefs = state.revision_policy(beliefs, obs, state.ontology)
        evidence_list.append(obs)

    return replace(
        state,
        beliefs=beliefs,
        evidence=tuple(evidence_list),
        metadata=replace(
            state.metadata,
            pending_observations=(),
            anomalies=tuple(anomalies),
        ),
    )


def run_strips_pipeline(
    problem: STRIPSProblem,
    meta_controller: MetaController | None = None,
) -> PipelineResult[STRIPSOntology, STRIPSBeliefs]:
    """Run a complete STRIPS planning pipeline.

    Composes all six stages: Frame -> Decompose -> Model -> Select ->
    Test -> Integrate. Returns the result with full trace and
    meta-layer evaluation.

    Args:
        problem: the STRIPS planning problem specification.
        meta_controller: meta-epistemic controller. Defaults to v0.1 stub.

    Returns:
        PipelineResult with final state, trace, and meta decision.
    """
    initial_state = strips_frame(problem)

    return run_pipeline(
        initial_state=initial_state,
        stages=[
            strips_decompose,
            identity_stage,  # Model: revision policy is set in Frame
            strips_select,
            strips_test,
            identity_stage,  # Integrate: the plan is already in beliefs
        ],
        meta_controller=meta_controller,
    )
