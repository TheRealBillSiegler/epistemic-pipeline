# MCS‑F — Code Skeleton Generator (v1.0‑Complete)

**Purpose:** Provide a complete repository scaffold with all modules,
classes, and function signatures
**Form:** Portable, implementation‑free, deterministic

---

## 0. Repository Layout

```text
epistemic-pipeline/
│
├── docs/
│   └── spec/
│       ├── encodings/
│       │   ├── bayes.md
│       │   ├── strips.md
│       │   ├── search.md
│       │   └── mdp.md
│       ├── llm_integration.md
│       └── tool_integration.md
│
├── src/
│   └── epistemic_pipeline/
│       ├── state.py
│       ├── pipeline.py
│       ├── norms.py
│       ├── meta.py
│       ├── encodings/
│       │   ├── bayes.py
│       │   ├── strips.py
│       │   ├── search.py
│       │   └── mdp.py
│       ├── tools/
│       │   └── tool_interfaces.py
│       └── llm/
│           └── llm_interfaces.py
│
└── tests/
    ├── test_bayes.py
    ├── test_strips.py
    ├── test_search.py
    ├── test_mdp.py
    ├── test_meta.py
    ├── test_llm_integration.py
    └── test_tool_integration.py
```

---

## 1. `state.py` — Epistemic State Model Skeleton

```python
class Ontology:
    # symbols, types, constraints, causal structure, transitions, operators
    pass

class Evidence:
    # variable, value, source, timestamp, confidence, etype, modality
    pass

class Beliefs:
    # distributions, plans, frontiers, value functions, causal graphs
    pass

class RevisionPolicy:
    def update(self, beliefs, evidence, ontology, context):
        pass

class EpistemicState:
    def __init__(self, ontology, evidence, beliefs, revision_policy, metadata):
        pass
```

---

## 2. `pipeline.py` — Six‑Stage Pipeline Skeleton

```python
class Pipeline:
    def frame(self, state, query):
        pass

    def decompose(self, state):
        pass

    def model(self, state):
        pass

    def select(self, state):
        pass

    def test(self, state):
        pass

    def integrate(self, state):
        pass

    def run(self, query):
        # frame → decompose → model → select → test → integrate
        pass
```

---

## 3. `norms.py` — Norms Skeleton

```python
class NormScore:
    def __init__(self, reliability, efficiency, justification, power):
        pass

class Norms:
    def reliability(self, trace, ground_truth):
        pass

    def efficiency(self, trace):
        pass

    def justification(self, trace):
        pass

    def power(self, ontology, evidence):
        pass

    def score_pipeline_run(self, trace, ground_truth):
        pass
```

---

## 4. `meta.py` — Meta‑Epistemic Layer Skeleton

```python
class MetaDecision:
    ACCEPT = "ACCEPT"
    REFRAME = "REFRAME"
    SWITCH_STRATEGY = "SWITCH_STRATEGY"
    ESCALATE = "ESCALATE"

class MetaController:
    def monitor(self, trace, scores, ontology, strategy, decomposition):
        pass
```

---

## 5. Encodings

### 5.1 `encodings/bayes.py`

```python
class BayesOntology:
    pass

class BayesBeliefs:
    pass

class BayesRevisionPolicy:
    def update(self, beliefs, evidence, ontology, context):
        pass
```

---

### 5.2 `encodings/strips.py`

```python
class STRIPSOntology:
    pass

class STRIPSBeliefs:
    pass

class STRIPSRevisionPolicy:
    def update(self, beliefs, evidence, ontology, context):
        pass
```

---

### 5.3 `encodings/search.py`

```python
class SearchOntology:
    pass

class SearchBeliefs:
    pass

class SearchRevisionPolicy:
    def update(self, beliefs, evidence, ontology, context):
        pass
```

---

### 5.4 `encodings/mdp.py`

```python
class MDPOntology:
    pass

class MDPBeliefs:
    pass

class MDPRevisionPolicy:
    def update(self, beliefs, evidence, ontology, context):
        pass
```

---

## 6. Tool Integration — `tools/tool_interfaces.py`

```python
class ToolInterface:
    def invoke(self, params):
        pass

class ToolEvidenceAdapter:
    def to_evidence(self, tool_output):
        pass
```

---

## 7. LLM Integration — `llm/llm_interfaces.py`

```python
class LLMInterface:
    def propose_ontology(self, query):
        pass

    def decompose(self, query):
        pass

    def propose_strategy(self, state):
        pass

    def generate_explanation(self, state):
        pass

class LLMEvidenceAdapter:
    def to_evidence(self, llm_output):
        pass
```

---

## 8. Tests Skeleton

### 8.1 Bayesian

```python
def test_bayes_update():
    pass
```

### 8.2 STRIPS

```python
def test_strips_planning():
    pass
```

### 8.3 Search

```python
def test_search_frontier():
    pass
```

### 8.4 MDP

```python
def test_mdp_value_iteration():
    pass
```

### 8.5 Meta‑Layer

```python
def test_meta_decisions():
    pass
```

### 8.6 LLM Integration

```python
def test_llm_integration():
    pass
```

### 8.7 Tool Integration

```python
def test_tool_integration():
    pass
```

---

## 9. Completion Criteria for Code Generation

Claude should generate:

- all classes with full implementations
- all revision policies
- all pipeline stages
- all norms
- full meta‑layer logic
- all encodings
- all adapters
- all tests
- all documentation

Using **MCS‑E** (the ingestion bundle) + **MCS‑F** (this skeleton) as the blueprint.
