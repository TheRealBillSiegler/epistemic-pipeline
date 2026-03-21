# Epistemic Pipeline v1.0 Design Specification

**Date:** 2026-03-20
**Status:** Approved
**Delta from v0.2:** State-Space Search encoding, MDP encoding, tool/LLM integration interfaces, adaptive meta-layer with intervention budget and cycle detection.

---

## Part 1: State-Space Search Encoding

### 1.1 Types

```python
@dataclass(frozen=True)
class SearchOperator:
    """One search operator with a precondition test and cost.

    name: operator identifier (e.g. "move_A_to_B").
    applicable: function that returns True if the operator can
        be applied in the given state. Operators are defined by
        preconditions, not by enumerating states.
    apply: function that returns the new state after applying
        the operator.
    cost: function that returns the cost of applying the operator
        from the given state. Default is 1.0 for uniform cost.
    """

    name: str
    applicable: Callable[[str], bool]
    apply: Callable[[str], str]
    cost: Callable[[str], float]


@dataclass(frozen=True)
class SearchNode:
    """One node in the search frontier.

    state: the current state identifier.
    path: sequence of operator names that led here.
    cost: total path cost from the start state.
    priority: cost + heuristic(state) for A* ordering.
    """

    state: str
    path: tuple[str, ...]
    cost: float
    priority: float


@dataclass(frozen=True)
class SearchOntology:
    """Search ontology: states, operators, goal test, heuristic.

    states: all valid state identifiers in the problem space.
    operators: available search operators.
    goal_test: returns True if a state is a goal state.
    heuristic: estimated cost from a state to the nearest goal.
        Must be admissible (never overestimates) for A* optimality.
    """

    states: frozenset[str]
    operators: tuple[SearchOperator, ...]
    goal_test: Callable[[str], bool]
    heuristic: Callable[[str], float]

    def adequate(self, evidence: tuple[Observation, ...]) -> bool:
        """Every state mentioned in evidence is known."""
        ...


@dataclass(frozen=True)
class SearchBeliefs:
    """Search state: frontier, explored set, best solution so far.

    frontier: nodes to explore, ordered by priority.
    explored: states already visited.
    best_path: operator names in the best solution found so far.
    best_cost: cost of the best solution found so far.
    """

    frontier: tuple[SearchNode, ...]
    explored: frozenset[str]
    best_path: tuple[str, ...] | None = None
    best_cost: float | None = None
```

### 1.2 Revision Policy

`search_update(beliefs, evidence, ontology) -> SearchBeliefs`

One call expands the best node (lowest priority):

1. Pop node with lowest priority from frontier.
2. If node's state satisfies goal_test, record as best solution.
3. Otherwise, for each operator applicable to the current state, generate the successor. Skip explored states. Add to frontier with `priority = cost + heuristic(state)`.
4. Add current state to explored set.

### 1.3 Pipeline Stages

- **Frame:** Build `SearchOntology` from problem spec. Initialize frontier with start node. Create synthetic `search_step` observations.
- **Decompose:** No-op for basic search.
- **Model:** No-op. R set in Frame.
- **Select:** Record heuristic choice in metadata.
- **Test:** Run search iterations. Stop on goal found or empty frontier.
- **Integrate:** Extract best path.

### 1.4 Toy Problem: Weighted Graph Pathfinding

```text
Nodes: A, B, C, D, E
Edges (bidirectional, weighted):
  A-B: 1, A-C: 4, B-C: 2, B-D: 5, C-D: 1, D-E: 3
Goal: reach E from A
Optimal path: A -> B -> C -> D -> E (cost 7)
Heuristic: straight-line estimates (admissible)
```

### 1.5 SearchProblem

```python
@dataclass(frozen=True)
class SearchProblem:
    states: frozenset[str]
    operators: tuple[SearchOperator, ...]
    goal_test: Callable[[str], bool]
    heuristic: Callable[[str], float]
    initial_state: str
    max_search_steps: int = 1000
```

---

## Part 2: MDP Encoding

### 2.1 Types

```python
@dataclass(frozen=True)
class MDPOntology:
    """MDP ontology: states, actions, transitions, rewards, discount.

    states: all state identifiers.
    actions: available action names.
    transitions: T(s, a, s') -> probability. Keyed by (state, action, next_state).
    rewards: R(s, a) -> reward OR R(s) -> reward. Supports both
        action-dependent rewards (dict[tuple[str, str], float]) and
        state-only rewards (dict[str, float]). State-only rewards
        apply regardless of action.
    discount: gamma in [0, 1). How much to weight future rewards.
    terminal_states: states where no actions are available.
    epsilon: convergence threshold for value iteration.
    """

    states: frozenset[str]
    actions: tuple[str, ...]
    transitions: dict[tuple[str, str, str], float]
    rewards: dict[tuple[str, str], float] | dict[str, float]
    discount: float
    terminal_states: frozenset[str] = frozenset()
    epsilon: float = 1e-6

    def get_reward(self, state: str, action: str) -> float:
        """Get reward for a state-action pair.

        Checks action-dependent rewards first, then state-only.
        """
        ...

    def adequate(self, evidence: tuple[Observation, ...]) -> bool:
        """Every state mentioned in evidence is known."""
        ...


@dataclass(frozen=True)
class MDPBeliefs:
    """MDP beliefs: value function, policy, convergence status.

    value_function: V(s) for each state.
    policy: best action for each state.
    iteration: number of Bellman sweeps completed.
    converged: True when max|V'-V| < epsilon.
    """

    value_function: dict[str, float]
    policy: dict[str, str]
    iteration: int = 0
    converged: bool = False
```

### 2.2 Revision Policy

`mdp_update(beliefs, evidence, ontology) -> MDPBeliefs`

One call performs one full Bellman sweep:

```text
For each non-terminal state s:
    For each action a:
        Q(s,a) = R(s,a) + gamma * sum_s'( T(s,a,s') * V(s') )
    V'(s) = max_a Q(s,a)
    policy(s) = argmax_a Q(s,a)
delta = max_s |V'(s) - V(s)|
converged = (delta < epsilon)
```

### 2.3 Pipeline Stages

- **Frame:** Build `MDPOntology`. Initialize value function to zeros. Create synthetic `bellman_sweep` observations.
- **Decompose:** No-op.
- **Model:** No-op.
- **Select:** Record strategy in metadata.
- **Test:** Run Bellman sweeps. Stop when converged or max iterations reached. Flag `"value_divergence"` if not converged after all sweeps.
- **Integrate:** Extract optimal policy.

### 2.4 Toy Problem: 4x3 Grid World

Russell & Norvig style grid world:

```text
+---+---+---+---+
| 0 | 1 | 2 |+1 |   (0,0) to (3,2) coordinates as "r_c" strings
+---+---+---+---+
| 3 |   | 5 |-1 |   Cell 4 is a wall (not in states)
+---+---+---+---+
| 6 | 7 | 8 | 9 |
+---+---+---+---+

States: "0_0", "1_0", "2_0", "0_1", "2_1", "0_2", "1_2", "2_2", "3_2"
    plus terminal "3_0" (+1) and "3_1" (-1)
Actions: up, down, left, right
Transitions: 0.8 intended direction, 0.1 each perpendicular. Wall = stay.
Rewards: R("3_0") = +1.0, R("3_1") = -1.0, R(other) = -0.04
Discount: 0.9
```

Expected: optimal policy avoids the -1 terminal. States near -1 terminal move away from it.

---

## Part 3: Tool & LLM Integration

### 3.1 State Extension

`Observation` gains `modality: str | None = None`. Default preserves backward compatibility. Values: `"tool"`, `"llm"`, `"sensor"`, `"text"`, or None for v0.1/v0.2 observations.

### 3.2 Tool Interfaces (`tools/tool_interfaces.py`)

```python
@dataclass(frozen=True)
class ToolResult:
    """Output from a tool invocation.

    name: which tool was called.
    output: structured output data.
    success: True if the tool call succeeded.
    """

    name: str
    output: dict[str, object]
    success: bool


class ToolInterface(Protocol):
    """Protocol for tool implementations."""

    def invoke(self, name: str, args: dict[str, object]) -> ToolResult:
        """Call a tool by name with arguments."""
        ...


class ToolEvidenceAdapter:
    """Converts ToolResult to Observation with modality='tool'."""

    def adapt(self, result: ToolResult, timestamp: float) -> Observation:
        """Convert a tool result to an observation."""
        ...


class MockTool:
    """Test implementation. Returns canned responses."""

    def __init__(self, responses: dict[str, ToolResult]) -> None: ...
    def invoke(self, name: str, args: dict[str, object]) -> ToolResult: ...
```

### 3.3 LLM Interfaces (`llm/llm_interfaces.py`)

```python
@dataclass(frozen=True)
class LLMResponse:
    """Output from an LLM call.

    content: the generated text or structured response.
    confidence: model's self-assessed confidence in [0, 1].
    """

    content: str
    confidence: float


class LLMInterface(Protocol):
    """Protocol for LLM implementations."""

    def propose_ontology(self, problem: str) -> LLMResponse: ...
    def decompose(self, problem: str) -> LLMResponse: ...
    def propose_strategy(self, state_description: str) -> LLMResponse: ...
    def generate_explanation(self, state_description: str) -> LLMResponse: ...


class LLMEvidenceAdapter:
    """Converts LLMResponse to Observation with modality='llm'."""

    def adapt(
        self, response: LLMResponse, variable: str, timestamp: float,
    ) -> Observation:
        """Convert an LLM response to an observation."""
        ...


class MockLLM:
    """Test implementation. Returns canned responses."""

    def __init__(self, responses: dict[str, LLMResponse]) -> None: ...
    def propose_ontology(self, problem: str) -> LLMResponse: ...
    def decompose(self, problem: str) -> LLMResponse: ...
    def propose_strategy(self, state_description: str) -> LLMResponse: ...
    def generate_explanation(self, state_description: str) -> LLMResponse: ...
```

---

## Part 4: Adaptive Meta-Layer

### 4.1 New Triggers

Added to the v0.2 trigger set (repeated contradictions, low reliability, inadequacy, oscillation, high efficiency):

- **paradigm_mismatch:** norm scores suggest the encoding is wrong for the problem (e.g., using Bayesian for a planning problem).
- **tool_disagreement:** tool evidence (`modality="tool"`) contradicts current beliefs.
- **llm_disagreement:** LLM proposal (`modality="llm"`) contradicts current ontology or strategy.
- **causal_inconsistency:** evidence violates causal structure declared in ontology (if present).
- **value_divergence:** MDP value function not converging after expected iterations.

### 4.2 Extended MetaThresholds

```python
@dataclass(frozen=True)
class MetaThresholds:
    # v0.2 fields (unchanged)
    reliability_min: float = 0.5
    efficiency_ratio_max: float = 2.0
    expected_efficiency: int = 10
    # v1.0 additions
    value_divergence_threshold: float = 0.01
    max_interventions: int = 5  # K_max
```

### 4.3 Intervention Budget

`MetaController` tracks:

- `intervention_count: int` — how many non-ACCEPT decisions have been made.
- `last_trigger: tuple[str, str] | None` — the `(trigger_type, corrective_action)` pair from the last non-ACCEPT decision.

**Budget exhaustion:** When `intervention_count >= max_interventions`, unconditionally return ESCALATE with `"trigger": "budget_exhausted"`.

**Cycle detection:** If the current `(trigger_type, corrective_action)` pair equals `last_trigger`, return ESCALATE with `"trigger": "cycle_detected"`. Two consecutive REFRAMEs for different reasons are legitimate. Two REFRAMEs both triggered by the same reason with the same corrective action are a cycle.

### 4.4 Corrective Actions

`MetaResult.details` can include a `"corrective_action"` key:

- `"request_tool_evidence"` — recommend calling a tool for more data.
- `"request_llm_proposal"` — recommend asking an LLM for a new ontology/strategy.
- `"switch_paradigm"` — recommend changing the reasoning encoding.
- `"reframe_ontology"` — recommend restructuring the ontology.

### 4.5 Priority Order (v1.0)

1. **Budget exhaustion** (highest) — `k >= K_max`.
2. **Cycle detection** — same (trigger, action) pair recurring.
3. **ESCALATE** — repeated contradictions, causal inconsistency.
4. **REFRAME** — ontology inadequate, low reliability, paradigm mismatch.
5. **SWITCH_STRATEGY** — high efficiency, oscillation, tool/LLM disagreement, value divergence.
6. **ACCEPT** — default.

---

## File Structure

```text
src/epistemic_pipeline/
    state.py              # +modality field on Observation
    pipeline.py           # unchanged
    norms.py              # unchanged
    meta.py               # adaptive meta-layer with budget + cycle detection
    encodings/
        __init__.py       # +search, mdp exports
        bayes.py          # unchanged
        strips.py         # unchanged
        search.py         # NEW: state-space search encoding
        mdp.py            # NEW: MDP encoding
    tools/
        __init__.py
        tool_interfaces.py  # NEW: ToolInterface, ToolResult, MockTool, adapter
    llm/
        __init__.py
        llm_interfaces.py   # NEW: LLMInterface, LLMResponse, MockLLM, adapter
tests/
    test_bayes.py         # UNCHANGED
    test_meta.py          # UNCHANGED
    test_meta_decisions.py # UNCHANGED
    test_strips.py        # UNCHANGED
    test_search.py        # NEW: pathfinding with A*
    test_mdp.py           # NEW: grid world value iteration
    test_tool_integration.py  # NEW: MockTool + adapter
    test_llm_integration.py   # NEW: MockLLM + adapter
    test_meta_v1.py       # NEW: adaptive meta-layer triggers + budget
```

---

## Completion Criteria

1. State-Space Search encoding implemented with A* pathfinding test
2. MDP encoding implemented with grid world test (optimal policy verified)
3. Tool integration: ToolInterface protocol, ToolResult, ToolEvidenceAdapter, MockTool
4. LLM integration: LLMInterface protocol, LLMResponse, LLMEvidenceAdapter, MockLLM
5. Observation gains `modality: str | None = None` field
6. Adaptive meta-layer: paradigm mismatch, tool/LLM disagreement, causal inconsistency, value divergence triggers
7. Intervention budget with K_max and unconditional escalation
8. Cycle detection on (trigger_type, corrective_action) pairs
9. All 74 v0.1/v0.2 tests still pass
10. All new tests pass
11. Type checking passes (pyright)
12. Linting passes (ruff)
