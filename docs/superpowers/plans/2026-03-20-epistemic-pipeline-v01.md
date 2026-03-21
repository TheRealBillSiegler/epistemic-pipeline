# Epistemic Pipeline v0.1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the `(O, E, B, R)` state model, 6-stage pipeline, norm scoring, meta-layer stub, and Bayesian inference encoding — proving the architecture with a medical diagnosis toy problem.

**Architecture:** Frozen dataclasses for immutable state. Generic type parameters so encodings specialize `O`, `E`, `B`, `R`. Protocol-based pipeline stages. Pure functions throughout. Full state trace preserved.

**Tech Stack:** Python 3.14+, hatchling, pytest, pyright, ruff. Zero runtime dependencies.

**Spec:** `docs/superpowers/specs/2026-03-19-epistemic-pipeline-v01-design.md`

---

## File Map

| File | Responsibility |
|------|---------------|
| `src/epistemic_pipeline/__init__.py` | Public API re-exports |
| `src/epistemic_pipeline/py.typed` | PEP 561 marker (empty file) |
| `src/epistemic_pipeline/state.py` | `EpistemicState`, base protocols for O/E/B/R |
| `src/epistemic_pipeline/pipeline.py` | `Stage` protocol, `run_pipeline()`, `PipelineResult` |
| `src/epistemic_pipeline/norms.py` | `NormScore`, `score_pipeline_run()` |
| `src/epistemic_pipeline/meta.py` | `MetaDecision`, `MetaEpistemicController` stub |
| `src/epistemic_pipeline/encodings/__init__.py` | Encodings sub-package |
| `src/epistemic_pipeline/encodings/bayes.py` | `BayesVocabulary`, `BayesEvidence`, `BayesCredences`, `BayesRevision`, `bayes_stages()` |
| `tests/__init__.py` | Test package marker |
| `tests/test_state.py` | Immutability, generics, invariants |
| `tests/test_pipeline.py` | Stage composition, trace preservation, purity |
| `tests/test_norms.py` | Reliability, efficiency, justification scoring |
| `tests/test_meta.py` | Stub returns ACCEPT, wiring check |
| `tests/test_bayes.py` | End-to-end Bayesian encoding |
| `tests/test_trace_replay.py` | Replay reproduces final beliefs |
| `examples/medical_diagnosis.py` | Runnable toy problem |

---

## Task 0: Project Scaffolding

**Files:**
- Create: `src/epistemic_pipeline/__init__.py`
- Create: `src/epistemic_pipeline/py.typed`
- Create: `src/epistemic_pipeline/encodings/__init__.py`
- Create: `tests/__init__.py`
- Create: `examples/` (directory)

- [ ] **Step 1: Create directory structure**

```bash
mkdir -p src/epistemic_pipeline/encodings tests examples
```

- [ ] **Step 2: Create marker files**

Create `src/epistemic_pipeline/py.typed` as an empty file (PEP 561 typed package marker).

Create `src/epistemic_pipeline/__init__.py`:

```python
"""Epistemic Pipeline — a general-purpose reasoning architecture."""
```

Create `src/epistemic_pipeline/encodings/__init__.py`:

```python
"""Framework encodings for the epistemic pipeline."""
```

Create `tests/__init__.py` as an empty file.

- [ ] **Step 3: Verify uv can build the package**

Run: `uv run python -c "import epistemic_pipeline; print('ok')"`
Expected: `ok`

- [ ] **Step 4: Commit**

```bash
git add src/ tests/ examples/
git commit -m "chore: scaffold project directories and package markers"
```

---

## Task 1: State Model (`state.py`)

The core `(O, E, B, R)` tuple. Everything else depends on this.

**Files:**
- Create: `src/epistemic_pipeline/state.py`
- Create: `tests/test_state.py`

**Key design decisions:**
- `EpistemicState` is a frozen generic dataclass: `EpistemicState[O_t, E_t, B_t, R_t]`
- `metadata` uses `types.MappingProxyType` for immutability
- Base protocols define the contracts for O, E, B, R — encodings implement them
- Evidence protocol requires a `__add__` method (append-only semantics)
- Revision protocol requires `__call__(self, beliefs: B_t, evidence_item: Any, ontology: O_t) -> B_t`

- [ ] **Step 1: Write `state.py`**

```python
"""Core state model: the (O, E, B, R) tuple.

The system's complete state at any moment is four data structures:
- O (Ontology): the vocabulary of the problem
- E (Evidence): what has been observed (append-only)
- B (Beliefs): current confidence in each hypothesis
- R (Revision): the rule for updating beliefs from evidence

These four are bundled into an EpistemicState. The state is frozen.
Each pipeline stage takes one state and returns a new one.
"""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class Ontology(Protocol):
    """Contract for the vocabulary component (O).

    An ontology defines what concepts exist, what types they have,
    and what constraints apply. It stays fixed during a pipeline run.
    """


@runtime_checkable
class Evidence(Protocol):
    """Contract for the evidence component (E).

    Evidence is what has been observed. It is append-only:
    you can add observations but never remove them.
    """

    def append(self, item: Any) -> Evidence:
        """Return a new Evidence with the item added.

        Does not mutate self. Returns a fresh copy.
        """
        ...


@runtime_checkable
class Beliefs(Protocol):
    """Contract for the beliefs component (B).

    Beliefs map claims to confidence values.
    For probability distributions, values sum to 1.0.
    """


@runtime_checkable
class RevisionPolicy(Protocol):
    """Contract for the revision policy (R).

    R takes current beliefs, one new observation, and the vocabulary.
    It returns updated beliefs. No side effects.

    Signature: R(B, e, O) -> B'
    """

    def __call__(self, beliefs: Any, evidence_item: Any, ontology: Any) -> Any:
        """Apply the revision rule to produce updated beliefs."""
        ...


@dataclass(frozen=True)
class EpistemicState[O_t, E_t, B_t, R_t]:
    """The system's complete epistemic state at one moment.

    Frozen: once created, it never changes. Each pipeline stage
    takes one state and returns a new one. The full history of
    states (the trace) is preserved for auditing and replay.

    Type parameters let framework encodings specialize all four
    components. For Bayesian inference: O_t=BayesVocabulary,
    E_t=BayesEvidence, B_t=BayesCredences, R_t=BayesRevision.
    """

    ontology: O_t
    evidence: E_t
    beliefs: B_t
    revision_policy: R_t
    metadata: MappingProxyType[str, Any]

    def with_beliefs(self, new_beliefs: B_t) -> EpistemicState[O_t, E_t, B_t, R_t]:
        """Return a new state with updated beliefs. Everything else stays."""
        return EpistemicState(
            ontology=self.ontology,
            evidence=self.evidence,
            beliefs=new_beliefs,
            revision_policy=self.revision_policy,
            metadata=self.metadata,
        )

    def with_evidence(self, new_evidence: E_t) -> EpistemicState[O_t, E_t, B_t, R_t]:
        """Return a new state with updated evidence. Everything else stays."""
        return EpistemicState(
            ontology=self.ontology,
            evidence=new_evidence,
            beliefs=self.beliefs,
            revision_policy=self.revision_policy,
            metadata=self.metadata,
        )

    def with_metadata(
        self, new_metadata: MappingProxyType[str, Any],
    ) -> EpistemicState[O_t, E_t, B_t, R_t]:
        """Return a new state with updated metadata. Everything else stays."""
        return EpistemicState(
            ontology=self.ontology,
            evidence=self.evidence,
            beliefs=self.beliefs,
            revision_policy=self.revision_policy,
            metadata=new_metadata,
        )
```

- [ ] **Step 2: Write `test_state.py`**

```python
import pytest
from types import MappingProxyType
from epistemic_pipeline.state import EpistemicState


@pytest.fixture
def sample_state():
    return EpistemicState(
        ontology={"hypotheses": ["a", "b"]},
        evidence=[],
        beliefs={"a": 0.5, "b": 0.5},
        revision_policy=lambda b, e, o: b,
        metadata=MappingProxyType({}),
    )


class TestEpistemicStateImmutability:
    def test_frozen_cannot_assign(self, sample_state):
        with pytest.raises(AttributeError):
            sample_state.ontology = {"changed": True}

    def test_frozen_cannot_assign_beliefs(self, sample_state):
        with pytest.raises(AttributeError):
            sample_state.beliefs = {"a": 1.0}

    def test_frozen_cannot_assign_metadata(self, sample_state):
        with pytest.raises(AttributeError):
            sample_state.metadata = MappingProxyType({"key": "val"})

    def test_metadata_is_readonly(self, sample_state):
        with pytest.raises(TypeError):
            sample_state.metadata["new_key"] = "value"


class TestEpistemicStateTransitions:
    def test_with_beliefs_returns_new_state(self, sample_state):
        new = sample_state.with_beliefs({"a": 0.9, "b": 0.1})
        assert new.beliefs == {"a": 0.9, "b": 0.1}
        assert sample_state.beliefs == {"a": 0.5, "b": 0.5}
        assert new is not sample_state

    def test_with_evidence_returns_new_state(self, sample_state):
        new = sample_state.with_evidence([("fever", True)])
        assert new.evidence == [("fever", True)]
        assert sample_state.evidence == []
        assert new is not sample_state

    def test_with_metadata_returns_new_state(self, sample_state):
        new_meta = MappingProxyType({"strategy": "sequential"})
        new = sample_state.with_metadata(new_meta)
        assert new.metadata["strategy"] == "sequential"
        assert sample_state.metadata == MappingProxyType({})

    def test_with_beliefs_preserves_other_fields(self, sample_state):
        new = sample_state.with_beliefs({"a": 0.9, "b": 0.1})
        assert new.ontology is sample_state.ontology
        assert new.evidence is sample_state.evidence
        assert new.revision_policy is sample_state.revision_policy
        assert new.metadata is sample_state.metadata

    def test_with_evidence_preserves_other_fields(self, sample_state):
        new = sample_state.with_evidence([("fever", True)])
        assert new.ontology is sample_state.ontology
        assert new.beliefs is sample_state.beliefs
        assert new.revision_policy is sample_state.revision_policy
        assert new.metadata is sample_state.metadata


class TestEpistemicStateGenericTypes:
    def test_accepts_any_type_parameters(self):
        """EpistemicState is generic — it works with any types for O, E, B, R."""
        state: EpistemicState[str, list[int], dict[str, float], object] = (
            EpistemicState(
                ontology="simple",
                evidence=[1, 2, 3],
                beliefs={"x": 0.5},
                revision_policy=object(),
                metadata=MappingProxyType({}),
            )
        )
        assert state.ontology == "simple"
```

- [ ] **Step 3: Run tests**

Run: `uv run pytest tests/test_state.py -v`
Expected: All tests PASS

- [ ] **Step 4: Run pyright**

Run: `uv run pyright src/epistemic_pipeline/state.py`
Expected: 0 errors

- [ ] **Step 5: Commit**

```bash
git add src/epistemic_pipeline/state.py tests/test_state.py
git commit -m "feat: add EpistemicState (O,E,B,R) core state model"
```

---

## Task 2: Pipeline (`pipeline.py`)

The 6-stage pipeline runner. Stages are protocols. The runner composes them and preserves the trace.

**Files:**
- Create: `src/epistemic_pipeline/pipeline.py`
- Create: `tests/test_pipeline.py`

**Key design decisions:**
- `Stage` is a `Protocol` with a single `__call__` method: state in, state out
- `run_pipeline()` takes an initial state and a sequence of stages, runs them in order
- `PipelineResult` holds the final state and the full trace (list of every intermediate state)
- Each stage's output is appended to the trace before the next stage runs

- [ ] **Step 1: Write `pipeline.py`**

```python
"""Pipeline: stage protocol, runner, and trace.

Six stages process the state in sequence. Each is a pure function:
state in, state out.

    integrate(experiment(strategy(model(decompose(frame(initial_state))))))

The runner composes stages and preserves the full trace — every
intermediate state, from input through each stage's output.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from epistemic_pipeline.state import EpistemicState


class Stage(Protocol):
    """A single pipeline stage.

    Takes an EpistemicState, returns a new EpistemicState.
    Must be a pure function: no side effects, deterministic.
    """

    @property
    def name(self) -> str:
        """Short name for this stage (e.g., 'frame', 'experiment')."""
        ...

    def __call__(
        self,
        state: EpistemicState[Any, Any, Any, Any],
    ) -> EpistemicState[Any, Any, Any, Any]:
        """Process the state and return a new one."""
        ...


@dataclass(frozen=True)
class PipelineResult[O_t, E_t, B_t, R_t]:
    """The output of a pipeline run.

    Attributes:
        final_state: The state after all stages have run.
        trace: Every intermediate state, starting with the input.
            trace[0] is the initial state. trace[-1] is the final state.
    """

    final_state: EpistemicState[O_t, E_t, B_t, R_t]
    trace: tuple[EpistemicState[O_t, E_t, B_t, R_t], ...]


def run_pipeline[O_t, E_t, B_t, R_t](
    initial_state: EpistemicState[O_t, E_t, B_t, R_t],
    stages: Sequence[Stage],
) -> PipelineResult[O_t, E_t, B_t, R_t]:
    """Run a sequence of stages on an initial state.

    Each stage takes the current state and returns a new one.
    The trace records every intermediate state.

    Args:
        initial_state: The starting epistemic state.
        stages: Ordered sequence of pipeline stages to apply.

    Returns:
        PipelineResult with the final state and the full trace.
    """
    trace: list[EpistemicState[O_t, E_t, B_t, R_t]] = [initial_state]
    current = initial_state

    for stage in stages:
        current = stage(current)  # type: ignore[assignment]
        trace.append(current)

    return PipelineResult(
        final_state=current,
        trace=tuple(trace),
    )
```

Note: add `from collections.abc import Sequence` import.

- [ ] **Step 2: Write `test_pipeline.py`**

```python
import pytest
from types import MappingProxyType
from epistemic_pipeline.state import EpistemicState
from epistemic_pipeline.pipeline import Stage, PipelineResult, run_pipeline


class IdentityStage:
    """A no-op stage that returns the state unchanged."""

    @property
    def name(self) -> str:
        return "identity"

    def __call__(self, state):
        return state


class DoubleBeliefStage:
    """Test stage that doubles all belief values."""

    @property
    def name(self) -> str:
        return "double"

    def __call__(self, state):
        new_beliefs = {k: v * 2 for k, v in state.beliefs.items()}
        return state.with_beliefs(new_beliefs)


class AppendEvidenceStage:
    """Test stage that appends a fixed observation."""

    def __init__(self, observation):
        self._observation = observation

    @property
    def name(self) -> str:
        return "append_evidence"

    def __call__(self, state):
        return state.with_evidence([*state.evidence, self._observation])


@pytest.fixture
def initial_state():
    return EpistemicState(
        ontology={"hypotheses": ["a", "b"]},
        evidence=[],
        beliefs={"a": 0.5, "b": 0.5},
        revision_policy=lambda b, e, o: b,
        metadata=MappingProxyType({}),
    )


class TestRunPipeline:
    def test_empty_pipeline_returns_initial_state(self, initial_state):
        result = run_pipeline(initial_state, [])
        assert result.final_state is initial_state
        assert len(result.trace) == 1
        assert result.trace[0] is initial_state

    def test_single_stage(self, initial_state):
        result = run_pipeline(initial_state, [DoubleBeliefStage()])
        assert result.final_state.beliefs == {"a": 1.0, "b": 1.0}
        assert len(result.trace) == 2

    def test_multiple_stages_compose(self, initial_state):
        stages = [DoubleBeliefStage(), DoubleBeliefStage()]
        result = run_pipeline(initial_state, stages)
        assert result.final_state.beliefs == {"a": 2.0, "b": 2.0}
        assert len(result.trace) == 3

    def test_trace_preserves_all_intermediate_states(self, initial_state):
        stages = [DoubleBeliefStage(), DoubleBeliefStage()]
        result = run_pipeline(initial_state, stages)
        assert result.trace[0].beliefs == {"a": 0.5, "b": 0.5}
        assert result.trace[1].beliefs == {"a": 1.0, "b": 1.0}
        assert result.trace[2].beliefs == {"a": 2.0, "b": 2.0}

    def test_trace_first_is_initial_last_is_final(self, initial_state):
        result = run_pipeline(initial_state, [DoubleBeliefStage()])
        assert result.trace[0] is initial_state
        assert result.trace[-1] is result.final_state

    def test_identity_stage_preserves_state(self, initial_state):
        result = run_pipeline(initial_state, [IdentityStage()])
        assert result.final_state is initial_state

    def test_evidence_stage_appends(self, initial_state):
        stages = [
            AppendEvidenceStage(("fever", True)),
            AppendEvidenceStage(("cough", True)),
        ]
        result = run_pipeline(initial_state, stages)
        assert result.final_state.evidence == [("fever", True), ("cough", True)]


class TestPipelineResult:
    def test_pipeline_result_is_frozen(self, initial_state):
        result = run_pipeline(initial_state, [])
        with pytest.raises(AttributeError):
            result.final_state = initial_state

    def test_trace_is_tuple(self, initial_state):
        result = run_pipeline(initial_state, [])
        assert isinstance(result.trace, tuple)
```

- [ ] **Step 3: Run tests**

Run: `uv run pytest tests/test_pipeline.py -v`
Expected: All tests PASS

- [ ] **Step 4: Run pyright**

Run: `uv run pyright src/epistemic_pipeline/pipeline.py`
Expected: 0 errors

- [ ] **Step 5: Commit**

```bash
git add src/epistemic_pipeline/pipeline.py tests/test_pipeline.py
git commit -m "feat: add pipeline runner with stage protocol and trace"
```

---

## Task 3: Norm Scoring (`norms.py`)

The report card for a pipeline run. Three computable norms for v0.1.

**Files:**
- Create: `src/epistemic_pipeline/norms.py`
- Create: `tests/test_norms.py`

**Key design decisions:**
- `NormScore` is a frozen dataclass
- Reliability: `1.0` if top belief matches ground truth, `0.0` otherwise
- Efficiency: count of states in the trace minus 1 (number of stage applications)
- Justification: replay evidence through R from initial beliefs — if final beliefs match, justified
- Power: `Optional[str]`, not computed, described in words

- [ ] **Step 1: Write `norms.py`**

```python
"""Epistemic norms: scoring the quality of a pipeline run.

Four norms evaluate reasoning quality:
- Reliability: did the system get the right answer?
- Power: how many kinds of problems can it handle? (not computed in v0.1)
- Efficiency: how much work did it take?
- Justification: can we prove the final beliefs came from the evidence?
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from epistemic_pipeline.state import EpistemicState


@dataclass(frozen=True)
class NormScore:
    """Report card for one pipeline run.

    Attributes:
        reliability: 1.0 if the top belief matches ground truth, else 0.0.
        efficiency: Number of pipeline stages that ran.
        justification: True if replaying evidence from the initial state
            reproduces the final beliefs.
        power: Not computed in v0.1. A human-readable description.
    """

    reliability: float
    efficiency: int
    justification: bool
    power: str | None


def _get_top_belief(beliefs: Any) -> Any:
    """Return the key with the highest value from a dict-like beliefs object."""
    return max(beliefs, key=lambda k: beliefs[k])


def score_reliability(
    final_beliefs: Any,
    ground_truth: Any,
) -> float:
    """Score reliability: 1.0 if top belief matches ground truth, else 0.0.

    Args:
        final_beliefs: The beliefs at the end of the pipeline run.
            Must support dict-like iteration and indexing.
        ground_truth: The correct answer (e.g., "covid").

    Returns:
        1.0 or 0.0.
    """
    return 1.0 if _get_top_belief(final_beliefs) == ground_truth else 0.0


def score_efficiency(
    trace: tuple[EpistemicState[Any, Any, Any, Any], ...],
) -> int:
    """Score efficiency: number of stages that ran.

    Args:
        trace: The full pipeline trace.

    Returns:
        Number of stage transitions (len(trace) - 1).
    """
    return len(trace) - 1


def score_justification(
    trace: tuple[EpistemicState[Any, Any, Any, Any], ...],
) -> bool:
    """Score justification: can we reproduce the final beliefs by replay?

    Replays all evidence through R starting from the initial beliefs.
    If the result matches the final beliefs, the run is justified.

    This works because R is pure and deterministic. Same inputs,
    same outputs. Justification becomes a mathematical check.

    Args:
        trace: The full pipeline trace.

    Returns:
        True if replay produces the same final beliefs.
    """
    if len(trace) < 2:
        return True

    initial = trace[0]
    final = trace[-1]

    # Replay: apply R to each piece of evidence in order
    replayed_beliefs = initial.beliefs
    revision = initial.revision_policy
    ontology = initial.ontology

    # Collect all evidence from the final state
    evidence = final.evidence
    if not evidence:
        return replayed_beliefs == final.beliefs

    for item in evidence:
        replayed_beliefs = revision(replayed_beliefs, item, ontology)

    return replayed_beliefs == final.beliefs


def score_pipeline_run(
    trace: tuple[EpistemicState[Any, Any, Any, Any], ...],
    ground_truth: Any,
) -> NormScore:
    """Score a complete pipeline run against all v0.1 norms.

    Args:
        trace: The full pipeline trace (from PipelineResult.trace).
        ground_truth: The correct answer to compare against.

    Returns:
        A NormScore with all four evaluations.
    """
    final = trace[-1]
    return NormScore(
        reliability=score_reliability(final.beliefs, ground_truth),
        efficiency=score_efficiency(trace),
        justification=score_justification(trace),
        power=None,
    )
```

- [ ] **Step 2: Write `test_norms.py`**

```python
import pytest
from types import MappingProxyType
from epistemic_pipeline.state import EpistemicState
from epistemic_pipeline.norms import (
    NormScore,
    score_reliability,
    score_efficiency,
    score_justification,
    score_pipeline_run,
)


def _make_state(beliefs, evidence=None, revision_policy=None, ontology=None):
    return EpistemicState(
        ontology=ontology or {},
        evidence=evidence if evidence is not None else [],
        beliefs=beliefs,
        revision_policy=revision_policy or (lambda b, e, o: b),
        metadata=MappingProxyType({}),
    )


class TestReliability:
    def test_correct_top_belief(self):
        assert score_reliability({"flu": 0.1, "covid": 0.9}, "covid") == 1.0

    def test_incorrect_top_belief(self):
        assert score_reliability({"flu": 0.9, "covid": 0.1}, "covid") == 0.0

    def test_tie_goes_to_arbitrary_max(self):
        """When beliefs are tied, max() picks one. Either is acceptable."""
        result = score_reliability({"a": 0.5, "b": 0.5}, "a")
        assert result in (0.0, 1.0)


class TestEfficiency:
    def test_no_stages(self):
        trace = (_make_state({"a": 0.5}),)
        assert score_efficiency(trace) == 0

    def test_three_stages(self):
        s = _make_state({"a": 0.5})
        trace = (s, s, s, s)
        assert score_efficiency(trace) == 3


class TestJustification:
    def test_trivial_trace_is_justified(self):
        trace = (_make_state({"a": 0.5}),)
        assert score_justification(trace) is True

    def test_consistent_revision_is_justified(self):
        """If R doubles belief values, replaying should reproduce that."""
        def double_revision(beliefs, evidence_item, ontology):
            return {k: v * 2 for k, v in beliefs.items()}

        initial = _make_state(
            beliefs={"a": 0.5, "b": 0.5},
            evidence=[],
            revision_policy=double_revision,
        )
        final = _make_state(
            beliefs={"a": 1.0, "b": 1.0},
            evidence=[("obs1",)],
            revision_policy=double_revision,
        )
        trace = (initial, final)
        assert score_justification(trace) is True

    def test_inconsistent_beliefs_not_justified(self):
        """If final beliefs don't match what R would produce, not justified."""
        def double_revision(beliefs, evidence_item, ontology):
            return {k: v * 2 for k, v in beliefs.items()}

        initial = _make_state(
            beliefs={"a": 0.5, "b": 0.5},
            evidence=[],
            revision_policy=double_revision,
        )
        # Wrong final beliefs — R would give {a: 1.0, b: 1.0}
        final = _make_state(
            beliefs={"a": 0.3, "b": 0.7},
            evidence=[("obs1",)],
            revision_policy=double_revision,
        )
        trace = (initial, final)
        assert score_justification(trace) is False


class TestScorePipelineRun:
    def test_full_scoring(self):
        def identity_revision(beliefs, evidence_item, ontology):
            return beliefs

        initial = _make_state(
            beliefs={"a": 0.9, "b": 0.1},
            evidence=[],
            revision_policy=identity_revision,
        )
        final = _make_state(
            beliefs={"a": 0.9, "b": 0.1},
            evidence=[],
            revision_policy=identity_revision,
        )
        trace = (initial, final)
        score = score_pipeline_run(trace, ground_truth="a")

        assert score.reliability == 1.0
        assert score.efficiency == 1
        assert score.justification is True
        assert score.power is None

    def test_norm_score_is_frozen(self):
        score = NormScore(reliability=1.0, efficiency=1, justification=True, power=None)
        with pytest.raises(AttributeError):
            score.reliability = 0.5
```

- [ ] **Step 3: Run tests**

Run: `uv run pytest tests/test_norms.py -v`
Expected: All tests PASS

- [ ] **Step 4: Run pyright**

Run: `uv run pyright src/epistemic_pipeline/norms.py`
Expected: 0 errors

- [ ] **Step 5: Commit**

```bash
git add src/epistemic_pipeline/norms.py tests/test_norms.py
git commit -m "feat: add epistemic norm scoring (reliability, efficiency, justification)"
```

---

## Task 4: Meta-Epistemic Controller (`meta.py`)

A stub. The interface exists. It always returns ACCEPT. The point: prove all five layers wire up.

**Files:**
- Create: `src/epistemic_pipeline/meta.py`
- Create: `tests/test_meta.py`

- [ ] **Step 1: Write `meta.py`**

```python
"""Meta-epistemic layer: the system's self-monitor.

Watches the pipeline, checks the norm scores, and decides what to
do next. In v0.1 this is a stub — it always returns ACCEPT.

The point: prove all five layers of the architecture are wired up
before adding real decision logic in v0.2+.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import Any

from epistemic_pipeline.norms import NormScore
from epistemic_pipeline.state import EpistemicState


class MetaDecisionType(enum.Enum):
    """What the meta-layer decides to do.

    ACCEPT: the pipeline run is good. Keep the results.
    REFRAME: the vocabulary needs changing. Re-run with a new O.
    SWITCH_STRATEGY: the strategy is inefficient. Try a different one.
    ESCALATE: something is wrong that the system cannot fix alone.
    """

    ACCEPT = "accept"
    REFRAME = "reframe"
    SWITCH_STRATEGY = "switch_strategy"
    ESCALATE = "escalate"


@dataclass(frozen=True)
class MetaDecision:
    """A decision from the meta-epistemic layer.

    Attributes:
        decision: What to do next.
        details: Extra information for v0.2+ (e.g., why it chose REFRAME).
    """

    decision: MetaDecisionType
    details: dict[str, Any] = field(default_factory=dict)


class MetaEpistemicController:
    """The meta-epistemic controller.

    v0.1: always returns ACCEPT. The interface is the deliverable.
    """

    def monitor(
        self,
        trace: tuple[EpistemicState[Any, Any, Any, Any], ...],
        scores: NormScore,
    ) -> MetaDecision:
        """Evaluate a pipeline run and decide what to do next.

        Args:
            trace: The full pipeline trace.
            scores: The norm scores for this run.

        Returns:
            MetaDecision — always ACCEPT in v0.1.
        """
        return MetaDecision(decision=MetaDecisionType.ACCEPT)
```

- [ ] **Step 2: Write `test_meta.py`**

```python
import pytest
from types import MappingProxyType
from epistemic_pipeline.state import EpistemicState
from epistemic_pipeline.norms import NormScore
from epistemic_pipeline.meta import (
    MetaDecision,
    MetaDecisionType,
    MetaEpistemicController,
)


@pytest.fixture
def dummy_trace():
    state = EpistemicState(
        ontology={},
        evidence=[],
        beliefs={"a": 0.5},
        revision_policy=lambda b, e, o: b,
        metadata=MappingProxyType({}),
    )
    return (state,)


@pytest.fixture
def dummy_scores():
    return NormScore(reliability=1.0, efficiency=1, justification=True, power=None)


class TestMetaEpistemicController:
    def test_stub_returns_accept(self, dummy_trace, dummy_scores):
        controller = MetaEpistemicController()
        decision = controller.monitor(dummy_trace, dummy_scores)
        assert decision.decision == MetaDecisionType.ACCEPT

    def test_stub_returns_empty_details(self, dummy_trace, dummy_scores):
        controller = MetaEpistemicController()
        decision = controller.monitor(dummy_trace, dummy_scores)
        assert decision.details == {}

    def test_returns_meta_decision_type(self, dummy_trace, dummy_scores):
        controller = MetaEpistemicController()
        decision = controller.monitor(dummy_trace, dummy_scores)
        assert isinstance(decision, MetaDecision)


class TestMetaDecision:
    def test_meta_decision_is_frozen(self):
        d = MetaDecision(decision=MetaDecisionType.ACCEPT)
        with pytest.raises(AttributeError):
            d.decision = MetaDecisionType.REFRAME

    def test_all_decision_types_exist(self):
        assert MetaDecisionType.ACCEPT.value == "accept"
        assert MetaDecisionType.REFRAME.value == "reframe"
        assert MetaDecisionType.SWITCH_STRATEGY.value == "switch_strategy"
        assert MetaDecisionType.ESCALATE.value == "escalate"
```

- [ ] **Step 3: Run tests**

Run: `uv run pytest tests/test_meta.py -v`
Expected: All tests PASS

- [ ] **Step 4: Run pyright**

Run: `uv run pyright src/epistemic_pipeline/meta.py`
Expected: 0 errors

- [ ] **Step 5: Commit**

```bash
git add src/epistemic_pipeline/meta.py tests/test_meta.py
git commit -m "feat: add meta-epistemic controller stub (always ACCEPT)"
```

---

## Task 5: Bayesian Encoding (`encodings/bayes.py`)

The first expressiveness proof. Encode Bayesian inference as a special case of `(O, E, B, R)`.

**Files:**
- Create: `src/epistemic_pipeline/encodings/bayes.py`
- Create: `tests/test_bayes.py`

**Key design decisions:**
- `BayesVocabulary`: frozen dataclass with hypotheses, observables, and a likelihood table
- `BayesEvidence`: frozen dataclass wrapping a tuple of `(observable, value)` pairs, with `append()` returning a new instance
- `BayesCredences`: frozen dataclass wrapping a dict-like mapping from hypothesis to probability, must sum to ~1.0
- `BayesRevision`: callable implementing Bayes' rule — `P(H|e) = P(e|H) * P(H) / P(e)`
- `bayes_stages()`: returns the 6 pipeline stages pre-configured for Bayesian inference
- Likelihoods keyed as `(hypothesis, observable, value)` → `float`

- [ ] **Step 1: Write `encodings/bayes.py`**

```python
"""Bayesian inference encoding for the epistemic pipeline.

Encodes Bayesian inference as a special case of (O, E, B, R):
- O = BayesVocabulary: hypotheses, observables, likelihood table
- E = BayesEvidence: observed (observable, value) pairs
- B = BayesCredences: probability distribution over hypotheses
- R = BayesRevision: Bayes' rule

The toy problem: diagnose a patient from symptoms.
"""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Any

from epistemic_pipeline.state import EpistemicState


# ---------------------------------------------------------------------------
# O — Vocabulary
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class BayesVocabulary:
    """The vocabulary for a Bayesian inference problem.

    Attributes:
        hypotheses: The possible outcomes (e.g., diseases).
        observables: The things we can observe (e.g., symptoms).
        likelihoods: P(observable=value | hypothesis).
            Keyed as (hypothesis, observable, value) -> probability.
            Example: ("flu", "fever", True) -> 0.8 means
            "if the patient has flu, 80% chance of fever."
    """

    hypotheses: tuple[str, ...]
    observables: tuple[str, ...]
    likelihoods: MappingProxyType[tuple[str, str, bool], float]


# ---------------------------------------------------------------------------
# E — Evidence
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class BayesEvidence:
    """Observed data for a Bayesian inference problem.

    An ordered sequence of (observable, value) pairs.
    Append-only: call append() to get a new BayesEvidence with the
    item added. Does not mutate self.
    """

    observations: tuple[tuple[str, bool], ...]

    def append(self, item: tuple[str, bool]) -> BayesEvidence:
        """Return a new BayesEvidence with the item added."""
        return BayesEvidence(observations=(*self.observations, item))

    def __iter__(self):
        return iter(self.observations)

    def __len__(self) -> int:
        return len(self.observations)

    def __bool__(self) -> bool:
        return len(self.observations) > 0


# ---------------------------------------------------------------------------
# B — Credences
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class BayesCredences:
    """A probability distribution over hypotheses.

    Each hypothesis maps to a float between 0 and 1.
    Values must sum to approximately 1.0.
    """

    distribution: MappingProxyType[str, float]

    def __getitem__(self, key: str) -> float:
        return self.distribution[key]

    def __iter__(self):
        return iter(self.distribution)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, BayesCredences):
            return self.distribution == other.distribution
        return NotImplemented

    def top(self) -> str:
        """Return the hypothesis with the highest credence."""
        return max(self.distribution, key=lambda k: self.distribution[k])

    def items(self):
        """Return (hypothesis, credence) pairs."""
        return self.distribution.items()


def make_credences(mapping: dict[str, float]) -> BayesCredences:
    """Create BayesCredences from a plain dict.

    Args:
        mapping: Hypothesis -> probability. Must sum to ~1.0.

    Returns:
        Frozen BayesCredences.

    Raises:
        ValueError: If probabilities don't sum to ~1.0.
    """
    total = sum(mapping.values())
    if abs(total - 1.0) > 1e-9:
        msg = f"Probabilities must sum to 1.0, got {total}"
        raise ValueError(msg)
    return BayesCredences(distribution=MappingProxyType(mapping))


# ---------------------------------------------------------------------------
# R — Revision (Bayes' rule)
# ---------------------------------------------------------------------------

class BayesRevision:
    """Revision policy implementing Bayes' rule.

    For each hypothesis h and observation (observable, value):
        P(h | e) = P(e | h) * P(h) / P(e)

    where P(e) = sum over all h of P(e | h) * P(h).

    This is the standard formula for updating beliefs from evidence.
    """

    def __call__(
        self,
        beliefs: BayesCredences,
        evidence_item: tuple[str, bool],
        ontology: BayesVocabulary,
    ) -> BayesCredences:
        """Apply Bayes' rule for one observation.

        Args:
            beliefs: Current probability distribution.
            evidence_item: (observable, observed_value) pair.
            ontology: Vocabulary with likelihood table.

        Returns:
            Updated BayesCredences (posterior distribution).
        """
        observable, value = evidence_item

        # Compute unnormalized posteriors: P(e|h) * P(h) for each h
        unnormalized: dict[str, float] = {}
        for h in ontology.hypotheses:
            likelihood = ontology.likelihoods.get((h, observable, value), 0.0)
            prior = beliefs[h]
            unnormalized[h] = likelihood * prior

        # Normalize: divide by P(e) = sum of unnormalized
        total = sum(unnormalized.values())
        if total == 0:
            msg = f"Total probability is 0 for observation ({observable}, {value})"
            raise ValueError(msg)

        posterior = {h: p / total for h, p in unnormalized.items()}
        return BayesCredences(distribution=MappingProxyType(posterior))


# ---------------------------------------------------------------------------
# Pipeline stages for Bayesian inference
# ---------------------------------------------------------------------------

class BayesFrameStage:
    """Stage 1: Frame — set up the vocabulary.

    For pre-configured problems, this is a no-op. The vocabulary
    is already in the state.
    """

    @property
    def name(self) -> str:
        return "frame"

    def __call__(
        self,
        state: EpistemicState[BayesVocabulary, BayesEvidence, BayesCredences, BayesRevision],
    ) -> EpistemicState[BayesVocabulary, BayesEvidence, BayesCredences, BayesRevision]:
        return state


class BayesDecomposeStage:
    """Stage 2: Decompose — split into sub-problems.

    For simple single-question problems, this is a no-op.
    """

    @property
    def name(self) -> str:
        return "decompose"

    def __call__(
        self,
        state: EpistemicState[BayesVocabulary, BayesEvidence, BayesCredences, BayesRevision],
    ) -> EpistemicState[BayesVocabulary, BayesEvidence, BayesCredences, BayesRevision]:
        return state


class BayesModelStage:
    """Stage 3: Model — verify beliefs and revision are set up.

    Checks that B and R are compatible. For pre-configured problems
    where B and R are already in the state, this validates but
    does not change anything.
    """

    @property
    def name(self) -> str:
        return "model"

    def __call__(
        self,
        state: EpistemicState[BayesVocabulary, BayesEvidence, BayesCredences, BayesRevision],
    ) -> EpistemicState[BayesVocabulary, BayesEvidence, BayesCredences, BayesRevision]:
        # Validate: every hypothesis in O has a belief in B
        for h in state.ontology.hypotheses:
            if h not in state.beliefs.distribution:
                msg = f"Hypothesis '{h}' in ontology but missing from beliefs"
                raise ValueError(msg)
        return state


class BayesStrategyStage:
    """Stage 4: Strategy — decide evidence processing order.

    Stores the strategy in metadata. For v0.1: process all
    evidence in order, stop when confidence > 0.95 or all used.
    """

    def __init__(
        self,
        evidence_sequence: tuple[tuple[str, bool], ...],
        confidence_threshold: float = 0.95,
    ) -> None:
        self._evidence_sequence = evidence_sequence
        self._confidence_threshold = confidence_threshold

    @property
    def name(self) -> str:
        return "strategy"

    def __call__(
        self,
        state: EpistemicState[BayesVocabulary, BayesEvidence, BayesCredences, BayesRevision],
    ) -> EpistemicState[BayesVocabulary, BayesEvidence, BayesCredences, BayesRevision]:
        new_metadata = MappingProxyType({
            **state.metadata,
            "strategy": "sequential",
            "evidence_sequence": self._evidence_sequence,
            "confidence_threshold": self._confidence_threshold,
        })
        return state.with_metadata(new_metadata)


class BayesExperimentStage:
    """Stage 5: Experiment — apply R for each observation.

    Reads the evidence sequence from metadata (set by strategy).
    Applies Bayes' rule once per observation. Stops early if
    the top hypothesis exceeds the confidence threshold.
    """

    @property
    def name(self) -> str:
        return "experiment"

    def __call__(
        self,
        state: EpistemicState[BayesVocabulary, BayesEvidence, BayesCredences, BayesRevision],
    ) -> EpistemicState[BayesVocabulary, BayesEvidence, BayesCredences, BayesRevision]:
        evidence_sequence = state.metadata["evidence_sequence"]
        threshold = state.metadata["confidence_threshold"]
        revision = state.revision_policy

        current_beliefs = state.beliefs
        current_evidence = state.evidence

        for obs in evidence_sequence:
            current_beliefs = revision(current_beliefs, obs, state.ontology)
            current_evidence = current_evidence.append(obs)

            # Early stopping
            top_credence = max(current_beliefs.distribution.values())
            if top_credence >= threshold:
                break

        return EpistemicState(
            ontology=state.ontology,
            evidence=current_evidence,
            beliefs=current_beliefs,
            revision_policy=state.revision_policy,
            metadata=state.metadata,
        )


class BayesIntegrateStage:
    """Stage 6: Integrate — read the final state, produce a conclusion.

    Does not change O, E, B, or R. Stores the conclusion in metadata:
    the top hypothesis, its confidence, and the full distribution.
    """

    @property
    def name(self) -> str:
        return "integrate"

    def __call__(
        self,
        state: EpistemicState[BayesVocabulary, BayesEvidence, BayesCredences, BayesRevision],
    ) -> EpistemicState[BayesVocabulary, BayesEvidence, BayesCredences, BayesRevision]:
        top = state.beliefs.top()
        confidence = state.beliefs[top]
        new_metadata = MappingProxyType({
            **state.metadata,
            "conclusion": top,
            "confidence": confidence,
            "distribution": dict(state.beliefs.items()),
        })
        return state.with_metadata(new_metadata)


def bayes_stages(
    evidence: tuple[tuple[str, bool], ...],
    confidence_threshold: float = 0.95,
) -> tuple[
    BayesFrameStage,
    BayesDecomposeStage,
    BayesModelStage,
    BayesStrategyStage,
    BayesExperimentStage,
    BayesIntegrateStage,
]:
    """Return the 6 pipeline stages pre-configured for Bayesian inference.

    Args:
        evidence: The observations to process, in order.
        confidence_threshold: Stop early if top credence exceeds this.

    Returns:
        A tuple of 6 stages ready to pass to run_pipeline().
    """
    return (
        BayesFrameStage(),
        BayesDecomposeStage(),
        BayesModelStage(),
        BayesStrategyStage(evidence, confidence_threshold),
        BayesExperimentStage(),
        BayesIntegrateStage(),
    )
```

- [ ] **Step 2: Write `test_bayes.py`**

```python
import pytest
from types import MappingProxyType

from epistemic_pipeline.state import EpistemicState
from epistemic_pipeline.pipeline import run_pipeline
from epistemic_pipeline.norms import score_pipeline_run
from epistemic_pipeline.meta import MetaEpistemicController
from epistemic_pipeline.encodings.bayes import (
    BayesVocabulary,
    BayesEvidence,
    BayesCredences,
    BayesRevision,
    bayes_stages,
    make_credences,
)

# --- Fixtures: the medical diagnosis toy problem ---

LIKELIHOODS = MappingProxyType({
    ("flu",   "fever", True): 0.8,
    ("flu",   "fever", False): 0.2,
    ("flu",   "cough", True): 0.7,
    ("flu",   "cough", False): 0.3,
    ("flu",   "loss_of_smell", True): 0.05,
    ("flu",   "loss_of_smell", False): 0.95,
    ("cold",  "fever", True): 0.3,
    ("cold",  "fever", False): 0.7,
    ("cold",  "cough", True): 0.9,
    ("cold",  "cough", False): 0.1,
    ("cold",  "loss_of_smell", True): 0.02,
    ("cold",  "loss_of_smell", False): 0.98,
    ("covid", "fever", True): 0.85,
    ("covid", "fever", False): 0.15,
    ("covid", "cough", True): 0.8,
    ("covid", "cough", False): 0.2,
    ("covid", "loss_of_smell", True): 0.7,
    ("covid", "loss_of_smell", False): 0.3,
})


@pytest.fixture
def vocab():
    return BayesVocabulary(
        hypotheses=("flu", "cold", "covid"),
        observables=("fever", "cough", "loss_of_smell"),
        likelihoods=LIKELIHOODS,
    )


@pytest.fixture
def priors():
    return make_credences({"flu": 0.4, "cold": 0.4, "covid": 0.2})


@pytest.fixture
def evidence_sequence():
    return (("fever", True), ("cough", True), ("loss_of_smell", True))


# --- BayesVocabulary ---

class TestBayesVocabulary:
    def test_frozen(self, vocab):
        with pytest.raises(AttributeError):
            vocab.hypotheses = ("changed",)

    def test_lookup_likelihood(self, vocab):
        assert vocab.likelihoods[("flu", "fever", True)] == 0.8


# --- BayesEvidence ---

class TestBayesEvidence:
    def test_empty(self):
        e = BayesEvidence(observations=())
        assert len(e) == 0
        assert not e

    def test_append_returns_new(self):
        e = BayesEvidence(observations=())
        e2 = e.append(("fever", True))
        assert len(e) == 0
        assert len(e2) == 1
        assert e2.observations == (("fever", True),)

    def test_frozen(self):
        e = BayesEvidence(observations=())
        with pytest.raises(AttributeError):
            e.observations = (("fever", True),)


# --- BayesCredences ---

class TestBayesCredences:
    def test_make_credences_valid(self):
        c = make_credences({"a": 0.6, "b": 0.4})
        assert c["a"] == 0.6

    def test_make_credences_invalid_sum(self):
        with pytest.raises(ValueError, match="sum to 1.0"):
            make_credences({"a": 0.5, "b": 0.3})

    def test_top(self, priors):
        # Priors: flu=0.4, cold=0.4, covid=0.2. Tie between flu and cold.
        assert priors.top() in ("flu", "cold")

    def test_frozen(self, priors):
        with pytest.raises(AttributeError):
            priors.distribution = MappingProxyType({})


# --- BayesRevision ---

class TestBayesRevision:
    def test_single_update(self, vocab, priors):
        revision = BayesRevision()
        posterior = revision(priors, ("fever", True), vocab)
        # After fever: covid has highest likelihood (0.85) but flu is close (0.8).
        # With equal priors for flu/cold, flu should still lead over cold.
        assert posterior["flu"] > posterior["cold"]

    def test_probabilities_sum_to_one(self, vocab, priors):
        revision = BayesRevision()
        posterior = revision(priors, ("fever", True), vocab)
        total = sum(posterior[h] for h in vocab.hypotheses)
        assert abs(total - 1.0) < 1e-9

    def test_loss_of_smell_favors_covid(self, vocab, priors):
        revision = BayesRevision()
        posterior = revision(priors, ("loss_of_smell", True), vocab)
        assert posterior["covid"] > posterior["flu"]
        assert posterior["covid"] > posterior["cold"]


# --- End-to-end pipeline ---

class TestBayesEndToEnd:
    def test_medical_diagnosis_identifies_covid(self, vocab, priors, evidence_sequence):
        """The full pipeline: three symptoms in, covid diagnosis out."""
        stages = bayes_stages(evidence_sequence)
        initial = EpistemicState(
            ontology=vocab,
            evidence=BayesEvidence(observations=()),
            beliefs=priors,
            revision_policy=BayesRevision(),
            metadata=MappingProxyType({}),
        )
        result = run_pipeline(initial, stages)

        assert result.final_state.metadata["conclusion"] == "covid"
        assert result.final_state.metadata["confidence"] > 0.8

    def test_trace_has_correct_length(self, vocab, priors, evidence_sequence):
        stages = bayes_stages(evidence_sequence)
        initial = EpistemicState(
            ontology=vocab,
            evidence=BayesEvidence(observations=()),
            beliefs=priors,
            revision_policy=BayesRevision(),
            metadata=MappingProxyType({}),
        )
        result = run_pipeline(initial, stages)

        # 1 initial + 6 stages = 7 states in trace
        assert len(result.trace) == 7

    def test_norms_score_correctly(self, vocab, priors, evidence_sequence):
        stages = bayes_stages(evidence_sequence)
        initial = EpistemicState(
            ontology=vocab,
            evidence=BayesEvidence(observations=()),
            beliefs=priors,
            revision_policy=BayesRevision(),
            metadata=MappingProxyType({}),
        )
        result = run_pipeline(initial, stages)

        scores = score_pipeline_run(result.trace, ground_truth="covid")
        assert scores.reliability == 1.0
        assert scores.efficiency == 6  # 6 stages
        assert scores.justification is True

    def test_meta_controller_accepts(self, vocab, priors, evidence_sequence):
        stages = bayes_stages(evidence_sequence)
        initial = EpistemicState(
            ontology=vocab,
            evidence=BayesEvidence(observations=()),
            beliefs=priors,
            revision_policy=BayesRevision(),
            metadata=MappingProxyType({}),
        )
        result = run_pipeline(initial, stages)
        scores = score_pipeline_run(result.trace, ground_truth="covid")

        controller = MetaEpistemicController()
        decision = controller.monitor(result.trace, scores)
        from epistemic_pipeline.meta import MetaDecisionType
        assert decision.decision == MetaDecisionType.ACCEPT
```

- [ ] **Step 3: Run tests**

Run: `uv run pytest tests/test_bayes.py -v`
Expected: All tests PASS

- [ ] **Step 4: Run pyright on all source**

Run: `uv run pyright src/`
Expected: 0 errors

- [ ] **Step 5: Commit**

```bash
git add src/epistemic_pipeline/encodings/bayes.py tests/test_bayes.py
git commit -m "feat: add Bayesian inference encoding with medical diagnosis"
```

---

## Task 6: Trace Replay Test

Dedicated test proving replay reproduces final beliefs — the justification norm's backbone.

**Files:**
- Create: `tests/test_trace_replay.py`

- [ ] **Step 1: Write `test_trace_replay.py`**

```python
"""Replay tests: re-running evidence through R reproduces final beliefs.

This is the backbone of the justification norm. Because R is pure
and the trace is preserved, replay is a mathematical check.
"""

import pytest
from types import MappingProxyType

from epistemic_pipeline.state import EpistemicState
from epistemic_pipeline.pipeline import run_pipeline
from epistemic_pipeline.encodings.bayes import (
    BayesVocabulary,
    BayesEvidence,
    BayesCredences,
    BayesRevision,
    bayes_stages,
    make_credences,
)

LIKELIHOODS = MappingProxyType({
    ("flu",   "fever", True): 0.8,
    ("flu",   "fever", False): 0.2,
    ("flu",   "cough", True): 0.7,
    ("flu",   "cough", False): 0.3,
    ("flu",   "loss_of_smell", True): 0.05,
    ("flu",   "loss_of_smell", False): 0.95,
    ("cold",  "fever", True): 0.3,
    ("cold",  "fever", False): 0.7,
    ("cold",  "cough", True): 0.9,
    ("cold",  "cough", False): 0.1,
    ("cold",  "loss_of_smell", True): 0.02,
    ("cold",  "loss_of_smell", False): 0.98,
    ("covid", "fever", True): 0.85,
    ("covid", "fever", False): 0.15,
    ("covid", "cough", True): 0.8,
    ("covid", "cough", False): 0.2,
    ("covid", "loss_of_smell", True): 0.7,
    ("covid", "loss_of_smell", False): 0.3,
})


def _run_medical_diagnosis():
    """Run the full medical diagnosis pipeline and return the result."""
    vocab = BayesVocabulary(
        hypotheses=("flu", "cold", "covid"),
        observables=("fever", "cough", "loss_of_smell"),
        likelihoods=LIKELIHOODS,
    )
    priors = make_credences({"flu": 0.4, "cold": 0.4, "covid": 0.2})
    evidence = (("fever", True), ("cough", True), ("loss_of_smell", True))
    stages = bayes_stages(evidence)

    initial = EpistemicState(
        ontology=vocab,
        evidence=BayesEvidence(observations=()),
        beliefs=priors,
        revision_policy=BayesRevision(),
        metadata=MappingProxyType({}),
    )
    return run_pipeline(initial, stages)


class TestTraceReplay:
    def test_replay_reproduces_final_beliefs(self):
        """Manual replay of evidence through R matches the pipeline result."""
        result = _run_medical_diagnosis()
        initial = result.trace[0]
        final = result.final_state

        # Replay: apply R to each observation from initial beliefs
        revision = BayesRevision()
        beliefs = initial.beliefs
        for obs in final.evidence:
            beliefs = revision(beliefs, obs, initial.ontology)

        # Compare: replayed beliefs must match pipeline's final beliefs
        for h in initial.ontology.hypotheses:
            assert abs(beliefs[h] - final.beliefs[h]) < 1e-12

    def test_intermediate_states_are_preserved(self):
        """Each state in the trace is a distinct, frozen snapshot."""
        result = _run_medical_diagnosis()
        seen_ids = set()
        for state in result.trace:
            # States may be the same object if a stage is a no-op,
            # but beliefs should differ after experiment stage
            seen_ids.add(id(state))

        # At minimum: initial + 6 stages = 7 states
        assert len(result.trace) == 7

    def test_evidence_accumulates_monotonically(self):
        """Evidence only grows. Each state has >= the evidence of the prior."""
        result = _run_medical_diagnosis()
        prev_len = 0
        for state in result.trace:
            current_len = len(state.evidence)
            assert current_len >= prev_len
            prev_len = current_len
```

- [ ] **Step 2: Run tests**

Run: `uv run pytest tests/test_trace_replay.py -v`
Expected: All tests PASS

- [ ] **Step 3: Commit**

```bash
git add tests/test_trace_replay.py
git commit -m "test: add trace replay tests proving justification norm"
```

---

## Task 7: Public API and Example

Wire up the public API in `__init__.py` and create the runnable example.

**Files:**
- Modify: `src/epistemic_pipeline/__init__.py`
- Create: `examples/medical_diagnosis.py`

- [ ] **Step 1: Update `__init__.py` with public API**

```python
"""Epistemic Pipeline — a general-purpose reasoning architecture.

Public API:
    EpistemicState — the (O, E, B, R) state tuple
    run_pipeline — compose stages and collect the trace
    PipelineResult — final state + full trace
    score_pipeline_run, NormScore — evaluate reasoning quality
    MetaEpistemicController, MetaDecision, MetaDecisionType — self-monitor
"""

from epistemic_pipeline.meta import (
    MetaDecision,
    MetaDecisionType,
    MetaEpistemicController,
)
from epistemic_pipeline.norms import NormScore, score_pipeline_run
from epistemic_pipeline.pipeline import PipelineResult, run_pipeline
from epistemic_pipeline.state import EpistemicState

__all__ = [
    "EpistemicState",
    "MetaDecision",
    "MetaDecisionType",
    "MetaEpistemicController",
    "NormScore",
    "PipelineResult",
    "run_pipeline",
    "score_pipeline_run",
]
```

- [ ] **Step 2: Write `examples/medical_diagnosis.py`**

```python
"""Medical diagnosis — the v0.1 toy problem.

Three symptoms in. One diagnosis out. Every step recorded.

Run: uv run python examples/medical_diagnosis.py
"""

from types import MappingProxyType

from epistemic_pipeline import (
    EpistemicState,
    MetaEpistemicController,
    run_pipeline,
    score_pipeline_run,
)
from epistemic_pipeline.encodings.bayes import (
    BayesEvidence,
    BayesRevision,
    BayesVocabulary,
    bayes_stages,
    make_credences,
)

# --- Define the problem ---

vocab = BayesVocabulary(
    hypotheses=("flu", "cold", "covid"),
    observables=("fever", "cough", "loss_of_smell"),
    likelihoods=MappingProxyType({
        ("flu",   "fever", True): 0.8,
        ("flu",   "fever", False): 0.2,
        ("flu",   "cough", True): 0.7,
        ("flu",   "cough", False): 0.3,
        ("flu",   "loss_of_smell", True): 0.05,
        ("flu",   "loss_of_smell", False): 0.95,
        ("cold",  "fever", True): 0.3,
        ("cold",  "fever", False): 0.7,
        ("cold",  "cough", True): 0.9,
        ("cold",  "cough", False): 0.1,
        ("cold",  "loss_of_smell", True): 0.02,
        ("cold",  "loss_of_smell", False): 0.98,
        ("covid", "fever", True): 0.85,
        ("covid", "fever", False): 0.15,
        ("covid", "cough", True): 0.8,
        ("covid", "cough", False): 0.2,
        ("covid", "loss_of_smell", True): 0.7,
        ("covid", "loss_of_smell", False): 0.3,
    }),
)

priors = make_credences({"flu": 0.4, "cold": 0.4, "covid": 0.2})

symptoms: tuple[tuple[str, bool], ...] = (
    ("fever", True),
    ("cough", True),
    ("loss_of_smell", True),
)

# --- Build the initial state ---

initial_state = EpistemicState(
    ontology=vocab,
    evidence=BayesEvidence(observations=()),
    beliefs=priors,
    revision_policy=BayesRevision(),
    metadata=MappingProxyType({}),
)

# --- Run the pipeline ---

stages = bayes_stages(symptoms)
result = run_pipeline(initial_state, stages)

# --- Print results ---

print("=== Medical Diagnosis ===\n")

print(f"Diagnosis: {result.final_state.metadata['conclusion']}")
print(f"Confidence: {result.final_state.metadata['confidence']:.2%}\n")

print("Final distribution:")
for h, p in result.final_state.beliefs.items():
    print(f"  {h}: {p:.4f}")

print(f"\nEvidence processed: {len(result.final_state.evidence)} observations")
print(f"Pipeline stages: {len(result.trace) - 1}")

# --- Reasoning trace ---

print("\n=== Reasoning Trace ===\n")
for i, state in enumerate(result.trace):
    if hasattr(state.beliefs, "items"):
        dist = {h: f"{p:.4f}" for h, p in state.beliefs.items()}
        print(f"Step {i}: {dist}")
        print(f"  Evidence: {len(state.evidence)} observations")

# --- Norm scoring ---

print("\n=== Norm Scores ===\n")
scores = score_pipeline_run(result.trace, ground_truth="covid")
print(f"Reliability: {scores.reliability}")
print(f"Efficiency: {scores.efficiency} stages")
print(f"Justification: {scores.justification}")

# --- Meta-epistemic layer ---

controller = MetaEpistemicController()
decision = controller.monitor(result.trace, scores)
print(f"\nMeta-layer decision: {decision.decision.value}")
```

- [ ] **Step 3: Run the example**

Run: `uv run python examples/medical_diagnosis.py`
Expected: Diagnosis is covid with high confidence. Full trace printed.

- [ ] **Step 4: Run full test suite**

Run: `uv run pytest tests/ -v`
Expected: All tests PASS

- [ ] **Step 5: Run pyright on everything**

Run: `uv run pyright src/ tests/`
Expected: 0 errors

- [ ] **Step 6: Run ruff**

Run: `uv run ruff check src/ tests/ examples/`
Expected: 0 errors (or auto-fixable only)

- [ ] **Step 7: Commit**

```bash
git add src/epistemic_pipeline/__init__.py examples/medical_diagnosis.py
git commit -m "feat: add public API and medical diagnosis example"
```

---

## Task 8: Final Verification

All 10 success criteria from the design spec, checked one by one.

- [ ] **Step 1: Verify success criteria**

| # | Criterion | Command |
|---|-----------|---------|
| 1 | O, E, B, R are generic frozen dataclasses | `uv run pytest tests/test_state.py -v` |
| 2 | 6 pipeline stages run as pure functions | `uv run pytest tests/test_pipeline.py -v` |
| 3 | Bayesian inference is encoded | `uv run pytest tests/test_bayes.py -v` |
| 4 | Medical diagnosis runs end-to-end | `uv run python examples/medical_diagnosis.py` |
| 5 | Posterior converges to covid | Check example output |
| 6 | State trace is preserved and replayable | `uv run pytest tests/test_trace_replay.py -v` |
| 7 | Norm scoring works | `uv run pytest tests/test_norms.py -v` |
| 8 | Meta controller stub returns ACCEPT | `uv run pytest tests/test_meta.py -v` |
| 9 | All tests pass | `uv run pytest tests/ -v` |
| 10 | Pyright passes | `uv run pyright src/ tests/` |

- [ ] **Step 2: Run full verification**

```bash
uv run pytest tests/ -v && uv run pyright src/ tests/ && uv run ruff check src/ tests/ examples/ && uv run python examples/medical_diagnosis.py
```

Expected: All pass. Example prints covid diagnosis.

- [ ] **Step 3: Final commit**

```bash
git add -A
git commit -m "chore: v0.1 implementation complete — all 10 success criteria met"
```
