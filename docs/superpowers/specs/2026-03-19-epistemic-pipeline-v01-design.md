# Epistemic Pipeline v0.1 — Design Specification

**Date:** 2026-03-19
**Status:** Approved
**Scope:** Formal specification + reference implementation of a universal reasoning architecture

---

## 1. Mission

Develop a universal reasoning architecture that integrates epistemic norms, cognitive science, and structured problem-solving into a coherent pipeline. The system evaluates and orchestrates its own cognitive processes rather than merely producing fluent outputs.

**v0.1 goal:** A deterministic state machine implementing the `(O, E, B, R)` formal model, plus a Bayesian inference encoding as the first expressiveness proof. No LLM integration. Pure Python. Runnable and testable.

---

## 2. Audience

Both **academic/research** and **AI/ML practitioner** communities. The formal spec is rigorous and publishable. The code is a clean, installable Python package.

---

## 3. Core Architectural Insight

The system has two orthogonal views:

- **The 5-layer epistemic stack** — the *architecture* (what kinds of modules exist)
- **The `(O, E, B, R)` state tuple** — the *epistemic state* (what changes as reasoning progresses)

The stack is **vertical** (layers). The tuple is **horizontal** (state components). They intersect — each layer reads, writes, and transforms different components of the tuple.

### Layer × State Interaction Matrix

| Layer | O (Ontology) | E (Evidence) | B (Beliefs) | R (Revision) |
|-------|:---:|:---:|:---:|:---:|
| **Tool/Environment** | provides schemas | **produces** | — | — |
| **Cognitive Process** | **transforms** E→O | consumed | **transforms** O→B | — |
| **Pipeline** | sequences transforms | sequences gathering | sequences updates | — |
| **Norms** | evaluates adequacy | evaluates reliability | evaluates justification | evaluates appropriateness |
| **Meta-Epistemic** | triggers re-frame | requests more | forces revision | **modifies** |

---

## 4. The `(O, E, B, R)` State Model

The foundation. Four data structures representing complete epistemic state at any point in reasoning.

### O — Ontology

A typed container holding the problem's representational framework.

- **Symbols:** names, predicates, hypotheses
- **Types:** disease, symptom, variable, etc.
- **Constraints:** e.g., mutually exclusive hypotheses

O is static within a pipeline run unless the meta-layer triggers a re-frame.

**Invariant:** O must contain all symbols referenced in E or B later in the pipeline.

### E — Evidence

An ordered, append-only collection of observations.

Each observation is tagged with:
- Source
- Timestamp
- (v0.2+) Confidence/reliability metadata
- (v0.2+) Evidence type (observation, report, measurement)

E is append-only within a pipeline run.

### B — Beliefs

A mapping from propositions to confidence values.

Supports:
- Lookup
- Update
- Normalization (if probabilistic)
- (v0.2+) Consistency checks

### R — Revision Policy

A callable specification of how to update B given new E.

**Signature:** `R: (B, e, O) → B'` where `e` is a single observation (not the full evidence collection). R is applied per-observation during Stage 5; the pipeline manages the evidence accumulation.

Properties:
- **Pure** — no side effects
- **Deterministic** (for v0.1)
- **Typed** — R must be compatible with the B representation

Swapping R changes the reasoning framework. This is the heart of the architecture's generality.

### EpistemicState Tuple

```python
@dataclass(frozen=True)
class EpistemicState(Generic[O_t, E_t, B_t, R_t]):
    ontology: O_t
    evidence: E_t
    beliefs: B_t
    revision_policy: R_t
    metadata: MappingProxyType  # decomposition, strategy — immutable view, keeps core tuple clean
```

**Critical invariant:** The state is immutable per pipeline step. Each transition produces a new state. This gives full auditability, replayability, and deterministic traces.

---

## 5. Pipeline Stages & Transitions

Six stages, each a pure function `EpistemicState → EpistemicState`. The full pipeline is composable:

```
integrate(test(select(model(decompose(frame(input))))))
```

### Stage 1 — Problem Framing

- **Input:** Raw query
- **Output:** Initial O (hypothesis space, entities, constraints)
- **Invariant:** O₁ must contain all symbols referenced downstream

### Stage 2 — Decomposition

- **Input:** Framed problem
- **Output:** State with decomposition metadata attached
- **May be a no-op** for simple problems
- **Metadata:**
  ```
  {subproblems: [...], dependencies: [...], strategies: [...]}
  ```
  Stored in `state.metadata["decomposition"]`

### Stage 3 — Model Building

- **Input:** Decomposed problem
- **Output:** State with initialized B and R
- **This is where framework encoding happens** — choosing R determines the reasoning paradigm
- **Invariant:** Model building must produce a valid (B, R) pair such that `R(B, E, O)` is well-typed

### Stage 4 — Strategy Selection

- **Input:** Model (O, B, R)
- **Output:** Execution plan
- **Metadata:**
  ```
  {evidence_order: [...], stopping_criteria: ..., anomaly_checks: ...}
  ```
  Stored in `state.metadata["strategy"]`

### Stage 5 — Experimentation / Stress-Testing

- **Input:** Strategy + candidate state
- **Output:** Sequence of updated states as evidence is processed
- **Formal transition:**
  ```
  for e in strategy.evidence_order:
      B' = R(B, e, O)
      E' = E + [e]
      state = EpistemicState(O, E', B', R)
  ```
- Checks for anomalies (posterior collapse, contradictory evidence, oscillation)

### Stage 6 — Integration / Synthesis

- **Input:** Final state + trace
- **Output:** Coherent answer with confidence and caveats
- Does not modify O, E, B, R — reads them
- **Output structure:**
  ```
  {posterior: B, explanation: ..., anomalies: ..., confidence: ...}
  ```

### Design Properties

- Each stage is a **pure function**
- Stages can be **no-ops** for simple problems
- Stages are defined as a **Protocol/ABC** so framework encodings can override specific stages
- The **state trace** (list of all intermediate states) is preserved for auditability

---

## 6. Epistemic Norms & Scoring

Four norms evaluate the quality of reasoning processes. For v0.1, norms are defined in the spec and minimally implemented.

### Reliability

Tendency of R to produce correct outputs.

- **v0.1:** Binary correctness against known ground truth
  ```
  reliability = 1.0 if argmax(B_final) == ground_truth else 0.0
  ```
- **v0.2+:** Calibration curves, log-likelihood, KL divergence, posterior entropy

### Power

Range and complexity of problems the pipeline can handle.

- **v0.1:** Not computed. Demonstrated by expressiveness proofs (Bayesian, STRIPS, state-space search, MDPs)
- **v0.2+:** Formal expressiveness metrics

### Efficiency

Resource cost to reach acceptable outputs.

- **v0.1:** `efficiency = len(trace)` or number of R applications until confidence threshold
- **v0.2+:** Time, memory, token cost

### Justification

Support from reliable processes and evidence.

- **v0.1:** Trace replay verification
  ```
  replay(E, B₀, R) == B_final
  ```
  If true → justified. If false → anomaly.
- Justification is a **structural guarantee** of this architecture, not a heuristic

### Implementation

```python
@dataclass
class NormScore:
    reliability: float
    efficiency: int
    justification: bool
    power: Optional[str]  # documented, not computed

def score_pipeline_run(trace: list[EpistemicState], ground_truth: Any) -> NormScore: ...
```

### v0.2+ Roadmap (Spec Only)

- Norm-based triggers for the meta-epistemic loop
- Cross-run norm aggregation
- Norm weighting and trade-off analysis

---

## 7. Meta-Epistemic Layer

Monitors and adapts the entire system. For v0.1, defined in the spec but stubbed in code.

### Full Vision

- Monitor norm scores across pipeline runs
- Trigger re-framing when reliability drops
- Switch strategies when efficiency is poor
- Escalate when the pipeline can't converge
- Adjust R when the revision policy is inadequate
- Detect ontology inadequacy (missing hypotheses, missing variables)

### v0.1 Implementation

```python
class MetaDecision:
    decision: Enum  # ACCEPT | REFRAME | SWITCH_STRATEGY | ESCALATE
    details: dict   # payload for v0.2+

class MetaEpistemicController:
    def monitor(
        self,
        trace: list[EpistemicState],
        scores: NormScore,
        ontology: O,
        strategy: Optional[StrategyMetadata],
        decomposition: Optional[DecompositionMetadata]
    ) -> MetaDecision: ...
```

For v0.1, `monitor()` always returns `ACCEPT`. But the harness calls it, so the integration point exists and is tested.

### v0.2 Roadmap

- Reliability < 0.5 after all evidence → REFRAME
- Efficiency > 2× expected → SWITCH_STRATEGY
- Posterior oscillation detected → ESCALATE

---

## 8. Bayesian Inference Encoding (First Expressiveness Proof)

Encodes Bayesian inference as a special case of `(O, E, B, R)`.

### State Specialization

| Component | Bayesian Specialization |
|-----------|------------------------|
| O | `BayesOntology`: hypotheses (`list[str]`), observables (`list[str]`), likelihoods (`{(hypothesis, observable, value): float}`) |
| E | `BayesEvidence`: `list[Observation]` where `Observation = (variable: str, value: Any, source: str, timestamp: datetime)` |
| B | `BayesBelief`: `dict[str, float]` — invariant: `sum(values) == 1.0` |
| R | `BayesRevision`: `P'(h) = P(e|h) * P(h) / Σ_h' P(e|h') * P(h')` |

### Toy Problem — Medical Diagnosis

- **Hypotheses:** flu, cold, covid
- **Observables:** fever, cough, fatigue, loss_of_smell
- **Priors:** `{flu: 0.4, cold: 0.4, covid: 0.2}`
- **Likelihoods:** Matrix of `P(symptom | disease)` values
- **Evidence sequence:** `[fever=true, cough=true, loss_of_smell=true]`
- **Ground truth:** covid
- **Expected behavior:** Posterior shifts toward covid as loss_of_smell is observed

### Pipeline Stage Behavior

1. **Frame:** Parse diagnostic query → produce `BayesOntology`
2. **Decompose:** No-op (single problem)
3. **Model:** Set B to priors, R to Bayes' rule
4. **Strategy:** Process observations in order, stop when max posterior > 0.95 or evidence exhausted
5. **Experiment:** Apply R for each observation, record state after each update
6. **Integrate:** Report posterior distribution, MAP estimate, confidence, and trace

### What This Proves

- The `(O, E, B, R)` tuple can represent probabilistic reasoning
- The pipeline stages compose correctly for belief revision
- The state trace provides full auditability
- The norms can evaluate the run (reliability, efficiency, justification)

---

## 9. Framework Encoding Roadmap (v0.2+)

Priority order for future expressiveness proofs:

1. **Classical AI Planning (STRIPS/PDDL):** O = domain predicates, E = initial state, B = plan, R = search strategy
2. **Newell & Simon State-Space Search:** O = problem space, E = current state, B = path, R = operator selection
3. **Decision Theory / MDPs:** O = state space + transitions, E = observations/rewards, B = value function, R = Bellman updates

---

## 10. Project Structure

```
epistemic-pipeline/
├── docs/
│   └── spec/
│       ├── 00_mission.md
│       ├── 01_epistemic_stack.md
│       ├── 02_OEBR_formal_model.md
│       ├── 03_norms_spec.md
│       ├── 04_pipeline_spec.md
│       ├── 05_meta_loop_spec.md
│       ├── 06_encodings/
│       │   └── bayes.md
│       └── figures/
├── src/
│   └── epistemic_pipeline/
│       ├── __init__.py
│       ├── state.py
│       ├── pipeline.py
│       ├── norms.py
│       ├── meta.py
│       └── encodings/
│           ├── __init__.py
│           └── bayes.py
├── tests/
│   ├── test_state.py
│   ├── test_pipeline.py
│   ├── test_norms.py
│   ├── test_meta.py
│   ├── test_bayes.py
│   └── test_trace_replay.py
├── examples/
│   └── medical_diagnosis.py
├── pyproject.toml
├── README.md
├── LICENSE
└── .gitignore
```

### Tooling

- Python 3.12+
- `pyproject.toml` + setuptools
- `pytest` for testing
- `mypy` for type checking
- No external dependencies for v0.1
- (Optional) `ruff` for linting, `pre-commit` for hooks

### Separation of Concerns

- `docs/spec/` — standalone, publishable formal specification
- `src/epistemic_pipeline/` — standalone, installable Python package
- The spec defines the interfaces the code must implement
- Neither imports the other; both can evolve independently

---

## 11. Interleaved Build Order

Spec section → code → tests, for each component:

1. `02_OEBR_formal_model.md` → `state.py` → `test_state.py`
2. `04_pipeline_spec.md` → `pipeline.py` → `test_pipeline.py`
3. `03_norms_spec.md` → `norms.py` → `test_norms.py`
4. `05_meta_loop_spec.md` → `meta.py` → `test_meta.py`
5. `06_encodings/bayes.md` → `encodings/bayes.py` → `test_bayes.py`
6. `medical_diagnosis.py` — end-to-end demonstration
7. `00_mission.md` + `01_epistemic_stack.md` — framing docs written last

---

## 12. Success Criteria for v0.1

v0.1 is complete when:

1. O, E, B, R are defined as generic, frozen dataclasses
2. The 6 pipeline stages run deterministically as pure functions
3. Bayesian inference is encoded as a special case
4. The medical diagnosis toy problem runs end-to-end
5. The posterior converges to the correct hypothesis (covid)
6. The state trace is preserved and replayable
7. Norm scoring works: reliability (binary), efficiency (step count), justification (replay)
8. The meta-epistemic controller stub is called and returns ACCEPT
9. All tests pass
10. `mypy` passes with no errors
