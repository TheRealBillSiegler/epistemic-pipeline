# Epistemic Pipeline v0.2 — Dense Structural Compression (MCS‑B‑v0.2)

**Purpose:** Compact hierarchical representation for reconstruction and implementation
**Delta from v0.1:** Meta‑layer functional; norms expanded;
STRIPS encoding; strategy switching; evidence confidence;
ontology adequacy; anomaly detection.

---

## 1. Mission

- Extend v0.1 deterministic epistemic pipeline
- Add functional meta‑epistemic control
- Add second expressiveness proof (STRIPS)
- Add richer norms and anomaly detection
- Maintain pure Python, deterministic behavior

---

## 2. Architecture Overview

- Same 5 layers: Tool, Cognitive, Pipeline, Norms, Meta
- Same state tuple: O, E, B, R
- v0.2 adds:
  - confidence‑weighted evidence
  - ontology adequacy checks
  - strategy switching
  - meta‑layer decision logic
  - extended norms
  - STRIPS encoding

---

## 3. State Model Extensions

### 3.1 Ontology (O)

- v0.2 adds:
  - adequacy check: `adequate(O, E)`
  - used by meta‑layer and norms

### 3.2 Evidence (E)

- v0.2 adds fields:
  - `confidence: float ∈ [0,1]`
  - `etype: enum {observation, report, measurement}`

### 3.3 Beliefs (B)

- v0.2 adds:
  - optional consistency check: `consistent(B, O)`

### 3.4 Revision Policy (R)

- v0.2 allows confidence‑weighted updates
- Signature becomes:
  - `(B, e, O, e.confidence) → B'`

### 3.5 EpistemicState

- Same structure as v0.1
- Metadata may now include heuristic info

---

## 4. Pipeline Extensions

### 4.1 Stage 4 — Strategy Selection

- Metadata extended:

  ```text
  {
    evidence_order,
    stopping_criteria,
    anomaly_checks,
    heuristics
  }
  ```

### 4.2 Stage 5 — Test

- v0.2 adds anomaly detection:
  - posterior oscillation
  - contradictory evidence
  - confidence‑weighted updates
- Update rule:
  - `B' = R(B, e, O, e.confidence)`

---

## 5. Norms (v0.2)

### 5.1 Reliability

- v0.1 binary correctness
- v0.2 adds calibration:
  - log‑likelihood or cross‑entropy style scoring

### 5.2 Efficiency

- v0.1: trace length
- v0.2 adds:
  - heuristic cost
  - number of strategy switches

### 5.3 Justification

- v0.1: replay final state
- v0.2 adds:
  - intermediate consistency checks
  - monotonicity checks (where applicable)

### 5.4 Power

- v0.2 partially computed:
  - `power = adequacy(O, E)`

### 5.5 Scoring Function

- Same signature:
  - `score_pipeline_run(trace, ground_truth) → NormScore`
- Extended internal logic

---

## 6. Meta‑Epistemic Layer (Functional)

### 6.1 MetaDecision

- Enum unchanged:
  - `ACCEPT`, `REFRAME`, `SWITCH_STRATEGY`, `ESCALATE`
- Payload: `details: dict`

### 6.2 Controller Logic

- **REFRAME** when:
  - reliability < threshold
  - ontology inadequate
  - persistent contradictions

- **SWITCH_STRATEGY** when:
  - efficiency > 2× expected
  - heuristic failure
  - oscillation without contradiction

- **ESCALATE** when:
  - repeated contradictions
  - unresolvable oscillation
  - inconsistent beliefs

- **ACCEPT** otherwise

### 6.3 Controller Interface

`monitor(trace, scores, ontology, strategy, decomposition) → MetaDecision`

---

## 7. STRIPS Encoding (Expressiveness Proof 2)

### 7.1 Specializations

#### Ontology

```yaml
STRIPSOntology:
    predicates: list
    actions: list
    preconditions: mapping
    effects: mapping
```

#### Evidence

```yaml
STRIPSEvidence:
    initial_state: set[predicates]
    observations: list[Observation]
```

#### Beliefs

```yaml
STRIPSBelief:
    plan: list[actions]
```

#### Revision Policy

- Search operator:
  - `R(B, e, O) = apply_search_step(B, O, heuristics)`

### 7.2 Pipeline Behavior

- Frame → parse domain + problem
- Decompose → identify subgoals
- Model → initialize plan + search operator
- Select → choose heuristic strategy
- Test → search iterations
- Integrate → final plan + trace

### 7.3 Guarantees

- Symbolic planning expressible
- Multi‑paradigm reasoning supported
- Meta‑layer can switch heuristics or re‑frame

---

## 8. Project Structure (v0.2 Additions)

```text
docs/spec/
    07_encodings/strips.md
src/epistemic_pipeline/
    encodings/strips.py
tests/
    test_strips.py
    test_meta_decisions.py
```

---

## 9. v0.2 Completion Criteria

1. Evidence confidence implemented
2. Strategy switching implemented
3. Meta‑layer decisions functional
4. STRIPS encoding implemented
5. Extended norms implemented
6. Contradiction + oscillation detection
7. Ontology adequacy checks
8. All tests pass
9. Type checking passes
