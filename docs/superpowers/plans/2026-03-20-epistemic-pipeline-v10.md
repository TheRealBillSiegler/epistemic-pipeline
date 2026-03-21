# Epistemic Pipeline v1.0 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add State-Space Search and MDP encodings, tool/LLM integration interfaces, and adaptive meta-layer to complete the v1.0 expressiveness suite.

**Architecture:** Four independent parts built sequentially: (1) Search encoding, (2) MDP encoding, (3) Tool/LLM interfaces, (4) Adaptive meta-layer. Each part has its own test file. All 74 v0.2 tests must pass after each part.

**Tech Stack:** Python 3.14+, uv, pytest, pyright, ruff, frozen dataclasses, zero dependencies.

**Spec:** `docs/superpowers/specs/2026-03-20-epistemic-pipeline-v10-design.md`

**Style:** Graduate-level ideas in 8th-grade sentences. Short sentences, active voice, Google-style docstrings.

---

## Part 1: State-Space Search Encoding

### Task 1: Search Types and Revision Policy

**Files:**

- Create: `src/epistemic_pipeline/encodings/search.py`
- Create: `tests/test_search.py`

- [ ] **Step 1: Write tests for search types and A* pathfinding**

Create `tests/test_search.py` with the weighted graph pathfinding problem. The graph:

```text
A -1- B -2- C
|         |
4         1
|         |
C ------- D -3- E
     (via B-C edge above)
```

Edges: A-B:1, A-C:4, B-C:2, B-D:5, C-D:1, D-E:3. Optimal A->E path: A->B->C->D->E cost 7.

Tests needed:

- `TestSearchTypes`: frozen dataclasses (SearchOperator, SearchOntology, SearchBeliefs, SearchNode)
- `TestSearchOntologyAdequacy`: adequate with known/unknown states, empty evidence, search_step skip
- `TestSearchUpdate`: single expansion adds successors, goal found returns path
- `TestPathfindingPipeline`: finds optimal path (cost 7), goal reached, trace preserved, meta returns ACCEPT, evidence records search steps
- `TestSearchEdgeCases`: unreachable goal flags empty_frontier, empty frontier returns unchanged

Key test: `test_finds_optimal_path` — the A* heuristic must be admissible. Use straight-line distance estimates: h(A)=6, h(B)=5, h(C)=3, h(D)=3, h(E)=0.

The SearchOperator `applicable` field is `Callable[[str], bool]` — a function that checks if the operator can be applied in a given state. For graph search, each edge becomes two operators (one per direction), each applicable only at its source node.

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_search.py -v`

- [ ] **Step 3: Implement search.py**

Create `src/epistemic_pipeline/encodings/search.py` following the STRIPS encoding pattern:

- `SearchOperator`: frozen dataclass with `name`, `applicable: Callable[[str], bool]`, `apply: Callable[[str], str]`, `cost: Callable[[str], float]`
- `SearchNode`: frozen dataclass with `state`, `path: tuple[str, ...]`, `cost: float`, `priority: float`
- `SearchOntology`: frozen dataclass with `states`, `operators`, `goal_test: Callable[[str], bool]`, `heuristic: Callable[[str], float]`, `adequate()` method
- `SearchBeliefs`: frozen dataclass with `frontier: tuple[SearchNode, ...]`, `explored: frozenset[str]`, `best_path`, `best_cost`
- `search_update()`: expand best node (lowest priority), generate successors with priority = g + h, skip explored. **Sort frontier by priority after insertion** (A* requires best-first).
- `SearchProblem`: frozen dataclass with problem spec
- Six stage functions: `search_frame`, `search_decompose` (no-op), `search_model` (no-op), `search_select`, `search_test`, `search_integrate`
- `run_search_pipeline()` convenience function

The `search_test` stage loops through pending `search_step` observations. Each triggers one expansion. Stop when goal found or frontier empty.

The `adequate()` method on `SearchOntology`: check that every non-search_step observation's variable is a known state.

- [ ] **Step 4: Run all tests**

Run: `uv run pytest tests/ -v`
Expected: All pass (new + 74 existing).

- [ ] **Step 5: Run pyright and ruff**

Run: `uv run pyright src/epistemic_pipeline/encodings/search.py tests/test_search.py && uv run ruff check src/epistemic_pipeline/encodings/search.py tests/test_search.py`

- [ ] **Step 6: Commit**

```bash
git add src/epistemic_pipeline/encodings/search.py tests/test_search.py
git commit -m "feat: state-space search encoding — A* pathfinding"
```

---

## Part 2: MDP Encoding

### Task 2: MDP Types, Bellman Updates, and Grid World

**Files:**

- Create: `src/epistemic_pipeline/encodings/mdp.py`
- Create: `tests/test_mdp.py`

- [ ] **Step 1: Write tests for MDP types and grid world**

Create `tests/test_mdp.py` with the 4x3 grid world (Russell & Norvig style):

```text
States as "col_row":
  "0_2" "1_2" "2_2" "3_2"(+1 terminal)
  "0_1"  wall "2_1" "3_1"(-1 terminal)
  "0_0" "1_0" "2_0" "3_0"
```

Actions: up, down, left, right. Transitions: 0.8 intended, 0.1 each perpendicular. Wall/edge = stay.

Rewards: state-only. R("3_2")=+1.0, R("3_1")=-1.0, R(other)=-0.04. Use `dict[str, float]`.

Tests needed:

- `TestMDPTypes`: frozen dataclasses (MDPOntology, MDPBeliefs)
- `TestMDPOntologyAdequacy`: adequate with known/unknown states, empty evidence, bellman_sweep skip
- `TestMDPUpdate`: single Bellman sweep changes values, convergence detected
- `TestGridWorldPipeline`: converges, optimal policy avoids -1 terminal, policy at "2_1" is not "right" (that leads to -1), trace preserved, meta returns ACCEPT
- `TestMDPEdgeCases`: already converged returns unchanged

Key tests:
- `test_optimal_policy_avoids_negative_terminal`: policy at "2_1" should NOT be "right" (toward -1 terminal)
- `test_converges`: `result.final_state.beliefs.converged is True`
- `test_positive_terminal_has_highest_value`: V("3_2") is the highest value

The `MDPOntology.get_reward(state, action)` method: if rewards dict has `(state, action)` tuple keys, use that. If it has plain string keys, use `rewards[state]`. Return 0.0 if not found.

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_mdp.py -v`

- [ ] **Step 3: Implement mdp.py**

Create `src/epistemic_pipeline/encodings/mdp.py`:

- `MDPOntology`: frozen dataclass with `states`, `actions`, `transitions`, `rewards: dict[tuple[str, str], float] | dict[str, float]`, `discount`, `terminal_states`, `epsilon`. Methods: `get_reward()`, `adequate()`.
- `MDPBeliefs`: frozen dataclass with `value_function: dict[str, float]`, `policy: dict[str, str]`, `iteration: int`, `converged: bool`.
- `mdp_update()`: one Bellman sweep. For each non-terminal state, compute Q(s,a) for all actions, set V(s) = max Q, policy(s) = argmax Q. Track delta. Set converged = (delta < epsilon).
- `MDPProblem`: frozen dataclass with problem spec, `max_iterations: int = 1000`.
- Six stage functions following the pattern.
- `mdp_test`: loop Bellman sweeps via synthetic `bellman_sweep` observations. Stop on convergence or max iterations. Flag `"value_divergence"` if not converged.
- `run_mdp_pipeline()` convenience function.

The `adequate()` method: skip `bellman_sweep` observations, check state names against known states.

- [ ] **Step 4: Run all tests**

Run: `uv run pytest tests/ -v`
Expected: All pass (new + 74 existing).

- [ ] **Step 5: Run pyright and ruff**

Run: `uv run pyright src/epistemic_pipeline/encodings/mdp.py tests/test_mdp.py && uv run ruff check src/epistemic_pipeline/encodings/mdp.py tests/test_mdp.py`

- [ ] **Step 6: Commit**

```bash
git add src/epistemic_pipeline/encodings/mdp.py tests/test_mdp.py
git commit -m "feat: MDP encoding — grid world value iteration"
```

---

## Part 3: Tool & LLM Integration

### Task 3: Observation modality field

**Files:**

- Modify: `src/epistemic_pipeline/state.py`

- [ ] **Step 1: Add modality field to Observation**

Add `modality: str | None = None` as the last field of `Observation`. Default None preserves backward compatibility.

- [ ] **Step 2: Run existing tests**

Run: `uv run pytest tests/ -v`
Expected: All pass.

- [ ] **Step 3: Commit**

```bash
git add src/epistemic_pipeline/state.py
git commit -m "feat: add modality field to Observation"
```

### Task 4: Tool Interfaces

**Files:**

- Create: `src/epistemic_pipeline/tools/__init__.py`
- Create: `src/epistemic_pipeline/tools/tool_interfaces.py`
- Create: `tests/test_tool_integration.py`

- [ ] **Step 1: Write tests**

Create `tests/test_tool_integration.py`:

- `TestToolResult`: frozen, fields accessible
- `TestMockTool`: returns canned response for known tool, raises KeyError for unknown tool
- `TestToolEvidenceAdapter`: converts ToolResult to Observation with `modality="tool"`, `etype=EvidenceType.MEASUREMENT`, confidence from tool success (1.0 if success, 0.5 if not), variable=tool name, value=str(output)
- `TestToolIntegration`: create MockTool, invoke, adapt to Observation, verify fields

- [ ] **Step 2: Implement tool_interfaces.py**

```python
@dataclass(frozen=True)
class ToolResult:
    name: str
    output: dict[str, object]
    success: bool

class ToolInterface(Protocol):
    def invoke(self, name: str, args: dict[str, object]) -> ToolResult: ...

class ToolEvidenceAdapter:
    def adapt(self, result: ToolResult, timestamp: float) -> Observation: ...

class MockTool:
    def __init__(self, responses: dict[str, ToolResult]) -> None: ...
    def invoke(self, name: str, args: dict[str, object]) -> ToolResult: ...
```

Create `src/epistemic_pipeline/tools/__init__.py` with exports.

- [ ] **Step 3: Run all tests, pyright, ruff**

- [ ] **Step 4: Commit**

```bash
git add src/epistemic_pipeline/tools/ tests/test_tool_integration.py
git commit -m "feat: tool interfaces — ToolResult, MockTool, ToolEvidenceAdapter"
```

### Task 5: LLM Interfaces

**Files:**

- Create: `src/epistemic_pipeline/llm/__init__.py`
- Create: `src/epistemic_pipeline/llm/llm_interfaces.py`
- Create: `tests/test_llm_integration.py`

- [ ] **Step 1: Write tests**

Create `tests/test_llm_integration.py`:

- `TestLLMResponse`: frozen, fields accessible
- `TestMockLLM`: returns canned response for each method, maps by problem/state_description string
- `TestLLMEvidenceAdapter`: converts LLMResponse to Observation with `modality="llm"`, `etype=EvidenceType.REPORT`, confidence from response.confidence, variable from caller, value=response.content
- `TestLLMIntegration`: create MockLLM, call propose_ontology, adapt to Observation, verify fields

- [ ] **Step 2: Implement llm_interfaces.py**

```python
@dataclass(frozen=True)
class LLMResponse:
    content: str
    confidence: float

class LLMInterface(Protocol):
    def propose_ontology(self, problem: str) -> LLMResponse: ...
    def decompose(self, problem: str) -> LLMResponse: ...
    def propose_strategy(self, state_description: str) -> LLMResponse: ...
    def generate_explanation(self, state_description: str) -> LLMResponse: ...

class LLMEvidenceAdapter:
    def adapt(self, response: LLMResponse, variable: str, timestamp: float) -> Observation: ...

class MockLLM:
    def __init__(self, responses: dict[str, LLMResponse]) -> None: ...
    def propose_ontology(self, problem: str) -> LLMResponse: ...
    def decompose(self, problem: str) -> LLMResponse: ...
    def propose_strategy(self, state_description: str) -> LLMResponse: ...
    def generate_explanation(self, state_description: str) -> LLMResponse: ...
```

Create `src/epistemic_pipeline/llm/__init__.py` with exports.

- [ ] **Step 3: Run all tests, pyright, ruff**

- [ ] **Step 4: Commit**

```bash
git add src/epistemic_pipeline/llm/ tests/test_llm_integration.py
git commit -m "feat: LLM interfaces — LLMResponse, MockLLM, LLMEvidenceAdapter"
```

---

## Part 4: Adaptive Meta-Layer

### Task 6: Extended MetaThresholds and Adaptive MetaController

**Files:**

- Modify: `src/epistemic_pipeline/meta.py`
- Create: `tests/test_meta_v1.py`

- [ ] **Step 1: Write tests for v1.0 meta-layer**

Create `tests/test_meta_v1.py`:

**Budget tests:**
- `test_budget_exhaustion_escalates`: after K_max interventions, unconditionally ESCALATE
- `test_budget_tracks_non_accept_decisions`: ACCEPT doesn't increment counter
- `test_budget_resets_description`: verify details say "budget_exhausted"

**Cycle detection tests:**
- `test_cycle_detected_same_trigger_and_action`: same (trigger, corrective_action) pair twice in a row -> ESCALATE
- `test_no_cycle_different_reasons`: two REFRAMEs for different triggers are legitimate
- `test_cycle_details`: verify details say "cycle_detected"

**New trigger tests:**
- `test_value_divergence_triggers_switch`: "value_divergence" in anomalies -> SWITCH_STRATEGY
- `test_tool_disagreement_triggers_switch`: "tool_disagreement" in anomalies -> SWITCH_STRATEGY with corrective_action "request_tool_evidence"
- `test_llm_disagreement_triggers_switch`: "llm_disagreement" in anomalies -> SWITCH_STRATEGY with corrective_action "request_llm_proposal"
- `test_causal_inconsistency_triggers_escalate`: "causal_inconsistency" in anomalies -> ESCALATE
- `test_paradigm_mismatch_triggers_reframe`: "paradigm_mismatch" in anomalies -> REFRAME

**Priority tests:**
- `test_budget_beats_everything`: budget exhaustion overrides all other triggers
- `test_cycle_beats_normal_triggers`: cycle detection overrides normal trigger logic
- `test_causal_inconsistency_beats_reframe`: ESCALATE priority over REFRAME

**Corrective action tests:**
- `test_corrective_action_in_details`: non-ACCEPT results include corrective_action field
- `test_reframe_corrective_action`: REFRAME suggests "reframe_ontology"

All tests construct `MetaController` with `MetaThresholds(max_interventions=3)` or similar small values for testability. Use `EpistemicState` with mock metadata containing the relevant anomalies.

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_meta_v1.py -v`

- [ ] **Step 3: Extend MetaThresholds**

Add to `MetaThresholds`:

```python
    value_divergence_threshold: float = 0.01
    max_interventions: int = 5
```

- [ ] **Step 4: Add intervention tracking to MetaController**

Add `intervention_count: int = 0` and `last_trigger: tuple[str, str] | None = None` as mutable state on `MetaController.__init__`.

Update `monitor()` with the v1.0 priority order:

1. Budget exhaustion: `intervention_count >= max_interventions` -> ESCALATE
2. Cycle detection: current (trigger, action) == last_trigger -> ESCALATE
3. ESCALATE triggers: repeated contradictions, causal_inconsistency
4. REFRAME triggers: ontology inadequate, low reliability, paradigm_mismatch
5. SWITCH_STRATEGY triggers: high efficiency, oscillation, tool_disagreement, llm_disagreement, value_divergence
6. ACCEPT: default

For non-ACCEPT decisions: increment `intervention_count`, update `last_trigger`.

Each decision includes a `corrective_action` in details:
- ESCALATE: no corrective action (problem is beyond capabilities)
- REFRAME: `"reframe_ontology"` or `"switch_paradigm"` (for paradigm_mismatch)
- SWITCH_STRATEGY: `"request_tool_evidence"` (tool_disagreement), `"request_llm_proposal"` (llm_disagreement), or `"switch_strategy"` (others)

- [ ] **Step 5: Run all tests**

Run: `uv run pytest tests/ -v`
Expected: All pass (new + all existing including v0.2 meta tests).

- [ ] **Step 6: Run pyright and ruff**

- [ ] **Step 7: Commit**

```bash
git add src/epistemic_pipeline/meta.py tests/test_meta_v1.py
git commit -m "feat: adaptive meta-layer — intervention budget, cycle detection, v1.0 triggers"
```

---

## Part 5: Final Verification and Exports

### Task 7: Update Exports and Verify

**Files:**

- Modify: `src/epistemic_pipeline/encodings/__init__.py`
- Modify: `src/epistemic_pipeline/__init__.py`

- [ ] **Step 1: Update encodings `__init__.py`**

Add Search and MDP exports.

- [ ] **Step 2: Run full test suite**

Run: `uv run pytest tests/ -v --tb=short`

- [ ] **Step 3: Run type checker**

Run: `uv run pyright src/ tests/`

- [ ] **Step 4: Run linter**

Run: `uv run ruff check src/ tests/`

- [ ] **Step 5: Verify v1.0 completion criteria**

1. State-Space Search encoding with A* pathfinding ✓
2. MDP encoding with grid world value iteration ✓
3. Tool integration: ToolInterface, ToolResult, MockTool, adapter ✓
4. LLM integration: LLMInterface, LLMResponse, MockLLM, adapter ✓
5. Observation.modality field ✓
6. Adaptive meta-layer with v1.0 triggers ✓
7. Intervention budget with K_max ✓
8. Cycle detection on (trigger, action) pairs ✓
9. All v0.2 tests pass ✓
10. All new tests pass ✓
11. pyright passes ✓
12. ruff passes ✓

- [ ] **Step 6: Commit**

```bash
git add src/epistemic_pipeline/encodings/__init__.py src/epistemic_pipeline/__init__.py
git commit -m "feat: complete v1.0 — exports, verification, all criteria met"
```
