# Epistemic Pipeline v0.2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend the epistemic pipeline with confidence-weighted evidence, STRIPS planning encoding, functional meta-layer decisions, and extended norms.

**Architecture:** Bottom-up build order: state extensions → encoding changes (Bayes confidence + STRIPS) → extended norms → functional meta-layer. Each layer builds on the previous. All v0.1 tests must pass at every step.

**Tech Stack:** Python 3.14+, uv, pytest, pyright, frozen dataclasses, zero dependencies.

**Spec:** `docs/superpowers/specs/2026-03-20-epistemic-pipeline-v02-design.md`

**Style:** Graduate-level ideas in 8th-grade sentences. Short sentences, active voice, define terms on first use. Google-style docstrings.

---

### Task 1: State Model Extensions — EvidenceType and Observation

**Files:**

- Modify: `src/epistemic_pipeline/state.py:1-26`
- Modify: `src/epistemic_pipeline/__init__.py`
- Test: `tests/test_bayes.py` (existing, must still pass)
- Test: `tests/test_meta.py` (existing, must still pass)

- [ ] **Step 1: Add EvidenceType enum and extend Observation**

In `src/epistemic_pipeline/state.py`, add `EvidenceType` enum before `Observation`. Add `confidence` and `etype` fields to `Observation` with defaults so v0.1 code still works.

```python
from enum import Enum

class EvidenceType(Enum):
    """Type of evidence: how the observation was obtained.

    OBSERVATION: direct sensory input (e.g. seeing a symptom).
    REPORT: secondhand testimony (e.g. patient says "I feel sick").
    MEASUREMENT: instrument reading (e.g. thermometer shows 102F).
    """

    OBSERVATION = "observation"
    REPORT = "report"
    MEASUREMENT = "measurement"
```

Add to `Observation` after `timestamp`:

```python
    confidence: float = 1.0
    etype: EvidenceType = EvidenceType.OBSERVATION
```

- [ ] **Step 2: Add EvidenceType to `__init__.py` exports**

Add `EvidenceType` to the imports and `__all__` in `src/epistemic_pipeline/__init__.py`.

- [ ] **Step 3: Write tests for EvidenceType field**

Add to `tests/test_bayes.py`:

```python
from epistemic_pipeline.state import EvidenceType

class TestEvidenceType:
    """EvidenceType and confidence fields on Observation."""

    def test_default_etype_is_observation(self):
        obs = Observation(variable="x", value="1", source="s", timestamp=0.0)
        assert obs.etype == EvidenceType.OBSERVATION

    def test_default_confidence_is_one(self):
        obs = Observation(variable="x", value="1", source="s", timestamp=0.0)
        assert obs.confidence == 1.0

    def test_report_etype_round_trips(self):
        obs = Observation(
            variable="x", value="1", source="s", timestamp=0.0,
            etype=EvidenceType.REPORT, confidence=0.7,
        )
        assert obs.etype == EvidenceType.REPORT
        assert obs.confidence == 0.7

    def test_measurement_etype_round_trips(self):
        obs = Observation(
            variable="x", value="1", source="s", timestamp=0.0,
            etype=EvidenceType.MEASUREMENT, confidence=0.99,
        )
        assert obs.etype == EvidenceType.MEASUREMENT
```

- [ ] **Step 4: Run all tests to verify backward compatibility and new tests**

Run: `uv run pytest tests/ -v`
Expected: All tests pass. No v0.1 test should break because both new fields have defaults.

- [ ] **Step 5: Commit**

```bash
git add src/epistemic_pipeline/state.py src/epistemic_pipeline/__init__.py tests/test_bayes.py
git commit -m "feat: add EvidenceType enum and confidence/etype fields to Observation"
```

---

### Task 2: Metadata Extensions

**Files:**

- Modify: `src/epistemic_pipeline/state.py:29-44`

- [ ] **Step 1: Add new fields to Metadata**

Add three fields at the end of `Metadata` (all with defaults):

```python
    anomaly_checks: tuple[str, ...] = ()
    heuristics: tuple[str, ...] = ()
    strategy_switches: int = 0
```

Update the docstring to document them.

- [ ] **Step 2: Run existing tests**

Run: `uv run pytest tests/ -v`
Expected: All pass. New fields have defaults.

- [ ] **Step 3: Commit**

```bash
git add src/epistemic_pipeline/state.py
git commit -m "feat: add anomaly_checks, heuristics, strategy_switches to Metadata"
```

---

### Task 3: BayesOntology.adequate()

**Files:**

- Modify: `src/epistemic_pipeline/encodings/bayes.py:16-28`
- Test: `tests/test_bayes.py`

- [ ] **Step 1: Write failing tests**

Add to `tests/test_bayes.py`:

```python
class TestBayesOntologyAdequacy:
    """BayesOntology.adequate(E) returns True when every observation's
    (variable, value) pair has a likelihood entry for at least one hypothesis."""

    def test_adequate_when_all_evidence_covered(self):
        """Ontology that covers all observations is adequate."""
        ontology = BayesOntology(
            hypotheses=("A", "B"),
            observables=("x",),
            likelihoods={("A", "x", "1"): 0.8, ("B", "x", "1"): 0.2},
        )
        evidence = (
            Observation(variable="x", value="1", source="test", timestamp=0.0),
        )
        assert ontology.adequate(evidence) is True

    def test_inadequate_when_unknown_variable(self):
        """Ontology missing a variable is inadequate."""
        ontology = BayesOntology(
            hypotheses=("A",),
            observables=("x",),
            likelihoods={("A", "x", "1"): 0.8},
        )
        evidence = (
            Observation(variable="y", value="1", source="test", timestamp=0.0),
        )
        assert ontology.adequate(evidence) is False

    def test_inadequate_when_unknown_value(self):
        """Ontology missing a value for a known variable is inadequate."""
        ontology = BayesOntology(
            hypotheses=("A",),
            observables=("x",),
            likelihoods={("A", "x", "1"): 0.8},
        )
        evidence = (
            Observation(variable="x", value="999", source="test", timestamp=0.0),
        )
        assert ontology.adequate(evidence) is False

    def test_adequate_with_empty_evidence(self):
        """Empty evidence is always adequate."""
        ontology = BayesOntology(
            hypotheses=("A",),
            observables=("x",),
            likelihoods={("A", "x", "1"): 0.8},
        )
        assert ontology.adequate(()) is True
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_bayes.py::TestBayesOntologyAdequacy -v`
Expected: FAIL — `BayesOntology` has no `adequate` method.

- [ ] **Step 3: Implement adequate() on BayesOntology**

Add method to `BayesOntology` in `src/epistemic_pipeline/encodings/bayes.py`:

```python
    def adequate(self, evidence: tuple[Observation, ...]) -> bool:
        """Check if this ontology covers all evidence.

        Returns True when every observation's (variable, value) pair
        has a likelihood entry for at least one hypothesis.
        """
        for obs in evidence:
            found = any(
                (h, obs.variable, obs.value) in self.likelihoods
                for h in self.hypotheses
            )
            if not found:
                return False
        return True
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_bayes.py -v`
Expected: All pass (new + existing).

- [ ] **Step 5: Commit**

```bash
git add src/epistemic_pipeline/encodings/bayes.py tests/test_bayes.py
git commit -m "feat: add adequate() method to BayesOntology"
```

---

### Task 4: Confidence-Weighted Bayesian Updates

**Files:**

- Modify: `src/epistemic_pipeline/encodings/bayes.py:42-75`
- Test: `tests/test_bayes.py`

- [ ] **Step 1: Write failing tests**

Add to `tests/test_bayes.py`:

```python
class TestConfidenceWeightedUpdates:
    """Confidence-weighted Bayes: L_eff(e|h) = c*P(e|h) + (1-c)*P(e)."""

    def _simple_ontology(self) -> BayesOntology:
        return BayesOntology(
            hypotheses=("A", "B"),
            observables=("x",),
            likelihoods={("A", "x", "1"): 0.9, ("B", "x", "1"): 0.1},
        )

    def test_full_confidence_matches_standard_bayes(self):
        """confidence=1.0 gives the same result as v0.1 bayes_update."""
        ontology = self._simple_ontology()
        beliefs = BayesBeliefs(probabilities={"A": 0.5, "B": 0.5})
        obs = Observation(variable="x", value="1", source="t", timestamp=0.0, confidence=1.0)

        updated = bayes_update(beliefs, obs, ontology)

        assert math.isclose(updated.probabilities["A"], 0.9, rel_tol=1e-9)

    def test_zero_confidence_is_noop(self):
        """confidence=0.0 produces no change in beliefs."""
        ontology = self._simple_ontology()
        beliefs = BayesBeliefs(probabilities={"A": 0.5, "B": 0.5})
        obs = Observation(variable="x", value="1", source="t", timestamp=0.0, confidence=0.0)

        updated = bayes_update(beliefs, obs, ontology)

        assert math.isclose(updated.probabilities["A"], 0.5, rel_tol=1e-9)
        assert math.isclose(updated.probabilities["B"], 0.5, rel_tol=1e-9)

    def test_half_confidence_dampens_update(self):
        """confidence=0.5 produces a posterior between prior and full-update posterior."""
        ontology = self._simple_ontology()
        beliefs = BayesBeliefs(probabilities={"A": 0.5, "B": 0.5})
        obs = Observation(variable="x", value="1", source="t", timestamp=0.0, confidence=0.5)

        updated = bayes_update(beliefs, obs, ontology)

        # Should be between 0.5 (no update) and 0.9 (full update)
        assert 0.5 < updated.probabilities["A"] < 0.9

    def test_low_confidence_preserves_normalization(self):
        """Posteriors still sum to 1.0 with fractional confidence."""
        ontology = self._simple_ontology()
        beliefs = BayesBeliefs(probabilities={"A": 0.5, "B": 0.5})
        obs = Observation(variable="x", value="1", source="t", timestamp=0.0, confidence=0.3)

        updated = bayes_update(beliefs, obs, ontology)

        total = sum(updated.probabilities.values())
        assert math.isclose(total, 1.0, rel_tol=1e-9)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_bayes.py::TestConfidenceWeightedUpdates -v`
Expected: `test_zero_confidence_is_noop` and `test_half_confidence_dampens_update` FAIL. `test_full_confidence_matches_standard_bayes` may pass (default confidence=1.0 means no change to existing logic).

- [ ] **Step 3: Implement confidence-weighted update**

Replace the body of `bayes_update` in `src/epistemic_pipeline/encodings/bayes.py`:

```python
def bayes_update(
    beliefs: BayesBeliefs,
    evidence: Observation,
    ontology: BayesOntology,
) -> BayesBeliefs:
    """Apply confidence-weighted Bayes' rule: R(B, e, O) -> B'.

    L_eff(e|h) = c * P(e|h) + (1 - c) * P(e)
    P'(h) = L_eff(e|h) * P(h) / sum_h'(L_eff(e|h') * P(h'))

    c is evidence.confidence. At c=1.0, this is standard Bayes.
    At c=0.0, L_eff equals the marginal for all h, so beliefs don't change.
    """
    c = evidence.confidence

    # Raw likelihoods P(e|h)
    raw: dict[str, float] = {}
    for h in ontology.hypotheses:
        raw[h] = ontology.likelihoods.get(
            (h, evidence.variable, evidence.value), 0.0,
        )

    # Marginal P(e) = sum_h P(e|h) * P(h)
    marginal = sum(
        raw[h] * beliefs.probabilities[h] for h in ontology.hypotheses
    )

    # Effective likelihood: L_eff(e|h) = c * P(e|h) + (1 - c) * P(e)
    posteriors: dict[str, float] = {}
    total = 0.0
    for h in ontology.hypotheses:
        l_eff = c * raw[h] + (1.0 - c) * marginal
        unnormalized = l_eff * beliefs.probabilities[h]
        posteriors[h] = unnormalized
        total += unnormalized

    if total > 0:
        posteriors = {h: p / total for h, p in posteriors.items()}

    return BayesBeliefs(probabilities=posteriors)
```

- [ ] **Step 4: Run all tests**

Run: `uv run pytest tests/ -v`
Expected: All pass (new confidence tests + all v0.1 tests).

- [ ] **Step 5: Commit**

```bash
git add src/epistemic_pipeline/encodings/bayes.py tests/test_bayes.py
git commit -m "feat: confidence-weighted Bayesian updates (L_eff formula)"
```

---

### Task 5: Anomaly Detection — Oscillation and Contradiction

**Files:**

- Modify: `src/epistemic_pipeline/encodings/bayes.py:161-182` (bayes_test)
- Test: `tests/test_bayes.py`

- [ ] **Step 1: Write failing tests for oscillation detection**

Add to `tests/test_bayes.py`:

```python
class TestAnomalyDetection:
    """Anomaly detection in bayes_test: oscillation and contradiction."""

    def _oscillation_problem(self) -> BayesProblem:
        """Build a problem where evidence flip-flops the MAP hypothesis.

        6 observations alternating strong evidence for A then B.
        MAP should change >= 3 times in the last 6 steps -> oscillation.
        """
        return BayesProblem(
            hypotheses=("A", "B"),
            observables=("x",),
            likelihoods={
                ("A", "x", "pro_A"): 0.95,
                ("B", "x", "pro_A"): 0.05,
                ("A", "x", "pro_B"): 0.05,
                ("B", "x", "pro_B"): 0.95,
            },
            observations=(
                Observation(variable="x", value="pro_A", source="t", timestamp=1.0),
                Observation(variable="x", value="pro_B", source="t", timestamp=2.0),
                Observation(variable="x", value="pro_A", source="t", timestamp=3.0),
                Observation(variable="x", value="pro_B", source="t", timestamp=4.0),
                Observation(variable="x", value="pro_A", source="t", timestamp=5.0),
                Observation(variable="x", value="pro_B", source="t", timestamp=6.0),
            ),
        )

    def test_oscillation_detected(self):
        """MAP changing >= 3 times in last 6 steps flags oscillation."""
        result = run_bayesian_pipeline(self._oscillation_problem())
        assert "oscillation" in result.final_state.metadata.anomalies

    def test_no_oscillation_on_normal_convergence(self):
        """Normal medical diagnosis does not trigger oscillation."""
        result = run_bayesian_pipeline(_medical_problem())
        assert "oscillation" not in result.final_state.metadata.anomalies

    def test_same_variable_contradiction(self):
        """Two observations of the same variable with different values flags contradiction."""
        problem = BayesProblem(
            hypotheses=("A", "B"),
            observables=("x",),
            likelihoods={
                ("A", "x", "yes"): 0.9, ("B", "x", "yes"): 0.1,
                ("A", "x", "no"): 0.1, ("B", "x", "no"): 0.9,
            },
            observations=(
                Observation(variable="x", value="yes", source="t", timestamp=1.0),
                Observation(variable="x", value="no", source="t", timestamp=2.0),
            ),
        )
        result = run_bayesian_pipeline(problem)
        assert "contradiction" in result.final_state.metadata.anomalies

    def test_high_confidence_reversal(self):
        """MAP shift when prior MAP had probability > 0.8 flags contradiction."""
        problem = BayesProblem(
            hypotheses=("A", "B"),
            observables=("x", "y"),
            likelihoods={
                ("A", "x", "1"): 0.99, ("B", "x", "1"): 0.01,
                ("A", "y", "1"): 0.01, ("B", "y", "1"): 0.99,
            },
            observations=(
                # First observation strongly favors A (P(A) -> ~0.99)
                Observation(variable="x", value="1", source="t", timestamp=1.0),
                # Second observation strongly favors B, reversing MAP
                Observation(variable="y", value="1", source="t", timestamp=2.0),
            ),
        )
        result = run_bayesian_pipeline(problem)
        assert "contradiction" in result.final_state.metadata.anomalies
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_bayes.py::TestAnomalyDetection -v`
Expected: FAIL — `bayes_test` doesn't detect anomalies yet.

- [ ] **Step 3: Implement anomaly detection in bayes_test**

Replace `bayes_test` in `src/epistemic_pipeline/encodings/bayes.py`:

```python
def _detect_oscillation(map_history: list[str]) -> bool:
    """Check for oscillation: MAP changes >= 3 times in last 6 evidence steps.

    map_history contains one entry per evidence step (not the prior).
    A MAP change is when consecutive entries differ. A single flip
    is normal belief evolution. Three flips in six steps means the
    evidence is pushing beliefs back and forth without convergence.
    """
    window = map_history[-6:]
    if len(window) < 2:
        return False
    transitions = sum(
        1 for i in range(len(window) - 1) if window[i] != window[i + 1]
    )
    return transitions >= 3


def _detect_contradiction(
    obs: Observation,
    prior_evidence: tuple[Observation, ...],
    beliefs_before: BayesBeliefs,
    beliefs_after: BayesBeliefs,
) -> bool:
    """Check for contradiction after processing one observation.

    Two triggers:
    1. Same-variable conflict: another observation of this variable
       had a different value.
    2. High-confidence reversal: the MAP hypothesis changed AND
       the old MAP had probability > 0.8 before the update.
    """
    # Same-variable conflict
    for prev in prior_evidence:
        if prev.variable == obs.variable and prev.value != obs.value:
            return True

    # High-confidence reversal
    old_map = max(
        beliefs_before.probabilities,
        key=lambda h: beliefs_before.probabilities[h],
    )
    new_map = max(
        beliefs_after.probabilities,
        key=lambda h: beliefs_after.probabilities[h],
    )
    if old_map != new_map and beliefs_before.probabilities[old_map] > 0.8:
        return True

    return False


def bayes_test(
    state: EpistemicState[BayesOntology, BayesBeliefs],
) -> EpistemicState[BayesOntology, BayesBeliefs]:
    """Test stage: apply Bayes' rule for each pending observation.

    Processes observations in order. For each one, calls R(B, e, O)
    to get updated beliefs, then appends the observation to evidence.
    Detects anomalies (oscillation and contradiction) after each update.
    Clears pending_observations when done.
    """
    beliefs = state.beliefs
    evidence_list = list(state.evidence)
    anomalies = list(state.metadata.anomalies)
    map_history: list[str] = []

    for obs in state.metadata.pending_observations:
        beliefs_before = beliefs
        beliefs = state.revision_policy(beliefs, obs, state.ontology)
        evidence_list.append(obs)
        map_history.append(bayes_argmax(beliefs))

        if _detect_contradiction(
            obs, tuple(evidence_list[:-1]), beliefs_before, beliefs,
        ):
            anomalies.append("contradiction")

        if _detect_oscillation(map_history):
            anomalies.append("oscillation")

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
```

- [ ] **Step 4: Run all tests**

Run: `uv run pytest tests/ -v`
Expected: All pass.

- [ ] **Step 5: Commit**

```bash
git add src/epistemic_pipeline/encodings/bayes.py tests/test_bayes.py
git commit -m "feat: anomaly detection — oscillation and contradiction in bayes_test"
```

---

### Task 6: STRIPS Encoding — Types and Revision Policy

**Files:**

- Create: `src/epistemic_pipeline/encodings/strips.py`
- Create: `tests/test_strips.py`

- [ ] **Step 1: Write failing tests for STRIPS types and search**

Create `tests/test_strips.py`:

```python
"""STRIPS planning tests: blocks world scenario.

Two blocks (A, B) on a table. Goal: stack A on B.
Expected plan: [pickup_A, stack_A_B].
"""

from epistemic_pipeline.encodings.strips import (
    STRIPSAction,
    STRIPSBeliefs,
    STRIPSOntology,
    STRIPSProblem,
    run_strips_pipeline,
    strips_update,
)
from epistemic_pipeline.meta import MetaDecision
from epistemic_pipeline.state import Observation


def _blocks_world() -> STRIPSProblem:
    """Two blocks on a table. Goal: A on top of B."""
    predicates = frozenset({
        "on_table_A", "on_table_B", "clear_A", "clear_B",
        "on_A_B", "holding_A",
    })

    pickup_A = STRIPSAction(
        name="pickup_A",
        preconditions=frozenset({"on_table_A", "clear_A"}),
        add_effects=frozenset({"holding_A"}),
        delete_effects=frozenset({"on_table_A", "clear_A"}),
    )
    stack_A_B = STRIPSAction(
        name="stack_A_B",
        preconditions=frozenset({"holding_A", "clear_B"}),
        add_effects=frozenset({"on_A_B"}),
        delete_effects=frozenset({"holding_A", "clear_B"}),
    )

    initial_state = frozenset({"on_table_A", "on_table_B", "clear_A", "clear_B"})
    goal = frozenset({"on_A_B"})

    return STRIPSProblem(
        predicates=predicates,
        actions=(pickup_A, stack_A_B),
        goal=goal,
        initial_state=initial_state,
    )


class TestSTRIPSTypes:
    """STRIPS frozen dataclasses are immutable."""

    def test_action_is_frozen(self):
        action = STRIPSAction(
            name="a", preconditions=frozenset(), add_effects=frozenset(),
            delete_effects=frozenset(),
        )
        try:
            action.name = "b"  # type: ignore[misc]
        except AttributeError:
            pass
        else:
            raise AssertionError("STRIPSAction should be frozen")

    def test_ontology_is_frozen(self):
        ontology = STRIPSOntology(
            predicates=frozenset({"p"}),
            actions=(),
            goal=frozenset({"p"}),
        )
        try:
            ontology.goal = frozenset()  # type: ignore[misc]
        except AttributeError:
            pass
        else:
            raise AssertionError("STRIPSOntology should be frozen")

    def test_beliefs_is_frozen(self):
        beliefs = STRIPSBeliefs(current_state=frozenset({"p"}), plan=())
        try:
            beliefs.plan = ("a",)  # type: ignore[misc]
        except AttributeError:
            pass
        else:
            raise AssertionError("STRIPSBeliefs should be frozen")


class TestSTRIPSOntologyAdequacy:
    """STRIPSOntology.adequate(E) checks predicate coverage."""

    def test_adequate_when_all_predicates_known(self):
        ontology = STRIPSOntology(
            predicates=frozenset({"p", "q"}), actions=(), goal=frozenset(),
        )
        evidence = (
            Observation(variable="p", value="true", source="init", timestamp=0.0),
        )
        assert ontology.adequate(evidence) is True

    def test_inadequate_when_unknown_predicate(self):
        ontology = STRIPSOntology(
            predicates=frozenset({"p"}), actions=(), goal=frozenset(),
        )
        evidence = (
            Observation(variable="unknown", value="true", source="init", timestamp=0.0),
        )
        assert ontology.adequate(evidence) is False

    def test_adequate_with_empty_evidence(self):
        ontology = STRIPSOntology(
            predicates=frozenset({"p"}), actions=(), goal=frozenset(),
        )
        assert ontology.adequate(()) is True


class TestSTRIPSUpdate:
    """strips_update does one frontier expansion step."""

    def test_goal_reached_returns_plan(self):
        """When frontier state satisfies goal, plan is returned."""
        problem = _blocks_world()
        ontology = STRIPSOntology(
            predicates=problem.predicates,
            actions=problem.actions,
            goal=problem.goal,
        )
        # Put a goal state directly in the frontier
        goal_state = frozenset({"on_table_B", "on_A_B"})
        beliefs = STRIPSBeliefs(
            current_state=problem.initial_state,
            plan=("pickup_A", "stack_A_B"),
            frontier=((goal_state, ("pickup_A", "stack_A_B")),),
            explored=frozenset(),
        )
        step_obs = Observation(
            variable="search_step", value="expand",
            source="planner", timestamp=1.0,
        )

        updated = strips_update(beliefs, step_obs, ontology)

        assert ontology.goal.issubset(updated.current_state)

    def test_expansion_adds_successor_states(self):
        """Expanding the initial state produces successor states in frontier."""
        problem = _blocks_world()
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
        step_obs = Observation(
            variable="search_step", value="expand",
            source="planner", timestamp=1.0,
        )

        updated = strips_update(beliefs, step_obs, ontology)

        # Initial state has been explored
        assert problem.initial_state in updated.explored
        # Frontier should have successor states
        assert len(updated.frontier) > 0


class TestBlocksWorldPipeline:
    """End-to-end: blocks world finds plan [pickup_A, stack_A_B]."""

    def test_finds_correct_plan(self):
        result = run_strips_pipeline(_blocks_world())

        plan = result.final_state.beliefs.plan
        assert plan == ("pickup_A", "stack_A_B")

    def test_goal_is_satisfied(self):
        result = run_strips_pipeline(_blocks_world())

        goal = result.final_state.ontology.goal
        assert goal.issubset(result.final_state.beliefs.current_state)

    def test_trace_preserved(self):
        result = run_strips_pipeline(_blocks_world())

        # Trace has initial + 5 stages
        assert len(result.trace) == 6

    def test_meta_returns_accept(self):
        result = run_strips_pipeline(_blocks_world())

        assert result.meta_decision.decision == MetaDecision.ACCEPT

    def test_evidence_records_search_steps(self):
        result = run_strips_pipeline(_blocks_world())

        # Evidence should contain search step observations
        assert len(result.final_state.evidence) > 0
        for obs in result.final_state.evidence:
            assert obs.variable == "search_step"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_strips.py -v`
Expected: FAIL — module `epistemic_pipeline.encodings.strips` does not exist.

- [ ] **Step 3: Implement STRIPS types**

Create `src/epistemic_pipeline/encodings/strips.py`:

```python
"""STRIPS encoding: classical planning as forward-state search.

Expressiveness proof #2: planning as an (O, E, B, R) tuple.
STRIPS (Stanford Research Institute Problem Solver) is a classical
planning formalism. The ontology holds predicates, actions, and the
goal. Beliefs track the current state, plan, and search frontier.
The revision policy expands one frontier state per call.
"""

from dataclasses import dataclass, replace

from epistemic_pipeline.meta import MetaController
from epistemic_pipeline.pipeline import PipelineResult, run_pipeline
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
        appears in the ontology's predicate set.
        """
        for obs in evidence:
            if obs.variable == "search_step":
                continue  # synthetic search signals, not real predicates
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
    """Apply a STRIPS action to a state. Returns the new state."""
    return (state - action.delete_effects) | action.add_effects


def strips_update(
    beliefs: STRIPSBeliefs,
    evidence: Observation,
    ontology: STRIPSOntology,
) -> STRIPSBeliefs:
    """One search expansion step: R(B, e, O) -> B'.

    Pops the first frontier entry. If it satisfies the goal,
    returns beliefs with the completed plan. Otherwise, generates
    successor states from applicable actions and adds them to
    the frontier. Skips already-explored states.
    """
    if not beliefs.frontier:
        return beliefs  # no more states to explore

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
```

- [ ] **Step 4: Run tests to verify types and update work**

Run: `uv run pytest tests/test_strips.py::TestSTRIPSTypes tests/test_strips.py::TestSTRIPSOntologyAdequacy tests/test_strips.py::TestSTRIPSUpdate -v`
Expected: Pass.

- [ ] **Step 5: Commit**

```bash
git add src/epistemic_pipeline/encodings/strips.py tests/test_strips.py
git commit -m "feat: STRIPS types, adequate(), and strips_update revision policy"
```

---

### Task 7: STRIPS Pipeline Stages

**Files:**

- Modify: `src/epistemic_pipeline/encodings/strips.py`
- Test: `tests/test_strips.py`

- [ ] **Step 1: The pipeline tests from Task 6 are already written**

`TestBlocksWorldPipeline` in `tests/test_strips.py` covers the end-to-end pipeline. Run them now to confirm they fail.

Run: `uv run pytest tests/test_strips.py::TestBlocksWorldPipeline -v`
Expected: FAIL — `STRIPSProblem` and `run_strips_pipeline` don't exist.

- [ ] **Step 2: Implement STRIPSProblem and pipeline stages**

Add to `src/epistemic_pipeline/encodings/strips.py`:

```python
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

    # Synthetic observations: one per search step
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
    """Decompose stage: identify subgoals not yet satisfied."""
    unsatisfied = tuple(
        p for p in state.ontology.goal
        if p not in state.beliefs.current_state
    )
    return replace(
        state,
        metadata=replace(state.metadata, decomposition=unsatisfied),
    )


def strips_model(
    state: EpistemicState[STRIPSOntology, STRIPSBeliefs],
) -> EpistemicState[STRIPSOntology, STRIPSBeliefs]:
    """Model stage: no-op. Revision policy set in Frame."""
    return state


def strips_select(
    state: EpistemicState[STRIPSOntology, STRIPSBeliefs],
) -> EpistemicState[STRIPSOntology, STRIPSBeliefs]:
    """Select stage: record heuristic choice in metadata."""
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
    """
    beliefs = state.beliefs
    evidence_list = list(state.evidence)
    anomalies = list(state.metadata.anomalies)

    for obs in state.metadata.pending_observations:
        # Stop if goal is already reached
        if state.ontology.goal.issubset(beliefs.current_state):
            break

        # Stop if frontier is empty (unsolvable)
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


def strips_integrate(
    state: EpistemicState[STRIPSOntology, STRIPSBeliefs],
) -> EpistemicState[STRIPSOntology, STRIPSBeliefs]:
    """Integrate stage: the plan is in beliefs. Pass-through."""
    return state


def run_strips_pipeline(
    problem: STRIPSProblem,
    meta_controller: MetaController | None = None,
) -> PipelineResult[STRIPSOntology, STRIPSBeliefs]:
    """Run a complete STRIPS planning pipeline.

    Composes all six stages: Frame -> Decompose -> Model -> Select ->
    Test -> Integrate. Returns the result with full trace and
    meta-layer evaluation.
    """
    initial_state = strips_frame(problem)

    return run_pipeline(
        initial_state=initial_state,
        stages=[
            strips_decompose,
            strips_model,
            strips_select,
            strips_test,
            strips_integrate,
        ],
        meta_controller=meta_controller,
    )
```

- [ ] **Step 3: Add edge case tests**

Add to `tests/test_strips.py`:

```python
class TestSTRIPSEdgeCases:
    """Edge cases: unsolvable problems, empty frontier, search_step adequacy."""

    def test_unsolvable_problem_flags_empty_frontier(self):
        """When no action sequence reaches the goal, flag empty_frontier."""
        problem = STRIPSProblem(
            predicates=frozenset({"p", "q"}),
            actions=(),  # no actions available
            goal=frozenset({"q"}),
            initial_state=frozenset({"p"}),
            max_search_steps=10,
        )
        result = run_strips_pipeline(problem)
        assert "empty_frontier" in result.final_state.metadata.anomalies

    def test_strips_update_empty_frontier_returns_unchanged(self):
        """strips_update with empty frontier returns beliefs unchanged."""
        beliefs = STRIPSBeliefs(
            current_state=frozenset({"p"}), plan=(), frontier=(), explored=frozenset(),
        )
        ontology = STRIPSOntology(
            predicates=frozenset({"p"}), actions=(), goal=frozenset({"q"}),
        )
        obs = Observation(
            variable="search_step", value="expand",
            source="planner", timestamp=0.0,
        )
        updated = strips_update(beliefs, obs, ontology)
        assert updated == beliefs

    def test_adequate_skips_search_step_observations(self):
        """adequate() ignores search_step synthetic observations."""
        ontology = STRIPSOntology(
            predicates=frozenset({"p"}), actions=(), goal=frozenset(),
        )
        evidence = (
            Observation(variable="search_step", value="expand", source="planner", timestamp=0.0),
            Observation(variable="p", value="true", source="init", timestamp=1.0),
        )
        assert ontology.adequate(evidence) is True
```

- [ ] **Step 4: Run all tests**

Run: `uv run pytest tests/ -v`
Expected: All pass (STRIPS + all v0.1).

- [ ] **Step 5: Commit**

```bash
git add src/epistemic_pipeline/encodings/strips.py tests/test_strips.py
git commit -m "feat: STRIPS planning pipeline — blocks world solves in 2 steps"
```

---

### Task 8: Extended Norms

**Files:**

- Modify: `src/epistemic_pipeline/norms.py`
- Test: `tests/test_bayes.py`

- [ ] **Step 1: Write failing tests for extended norms**

Add to `tests/test_bayes.py`:

```python
class TestExtendedNorms:
    """v0.2 norm extensions: calibration, heuristic cost, consistency, power."""

    def test_calibration_perfect(self):
        """calibration = log(B(h*)) = 0.0 when B(h*) = 1.0."""
        result = run_bayesian_pipeline(_medical_problem())

        scores = score_pipeline_run(
            result.trace,
            ground_truth="flu",
            belief_argmax=bayes_argmax,
            belief_probability=lambda b, h: b.probabilities[h],
        )

        # flu probability is high but not 1.0, so calibration < 0
        assert scores.calibration < 0.0

    def test_calibration_uses_log_scoring(self):
        """calibration = log(B_final(h*)) for the ground truth hypothesis."""
        result = run_bayesian_pipeline(_medical_problem())

        p_flu = result.final_state.beliefs.probabilities["flu"]
        expected_cal = math.log(p_flu)

        scores = score_pipeline_run(
            result.trace,
            ground_truth="flu",
            belief_argmax=bayes_argmax,
            belief_probability=lambda b, h: b.probabilities[h],
        )

        assert math.isclose(scores.calibration, expected_cal, rel_tol=1e-9)

    def test_v01_scoring_still_works(self):
        """Calling score_pipeline_run with only v0.1 args still works."""
        result = run_bayesian_pipeline(_medical_problem())

        scores = score_pipeline_run(
            result.trace,
            ground_truth="flu",
            belief_argmax=bayes_argmax,
        )

        assert scores.reliability == 1.0
        assert scores.efficiency == 6
        assert scores.justification is True
        assert scores.power is None
        assert scores.calibration == 0.0  # default

    def test_power_with_adequate_ontology(self):
        """power = True when ontology covers all evidence."""
        result = run_bayesian_pipeline(_medical_problem())

        scores = score_pipeline_run(
            result.trace,
            ground_truth="flu",
            belief_argmax=bayes_argmax,
            ontology_adequate=lambda o, e: o.adequate(e),
        )

        assert scores.power is True

    def test_intermediate_consistency_checked(self):
        """Intermediate consistency calls the provided checker."""
        result = run_bayesian_pipeline(_medical_problem())

        def check_bayes_consistent(
            beliefs: BayesBeliefs, ontology: BayesOntology,
        ) -> bool:
            total = sum(beliefs.probabilities.values())
            return math.isclose(total, 1.0, rel_tol=1e-6)

        scores = score_pipeline_run(
            result.trace,
            ground_truth="flu",
            belief_argmax=bayes_argmax,
            belief_consistent=check_bayes_consistent,
        )

        assert scores.justification_intermediate_consistent is True

    def test_strategy_switches_from_metadata(self):
        """Strategy switches are read from the final state metadata."""
        result = run_bayesian_pipeline(_medical_problem())

        scores = score_pipeline_run(
            result.trace,
            ground_truth="flu",
            belief_argmax=bayes_argmax,
        )

        assert scores.efficiency_strategy_switches == 0

    def test_calibration_neg_inf_when_zero_probability(self):
        """calibration = -inf when B(h*) = 0."""
        result = run_bayesian_pipeline(_medical_problem())

        scores = score_pipeline_run(
            result.trace,
            ground_truth="nonexistent_hypothesis",
            belief_argmax=bayes_argmax,
            belief_probability=lambda b, h: b.probabilities.get(h, 0.0),
        )

        assert scores.calibration == float("-inf")

    def test_power_false_through_scorer(self):
        """power = False when ontology doesn't cover all evidence."""
        result = run_bayesian_pipeline(_medical_problem())

        def always_inadequate(
            ontology: BayesOntology, evidence: tuple[Observation, ...],
        ) -> bool:
            return False

        scores = score_pipeline_run(
            result.trace,
            ground_truth="flu",
            belief_argmax=bayes_argmax,
            ontology_adequate=always_inadequate,
        )

        assert scores.power is False

    def test_heuristic_cost_passed_through(self):
        """Heuristic cost is passed as a parameter."""
        result = run_bayesian_pipeline(_medical_problem())

        scores = score_pipeline_run(
            result.trace,
            ground_truth="flu",
            belief_argmax=bayes_argmax,
            heuristic_cost=42,
        )

        assert scores.efficiency_heuristic_cost == 42

    def test_heuristic_cost_defaults_to_zero(self):
        """Heuristic cost defaults to 0 when not provided."""
        result = run_bayesian_pipeline(_medical_problem())

        scores = score_pipeline_run(
            result.trace,
            ground_truth="flu",
            belief_argmax=bayes_argmax,
        )

        assert scores.efficiency_heuristic_cost == 0
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_bayes.py::TestExtendedNorms -v`
Expected: FAIL — `score_pipeline_run` doesn't accept keyword args yet.

- [ ] **Step 3: Extend NormScore and score_pipeline_run**

Rewrite `src/epistemic_pipeline/norms.py`:

```python
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


def score_pipeline_run[O, B](
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
```

- [ ] **Step 4: Run all tests**

Run: `uv run pytest tests/ -v`
Expected: All pass.

- [ ] **Step 5: Commit**

```bash
git add src/epistemic_pipeline/norms.py tests/test_bayes.py
git commit -m "feat: extended norms — calibration, heuristic cost, consistency, power"
```

---

### Task 9: Functional Meta-Layer

**Files:**

- Modify: `src/epistemic_pipeline/meta.py`
- Create: `tests/test_meta_decisions.py`
- Modify: `src/epistemic_pipeline/__init__.py`

- [ ] **Step 1: Write failing tests for meta-layer decisions**

Create `tests/test_meta_decisions.py`:

```python
"""Tests for functional meta-layer decisions.

Each MetaDecision has specific triggers. Tests verify the priority
order: ESCALATE > REFRAME > SWITCH_STRATEGY > ACCEPT.
"""

from epistemic_pipeline.meta import (
    MetaController,
    MetaDecision,
    MetaThresholds,
)
from epistemic_pipeline.norms import NormScore


class TestMetaAccept:
    """ACCEPT is the default when no triggers fire."""

    def test_accept_when_everything_normal(self):
        controller = MetaController()
        result = controller.monitor(
            trace=(),
            scores=NormScore(reliability=0.9, efficiency=5, justification=True, power=True),
            ontology=None,
            strategy="bayesian",
            decomposition=(),
        )
        assert result.decision == MetaDecision.ACCEPT

    def test_accept_when_no_scores(self):
        """No scores and no anomalies -> ACCEPT."""
        controller = MetaController()
        result = controller.monitor(
            trace=(),
            scores=None,
            ontology=None,
            strategy="bayesian",
            decomposition=(),
        )
        assert result.decision == MetaDecision.ACCEPT


class TestMetaEscalate:
    """ESCALATE: repeated contradictions (highest priority)."""

    def test_escalate_on_repeated_contradictions(self):
        """Two or more contradictions in anomalies triggers ESCALATE."""
        from epistemic_pipeline.state import EpistemicState, Metadata, Observation

        # Build a minimal trace with repeated contradictions in anomalies
        meta = Metadata(anomalies=("contradiction", "contradiction"))
        state = EpistemicState(
            ontology=None,
            evidence=(),
            beliefs=None,
            revision_policy=lambda b, e, o: b,
            metadata=meta,
        )

        controller = MetaController()
        result = controller.monitor(
            trace=(state,),
            scores=NormScore(reliability=0.9, efficiency=5, justification=True, power=True),
            ontology=None,
            strategy="bayesian",
            decomposition=(),
        )
        assert result.decision == MetaDecision.ESCALATE
        assert "contradiction" in str(result.details)

    def test_escalate_beats_reframe(self):
        """ESCALATE takes priority over REFRAME."""
        from epistemic_pipeline.state import EpistemicState, Metadata

        meta = Metadata(anomalies=("contradiction", "contradiction"))
        state = EpistemicState(
            ontology=None, evidence=(), beliefs=None,
            revision_policy=lambda b, e, o: b, metadata=meta,
        )

        controller = MetaController()
        result = controller.monitor(
            trace=(state,),
            scores=NormScore(
                reliability=0.1, efficiency=5, justification=True, power=False,
            ),
            ontology=None,
            strategy="bayesian",
            decomposition=(),
        )
        # Even with low reliability and inadequate ontology, ESCALATE wins
        assert result.decision == MetaDecision.ESCALATE


class TestMetaReframe:
    """REFRAME: ontology inadequate or reliability too low."""

    def test_reframe_when_ontology_inadequate(self):
        controller = MetaController()
        result = controller.monitor(
            trace=(),
            scores=NormScore(
                reliability=0.9, efficiency=5, justification=True, power=False,
            ),
            ontology=None,
            strategy="bayesian",
            decomposition=(),
        )
        assert result.decision == MetaDecision.REFRAME

    def test_reframe_when_reliability_below_threshold(self):
        controller = MetaController(thresholds=MetaThresholds(reliability_min=0.5))
        result = controller.monitor(
            trace=(),
            scores=NormScore(
                reliability=0.3, efficiency=5, justification=True, power=True,
            ),
            ontology=None,
            strategy="bayesian",
            decomposition=(),
        )
        assert result.decision == MetaDecision.REFRAME

    def test_reframe_beats_switch_strategy(self):
        """REFRAME takes priority over SWITCH_STRATEGY."""
        from epistemic_pipeline.state import EpistemicState, Metadata

        meta = Metadata(anomalies=("oscillation",))
        state = EpistemicState(
            ontology=None, evidence=(), beliefs=None,
            revision_policy=lambda b, e, o: b, metadata=meta,
        )

        controller = MetaController()
        result = controller.monitor(
            trace=(state,),
            scores=NormScore(
                reliability=0.9, efficiency=5, justification=True, power=False,
            ),
            ontology=None,
            strategy="bayesian",
            decomposition=(),
        )
        # power=False triggers REFRAME, which beats oscillation's SWITCH_STRATEGY
        assert result.decision == MetaDecision.REFRAME


class TestMetaSwitchStrategy:
    """SWITCH_STRATEGY: efficiency too high or oscillation detected."""

    def test_switch_on_high_efficiency(self):
        controller = MetaController(
            thresholds=MetaThresholds(
                efficiency_ratio_max=2.0, expected_efficiency=5,
            ),
        )
        result = controller.monitor(
            trace=(),
            scores=NormScore(
                reliability=0.9, efficiency=11, justification=True, power=True,
            ),
            ontology=None,
            strategy="bayesian",
            decomposition=(),
        )
        assert result.decision == MetaDecision.SWITCH_STRATEGY

    def test_switch_on_oscillation(self):
        from epistemic_pipeline.state import EpistemicState, Metadata

        meta = Metadata(anomalies=("oscillation",))
        state = EpistemicState(
            ontology=None, evidence=(), beliefs=None,
            revision_policy=lambda b, e, o: b, metadata=meta,
        )

        controller = MetaController()
        result = controller.monitor(
            trace=(state,),
            scores=NormScore(
                reliability=0.9, efficiency=5, justification=True, power=True,
            ),
            ontology=None,
            strategy="bayesian",
            decomposition=(),
        )
        assert result.decision == MetaDecision.SWITCH_STRATEGY

    def test_switch_on_oscillation_without_scores(self):
        """Oscillation triggers SWITCH_STRATEGY even without scores."""
        from epistemic_pipeline.state import EpistemicState, Metadata

        meta = Metadata(anomalies=("oscillation",))
        state = EpistemicState(
            ontology=None, evidence=(), beliefs=None,
            revision_policy=lambda b, e, o: b, metadata=meta,
        )

        controller = MetaController()
        result = controller.monitor(
            trace=(state,),
            scores=None,
            ontology=None,
            strategy="bayesian",
            decomposition=(),
        )
        assert result.decision == MetaDecision.SWITCH_STRATEGY


class TestMetaThresholds:
    """MetaThresholds configures decision boundaries."""

    def test_custom_reliability_threshold(self):
        controller = MetaController(
            thresholds=MetaThresholds(reliability_min=0.9),
        )
        result = controller.monitor(
            trace=(),
            scores=NormScore(
                reliability=0.85, efficiency=5, justification=True, power=True,
            ),
            ontology=None,
            strategy="bayesian",
            decomposition=(),
        )
        assert result.decision == MetaDecision.REFRAME

    def test_default_thresholds(self):
        t = MetaThresholds()
        assert t.reliability_min == 0.5
        assert t.efficiency_ratio_max == 2.0
        assert t.expected_efficiency == 10
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_meta_decisions.py -v`
Expected: FAIL — `MetaThresholds` does not exist, `MetaController` doesn't accept `thresholds`.

- [ ] **Step 3: Implement functional meta-layer**

Rewrite `src/epistemic_pipeline/meta.py`:

```python
"""Meta-epistemic layer: monitors reasoning and decides how to proceed.

Evaluates the pipeline trace, norm scores, ontology adequacy, and
anomalies. Returns one of four decisions: ACCEPT, REFRAME,
SWITCH_STRATEGY, or ESCALATE. Priority order ensures safety:
escalation beats reframing beats strategy switching.
"""

from dataclasses import dataclass, field
from enum import Enum

from epistemic_pipeline.norms import NormScore


class MetaDecision(Enum):
    """What the meta-layer can decide about the current reasoning state.

    ACCEPT: reasoning is on track, continue.
    REFRAME: the ontology needs restructuring.
    SWITCH_STRATEGY: try a different reasoning strategy.
    ESCALATE: the problem is beyond current capabilities.
    """

    ACCEPT = "ACCEPT"
    REFRAME = "REFRAME"
    SWITCH_STRATEGY = "SWITCH_STRATEGY"
    ESCALATE = "ESCALATE"


@dataclass(frozen=True)
class MetaResult:
    """Result from the meta-epistemic monitor.

    decision: which action to take.
    details: additional context about why this decision was made.
    """

    decision: MetaDecision
    details: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class MetaThresholds:
    """Configuration for meta-layer decision boundaries.

    reliability_min: below this reliability, trigger REFRAME.
    efficiency_ratio_max: if efficiency > ratio * expected, trigger SWITCH.
    expected_efficiency: baseline expected trace length.
    """

    reliability_min: float = 0.5
    efficiency_ratio_max: float = 2.0
    expected_efficiency: int = 10


class MetaController:
    """Meta-epistemic controller with functional decision logic.

    Evaluates triggers in priority order:
    1. ESCALATE — repeated contradictions.
    2. REFRAME — ontology inadequate or reliability too low.
    3. SWITCH_STRATEGY — efficiency too high or oscillation.
    4. ACCEPT — no triggers fired.
    """

    def __init__(self, thresholds: MetaThresholds | None = None) -> None:
        """Initialize with optional thresholds.

        Args:
            thresholds: decision boundaries. Uses defaults if None.
        """
        self.thresholds = thresholds or MetaThresholds()

    def _collect_anomalies(
        self, trace: tuple[object, ...],
    ) -> tuple[str, ...]:
        """Collect anomalies from all states in the trace."""
        anomalies: list[str] = []
        for state in trace:
            meta = getattr(state, "metadata", None)
            if meta is not None:
                anomalies.extend(getattr(meta, "anomalies", ()))
        return tuple(anomalies)

    def monitor(
        self,
        trace: tuple[object, ...],
        scores: NormScore | object | None,
        ontology: object,
        strategy: str,
        decomposition: tuple[str, ...],
    ) -> MetaResult:
        """Evaluate the current pipeline state and decide how to proceed.

        Args:
            trace: sequence of EpistemicStates from the run.
            scores: norm scores. Can be NormScore, dict, or None.
            ontology: the current ontology.
            strategy: the current reasoning strategy name.
            decomposition: sub-problems from the Decompose stage.

        Returns:
            MetaResult with decision and details.
        """
        anomalies = self._collect_anomalies(trace)

        # Extract NormScore fields safely
        norm: NormScore | None = None
        if isinstance(scores, NormScore):
            norm = scores

        # 1. ESCALATE: repeated contradictions
        contradiction_count = anomalies.count("contradiction")
        if contradiction_count >= 2:
            return MetaResult(
                decision=MetaDecision.ESCALATE,
                details={
                    "trigger": "repeated_contradictions",
                    "contradiction_count": contradiction_count,
                },
            )

        # 2. REFRAME: ontology inadequate or low reliability
        if norm is not None:
            if norm.power is False:
                return MetaResult(
                    decision=MetaDecision.REFRAME,
                    details={
                        "trigger": "ontology_inadequate",
                        "power": norm.power,
                    },
                )
            if norm.reliability < self.thresholds.reliability_min:
                return MetaResult(
                    decision=MetaDecision.REFRAME,
                    details={
                        "trigger": "low_reliability",
                        "reliability": norm.reliability,
                        "threshold": self.thresholds.reliability_min,
                    },
                )

        # 3. SWITCH_STRATEGY: high efficiency cost or oscillation
        if norm is not None:
            max_eff = (
                self.thresholds.efficiency_ratio_max
                * self.thresholds.expected_efficiency
            )
            if norm.efficiency > max_eff:
                return MetaResult(
                    decision=MetaDecision.SWITCH_STRATEGY,
                    details={
                        "trigger": "high_efficiency",
                        "efficiency": norm.efficiency,
                        "threshold": max_eff,
                    },
                )

        if "oscillation" in anomalies:
            return MetaResult(
                decision=MetaDecision.SWITCH_STRATEGY,
                details={"trigger": "oscillation"},
            )

        # 4. ACCEPT: default
        return MetaResult(decision=MetaDecision.ACCEPT)
```

- [ ] **Step 4: Fix circular import**

`meta.py` now imports from `norms.py`, and `norms.py` imports from `state.py`. Check that there are no circular imports. The pipeline imports meta but not norms, so the chain is: `state <- norms <- meta <- pipeline`. This is fine.

However, `__init__.py` imports from both `meta` and `norms`. Verify there's no issue.

Run: `uv run python -c "from epistemic_pipeline import MetaController, NormScore"`
Expected: No import error.

If there IS a circular import (meta imports NormScore from norms, but norms doesn't import meta), fix by using `TYPE_CHECKING` guard in `meta.py`:

```python
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from epistemic_pipeline.norms import NormScore
```

And use string annotation for the isinstance check via a runtime import inside the method.

- [ ] **Step 5: Add MetaThresholds to `__init__.py` exports**

Add `MetaThresholds` to the imports and `__all__` in `src/epistemic_pipeline/__init__.py`.

- [ ] **Step 6: Run all tests**

Run: `uv run pytest tests/ -v`
Expected: All pass — v0.1 tests, v0.2 tests, everything.

- [ ] **Step 7: Run type checker**

Run: `uv run pyright src/ tests/`
Expected: No errors.

- [ ] **Step 8: Commit**

```bash
git add src/epistemic_pipeline/meta.py src/epistemic_pipeline/__init__.py tests/test_meta_decisions.py
git commit -m "feat: functional meta-layer — ESCALATE, REFRAME, SWITCH_STRATEGY decisions"
```

---

### Task 10: Final Verification and Exports

**Files:**

- Modify: `src/epistemic_pipeline/__init__.py`
- Modify: `src/epistemic_pipeline/encodings/__init__.py`

- [ ] **Step 1: Update encodings `__init__.py`**

Add STRIPS exports to `src/epistemic_pipeline/encodings/__init__.py`:

```python
"""Encoding implementations for the epistemic pipeline."""

from epistemic_pipeline.encodings.bayes import (
    BayesBeliefs,
    BayesOntology,
    BayesProblem,
    bayes_argmax,
    bayes_update,
    run_bayesian_pipeline,
)
from epistemic_pipeline.encodings.strips import (
    STRIPSAction,
    STRIPSBeliefs,
    STRIPSOntology,
    STRIPSProblem,
    run_strips_pipeline,
    strips_update,
)

__all__ = [
    "BayesBeliefs",
    "BayesOntology",
    "BayesProblem",
    "STRIPSAction",
    "STRIPSBeliefs",
    "STRIPSOntology",
    "STRIPSProblem",
    "bayes_argmax",
    "bayes_update",
    "run_bayesian_pipeline",
    "run_strips_pipeline",
    "strips_update",
]
```

- [ ] **Step 2: Run full test suite**

Run: `uv run pytest tests/ -v --tb=short`
Expected: All tests pass.

- [ ] **Step 3: Run type checker**

Run: `uv run pyright src/ tests/`
Expected: No errors.

- [ ] **Step 4: Run linter**

Run: `uv run ruff check src/ tests/`
Expected: No errors.

- [ ] **Step 5: Verify v0.2 completion criteria**

Check each criterion:

1. Evidence confidence field — `Observation.confidence: float = 1.0` ✓
2. Evidence etype field — `Observation.etype: EvidenceType` ✓
3. Confidence-weighted updates — `L_eff` formula in `bayes_update` ✓
4. STRIPS encoding — `STRIPSOntology` with goal, `STRIPSBeliefs` with frontier/explored ✓
5. Strategy switching — `metadata.strategy_switches`, meta returns `SWITCH_STRATEGY` ✓
6. Meta-layer decisions — REFRAME, SWITCH_STRATEGY, ESCALATE with triggers ✓
7. Ontology adequacy — `O.adequate(E)` on both ontology types ✓
8. Anomaly detection — oscillation (>=3 in 6) + contradiction (same-var + high-conf reversal) ✓
9. Extended norms — calibration, heuristic cost, strategy switches, consistency, power ✓
10. All v0.1 tests pass ✓
11. All v0.2 tests pass ✓
12. Type checking passes ✓

- [ ] **Step 6: Commit**

```bash
git add src/epistemic_pipeline/encodings/__init__.py
git commit -m "feat: complete v0.2 — exports, verification, all criteria met"
```
