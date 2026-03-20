# Epistemic Pipeline

> **Status: design phase.** The formal spec is complete. Implementation is in progress. The code example below shows the target API — it does not run yet.

A formal system for making reasoning explicit. It tracks what concepts exist, what has been observed, what the system believes, and *how it updates those beliefs*.

[Formal Spec](docs/spec/) · [Design Document](docs/superpowers/specs/2026-03-19-epistemic-pipeline-v01-design.md)

Python 3.14+ | Zero dependencies | MIT License

---

## The Idea

Every reasoning system — human or artificial — does four things:

1. **Defines a vocabulary** for the problem → what concepts exist?
2. **Gathers evidence** → what has been observed?
3. **Holds credences** → how confident is it in each hypothesis?
4. **Revises those credences** when new evidence arrives → how does it update?

This project makes those four things explicit:

| | Component | What it is | Example |
|:-:|-----------|-----------|---------|
| **O** | Vocabulary | The concepts, types, and constraints of the problem | `diseases: [flu, cold, covid]` / `symptoms: [fever, cough, loss_of_smell]` |
| **E** | Evidence | What has been observed | `[fever=true, cough=true, loss_of_smell=true]` |
| **B** | Credences | Current confidence in each hypothesis | `{flu: 0.03, cold: 0.01, covid: 0.96}` |
| **R** | Revision | The rule for updating credences | Bayes' rule, search algorithms, Bellman updates — your choice |

**R is the key.** Swap it and you get a completely different reasoning system:

- Set R to **Bayes' rule** → probabilistic reasoning
- Set R to a **search algorithm** → planning
- Set R to a **Bellman update** → decision-making

Everything else stays the same.

This makes `(O, E, B, R)` a generic state machine with an append-only log (E), a read-only vocabulary (O), a mutable state (B), and a pluggable transition function (R). That generality is deliberate — but it means the interesting question is not *whether* a framework can be encoded, but *whether the encoding preserves its essential properties*. That's what the expressiveness proofs must show.

---

## Why This Matters

Many AI systems produce outputs without tracking how they got there. They can't replay their reasoning. They can't evaluate whether their process was any good.

This design changes that.

Every state is immutable. Every transition is a pure function. The full reasoning trace is preserved. You can always answer:

> *How did the system reach this conclusion?*

That's not a feature. That's the point.

---

## Target API

> This is the planned API. It does not run yet.

```python
from epistemic_pipeline import run_pipeline
from epistemic_pipeline.encodings.bayes import (
    BayesOntology, BayesCredences, BayesRevision, bayes_stages,
)

# Define the problem
ontology = BayesOntology(
    hypotheses=["flu", "cold", "covid"],
    observables=["fever", "cough", "loss_of_smell"],
    likelihoods={
        ("flu",   "fever", True): 0.8,   ("flu",   "cough", True): 0.7,  ("flu",   "loss_of_smell", True): 0.05,
        ("cold",  "fever", True): 0.3,   ("cold",  "cough", True): 0.9,  ("cold",  "loss_of_smell", True): 0.02,
        ("covid", "fever", True): 0.85,  ("covid", "cough", True): 0.8,  ("covid", "loss_of_smell", True): 0.7,
    },
)

# Start with prior credences
credences = BayesCredences({"flu": 0.4, "cold": 0.4, "covid": 0.2})

# Run the pipeline
result = run_pipeline(
    ontology=ontology,
    credences=credences,
    revision_policy=BayesRevision(),
    evidence=[("fever", True), ("cough", True), ("loss_of_smell", True)],
    stages=bayes_stages(),
)

print(result.credences)
# → {flu: 0.03, cold: 0.01, covid: 0.96}

# Replay the reasoning trace
for i, state in enumerate(result.trace):
    print(f"Step {i}: {state.credences}")
# → Step 0: {flu: 0.40, cold: 0.40, covid: 0.20}
# → Step 1: {flu: 0.35, cold: 0.13, covid: 0.52}   (after fever)
# → Step 2: {flu: 0.29, cold: 0.14, covid: 0.57}   (after cough)
# → Step 3: {flu: 0.03, cold: 0.01, covid: 0.96}   (after loss_of_smell)
```

Three symptoms in. One diagnosis out. Every step recorded and replayable.

---

## The Architecture

Two views of one system. The **stack** describes what kinds of modules exist. The **tuple** describes what changes as reasoning progresses.

```text
  ╔═══════════════════════════════════════════════════════════════╗
  ║                    META-EPISTEMIC LAYER                      ║
  ║         watches everything · decides what to do next         ║
  ╠═══════════════════════════════════════════════════════════════╣
  ║                    EPISTEMIC NORMS                           ║
  ║         accurate? · efficient? · reproducible?               ║
  ╠═══════════════════════════════════════════════════════════════╣
  ║                    PIPELINE                                  ║
  ║         frame → decompose → model → strategy → test → integrate
  ╠═══════════════════════════════════════════════════════════════╣
  ║                    COGNITIVE PROCESSES                       ║
  ║         inference · search · memory · heuristics · planning  ║
  ╠═══════════════════════════════════════════════════════════════╣
  ║                    TOOLS / ENVIRONMENT                       ║
  ║         LLMs · APIs · databases · simulators · sensors       ║
  ╚═══════════════════════════════════════════════════════════════╝

                    State: ( O , E , B , R )
```

Each layer reads and writes different parts of the state tuple:

| Layer | O | E | B | R |
|-------|---|---|---|---|
| **Tool / Environment** | provides | **produces** | — | — |
| **Cognitive Process** | reads | reads | **transforms** | — |
| **Pipeline** | sequences | sequences | sequences | — |
| **Norms** | evaluates | evaluates | evaluates | evaluates |
| **Meta-Epistemic** | re-frames | requests more | forces revision | **modifies** |

---

## v0.1 — Deliberately Small, Deliberately Rigorous

**Status: spec complete, implementation in progress.**

- Deterministic state machine implementing `(O, E, B, R)`
- Bayesian inference as the first expressiveness proof
- Toy medical diagnosis running end-to-end
- Full state trace, norm scoring, meta-layer stub
- No LLM. No external dependencies. Pure Python.

The formal spec lives in [`docs/spec/`](docs/spec/). The code will live in [`src/epistemic_pipeline/`](src/epistemic_pipeline/). The spec defines the interfaces. The code implements them. Neither imports the other.

---

## Expressiveness Roadmap

v0.1 will prove the architecture works with one framework. The roadmap tests it with four:

| | Framework | What it proves | R becomes |
|:-:|-----------|---------------|-----------|
| **v0.1** | Bayesian inference | Probabilistic reasoning | Bayes' rule |
| **v0.2** | STRIPS / PDDL | Goal-directed planning | Search strategy |
| **v0.3** | Newell & Simon | General problem solving | Operator selection |
| **v0.4** | MDPs | Decisions under uncertainty | Bellman updates |

The key question is not whether these frameworks *can* be encoded — the tuple is general enough that most things can. The question is whether each encoding *preserves the essential properties* of the original framework. That's what the expressiveness proofs must demonstrate.

---

## Quick Start

> Implementation in progress. These commands will work once v0.1 ships.

```bash
# Install
uv pip install -e .

# Test
pytest

# Type check
pyright
```

---

## Project Structure

```text
epistemic-pipeline/
├── docs/spec/                      Formal specification — standalone, publishable
├── src/epistemic_pipeline/         Reference implementation — standalone, installable
├── tests/                          pytest suite
├── examples/                       Runnable demonstrations
└── pyproject.toml
```

---

## Related Work

This project draws on several traditions. It doesn't replace any of them.

**Belief revision theory.** The [AGM framework](https://plato.stanford.edu/entries/logic-belief-revision/) defines axioms for rational belief change over logically closed belief sets. Our R component can accommodate AGM-compliant revision as one policy. But AGM operates on belief sets and sentences, while our R operates on credences and observations — the type signatures differ. Showing that AGM's postulates hold under our encoding is an open task, not a settled claim.

**Goldman's reliabilism.** Goldman's [*Epistemology and Cognition*](https://www.hup.harvard.edu/books/9780674258969) (1986) argues that a belief is justified if the process that produced it reliably tracks truth. Our Norms layer draws on this idea. But Goldman's "reliability" is a property of a *process type* across many cases. Our v0.1 "accuracy" norm is a single-run correctness check — a starting point, not the full Goldmanian picture.

**Cognitive architectures.** [ACT-R](http://act-r.psy.cmu.edu/) and [SOAR](https://soar.eecs.umich.edu/) model human cognition as modular systems with detailed memory, timing, and learning mechanisms. Our 5-layer stack shares the modular philosophy. It adds explicit normative evaluation. But it lacks their empirical grounding — ACT-R predicts response times, SOAR models goal-directed impasse resolution. This project is a computational framework, not a cognitive model.

**Probabilistic programming.** Languages like Pyro, Stan, and WebPPL bundle models, data, and inference into one framework. They excel at probabilistic reasoning. Our architecture aims to be inference-method-agnostic — R can be Bayesian, but also search or decision-theoretic. The pipeline and norms layers have no equivalent in PPLs.

**Epistemic integrity in AI.** [*Beyond Prediction*](https://arxiv.org/html/2506.17331) (preprint, 2025) proposes an architecture where AI agents justify beliefs under formal constraints. Similar goals, different formalism. They use Kripke semantics. We use a state-machine pipeline with pluggable revision policies.

**What this project does not yet cover.** Goals and motivation (central to SOAR and human cognition). Attention and salience. Dual-process reasoning (Kahneman's System 1/System 2). Bounded rationality (Simon, Gigerenzer). Metacognitive monitoring signals. Active inference (Friston). These are real gaps, not future features — they reflect scope decisions, not oversights.

**What's new here.** Few frameworks explicitly separate vocabulary, evidence, credences, and revision as a generic typed state tuple with immutability and trace preservation. Fewer score each run against epistemic norms. Whether this decomposition is genuinely illuminating — or merely a relabeling of generic state machines — depends on whether the expressiveness proofs preserve the essential structure of each encoded framework. v0.1 starts that argument. It doesn't finish it.

---

*Graduate-level ideas. 8th-grade sentences.*
