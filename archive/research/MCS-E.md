# MCS‑E — Single‑Message Claude Ingestion Bundle

**Unified Canonical Specification (v1.0‑Complete)**
**Purpose:** One‑shot ingestion of the entire epistemic pipeline architecture
**Form:** Fully merged, lossless, hierarchical, portable

---

## 0. Mission

Universal reasoning engine built on a deterministic epistemic state machine.
Implements multi‑paradigm reasoning (Bayes, STRIPS, Search, MDPs).
Integrates LLMs and tools as controlled cognitive processes.
Provides adaptive meta‑epistemic control.
Fully auditable, replayable, explainable.

---

## 1. State Model

### 1.1 Ontology (O)

- symbols
- types
- constraints
- causal structure (optional)
- transition model (MDPs)
- operator schema (planning/search)
- adequacy: `adequate(O, E, task) → bool`

### 1.2 Evidence (E)

Observation fields:

- variable
- value
- source
- timestamp
- confidence ∈ [0,1]
- etype ∈ {observation, report, measurement}
- modality ∈ {text, sensor, tool, LLM}

### 1.3 Beliefs (B)

Representations:

- probability distributions
- plans
- search frontiers
- value functions
- causal graphs
Consistency: `consistent(B, O)`

### 1.4 Revision Policy (R)

Generalized update:
`R(B, e, O, context) → B'`
Context includes:

- strategy
- heuristics
- tool outputs
- LLM proposals

### 1.5 EpistemicState

- ontology
- evidence
- beliefs
- revision_policy
- metadata:
  - decomposition
  - strategy
  - heuristics
  - tool calls
  - LLM proposals
  - meta‑decisions
- immutable per transition

---

## 2. Pipeline

### 2.1 Stages

1. Frame
2. Decompose
3. Model
4. Select
5. Test
6. Integrate

Each stage: `EpistemicState → EpistemicState`.

### 2.2 Stage Semantics

#### Frame

- construct initial ontology
- LLM‑assisted ontology proposal allowed
- tool‑assisted schema extraction allowed

#### Decompose

- hierarchical subgoal generation
- LLM‑assisted decomposition allowed

#### Model

- choose paradigm: Bayesian, STRIPS, Search, MDP, Hybrid
- initialize B and R accordingly

#### Select

- dynamic strategy selection
- heuristics
- ensembles
- meta‑layer override allowed

#### Test

- multi‑paradigm update loop
- confidence‑weighted updates
- anomaly detection:
  - oscillation
  - contradiction
  - causal inconsistency
  - value divergence
- tool calls allowed
- LLM proposals allowed

#### Integrate

- posterior / plan / value function
- causal justification
- uncertainty quantification
- multi‑modal explanation

---

## 3. Norms

### 3.1 Reliability

- correctness
- calibration
- predictive accuracy
- cross‑paradigm agreement

### 3.2 Efficiency

- step count
- heuristic cost
- strategy switching cost
- tool cost
- LLM cost
- search cost

### 3.3 Justification

- replayability
- intermediate consistency
- causal support
- tool‑evidence alignment
- LLM‑proposal justification

### 3.4 Power

- ontology adequacy
- paradigm adequacy
- representational sufficiency

### 3.5 NormScore

```yaml
NormScore:
    reliability: float
    efficiency: int
    justification: bool
    power: string | None
```

---

## 4. Meta‑Epistemic Layer

### 4.1 MetaDecision

Enum:

- ACCEPT
- REFRAME
- SWITCH_STRATEGY
- ESCALATE

Payload: `details: dict`.

### 4.2 Decision Logic

Triggers include:

- reliability failure
- ontology inadequacy
- paradigm mismatch
- tool disagreement
- LLM disagreement
- causal inconsistency
- value‑function divergence
- persistent oscillation
- repeated contradictions

### 4.3 Capabilities

- modify ontology
- modify strategy
- switch paradigms
- request tool evidence
- request LLM proposals
- escalate anomalies

### 4.4 Interface

`monitor(trace, scores, ontology, strategy, decomposition) → MetaDecision`

---

## 5. Expressiveness Suite

### 5.1 Bayesian Inference

- O: hypotheses, observables, likelihoods
- E: observations
- B: probability distribution
- R: Bayes' rule

### 5.2 STRIPS Planning

- O: predicates, actions, preconditions, effects
- E: initial state
- B: plan
- R: search operator

### 5.3 State‑Space Search

- O: problem space
- E: current state
- B: frontier
- R: operator selection

### 5.4 MDPs

- O: states, actions, transitions
- E: observations, rewards
- B: value function
- R: Bellman update

---

## 6. Tool Integration

### 6.1 Allowed Stages

- Frame
- Test
- Integrate

### 6.2 Semantics

- tool outputs treated as evidence with modality
- must be typed and timestamped
- must pass consistency checks

---

## 7. LLM Integration

### 7.1 LLM Roles

- ontology proposal
- decomposition
- strategy proposal
- hypothesis generation
- explanation generation
- plan refinement

### 7.2 Semantics

- LLM outputs treated as evidence with modality
- must be evaluated by norms
- meta‑layer may override or reject

---

## 8. Project Structure

```text
docs/spec/
    encodings/
        bayes.md
        strips.md
        search.md
        mdp.md
    llm_integration.md
    tool_integration.md

src/epistemic_pipeline/
    state.py
    pipeline.py
    norms.py
    meta.py
    encodings/
        bayes.py
        strips.py
        search.py
        mdp.py
    tools/
        tool_interfaces.py
    llm/
        llm_interfaces.py

tests/
    test_bayes.py
    test_strips.py
    test_search.py
    test_mdp.py
    test_meta.py
    test_llm_integration.py
    test_tool_integration.py
```

---

## 9. Completion Criteria (v1.0)

1. All four reasoning paradigms implemented
2. Meta‑layer fully adaptive
3. LLM integration functional
4. Tool integration functional
5. Extended norms implemented
6. Real‑world examples implemented
7. All tests pass
8. Type checking passes
9. Full documentation + whitepaper
