"""MDP encoding: value iteration as an (O, E, B, R) tuple.

Expressiveness proof #3: sequential decision-making as epistemic state.
An MDP (Markov Decision Process) defines states, actions, stochastic
transitions, and rewards. The agent's goal is to find a policy that
maximizes expected discounted reward. Value iteration is the revision
policy: each Bellman sweep updates the value estimate for every state.

Ontology O: state space, action set, transition model, reward function.
Evidence E: one synthetic observation per Bellman sweep.
Beliefs B: current value function and derived policy.
Revision R: one full Bellman sweep — R(B, e, O) -> B'.
"""

from dataclasses import dataclass, replace

from epistemic_pipeline.meta import MetaController
from epistemic_pipeline.pipeline import PipelineResult, run_pipeline
from epistemic_pipeline.state import EpistemicState, Metadata, Observation


@dataclass(frozen=True)
class MDPOntology:
    """MDP ontology: the full problem structure.

    states: all state names (e.g. frozenset({"s0", "s1"})).
    actions: action names in a fixed order.
    transitions: T(s, a, s') probabilities. Key is (s, a, s') tuple.
      Only non-zero entries need to be present.
    rewards: either R(s, a) with tuple keys or R(s) with string keys.
    discount: gamma in [0, 1). Scales future rewards.
    terminal_states: states where the episode ends. No outgoing value.
    epsilon: convergence threshold. Iteration stops when max delta < epsilon.
    """

    states: frozenset[str]
    actions: tuple[str, ...]
    transitions: dict[tuple[str, str, str], float]
    rewards: dict[tuple[str, str], float] | dict[str, float]
    discount: float
    terminal_states: frozenset[str] = frozenset()
    epsilon: float = 1e-6

    def get_reward(self, state: str, action: str) -> float:
        """Look up the reward for a (state, action) pair.

        Tries (state, action) tuple key first. Falls back to plain
        string key. Returns 0.0 if neither key exists.

        Args:
            state: the current state name.
            action: the action taken.

        Returns:
            Reward value, or 0.0 if not found.
        """
        sa_key: tuple[str, str] = (state, action)
        # Try tuple key (state, action) first.
        if sa_key in self.rewards:
            return float(self.rewards[sa_key])  # type: ignore[index]
        # Fall back to plain string key.
        if state in self.rewards:
            return float(self.rewards[state])  # type: ignore[index]
        return 0.0

    def adequate(self, evidence: tuple[Observation, ...]) -> bool:
        """Check that all observed variables are known states.

        Skips synthetic bellman_sweep observations — those are planner
        signals, not real state variables.

        Args:
            evidence: observations to check against this ontology.

        Returns:
            True if every non-bellman_sweep variable is a known state.
        """
        for obs in evidence:
            if obs.variable == "bellman_sweep":
                continue
            if obs.variable not in self.states:
                return False
        return True


@dataclass(frozen=True)
class MDPBeliefs:
    """Value function and policy derived by value iteration.

    value_function: V(s) — estimated total discounted reward from state s.
    policy: pi(s) — best action to take from state s.
    iteration: how many Bellman sweeps have run.
    converged: True when max delta across all states dropped below epsilon.
    """

    value_function: dict[str, float]
    policy: dict[str, str]
    iteration: int = 0
    converged: bool = False


@dataclass(frozen=True)
class MDPProblem:
    """Full specification of an MDP problem.

    states: all state names.
    actions: action names.
    transitions: T(s, a, s') non-zero probability entries.
    rewards: R(s,a) with tuple keys or R(s) with string keys.
    discount: gamma in [0, 1).
    terminal_states: absorbing states.
    epsilon: convergence threshold.
    max_iterations: cap on Bellman sweeps before giving up.
    """

    states: frozenset[str]
    actions: tuple[str, ...]
    transitions: dict[tuple[str, str, str], float]
    rewards: dict[tuple[str, str], float] | dict[str, float]
    discount: float
    terminal_states: frozenset[str] = frozenset()
    epsilon: float = 1e-6
    max_iterations: int = 1000


def mdp_update(
    beliefs: MDPBeliefs,
    _evidence: Observation,
    ontology: MDPOntology,
) -> MDPBeliefs:
    """One full Bellman sweep: R(B, e, O) -> B'.

    For each non-terminal state, computes Q(s, a) for every action and
    sets V'(s) = max_a Q(s, a). Policy pi(s) is the argmax action.
    Terminal states keep their current value unchanged.

    Convergence: delta = max |V'(s) - V(s)| over non-terminal states.
    Sets converged=True when delta < ontology.epsilon.

    Args:
        beliefs: current value function and policy.
        _evidence: a bellman_sweep observation (used as a clock tick).
        ontology: holds transitions, rewards, discount, and epsilon.

    Returns:
        Updated MDPBeliefs after one Bellman sweep.
    """
    old_v = beliefs.value_function
    new_v: dict[str, float] = dict(old_v)
    new_policy: dict[str, str] = dict(beliefs.policy)

    delta = 0.0

    for s in ontology.states:
        if s in ontology.terminal_states:
            continue

        best_value = float("-inf")
        best_action = ontology.actions[0]

        for a in ontology.actions:
            # Q(s, a) = R(s, a) + gamma * sum_s'[ T(s,a,s') * V(s') ]
            q = ontology.get_reward(s, a)
            for s_prime in ontology.states:
                prob = ontology.transitions.get((s, a, s_prime), 0.0)
                if prob > 0.0:
                    q += ontology.discount * prob * old_v.get(s_prime, 0.0)

            if q > best_value:
                best_value = q
                best_action = a

        new_v[s] = best_value
        new_policy[s] = best_action
        delta = max(delta, abs(best_value - old_v.get(s, 0.0)))

    converged = delta < ontology.epsilon

    return MDPBeliefs(
        value_function=new_v,
        policy=new_policy,
        iteration=beliefs.iteration + 1,
        converged=converged,
    )


def mdp_frame(
    problem: MDPProblem,
) -> EpistemicState[MDPOntology, MDPBeliefs]:
    """Frame stage: build ontology and initialize value function.

    Non-terminal states start at V(s) = 0. Terminal states start at
    their reward value. Policy initializes to the first action for all
    states. Creates synthetic bellman_sweep observations for the Test stage.

    Args:
        problem: the full MDP problem specification.

    Returns:
        Initial EpistemicState ready for the pipeline.
    """
    ontology = MDPOntology(
        states=problem.states,
        actions=problem.actions,
        transitions=problem.transitions,
        rewards=problem.rewards,
        discount=problem.discount,
        terminal_states=problem.terminal_states,
        epsilon=problem.epsilon,
    )

    # Initialize V: 0 for non-terminal, reward for terminal.
    value_function: dict[str, float] = {}
    policy: dict[str, str] = {}
    first_action = problem.actions[0] if problem.actions else ""

    for s in problem.states:
        if s in problem.terminal_states:
            value_function[s] = ontology.get_reward(s, first_action)
        else:
            value_function[s] = 0.0
        policy[s] = first_action

    beliefs = MDPBeliefs(
        value_function=value_function,
        policy=policy,
    )

    sweep_observations = tuple(
        Observation(
            variable="bellman_sweep",
            value=str(i),
            source="planner",
            timestamp=float(i),
        )
        for i in range(problem.max_iterations)
    )

    metadata = Metadata(
        strategy="mdp_value_iteration",
        pending_observations=sweep_observations,
    )

    return EpistemicState(
        ontology=ontology,
        evidence=(),
        beliefs=beliefs,
        revision_policy=mdp_update,
        metadata=metadata,
    )


def mdp_decompose(
    state: EpistemicState[MDPOntology, MDPBeliefs],
) -> EpistemicState[MDPOntology, MDPBeliefs]:
    """Decompose stage: no-op. Value iteration has no sub-problems.

    Args:
        state: current epistemic state.

    Returns:
        State unchanged.
    """
    return state


def mdp_model(
    state: EpistemicState[MDPOntology, MDPBeliefs],
) -> EpistemicState[MDPOntology, MDPBeliefs]:
    """Model stage: no-op. Transition model is already in the ontology.

    Args:
        state: current epistemic state.

    Returns:
        State unchanged.
    """
    return state


def mdp_select(
    state: EpistemicState[MDPOntology, MDPBeliefs],
) -> EpistemicState[MDPOntology, MDPBeliefs]:
    """Select stage: record value iteration as the chosen strategy.

    Args:
        state: current epistemic state.

    Returns:
        State with heuristic and anomaly check names recorded.
    """
    return replace(
        state,
        metadata=replace(
            state.metadata,
            heuristics=("bellman_optimality",),
            anomaly_checks=("value_divergence",),
        ),
    )


def mdp_test(
    state: EpistemicState[MDPOntology, MDPBeliefs],
) -> EpistemicState[MDPOntology, MDPBeliefs]:
    """Test stage: run Bellman sweeps until convergence or budget exhausted.

    Each pending observation triggers one full Bellman sweep via the
    revision policy. Stops early when beliefs.converged is True. Flags
    "value_divergence" anomaly if the budget runs out before convergence.

    Args:
        state: current epistemic state with pending bellman_sweep observations.

    Returns:
        Updated state with converged value function and accumulated evidence.
    """
    beliefs = state.beliefs
    evidence_list = list(state.evidence)
    anomalies = list(state.metadata.anomalies)

    for obs in state.metadata.pending_observations:
        if beliefs.converged:
            break
        beliefs = state.revision_policy(beliefs, obs, state.ontology)
        evidence_list.append(obs)

    if not beliefs.converged:
        anomalies.append("value_divergence")

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


def mdp_integrate(
    state: EpistemicState[MDPOntology, MDPBeliefs],
) -> EpistemicState[MDPOntology, MDPBeliefs]:
    """Integrate stage: no-op. Policy is in beliefs.

    Args:
        state: current epistemic state.

    Returns:
        State unchanged.
    """
    return state


def run_mdp_pipeline(
    problem: MDPProblem,
    meta_controller: MetaController | None = None,
) -> PipelineResult[MDPOntology, MDPBeliefs]:
    """Run a complete MDP value iteration pipeline.

    Composes all six stages: Frame -> Decompose -> Model -> Select ->
    Test -> Integrate. Returns the result with full trace and
    meta-layer evaluation.

    Args:
        problem: the MDP problem specification.
        meta_controller: meta-epistemic controller. Defaults to v0.1 stub.

    Returns:
        PipelineResult with final state, trace, and meta decision.
    """
    initial_state = mdp_frame(problem)

    return run_pipeline(
        initial_state=initial_state,
        stages=[
            mdp_decompose,
            mdp_model,
            mdp_select,
            mdp_test,
            mdp_integrate,
        ],
        meta_controller=meta_controller,
    )


# ---------------------------------------------------------------------------
# 4x3 Grid World (Russell & Norvig)
# ---------------------------------------------------------------------------

def grid_world() -> MDPProblem:
    """Build the Russell & Norvig 4x3 grid world MDP.

    State names use "col_row" format. Row 2 is the top row.
    Terminal states: "3_2" (+1 reward), "3_1" (-1 reward).
    Wall at (col=1, row=1): that cell is not a state.

    Non-terminal states (9):
      row 0: 0_0, 1_0, 2_0, 3_0
      row 1: 0_1, 2_1          (no 1_1 — it's a wall)
      row 2: 0_2, 1_2, 2_2

    Terminal states (2): 3_2, 3_1

    Actions: up, down, left, right.
    Stochastic: 0.8 intended, 0.1 each perpendicular.
    Walls and grid edges: agent stays put if movement is blocked.

    Rewards: -0.04 for all non-terminal states, +1 for 3_2, -1 for 3_1.
    Discount: 0.9.

    Returns:
        MDPProblem for the 4x3 grid world.
    """
    terminal_states = frozenset({"3_2", "3_1"})

    non_terminal = {
        "0_0", "1_0", "2_0", "3_0",
        "0_1", "2_1",
        "0_2", "1_2", "2_2",
    }
    all_states = frozenset(non_terminal | terminal_states)

    actions: tuple[str, ...] = ("up", "down", "left", "right")

    # Grid dimensions.
    num_cols = 4
    num_rows = 3
    wall = (1, 1)  # (col, row)

    def state_name(col: int, row: int) -> str:
        return f"{col}_{row}"

    def is_valid(col: int, row: int) -> bool:
        """A cell is valid if it's in bounds and not the wall."""
        if col < 0 or col >= num_cols or row < 0 or row >= num_rows:
            return False
        return (col, row) != wall

    def parse_state(s: str) -> tuple[int, int]:
        col_str, row_str = s.split("_")
        return int(col_str), int(row_str)

    # Direction deltas for each action.
    deltas: dict[str, tuple[int, int]] = {
        "up":    (0, +1),
        "down":  (0, -1),
        "left":  (-1, 0),
        "right": (+1, 0),
    }

    # Perpendicular actions for each action.
    perp: dict[str, tuple[str, str]] = {
        "up":    ("left", "right"),
        "down":  ("left", "right"),
        "left":  ("up", "down"),
        "right": ("up", "down"),
    }

    def next_state(s: str, action: str) -> str:
        """Resolve one move: returns the actual next state name."""
        col, row = parse_state(s)
        dc, dr = deltas[action]
        nc, nr = col + dc, row + dr
        if is_valid(nc, nr):
            return state_name(nc, nr)
        return s  # blocked — stay put

    transitions: dict[tuple[str, str, str], float] = {}

    for s in non_terminal:
        for a in actions:
            p1, p2 = perp[a]
            outcomes: list[tuple[str, float]] = [
                (next_state(s, a),  0.8),
                (next_state(s, p1), 0.1),
                (next_state(s, p2), 0.1),
            ]
            # Accumulate probabilities for each destination.
            dest_prob: dict[str, float] = {}
            for dest, prob in outcomes:
                dest_prob[dest] = dest_prob.get(dest, 0.0) + prob

            for dest, prob in dest_prob.items():
                key = (s, a, dest)
                transitions[key] = prob

    rewards: dict[str, float] = dict.fromkeys(non_terminal, -0.04)
    rewards["3_2"] = 1.0
    rewards["3_1"] = -1.0

    return MDPProblem(
        states=all_states,
        actions=actions,
        transitions=transitions,
        rewards=rewards,
        discount=0.9,
        terminal_states=terminal_states,
        epsilon=1e-6,
        max_iterations=1000,
    )
