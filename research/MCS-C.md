# MCS‑C — Version Evolution Map (v0.1 → v0.2 → v1.0)

**Form:** Ultra‑compressed, lossless, structural deltas
**Purpose:** Capture the architectural evolution across
versions in a single artifact

---

## 0. Overview

This map expresses:

- what each version *adds*
- what each version *modifies*
- what each version *activates*
- what each version *deprecates*
- how the reasoning engine evolves from
  deterministic → adaptive → universal

It is organized as a **delta matrix** across the core
architectural axes:

- State Model
- Pipeline
- Norms
- Meta‑Layer
- Expressiveness
- Evidence Model
- Strategy Model
- Tool/LLM Integration
- Project Structure
- Success Criteria

---

## 1. State Model Evolution

| Component | v0.1 | v0.2 | v1.0 |
| --- | --- | --- | --- |
| Ontology | static | +adequacy | +causal, operators |
| Evidence | basic obs | +confidence, etype | +modality |
| Beliefs | distributions | +consistency | +value fns, causal |
| Revision | pure fn | +confidence‑wt | +context‑aware |
| State | immutable | +heuristic meta | +tool/LLM meta |

---

## 2. Pipeline Evolution

| Stage | v0.1 | v0.2 | v1.0 |
| --- | --- | --- | --- |
| Frame | determ. ontology | — | +LLM/tool assist |
| Decompose | optional | — | +LLM hierarchical |
| Model | init B,R | +paradigm sel. | full suite |
| Select | static | +heuristics | +ensembles, meta |
| Test | determ. updates | +anomaly det. | +multi‑paradigm |
| Integrate | posterior/expl. | — | +causal, uncert. |

---

## 3. Norms Evolution

| Norm | v0.1 | v0.2 | v1.0 |
| --- | --- | --- | --- |
| Reliability | binary | +calibration | +predictive, x‑par |
| Efficiency | trace len | +heuristic cost | +tool/LLM/search |
| Justification | replay | +intermediate | +causal, tool/LLM |
| Power | doc only | adequacy(O,E) | full repr. suff. |

---

## 4. Meta‑Epistemic Layer Evolution

| Capability | v0.1 | v0.2 | v1.0 |
| --- | --- | --- | --- |
| Decision | ACCEPT | triggers | full adaptive |
| Reframe | stub | reliability | +paradigm |
| Switch | stub | efficiency | +paradigm sw. |
| Escalate | stub | contradiction | +causal/value |
| Accept | always | default | default |

---

## 5. Expressiveness Evolution

| Paradigm | v0.1 | v0.2 | v1.0 |
| --- | --- | --- | --- |
| Bayesian | ✔ | ✔ | ✔ |
| STRIPS | — | ✔ | ✔ |
| State‑Space Search | — | — | ✔ |
| MDPs | — | — | ✔ |
| Hybrid Reasoning | — | — | ✔ |

---

## 6. Evidence Model Evolution

| Feature | v0.1 | v0.2 | v1.0 |
| --- | --- | --- | --- |
| Confidence | — | ✔ | ✔ |
| Evidence Type | — | ✔ | ✔ |
| Modality | — | — | ✔ (tool, LLM, sensor) |
| Multi‑modal Fusion | — | — | ✔ |

---

## 7. Strategy Model Evolution

| Feature | v0.1 | v0.2 | v1.0 |
| --- | --- | --- | --- |
| Static Strategy | ✔ | — | — |
| Heuristics | — | ✔ | ✔ |
| Strategy Switching | — | ✔ | ✔ |
| Paradigm Switching | — | — | ✔ |
| Ensembles | — | — | ✔ |

---

## 8. Tool & LLM Integration Evolution

| Integration | v0.1 | v0.2 | v1.0 |
| --- | --- | --- | --- |
| Tools | — | — | ✔ (evidence acquisition) |
| LLMs | — | — | ✔ (cognitive processes) |
| LLM as Ontology Gen | — | — | ✔ |
| LLM as Decomposer | — | — | ✔ |
| LLM as Strategy | — | — | ✔ |
| LLM as Explainer | — | — | ✔ |

---

## 9. Project Structure Evolution

| Area | v0.1 | v0.2 | v1.0 |
| --- | --- | --- | --- |
| Encodings | bayes | +strips | +search +mdp |
| Meta Tests | basic | +decision tests | +adaptive tests |
| Tool/LLM Modules | — | — | ✔ |
| Docs | core spec | +strips spec | +search, mdp, llm, tool specs |

---

## 10. Success Criteria Evolution

| Criterion | v0.1 | v0.2 | v1.0 |
| --- | --- | --- | --- |
| Deterministic Pipeline | ✔ | ✔ | ✔ |
| Adaptive Meta‑Layer | — | ✔ | ✔ |
| Multi‑Paradigm | Bayes | Bayes + STRIPS | Full suite |
| LLM Integration | — | — | ✔ |
| Tool Integration | — | — | ✔ |
| Real‑World Tasks | toy example | planning tasks | full real‑world examples |
| Norms | minimal | extended | full |
| Tests | core | +meta +strips | +search +mdp +llm +tool |

---

## 11. Version Summary (One‑Line Deltas)

- **v0.1 → v0.2:**
  Deterministic → Adaptive.
  Adds meta‑layer logic, STRIPS, heuristics,
  confidence, anomaly detection.

- **v0.2 → v1.0:**
  Adaptive → Universal.
  Adds LLMs, tools, full paradigm suite,
  causal/value reasoning, dynamic
  strategy/paradigm switching.
