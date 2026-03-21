# Epistemic Pipeline — Dense Structural Compression (MCS‑B)

**Version:** v0.1  
**Purpose:** Compact hierarchical representation for reconstruction and implementation

---

## 1. Mission

- Universal reasoning architecture  
- Deterministic state machine  
- Implements `(O, E, B, R)`  
- First expressiveness proof: Bayesian inference  
- Pure Python, no LLMs  

---

## 2. Architecture Overview

- 5 layers: Tool, Cognitive, Pipeline, Norms, Meta  
- Horizontal state tuple: O, E, B, R  
- Layers transform or evaluate components of the tuple  

---

## 3. State Model

### 3.1 Ontology (O)

- Symbols  
- Types  
- Constraints  
- Static unless re‑frame  
- Must contain all referenced symbols  

### 3.2 Evidence (E)

- Ordered, append‑only list  
- Observation fields: variable, value, source, timestamp  
- (v0.2+) confidence, evidence type  

### 3.3 Beliefs (B)

- Mapping: proposition → confidence  
- Supports lookup, update, normalization  

### 3.4 Revision Policy (R)

- Pure function: `(B, e, O) → B'`  
- Deterministic  
- Must accept B’s type  

### 3.5 EpistemicState

- `ontology: O`  
- `evidence: E`  
- `beliefs: B`  
- `revision_policy: R`  
- `metadata: immutable mapping`  
- Immutable per transition  

---

## 4. Pipeline

### 4.1 Stages (pure functions)

1. **Frame**  
2. **Decompose**  
3. **Model**  
4. **Select**  
5. **Test**  
6. **Integrate**

### 4.2 Composition

`Integrate(Test(Select(Model(Decompose(Frame(input))))))`

### 4.3 Stage Definitions

#### Frame

- Input: raw query  
- Output: initial O  
- Invariant: O contains all downstream symbols  

#### Decompose

- Adds metadata: `{subproblems, dependencies, strategies}`  
- May be no‑op  

#### Model

- Initializes B and R  
- Invariant: R(B, e, O) well‑typed  

#### Select

- Adds strategy metadata:
  `{evidence_order, stopping_criteria, anomaly_checks}`

#### Test

- For each e in evidence_order:  
  - `B' = R(B, e, O)`  
  - `E' = E + [e]`  
  - New state = `(O, E', B', R)`  
- Detect anomalies  

#### Integrate

- Reads final state + trace  
- Output: `{posterior, explanation, anomalies, confidence}`  

---

## 5. Norms

### 5.1 NormScore

- `reliability: float`  
- `efficiency: int`  
- `justification: bool`  
- `power: optional string`  

### 5.2 Definitions

- **Reliability (v0.1):** `1.0 if argmax(B_final) == ground_truth else 0.0`  
- **Efficiency (v0.1):** `len(trace)`  
- **Justification (v0.1):** `replay(E, B0, R) == B_final`  
- **Power (v0.1):** documented only  

### 5.3 Scoring Function

`score_pipeline_run(trace, ground_truth) → NormScore`

---

## 6. Meta‑Epistemic Layer

### 6.1 MetaDecision

Enum: `ACCEPT`, `REFRAME`, `SWITCH_STRATEGY`, `ESCALATE`  
Payload: `details: dict`

### 6.2 Controller Interface

`monitor(trace, scores, ontology, strategy, decomposition) → MetaDecision`

### 6.3 v0.1 Behavior

Always returns `ACCEPT`

---

## 7. Bayesian Encoding (Expressiveness Proof 1)

### 7.1 Specializations

- **O → BayesOntology:**  
  - `hypotheses: list[str]`  
  - `observables: list[str]`  
  - `likelihoods: {(h, o, v): float}`  

- **E → BayesEvidence:**  
  - list of Observations  

- **B → BayesBelief:**  
  - `{hypothesis: float}`  
  - sum(values) = 1.0  

- **R → BayesRevision:**  
  - Bayes’ rule  

### 7.2 Pipeline Behavior

- Frame → build ontology  
- Decompose → no‑op  
- Model → priors + BayesRevision  
- Select → evidence order + stopping rule  
- Test → apply BayesRevision per observation  
- Integrate → posterior, MAP, confidence, trace  

### 7.3 Guarantees

- Probabilistic reasoning expressible  
- Pipeline composition valid  
- Trace auditability  
- Norms computable  

---

## 8. Project Structure

```text
docs/spec/
src/epistemic_pipeline/
    state.py
    pipeline.py
    norms.py
    meta.py
    encodings/bayes.py
tests/
examples/
pyproject.toml
```

---

## 9. v0.1 Completion Criteria

1. Generic frozen dataclasses for O/E/B/R  
2. Six pure pipeline stages  
3. Bayesian encoding implemented  
4. End‑to‑end example runs  
5. Posterior converges to ground truth  
6. Trace preserved + replayable  
7. Norm scoring functional  
8. Meta‑layer stub invoked  
9. All tests pass  
10. Type checking passes  
