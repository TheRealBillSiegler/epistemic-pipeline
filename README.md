<p align="center">
  <h1 align="center">Epistemic Pipeline</h1>
  <p align="center">
    <strong>What if reasoning had an architecture?</strong>
    <br />
    Not a prompt. Not a chain. A formal system that tracks what it knows,<br />what it believes, and <em>how it decides to change its mind</em>.
  </p>
  <p align="center">
    <a href="docs/spec/">Formal Spec</a> &middot;
    <a href="src/epistemic_pipeline/">Reference Implementation</a> &middot;
    <a href="docs/superpowers/specs/2026-03-19-epistemic-pipeline-v01-design.md">Design Document</a>
  </p>
</p>

<br />

<p align="center">
  <code>pip install -e .</code> &nbsp;&nbsp;|&nbsp;&nbsp; Python 3.14+ &nbsp;&nbsp;|&nbsp;&nbsp; Zero dependencies &nbsp;&nbsp;|&nbsp;&nbsp; MIT License
</p>

---

<br />

## The Idea

Every reasoning system — human or artificial — does four things:

> **1.** Defines a vocabulary for the problem &nbsp;→&nbsp; what concepts exist?
> **2.** Gathers evidence &nbsp;→&nbsp; what has been observed?
> **3.** Holds beliefs &nbsp;→&nbsp; what does it think is true?
> **4.** Revises those beliefs when new evidence arrives &nbsp;→&nbsp; how does it update?

This project makes those four things explicit:

<table>
<tr>
<td width="120"><strong>O</strong><br /><sub>Ontology</sub></td>
<td width="200">The vocabulary of the problem</td>
<td><code>diseases: [flu, cold, covid]</code><br /><code>symptoms: [fever, cough, loss_of_smell]</code></td>
</tr>
<tr>
<td><strong>E</strong><br /><sub>Evidence</sub></td>
<td>What has been observed</td>
<td><code>[fever=true, cough=true, loss_of_smell=true]</code></td>
</tr>
<tr>
<td><strong>B</strong><br /><sub>Beliefs</sub></td>
<td>Current confidence in each hypothesis</td>
<td><code>{flu: 0.03, cold: 0.01, covid: 0.96}</code></td>
</tr>
<tr>
<td><strong>R</strong><br /><sub>Revision</sub></td>
<td>The rule for updating beliefs</td>
<td>Bayes' rule, search algorithms, Bellman updates — your choice</td>
</tr>
</table>

**R is the key.** Swap it and you get a completely different reasoning system:

- Set R to **Bayes' rule** → probabilistic reasoning
- Set R to a **search algorithm** → planning
- Set R to a **Bellman update** → decision-making

Everything else stays the same.

<br />

## Why This Matters

Most AI systems are black boxes. They produce fluent outputs. They don't track *why* they believe what they believe. They can't replay their reasoning. They can't evaluate whether their own process was any good.

This system can.

Every state is frozen. Every transition is a pure function. The full reasoning trace is preserved. You can always answer:

> *How did the system reach this conclusion?*

That's not a feature. That's the point.

<br />

## What It Looks Like

```python
from epistemic_pipeline import EpistemicState, run_pipeline
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
```

Three symptoms in. One diagnosis out. Every step recorded and replayable.

<br />

## The Architecture

Two views of one system. The **stack** is vertical — what kinds of modules exist. The **tuple** is horizontal — what changes as reasoning progresses.

```
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
|-------|:-:|:-:|:-:|:-:|
| **Tool / Environment** | provides | **produces** | — | — |
| **Cognitive Process** | **transforms** | reads | **transforms** | — |
| **Pipeline** | sequences | sequences | sequences | — |
| **Norms** | evaluates | evaluates | evaluates | evaluates |
| **Meta-Epistemic** | re-frames | requests more | forces revision | **modifies** |

<br />

## v0.1 — Deliberately Small, Deliberately Rigorous

- [x] Deterministic state machine implementing `(O, E, B, R)`
- [x] Bayesian inference as the first expressiveness proof
- [x] Toy medical diagnosis running end-to-end
- [x] Full state trace, norm scoring, meta-layer stub
- [ ] No LLM. No external dependencies. Pure Python.

The formal spec lives in [`docs/spec/`](docs/spec/). The code lives in [`src/epistemic_pipeline/`](src/epistemic_pipeline/). They reference each other but neither imports the other.

**The spec is publishable. The code is installable.**

<br />

## Expressiveness Roadmap

The architecture is general. v0.1 proves it with one framework. The roadmap proves it with four:

| | Framework | What it proves | R becomes |
|:-:|-----------|---------------|-----------|
| **v0.1** | Bayesian inference | Probabilistic reasoning | Bayes' rule |
| **v0.2** | STRIPS / PDDL | Goal-directed planning | Search strategy |
| **v0.3** | Newell & Simon | General problem solving | Operator selection |
| **v0.4** | MDPs | Decisions under uncertainty | Bellman updates |

If all four fit, the architecture can express every major reasoning paradigm in AI and cognitive science.

<br />

## Quick Start

```bash
# Install
pip install -e .

# Test
pytest

# Type check
pyright
```

<br />

## Project Structure

```
epistemic-pipeline/
├── docs/spec/                      Formal specification — standalone, publishable
├── src/epistemic_pipeline/         Reference implementation — standalone, installable
├── tests/                          pytest suite
├── examples/                       Runnable demonstrations
└── pyproject.toml
```

<br />

## Related Work

This project draws on several traditions but doesn't duplicate any of them.

**Belief revision theory.** The [AGM framework](https://plato.stanford.edu/entries/logic-belief-revision/) (Alchourrón, Gärdenfors, Makinson) defines axioms for how rational agents should change their beliefs. Our R component generalizes AGM — it's a pluggable slot where Bayes' rule, AGM contraction, or any other revision policy can live.

**Goldman's reliabilism.** Alvin Goldman's [*Epistemology and Cognition*](https://www.hup.harvard.edu/books/9780674258969) (1986) argues that a cognitive process is epistemically good if it reliably produces true beliefs. Our Norms layer (reliability, power, efficiency, justification) operationalizes Goldman's framework as computable scores over a reasoning trace.

**Cognitive architectures.** [ACT-R](http://act-r.psy.cmu.edu/) and [SOAR](https://soar.eecs.umich.edu/) model human cognition as modular systems with memory, perception, and production rules. Our 5-layer stack shares this modular philosophy but adds epistemic norms and a formal state model that those architectures lack.

**Epistemic integrity in AI.** [*Beyond Prediction: Structuring Epistemic Integrity in Artificial Reasoning Systems*](https://arxiv.org/html/2506.17331) (2025) proposes an architecture where AI agents justify beliefs according to normative standards. Similar goals, different formalism — they use Kripke semantics and formal logic; we use a state-machine pipeline with pluggable revision policies.

**What's new here:** No existing framework bundles ontology, evidence, beliefs, and revision into a generic state tuple, runs it through a scored pipeline, and proves expressiveness by encoding multiple reasoning paradigms as special cases of one architecture.

<br />

---

<p align="center">
  <sub>Graduate-level ideas. 8th-grade sentences. Rigorous structures, simple prose.</sub>
</p>
