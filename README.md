# Epistemic Pipeline

**What if reasoning had an architecture?**

Not a prompt. Not a chain. A formal system that tracks what it knows, what it believes, and *how it decides to change its mind*.

[Formal Spec](docs/spec/) · [Reference Implementation](src/epistemic_pipeline/) · [Design Document](docs/superpowers/specs/2026-03-19-epistemic-pipeline-v01-design.md)

`uv pip install -e .` | Python 3.14+ | Zero dependencies | MIT License

---

## The Idea

Every reasoning system — human or artificial — does four things:

1. **Defines a vocabulary** for the problem → what concepts exist?
2. **Gathers evidence** → what has been observed?
3. **Holds beliefs** → what does it think is true?
4. **Revises those beliefs** when new evidence arrives → how does it update?

This project makes those four things explicit:

| | Component | What it is | Example |
|:-:|-----------|-----------|---------|
| **O** | Ontology | The vocabulary of the problem | `diseases: [flu, cold, covid]` / `symptoms: [fever, cough, loss_of_smell]` |
| **E** | Evidence | What has been observed | `[fever=true, cough=true, loss_of_smell=true]` |
| **B** | Beliefs | Current confidence in each hypothesis | `{flu: 0.03, cold: 0.01, covid: 0.96}` |
| **R** | Revision | The rule for updating beliefs | Bayes' rule, search algorithms, Bellman updates — your choice |

**R is the key.** Swap it and you get a completely different reasoning system:

- Set R to **Bayes' rule** → probabilistic reasoning
- Set R to a **search algorithm** → planning
- Set R to a **Bellman update** → decision-making

Everything else stays the same.

---

## Why This Matters

Most AI systems are black boxes. They produce fluent outputs. They don't track *why* they believe what they believe. They can't replay their reasoning. They can't grade whether their own process was any good.

This system can.

Every state is frozen. Every transition is a pure function. The full reasoning trace is preserved. You can always answer:

> *How did the system reach this conclusion?*

That's not a feature. That's the point.

---

## What It Looks Like

```python
from epistemic_pipeline import run_pipeline
from epistemic_pipeline.encodings.bayes import (
    BayesOntology, BayesBelief, BayesRevision, bayes_stages,
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

# Start with prior beliefs
beliefs = BayesBelief({"flu": 0.4, "cold": 0.4, "covid": 0.2})

# Run the pipeline
result = run_pipeline(
    ontology=ontology,
    beliefs=beliefs,
    revision_policy=BayesRevision(),
    evidence=[("fever", True), ("cough", True), ("loss_of_smell", True)],
    stages=bayes_stages(),
)

print(result.beliefs)
# → {flu: 0.03, cold: 0.01, covid: 0.96}

# Replay the reasoning trace
for i, state in enumerate(result.trace):
    print(f"Step {i}: {state.beliefs}")
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
  ║         reliable? · efficient? · justified? · powerful?      ║
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

The formal spec lives in [`docs/spec/`](docs/spec/). The code lives in [`src/epistemic_pipeline/`](src/epistemic_pipeline/). The spec defines the interfaces. The code implements them. Neither imports the other.

---

## Expressiveness Roadmap

v0.1 proves the architecture works with one framework. The roadmap tests it with four:

| | Framework | What it proves | R becomes |
|:-:|-----------|---------------|-----------|
| **v0.1** | Bayesian inference | Probabilistic reasoning | Bayes' rule |
| **v0.2** | STRIPS / PDDL | Goal-directed planning | Search strategy |
| **v0.3** | Newell & Simon | General problem solving | Operator selection |
| **v0.4** | MDPs | Decisions under uncertainty | Bellman updates |

If all four fit, the architecture covers the major reasoning paradigms in AI and cognitive science.

---

## Quick Start

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

**Belief revision theory.** The [AGM framework](https://plato.stanford.edu/entries/logic-belief-revision/) defines axioms for rational belief change. Our R component accommodates AGM as one possible revision policy. Plug in AGM-compliant contraction and the axioms hold. Plug in Bayes' rule and you get a different system.

**Goldman's reliabilism.** Goldman's [*Epistemology and Cognition*](https://www.hup.harvard.edu/books/9780674258969) (1986) argues that a belief is justified if the process that produced it reliably tracks truth. Our Norms layer draws on this idea. It scores each pipeline run for reliability, efficiency, and justification.

**Cognitive architectures.** [ACT-R](http://act-r.psy.cmu.edu/) and [SOAR](https://soar.eecs.umich.edu/) model human cognition as modular systems with memory, perception, and production rules. Our 5-layer stack shares this modular philosophy. It adds explicit normative evaluation that those architectures don't provide.

**Probabilistic programming.** Languages like Pyro, Stan, and WebPPL bundle models, data, and inference into one framework. They excel at probabilistic reasoning. Our architecture is broader — R can be Bayesian inference, but it can also be search, planning, or decision-theoretic. The pipeline, norms, and meta-layer have no equivalent in probabilistic programming.

**Epistemic integrity in AI.** [*Beyond Prediction*](https://arxiv.org/html/2506.17331) (preprint, 2025) proposes an architecture where AI agents justify beliefs under formal constraints. Similar goals, different formalism. They use Kripke semantics. We use a state-machine pipeline with pluggable revision policies.

**What's new here.** Few frameworks explicitly separate ontology, evidence, beliefs, and revision as a generic typed state tuple. Fewer run that tuple through a scored pipeline. None we've found prove expressiveness by encoding multiple reasoning paradigms as special cases of one architecture.

---

*Graduate-level ideas. 8th-grade sentences. Rigorous structures, simple prose.*
