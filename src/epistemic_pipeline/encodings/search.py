"""State-space search encoding: A* pathfinding as an (O, E, B, R) tuple.

Expressiveness proof #3: graph search as an epistemic pipeline.
The ontology holds states, operators, a goal test, and a heuristic.
Beliefs track the A* frontier, explored set, and the best path found.
The revision policy expands one frontier node per call.
"""

from collections.abc import Callable
from dataclasses import dataclass, field, replace

from epistemic_pipeline.meta import MetaController
from epistemic_pipeline.pipeline import PipelineResult, run_pipeline
from epistemic_pipeline.state import EpistemicState, Metadata, Observation


@dataclass(frozen=True)
class SearchOperator:
    """One search operator: applicable test, state transition, and cost.

    name: operator identifier (e.g. "A_to_B").
    applicable: returns True if this operator can fire in a given state.
    apply: returns the successor state after applying this operator.
    cost: returns the step cost of applying this operator in a given state.

    Example: for edge A-B with cost 1.0:
        applicable=lambda s: s == "A"
        apply=lambda s: "B"
        cost=lambda s: 1.0
    """

    name: str
    applicable: Callable[[str], bool]
    apply: Callable[[str], str]
    cost: Callable[[str], float] = field(default_factory=lambda: lambda _s: 1.0)


@dataclass(frozen=True)
class SearchNode:
    """One node in the A* frontier.

    state: the search state this node represents.
    path: sequence of states from start to (and including) this state.
    cost: actual path cost g(n) from start to this node.
    priority: f(n) = g(n) + h(n) used to sort the frontier.
    """

    state: str
    path: tuple[str, ...]
    cost: float
    priority: float


@dataclass(frozen=True)
class SearchOntology:
    """Search ontology: the problem's structure.

    states: all valid state names in the search space.
    operators: available transitions between states.
    goal_test: returns True when a state satisfies the goal.
    heuristic: h(state) — admissible estimate of remaining cost.
    """

    states: frozenset[str]
    operators: tuple[SearchOperator, ...]
    goal_test: Callable[[str], bool]
    heuristic: Callable[[str], float]

    def adequate(self, evidence: tuple[Observation, ...]) -> bool:
        """Check if this ontology covers all evidence.

        Returns True when every state name in evidence appears in the
        ontology's state set. Skips synthetic search_step observations
        — those are planner signals, not real state names.

        Args:
            evidence: observations to check against this ontology.

        Returns:
            True if every non-search-step observation is covered; False otherwise.
        """
        for obs in evidence:
            if obs.variable == "search_step":
                continue
            if obs.variable not in self.states:
                return False
        return True


@dataclass(frozen=True)
class SearchBeliefs:
    """A* search state.

    frontier: nodes waiting to be expanded, sorted by priority (lowest first).
    explored: state names already expanded (for cycle detection).
    best_path: state sequence of the first goal solution found, or None.
    best_cost: path cost of the best solution found, or None.
    """

    frontier: tuple[SearchNode, ...]
    explored: frozenset[str]
    best_path: tuple[str, ...] | None = None
    best_cost: float | None = None


def search_update(
    beliefs: SearchBeliefs,
    _evidence: Observation,
    ontology: SearchOntology,
) -> SearchBeliefs:
    """One A* expansion step: R(B, e, O) -> B'.

    Pops the lowest-priority node from the frontier. If its state
    satisfies the goal, records the solution. Otherwise, generates
    successors for all applicable operators and adds them to the
    frontier. Skips states already explored. Keeps frontier sorted
    by priority for best-first expansion.

    Args:
        beliefs: current A* state with frontier and explored set.
        _evidence: a search_step observation triggering one expansion.
        ontology: holds the operators, goal test, and heuristic.

    Returns:
        Updated SearchBeliefs after one frontier expansion.
    """
    if not beliefs.frontier:
        return beliefs

    # frontier is sorted; pop the lowest-priority node
    best_node, *rest = beliefs.frontier

    # skip states already explored (lazy deletion)
    while best_node.state in beliefs.explored:
        if not rest:
            return replace(beliefs, frontier=())
        best_node, *rest = rest

    current_state = best_node.state
    new_explored = beliefs.explored | {current_state}

    # goal check
    if ontology.goal_test(current_state):
        return replace(
            beliefs,
            frontier=tuple(rest),
            explored=new_explored,
            best_path=best_node.path,
            best_cost=best_node.cost,
        )

    # expand: generate successors for all applicable operators
    successors: list[SearchNode] = []
    for op in ontology.operators:
        if op.applicable(current_state) and op.apply(current_state) not in new_explored:
            new_state = op.apply(current_state)
            new_cost = best_node.cost + op.cost(current_state)
            new_priority = new_cost + ontology.heuristic(new_state)
            successors.append(SearchNode(
                state=new_state,
                path=(*best_node.path, new_state),
                cost=new_cost,
                priority=new_priority,
            ))

    # merge rest and successors; sort by priority for A* ordering
    new_frontier = tuple(
        sorted(list(rest) + successors, key=lambda n: n.priority)
    )

    return replace(
        beliefs,
        frontier=new_frontier,
        explored=new_explored,
    )


@dataclass(frozen=True)
class SearchProblem:
    """Full specification of a state-space search problem.

    states: all valid state names.
    operators: available transitions between states.
    goal_test: returns True when a state satisfies the goal.
    heuristic: h(state) — admissible cost-to-go estimate.
    initial_state: the state where search begins.
    max_search_steps: maximum frontier expansions before giving up.
    """

    states: frozenset[str]
    operators: tuple[SearchOperator, ...]
    goal_test: Callable[[str], bool]
    heuristic: Callable[[str], float]
    initial_state: str
    max_search_steps: int = 1000


def search_frame(
    problem: SearchProblem,
) -> EpistemicState[SearchOntology, SearchBeliefs]:
    """Frame stage: build ontology and set initial A* state.

    Creates the SearchOntology from the problem. Seeds the frontier
    with a single node for the initial state. Generates synthetic
    search_step observations for the Test stage.

    Args:
        problem: the full state-space search problem specification.

    Returns:
        Initial EpistemicState ready for the pipeline.
    """
    ontology = SearchOntology(
        states=problem.states,
        operators=problem.operators,
        goal_test=problem.goal_test,
        heuristic=problem.heuristic,
    )

    initial_node = SearchNode(
        state=problem.initial_state,
        path=(problem.initial_state,),
        cost=0.0,
        priority=problem.heuristic(problem.initial_state),
    )

    beliefs = SearchBeliefs(
        frontier=(initial_node,),
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
        strategy="astar_search",
        pending_observations=search_steps,
    )

    return EpistemicState(
        ontology=ontology,
        evidence=(),
        beliefs=beliefs,
        revision_policy=search_update,
        metadata=metadata,
    )


def search_decompose(
    state: EpistemicState[SearchOntology, SearchBeliefs],
) -> EpistemicState[SearchOntology, SearchBeliefs]:
    """Decompose stage: no-op. No sub-goals for graph search.

    Args:
        state: current epistemic state.

    Returns:
        State unchanged.
    """
    return state


def search_model(
    state: EpistemicState[SearchOntology, SearchBeliefs],
) -> EpistemicState[SearchOntology, SearchBeliefs]:
    """Model stage: no-op. Revision policy set in Frame.

    Args:
        state: current epistemic state.

    Returns:
        State unchanged.
    """
    return state


def search_select(
    state: EpistemicState[SearchOntology, SearchBeliefs],
) -> EpistemicState[SearchOntology, SearchBeliefs]:
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
            heuristics=("astar_heuristic",),
            anomaly_checks=("empty_frontier",),
        ),
    )


def search_test(
    state: EpistemicState[SearchOntology, SearchBeliefs],
) -> EpistemicState[SearchOntology, SearchBeliefs]:
    """Test stage: run A* expansions until goal found or frontier empty.

    Each pending observation triggers one frontier expansion.
    Stops early when a goal is found (beliefs.best_path is not None)
    or the frontier is exhausted. Records each search_step as evidence.

    Args:
        state: current epistemic state with pending search_step observations.

    Returns:
        Updated state with final beliefs, accumulated evidence, and anomalies.
    """
    beliefs = state.beliefs
    evidence_list = list(state.evidence)
    anomalies = list(state.metadata.anomalies)

    for obs in state.metadata.pending_observations:
        # stop as soon as a goal solution is found
        if beliefs.best_path is not None:
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


def search_integrate(
    state: EpistemicState[SearchOntology, SearchBeliefs],
) -> EpistemicState[SearchOntology, SearchBeliefs]:
    """Integrate stage: the best path is in beliefs. Pass-through.

    Args:
        state: current epistemic state.

    Returns:
        State unchanged.
    """
    return state


def run_search_pipeline(
    problem: SearchProblem,
    meta_controller: MetaController | None = None,
) -> PipelineResult[SearchOntology, SearchBeliefs]:
    """Run a complete A* search pipeline.

    Composes all six stages: Frame -> Decompose -> Model -> Select ->
    Test -> Integrate. Returns the result with full trace and
    meta-layer evaluation.

    Args:
        problem: the state-space search problem specification.
        meta_controller: meta-epistemic controller. Defaults to v0.1 stub.

    Returns:
        PipelineResult with final state, trace, and meta decision.
    """
    initial_state = search_frame(problem)

    return run_pipeline(
        initial_state=initial_state,
        stages=[
            search_decompose,
            search_model,
            search_select,
            search_test,
            search_integrate,
        ],
        meta_controller=meta_controller,
    )
