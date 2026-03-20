# Epistemic Pipeline v0.1 — Design Specification

**Date:** 2026-03-19
**Status:** Approved
**Scope:** Formal specification + reference implementation of a universal reasoning architecture

---

## At a Glance

This system reasons by tracking four things: what concepts exist (O), what has been observed (E), what it currently believes (B), and how it updates those beliefs (R). These four components flow through a 6-stage pipeline. Each stage is a pure function that takes the current state and returns a new one.

v0.1 proves this works by encoding Bayesian inference — probability math for updating beliefs from evidence — as a special case. The test: a toy medical diagnosis where the system correctly identifies covid from symptoms.

No LLM. No external dependencies. Pure Python.

**The core insight:** The system has two views that work together:

- A 5-layer **stack** describes *what kinds of modules exist* (tools, cognitive processes, pipeline stages, evaluation norms, and a meta-layer that watches everything)
- A 4-component **state tuple** `(O, E, B, R)` describes *what changes as reasoning progresses*

The stack is the architecture. The tuple is the data flowing through it. Each layer reads and writes different parts of the tuple:

| Layer | O (Ontology) | E (Evidence) | B (Beliefs) | R (Revision) |
|-------|---|---|---|---|
| **Tool/Environment** | provides schemas | **produces** | — | — |
| **Cognitive Process** | **transforms** E→O | consumed | **transforms** O→B | — |
| **Pipeline** | sequences | sequences | sequences | — |
| **Norms** | evaluates | evaluates | evaluates | evaluates |
| **Meta-Epistemic** | re-frames | requests more | forces revision | **modifies** |

**Audience:** Academic researchers (the spec is rigorous enough to publish) and AI/ML practitioners (the code is a clean, installable Python package). The spec defines the interfaces. The code implements them. Neither imports the other.

**Done when:** The medical diagnosis toy problem runs end-to-end, the posterior converges to the correct hypothesis, the state trace is replayable, all norms score correctly, and all tests and mypy pass.

---

## Part I — Formal Model

### The `(O, E, B, R)` State Tuple

The system's complete state at any moment is four data structures bundled together. This bundle is **frozen** — you never modify it in place. Each pipeline stage takes one state and returns a new one. This means you get a full history of every reasoning step for free.

#### O — Ontology

The vocabulary of the problem. What things exist, what types they have, and what constraints apply.

For example, in a medical diagnosis: the diseases are flu, cold, and covid. The symptoms are fever, cough, and loss of smell. A patient can only have one disease at a time.

- O stays fixed during a pipeline run. Only the meta-layer (the system's self-monitor) can change it.
- **Invariant:** Every symbol used in E or B must already be defined in O.

#### E — Evidence

What has been observed. An ordered list of observations, each tagged with where it came from and when.

- You can only add to E, never remove. Evidence accumulates.

#### B — Beliefs

What the system currently thinks is true. A mapping from propositions to confidence values.

For example: `{flu: 0.3, cold: 0.1, covid: 0.6}` means "60% confident it's covid."

Supports lookup, update, and normalization (making sure the values sum to 1.0 when they represent probabilities).

#### R — Revision Policy

The rule for how to update beliefs when new evidence arrives. A pure function: give it the current beliefs (B), one new observation (e), and the vocabulary (O), and it returns updated beliefs (B').

Written formally: `R: (B, e, O) → B'`

R is what makes the architecture general. **Swap R and you get a completely different reasoning system.** Bayes' rule gives you probabilistic reasoning. A search algorithm gives you planning. A Bellman update gives you decision-making. The rest of the architecture stays the same.

Properties that R must have:

- **Pure** — no side effects, same inputs always produce same outputs
- **Deterministic** (for v0.1)
- **Type-compatible** — R must know how to work with the specific kind of B it receives

#### In Python

```python
@dataclass(frozen=True)
class EpistemicState(Generic[O_t, E_t, B_t, R_t]):
    ontology: O_t
    evidence: E_t
    beliefs: B_t
    revision_policy: R_t
    metadata: MappingProxyType  # extra info (decomposition, strategy) — also immutable
```

---

### Pipeline Stages

Six stages process the state in sequence. Each is a pure function: state in, state out.

```
integrate(test(select(model(decompose(frame(input))))))
```

| Stage | What it does | Key rule |
|-------|-------------|----------|
| **1. Frame** | Turns a raw question into a structured vocabulary (O) | O must define every symbol used later |
| **2. Decompose** | Splits complex problems into sub-problems | Can be a no-op for simple problems |
| **3. Model** | Sets up initial beliefs (B) and chooses a revision rule (R) | B and R must be compatible — `R(B, e, O)` must be valid |
| **4. Strategy** | Decides what evidence to look at, in what order, and when to stop | Stored in `state.metadata["strategy"]` |
| **5. Experiment** | Applies R once per observation, building up the evidence trail | `for each e: B' = R(B, e, O); E' = E + [e]` |
| **6. Integrate** | Reads the final state and produces an answer with confidence levels | Does not change O, E, B, or R — only reads them |

**Design properties:**

- Every stage is a pure function (no side effects)
- Any stage can be a no-op if the problem doesn't need it
- Stages are defined as a Protocol/ABC, so each framework encoding can override them
- The full list of intermediate states (the "trace") is kept for auditing and replay

---

### Epistemic Norms

Four standards for judging whether the reasoning was good. Think of them as a report card for the pipeline run.

| Norm | Question it answers | How v0.1 measures it |
|------|-------------------|---------------------|
| **Reliability** | Did R get the right answer? | Binary: `1.0` if the top belief matches ground truth, `0.0` otherwise |
| **Power** | How many kinds of problems can this handle? | Not computed — demonstrated by encoding multiple frameworks |
| **Efficiency** | How much work did it take? | Count of pipeline steps or R applications |
| **Justification** | Can we prove the final beliefs came from the evidence? | Replay: re-run all evidence through R from the starting beliefs. If you get the same result, it's justified. |

Justification is special. Because R is pure and the full trace is saved, justification isn't a judgment call — it's a **mathematical check**. You can always reconstruct exactly how the system reached its conclusions.

```python
@dataclass
class NormScore:
    reliability: float
    efficiency: int
    justification: bool
    power: Optional[str]  # described in words, not computed

def score_pipeline_run(trace: list[EpistemicState], ground_truth: Any) -> NormScore: ...
```

---

### Meta-Epistemic Layer

The system's self-monitor. It watches the pipeline run, looks at the norm scores, and decides what to do next.

**v0.1: this is a stub.** The interface exists and gets called, but it always says "looks good, accept the result." The point is to prove the architecture has all five layers wired up, even before the meta-layer has real logic.

```python
class MetaDecision:
    decision: Enum  # ACCEPT | REFRAME | SWITCH_STRATEGY | ESCALATE
    details: dict   # extra info for v0.2+

class MetaEpistemicController:
    def monitor(self, trace, scores, ontology, strategy, decomposition) -> MetaDecision: ...
```

**What it will eventually do** (spec only, not built yet): re-frame the problem when reliability is low, switch strategies when efficiency is poor, escalate when evidence contradicts itself, flag when the vocabulary is missing important concepts.

---

## Part II — First Expressiveness Proof: Bayesian Inference

### Bayesian Encoding

To prove the architecture actually works, we encode Bayesian inference — the standard math for updating beliefs from evidence — as a special case of `(O, E, B, R)`.

"Expressiveness proof" means: we show that a well-known reasoning framework fits naturally into our architecture as just one configuration of the same machinery.

#### State Specialization

| Component | What it becomes for Bayesian inference |
|-----------|---------------------------------------|
| O | `BayesOntology`: a list of hypotheses, a list of observable symptoms, and a table of how likely each symptom is given each hypothesis |
| E | `BayesEvidence`: a list of observations like "fever = true" |
| B | `BayesBelief`: a probability distribution — e.g., `{flu: 0.4, cold: 0.4, covid: 0.2}` — must sum to 1.0 |
| R | `BayesRevision`: Bayes' rule — the standard formula for updating probabilities from evidence |

#### Toy Problem — Medical Diagnosis

- **Hypotheses:** flu, cold, covid
- **Starting beliefs (priors):** `{flu: 0.4, cold: 0.4, covid: 0.2}`
- **Evidence observed:** `[fever=true, cough=true, loss_of_smell=true]`
- **Correct answer:** covid
- **What should happen:** As each symptom is observed, beliefs update. Loss of smell is rare for flu and cold but common for covid, so the posterior should shift strongly toward covid.

#### How the Pipeline Stages Map

1. **Frame:** Turn the diagnostic question into a `BayesOntology`
2. **Decompose:** No-op (this is a single, simple problem)
3. **Model:** Set B to the prior probabilities, set R to Bayes' rule
4. **Strategy:** Process symptoms in order, stop when confidence exceeds 0.95 or all evidence is used
5. **Experiment:** Apply Bayes' rule for each symptom, saving the state after each update
6. **Integrate:** Report the final probability distribution, the most likely diagnosis, confidence, and the full trace

#### What This Proves

- `(O, E, B, R)` can represent probabilistic reasoning
- The pipeline stages compose correctly for belief revision
- The state trace gives full auditability
- All four norms (reliability, power, efficiency, justification) can be evaluated on this run

---

## Part III — Engineering

### Project Structure

```
epistemic-pipeline/
├── docs/spec/                          # Publishable formal specification
│   ├── 00_mission.md
│   ├── 01_epistemic_stack.md
│   ├── 02_OEBR_formal_model.md
│   ├── 03_norms_spec.md
│   ├── 04_pipeline_spec.md
│   ├── 05_meta_loop_spec.md
│   ├── 06_encodings/bayes.md
│   └── figures/
├── src/epistemic_pipeline/             # Installable Python package
│   ├── __init__.py
│   ├── state.py                        # EpistemicState, O/E/B/R base types
│   ├── pipeline.py                     # Stage protocol, runner, trace
│   ├── norms.py                        # NormScore, score_pipeline_run()
│   ├── meta.py                         # MetaEpistemicController, MetaDecision
│   └── encodings/bayes.py              # Bayesian specialization + stages
├── tests/                              # pytest suite
│   ├── test_state.py                   # Immutability, generics, invariants
│   ├── test_pipeline.py                # Purity, composition, trace
│   ├── test_norms.py                   # Reliability, efficiency, justification
│   ├── test_meta.py                    # Stub behavior, integration point
│   ├── test_bayes.py                   # End-to-end Bayesian encoding
│   └── test_trace_replay.py            # Replay reproduces final beliefs
├── examples/medical_diagnosis.py       # End-to-end toy problem
├── pyproject.toml
├── README.md
├── LICENSE
└── .gitignore
```

**Tooling:** Python 3.12+, setuptools, pytest, mypy. No external dependencies. Optional: ruff, pre-commit.

**Separation:** `docs/spec/` and `src/epistemic_pipeline/` are independently coherent. The spec defines interfaces. The code implements them. Neither imports the other.

### Build Order

Each component is built in three steps: write the spec, implement the code, write the tests. Then move to the next component.

| Step | Spec | Code | Tests |
|------|------|------|-------|
| 1 | `02_OEBR_formal_model.md` | `state.py` | `test_state.py` |
| 2 | `04_pipeline_spec.md` | `pipeline.py` | `test_pipeline.py` |
| 3 | `03_norms_spec.md` | `norms.py` | `test_norms.py` |
| 4 | `05_meta_loop_spec.md` | `meta.py` | `test_meta.py` |
| 5 | `06_encodings/bayes.md` | `encodings/bayes.py` | `test_bayes.py` |
| 6 | — | `medical_diagnosis.py` | — |
| 7 | `00_mission.md` + `01_epistemic_stack.md` | — | — |

### Success Criteria

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

---

## Appendix — v0.2+ Roadmap

Collected here to keep the v0.1 spec focused.

**Framework encodings:** Classical AI Planning (STRIPS/PDDL) → Newell & Simon State-Space Search → Decision Theory / MDPs

**Norms:** Calibration curves, KL divergence, posterior entropy for reliability. Time/memory/token cost for efficiency. Cross-run aggregation. Norm weighting and trade-offs.

**Meta-epistemic triggers:** Reliability < 0.5 → REFRAME. Efficiency > 2x expected → SWITCH_STRATEGY. Posterior oscillation → ESCALATE. Ontology inadequacy detection.

**Evidence:** Confidence/reliability metadata per observation. Evidence typing (observation, report, measurement).

**Beliefs:** Consistency checks.
