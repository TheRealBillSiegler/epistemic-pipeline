# Epistemic Pipeline

> **Status: design phase.** The formal spec is complete. Implementation is in progress. The code example below shows the target API — it does not run yet.

A formal system for making reasoning explicit and auditable. It tracks the vocabulary of a problem, what has been observed, how confident the system is in each hypothesis, and the rule it uses to update that confidence.

**Who is this for?** Researchers and engineers who build systems that reason — and need to inspect, replay, and evaluate that reasoning after the fact.

[Formal Spec](docs/spec/) · [Design Document](docs/superpowers/specs/2026-03-19-epistemic-pipeline-v01-design.md)

Python 3.14+ | Zero dependencies | MIT License

---

## The Idea

Every reasoning system — human or artificial — does four things:

1. **Defines a vocabulary** for the problem → what concepts exist?
2. **Gathers evidence** → what has been observed?
3. **Holds credences** (confidence levels) → how sure is it about each hypothesis?
4. **Revises those credences** when new evidence arrives → how does it update?

This project makes those four things explicit:

| | Component | What it is | Example |
|:-:|-----------|-----------|---------|
| **O** | Vocabulary | The concepts, types, and constraints of the problem | `diseases: [flu, cold, covid]` / `symptoms: [fever, cough, loss_of_smell]` |
| **E** | Evidence | What has been observed | `[fever=true, cough=true, loss_of_smell=true]` |
| **B** | Credences | Current confidence in each hypothesis | `{flu: 0.10, cold: 0.02, covid: 0.88}` |
| **R** | Revision | The rule for updating credences | Bayes' rule, search algorithms, or Bellman updates — your choice |

**R is the key.** Swap it and you get a completely different reasoning system:

- Set R to **Bayes' rule** → probabilistic reasoning (updating confidence from evidence)
- Set R to a **search algorithm** → planning (finding a path to a goal)
- Set R to a **Bellman update** → decision-making (choosing actions that maximize future reward)

Under the hood, `(O, E, B, R)` is a state machine. O is read-only. E is append-only. B is the mutable state. R is the transition function you plug in. That generality is deliberate — and it means the hard question is not *can* a framework be encoded, but *does the encoding preserve what matters about it*.

---

## Why This Matters

Many AI systems produce outputs without tracking how they got there. They can't replay their reasoning or evaluate whether their process was any good.

This design fixes that. Every state is immutable. Every transition is a pure function (same inputs, same outputs, no side effects). The system preserves the full reasoning trace. You can always answer:

> *How did the system reach this conclusion?*

---

## Target API

> This is the planned API. It does not run yet.

```python
from epistemic_pipeline import run_pipeline
from epistemic_pipeline.encodings.bayes import (
    BayesVocabulary, BayesCredences, BayesRevision, bayes_stages,
)

# Define the problem vocabulary
vocab = BayesVocabulary(
    hypotheses=["flu", "cold", "covid"],
    observables=["fever", "cough", "loss_of_smell"],
    likelihoods={
        ("flu",   "fever", True): 0.8,   ("flu",   "cough", True): 0.7,  ("flu",   "loss_of_smell", True): 0.05,
        ("cold",  "fever", True): 0.3,   ("cold",  "cough", True): 0.9,  ("cold",  "loss_of_smell", True): 0.02,
        ("covid", "fever", True): 0.85,  ("covid", "cough", True): 0.8,  ("covid", "loss_of_smell", True): 0.7,
    },
)

# Start with prior credences (initial confidence in each disease)
credences = BayesCredences({"flu": 0.4, "cold": 0.4, "covid": 0.2})

# Run the pipeline — each stage is a pure function, state in, state out
result = run_pipeline(
    vocabulary=vocab,
    credences=credences,
    revision_policy=BayesRevision(),
    evidence=[("fever", True), ("cough", True), ("loss_of_smell", True)],
    stages=bayes_stages(),  # the 6 pipeline stages configured for Bayesian inference
)

print(result.credences)
# → {flu: 0.10, cold: 0.02, covid: 0.88}

# Replay the reasoning trace — every intermediate state is preserved
for i, state in enumerate(result.trace):
    print(f"Step {i}: {state.credences}")
# → Step 0: {flu: 0.40, cold: 0.40, covid: 0.20}
# → Step 1: {flu: 0.52, cold: 0.20, covid: 0.28}   (after fever)
# → Step 2: {flu: 0.48, cold: 0.23, covid: 0.29}   (after cough)
# → Step 3: {flu: 0.10, cold: 0.02, covid: 0.88}   (after loss_of_smell)
```

Three symptoms in. One diagnosis out. Every step recorded and replayable.

Note: the model assumes symptoms are conditionally independent given the disease (the naive Bayes assumption). Real medical diagnosis is more complex, but this keeps the example clear.

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

An "expressiveness proof" shows that a well-known reasoning framework fits into this architecture as one configuration — and that the encoding preserves the framework's essential properties, not just its inputs and outputs.

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

The tuple is general enough to encode most things. The real test is whether each encoding preserves what makes its framework distinct. That's what the proofs must demonstrate.

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

**Belief revision theory.** The [AGM framework](https://plato.stanford.edu/entries/logic-belief-revision/) defines axioms for rational belief change over logically closed belief sets. (A logically closed set contains every consequence of its beliefs.) Our R component can accommodate AGM-compliant revision as one policy. But AGM operates on belief sets and sentences. Our R operates on credences and observations. Showing that AGM's postulates hold under our encoding is an open task.

**Goldman's reliabilism.** Goldman's [*Epistemology and Cognition*](https://www.hup.harvard.edu/books/9780674258969) (1986) argues that a belief is justified if the process that produced it reliably tracks truth across many cases. Our Norms layer draws on this idea. But our v0.1 "accuracy" norm is a single-run correctness check — a starting point, not Goldman's full theory.

**Cognitive architectures.** [ACT-R](http://act-r.psy.cmu.edu/) and [SOAR](https://soar.eecs.umich.edu/) model human cognition with detailed memory, timing, and learning mechanisms. ACT-R predicts response times. SOAR models goal-directed problem solving through impasse resolution (detecting when the system doesn't know what to do next). Our 5-layer stack shares the modular philosophy and adds normative evaluation. But it lacks their empirical grounding. This project is a computational framework, not a cognitive model.

**Probabilistic programming.** Languages like Pyro, Stan, and WebPPL bundle models, data, and inference into one framework. They handle continuous parameters, hierarchical models, and advanced sampling methods. Our architecture aims to be inference-method-agnostic — R can be Bayesian, but also search or decision-theoretic. The pipeline and norms layers have no direct equivalent in PPLs, though PPLs have their own diagnostics (convergence checks, model comparison).

**Epistemic integrity in AI.** [*Beyond Prediction*](https://arxiv.org/html/2506.17331) (preprint, 2025) proposes an architecture where AI agents justify beliefs under formal constraints using Kripke semantics (a formal model of knowledge across possible worlds). Similar goals, different formalism.

**What this project does not cover.** Goals and motivation (central to SOAR and human cognition). Attention and salience. Dual-process reasoning (fast intuitive judgment vs. slow deliberation — Kahneman). Bounded rationality (reasoning under limited time and memory — Simon, Gigerenzer). Online metacognitive monitoring. Active inference (Friston). These reflect scope decisions for v0.1, not claims that they don't matter.

**What's new here.** Few frameworks separate vocabulary, evidence, credences, and revision into a typed, immutable state tuple that preserves every trace. Fewer score each run against epistemic norms. Is this genuinely illuminating, or just a relabeling of generic state machines? The expressiveness proofs must answer that. Each encoding must preserve what makes its framework distinct.
