# Epistemic Pipeline v0.2 — Minimal Canonical Specification (MCS‑A‑v0.2)

**Form:** Ultra‑formal, compressed, lossless
**Purpose:** Canonical reference for reconstruction of v0.2 architecture
**Delta from v0.1:** Meta‑layer becomes functional; norms expanded;
second expressiveness proof (STRIPS); strategy switching;
evidence confidence; ontology adequacy checks.

---

## 1. State Model Extensions

### 1.1 Evidence (E) Extensions

Observation gains:

- `confidence: float ∈ [0,1]`
- `etype: enum {observation, report, measurement}`

### 1.2 Beliefs (B) Extensions

Add optional consistency checks:
\[
\text{consistent}(B, O) = \text{True/False}
\]

### 1.3 Ontology (O) Extensions

Add adequacy checks:
\[
\text{adequate}(O, E) = \text{True/False}
\]

---

## 2. Pipeline Extensions

### 2.1 Strategy Selection (Stage 4)

Strategy metadata extended:

```text
{evidence_order, stopping_criteria, anomaly_checks, heuristics}
```

### 2.2 Test Stage (Stage 5)

Add anomaly detection rules:

- posterior oscillation
- contradiction detection
- confidence‑weighted updates

Formal update:
\[
B' = R(B, e, O, \text{confidence}(e))
\]

---

## 3. Norms (v0.2)

### 3.1 Reliability

Extended metric:
\[
\text{reliability} = \text{binary correctness} + \text{calibration score}
\]

Calibration score:
\[
\sum_h B(h) \cdot \log P(h|\text{truth})
\]

### 3.2 Efficiency

Extended metric includes:

- number of updates
- heuristic cost
- strategy switches

### 3.3 Justification

Extended:

- check consistency of intermediate states
- check monotonicity where applicable

### 3.4 Power

Partial computation:
\[
\text{power} = \text{adequacy}(O, E)
\]

---

## 4. Meta‑Epistemic Layer (Functional in v0.2)

### 4.1 Decision Rules

#### REFRAME

Triggered when:

- reliability < threshold
- ontology inadequate
- persistent contradictions

#### SWITCH_STRATEGY

Triggered when:

- efficiency > 2× expected
- heuristic failure
- oscillation without contradiction

#### ESCALATE

Triggered when:

- repeated contradictions
- unresolvable oscillation
- inconsistent beliefs

#### ACCEPT

Default when no triggers fire.

### 4.2 Controller Signature

```text
monitor(trace, scores, ontology, strategy, decomposition) -> MetaDecision
```

---

## 5. STRIPS Encoding (Expressiveness Proof 2)

### 5.1 Specializations

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

Search operator:
\[
R(B, e, O) = \text{apply search step using heuristics}
\]

### 5.2 Pipeline Behavior

- Frame → parse domain + problem
- Decompose → identify subgoals
- Model → initialize plan + search operator
- Select → choose heuristic strategy
- Test → search iterations
- Integrate → final plan + trace

---

## 6. v0.2 Completion Criteria

1. Evidence confidence implemented
2. Strategy switching implemented
3. Meta‑layer decisions functional
4. STRIPS encoding implemented
5. Norms extended (reliability, efficiency, justification, power)
6. Contradiction + oscillation detection
7. Ontology adequacy checks
8. All tests pass
9. Type checking passes
