# Epistemic Pipeline v0.2 Design Specification

**Date:** 2026-03-20
**Status:** Approved
**Delta from v0.1:** Functional meta-layer, extended norms, STRIPS encoding, evidence confidence, strategy switching, ontology adequacy, anomaly detection.

---

## 1. State Model Extensions

### 1.1 Evidence

`Observation` gains two fields:

```python
class EvidenceType(Enum):
    OBSERVATION = "observation"   # direct sensory input
    REPORT = "report"             # secondhand testimony
    MEASUREMENT = "measurement"   # instrument reading

@dataclass(frozen=True)
class Observation:
    variable: str
    value: str
    source: str
    timestamp: float
    confidence: float = 1.0       # float in [0, 1]; 1.0 = fully trusted
    etype: EvidenceType = EvidenceType.OBSERVATION
```

`confidence` controls how much an observation moves beliefs. `etype` labels the evidence modality. Both default to v0.1 behavior so existing code is unaffected.

### 1.2 Metadata

`Metadata` gains three new fields. All existing defaults are preserved — v0.1 code that constructs `Metadata()` with no arguments still works.

```python
@dataclass(frozen=True)
class Metadata:
    # v0.1 fields (all have defaults, unchanged)
    decomposition: tuple[str, ...] = ()
    strategy: str = ""
    evidence_order: tuple[str, ...] = ()
    anomalies: tuple[str, ...] = ()
    pending_observations: tuple[Observation, ...] = ()
    # v0.2 additions
    anomaly_checks: tuple[str, ...] = ()     # names of checks to run
    heuristics: tuple[str, ...] = ()          # names of heuristics in use
    strategy_switches: int = 0                # count of strategy changes
```

### 1.3 Ontology Adequacy

Ontology types gain an `adequate` method. This is an ontological commitment: the ontology itself knows whether it covers the evidence.

```python
# Protocol (not enforced at type level in v0.2, but followed by convention)
class OntologyWithAdequacy:
    def adequate(self, evidence: tuple[Observation, ...]) -> bool: ...
```

Each encoding implements this on its own ontology type.

**BayesOntology.adequate(E):** Returns True when every observation's exact `(hypothesis, variable, value)` triple has an entry in the likelihood table for at least one hypothesis. Concretely: for each observation `o`, there must exist at least one `h` in `hypotheses` such that `(h, o.variable, o.value)` is a key in `likelihoods`. An observation about a variable or value the ontology doesn't know about means the ontology is inadequate.

**STRIPSOntology.adequate(E):** Returns True when every predicate mentioned in evidence appears in the ontology's predicate set. An observation referencing an unknown predicate means the ontology is inadequate.

---

## 2. STRIPS Encoding

Second expressiveness proof. STRIPS (Stanford Research Institute Problem Solver) is a classical planning formalism. This section shows the `(O, E, B, R)` tuple can express STRIPS planning as forward-state search. Forward-state search starts from the initial state and applies actions until it reaches the goal.

### 2.1 Types

```python
@dataclass(frozen=True)
class STRIPSAction:
    name: str
    preconditions: frozenset[str]   # predicates that must be true
    add_effects: frozenset[str]     # predicates made true
    delete_effects: frozenset[str]  # predicates made false

@dataclass(frozen=True)
class STRIPSOntology:
    predicates: frozenset[str]
    actions: tuple[STRIPSAction, ...]
    goal: frozenset[str]              # goal is ontological, not a belief

    def adequate(self, evidence: tuple[Observation, ...]) -> bool:
        """Every predicate in evidence is known to the ontology."""
        ...

@dataclass(frozen=True)
class STRIPSBeliefs:
    current_state: frozenset[str]      # predicates currently true
    plan: tuple[str, ...]              # action names chosen so far
    frontier: tuple[tuple[frozenset[str], tuple[str, ...]], ...] = ()
        # each entry is (state, plan_so_far) — search needs to track
        # which actions led to each frontier state
    explored: frozenset[frozenset[str]] = frozenset()  # states already seen
```

### 2.2 Revision Policy

`STRIPSRevisionPolicy` is forward-state search:

```text
R(B, e, O) -> B'
```

One call to R expands one frontier state:

1. Pop first state from frontier.
2. If state satisfies goal, return beliefs with completed plan.
3. Otherwise, find applicable actions (preconditions met).
4. Generate successor states by applying each action.
5. Add new states to frontier (skip explored states).
6. Add current state to explored set.

The search terminates when goal is reached or frontier is empty. Each pipeline step applies R once per pending observation. In STRIPS, observations are synthetic search-step signals, not real observations. They use `variable="search_step"`, `value="expand"`, `source="planner"`, and sequential timestamps. Their role is to trigger one expansion of the frontier per call to R.

### 2.3 Pipeline Stages

- **Frame:** Parse domain (predicates, actions, goal) into `STRIPSOntology`. Set initial state as first evidence. Create `STRIPSBeliefs` with empty plan and initial frontier.
- **Decompose:** Identify subgoals (predicates in goal not yet true). Record in metadata.
- **Model:** Set revision policy to forward-state search. No-op if already set in Frame.
- **Select:** Choose heuristic (e.g., goal-count). Record in metadata.
- **Test:** Run search iterations. Each "observation" triggers one expansion step. Detect anomalies (empty frontier = unsolvable).
- **Integrate:** Extract plan from final beliefs. Report success/failure.

### 2.4 Toy Problem: Blocks World

Two blocks (A, B) on a table. Goal: stack A on B.

```text
Predicates: {on_table_A, on_table_B, clear_A, clear_B, on_A_B, holding_A}
Actions:
  pickup_A: pre={on_table_A, clear_A} add={holding_A} del={on_table_A, clear_A}
  stack_A_B: pre={holding_A, clear_B} add={on_A_B} del={holding_A, clear_B}
Goal: {on_A_B}
Initial: {on_table_A, on_table_B, clear_A, clear_B}
```

Expected plan: `[pickup_A, stack_A_B]`.

---

## 3. Confidence-Weighted Bayesian Updates

When evidence has confidence < 1.0, the effective likelihood is dampened:

```text
L_eff(e|h) = c * P(e|h) + (1 - c) * P(e)
```

where:

- `c` is `evidence.confidence`
- `P(e|h)` is the likelihood from the ontology
- `P(e) = sum_h'( P(e|h') * P(h') )` is the marginal probability

At `c = 1.0`, this reduces to standard Bayes. At `c = 0.0`, the likelihood equals the marginal for every hypothesis, so the update is a no-op (evidence carries no information).

The Bayesian revision policy signature changes:

```python
def bayes_update(beliefs, evidence, ontology) -> BayesBeliefs:
    # reads evidence.confidence internally
```

The `R(B, e, O) -> B'` signature stays the same. Confidence is part of the evidence.

---

## 4. Anomaly Detection

The Test stage checks for two anomalies after each update.

### 4.1 Oscillation

**Definition:** The MAP (maximum a posteriori) hypothesis changes 3 or more times within the last 6 evidence steps.

**Detection:** After each update, record the MAP hypothesis. Look at the last 6 MAP values. Count transitions (consecutive pairs where the hypothesis changes). If transitions >= 3, flag `"oscillation"`.

**Why a window:** A single flip is normal belief evolution. Oscillation means the evidence is pushing beliefs back and forth without convergence.

### 4.2 Contradiction

Two triggers:

1. **Same-variable conflict:** Two observations of the same variable with different values within the current pipeline run.

2. **High-confidence reversal:** A single evidence update shifts the MAP hypothesis AND the belief probability of the previously-leading hypothesis exceeded 0.8 before the update. This catches the important case where strong beliefs get suddenly overturned.

Both are recorded in `metadata.anomalies`.

---

## 5. Extended Norms

### 5.1 NormScore (Backward Compatible)

New fields all have defaults so v0.1 code that constructs `NormScore(reliability=..., efficiency=..., justification=..., power=None)` still works. The `power` field type widens from `str | None` to `str | bool | None` to accept both v0.1 (`None`) and v0.2 (`True`/`False`) values.

```python
@dataclass(frozen=True)
class NormScore:
    # v0.1 fields (unchanged)
    reliability: float                              # binary correctness (0.0 or 1.0)
    efficiency: int                                 # trace length
    justification: bool                             # replay check passes
    power: str | bool | None = None                 # v0.1: None; v0.2: adequacy(O, E)
    # v0.2 additions (all have defaults)
    calibration: float = 0.0                        # log B(h*) where h* is ground truth
    efficiency_heuristic_cost: int = 0              # heuristic evaluations
    efficiency_strategy_switches: int = 0           # strategy change count
    justification_intermediate_consistent: bool = True  # intermediate states consistent
```

### 5.2 Calibration

The log scoring rule. `calibration = log(B_final(h*))` where `h*` is the ground truth hypothesis. Perfect calibration = 0.0 (when `B(h*) = 1.0`). Worse calibration = more negative. If `B(h*) = 0`, report `float('-inf')`.

### 5.3 Efficiency

Three components:

- **Trace length:** Number of states in the trace (same as v0.1).
- **Heuristic cost:** Number of search steps (frontier expansions). For Bayesian, this is 0. For STRIPS, this is the number of search-step observations in the evidence. The scorer takes an optional `heuristic_cost: int | None` parameter. If not provided, defaults to 0.
- **Strategy switches:** Read from `metadata.strategy_switches` on the final state.

### 5.4 Justification

Two checks:

- **Replay:** Same as v0.1 — replay R over E from B_0, verify B_final matches.
- **Intermediate consistency:** For each intermediate state in the trace, verify beliefs are internally consistent (e.g., probabilities sum to 1.0 for Bayesian, no contradictory predicates for STRIPS). The scorer takes an optional `belief_consistent: Callable[[B, O], bool]` parameter. If not provided, intermediate consistency defaults to `True` (v0.1 behavior).

### 5.5 Power

```text
power = O.adequate(E)
```

True if the ontology covers all the evidence. The scorer takes an optional `ontology_adequate: Callable[[O, tuple[Observation, ...]], bool]` parameter. If not provided, power defaults to `None` (v0.1 behavior).

### 5.6 score_pipeline_run Signature (v0.2)

```python
def score_pipeline_run[O, B](
    trace: tuple[EpistemicState[O, B], ...],
    ground_truth: str,
    belief_argmax: Callable[[B], str],
    *,
    # v0.2 optional parameters (keyword-only, all have defaults)
    belief_probability: Callable[[B, str], float] | None = None,  # B(h) -> float
    belief_consistent: Callable[[B, O], bool] | None = None,      # consistent(B, O)?
    ontology_adequate: Callable[[O, tuple[Observation, ...]], bool] | None = None,
    heuristic_cost: int | None = None,  # number of search steps (frontier expansions)
) -> NormScore:
```

All new parameters are keyword-only with `None` defaults. When `None`, the scorer uses v0.1 behavior for that norm. This preserves full backward compatibility.

---

## 6. Functional Meta-Layer

The `MetaController` gains a `thresholds` field and real decision logic.

### 6.1 Configuration

`MetaThresholds` is a frozen dataclass stored as a field on `MetaController`. The controller reads thresholds during `monitor()`.

```python
@dataclass(frozen=True)
class MetaThresholds:
    reliability_min: float = 0.5
    efficiency_ratio_max: float = 2.0
    expected_efficiency: int = 10

class MetaController:
    def __init__(self, thresholds: MetaThresholds | None = None) -> None:
        self.thresholds = thresholds or MetaThresholds()
```

When `scores` is `None` (no norms computed yet), the controller can only fire anomaly-based triggers (ESCALATE from contradictions, SWITCH_STRATEGY from oscillation). Score-based triggers (REFRAME from low reliability, SWITCH_STRATEGY from high efficiency) require `scores` to be provided.

### 6.2 Decision Rules

`monitor()` evaluates triggers in priority order:

1. **ESCALATE** (highest priority): `"contradiction"` appears in anomalies more than once across the trace.
2. **REFRAME:** `power is False` (ontology inadequate) OR `reliability < reliability_min`.
3. **SWITCH_STRATEGY:** `efficiency > efficiency_ratio_max * expected_efficiency` OR `"oscillation"` in anomalies.
4. **ACCEPT:** No triggers fired.

First trigger that fires wins. This priority order ensures safety: escalation beats reframing beats strategy switching.

### 6.3 Signature

```python
def monitor(
    self,
    trace: tuple[EpistemicState, ...],
    scores: NormScore | None,
    ontology: object,
    strategy: str,
    decomposition: tuple[str, ...],
) -> MetaResult:
```

The `details` dict in `MetaResult` includes which trigger fired and relevant values.

---

## 7. Strategy Switching

The pipeline does not switch strategies automatically. The meta-layer recommends a switch; the caller decides what to do. This keeps the pipeline pure.

In v0.2, strategy switching means:

- The meta-layer can return `SWITCH_STRATEGY` with a reason.
- The `metadata.strategy_switches` counter tracks how many times this happened.
- The caller (or a future outer loop) acts on the recommendation.

---

## 8. File Structure

```text
src/epistemic_pipeline/
    state.py              # extended with confidence, etype, EvidenceType
    pipeline.py           # unchanged
    norms.py              # extended with calibration, heuristic cost, consistency, power
    meta.py               # functional decision logic + MetaThresholds
    encodings/
        __init__.py
        bayes.py          # confidence-weighted updates, anomaly detection, adequate()
        strips.py         # NEW: STRIPS encoding
tests/
    test_bayes.py         # UNCHANGED (v0.1 tests preserved)
    test_meta.py          # UNCHANGED (v0.1 tests preserved)
    test_strips.py        # NEW: STRIPS planning BDD scenarios
    test_meta_decisions.py # NEW: meta-layer decision BDD scenarios
```

---

## 9. Completion Criteria

1. Evidence confidence field implemented (`float` in `[0, 1]`)
2. Evidence etype field (`observation`, `report`, `measurement`)
3. Confidence-weighted Bayesian updates: `L_eff(e|h) = c*P(e|h) + (1-c)*P(e)`
4. STRIPS encoding (`STRIPSOntology` with goal, `STRIPSBeliefs` with frontier + explored, `STRIPSRevisionPolicy` as forward-state search)
5. Strategy switching implemented
6. Meta-layer decisions functional (REFRAME, SWITCH_STRATEGY, ESCALATE with defined triggers)
7. Ontology adequacy checks: `O.adequate(E)` with coverage and structural sufficiency
8. Anomaly detection: oscillation (MAP changes >= 3 in last 6 steps), contradiction (same-variable conflict + high-confidence reversal)
9. Extended norms: reliability + calibration, efficiency + heuristic cost + strategy switches, justification + intermediate consistency, power = adequacy
10. All v0.1 tests still pass
11. All v0.2 tests pass
12. Type checking passes
