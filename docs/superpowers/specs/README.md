# Design specs — index

This folder holds the **current** design specs. Older versions are archived in
[`/archive/specs/`](../../../archive/specs/). Read this index first to know which
spec describes the code you are looking at.

## Current

| Spec | Status | What it covers |
|------|--------|----------------|
| [v1.1 design](2026-05-14-epistemic-pipeline-v11-design.md) | **Implemented** — current baseline | The shipped architecture: `(O, E, B, R)` state, six-stage pipeline, norms, adaptive meta-layer, five encodings (Bayes, STRIPS, search, MDP, LLM-agent), JSONL trace persistence, the `epc` CLI. |
| [Worldview — Subjective Logic design](2026-06-23-worldview-subjective-logic-design.md) | **Proposed** — in progress | The next belief representation `B` and revision rule `R` for the worldview encoding. Supersedes the v1.1 "renormalize over the latest vector" rule. |

The active research behind the worldview work lives in [`/docs/research/`](../../research/).

## Superseded (history)

These are kept for the record in [`/archive/specs/`](../../../archive/specs/). They do
**not** describe the current code.

| Spec | Superseded by |
|------|---------------|
| v0.1 design (2026-03-19) | v1.1 |
| v0.2 design (2026-03-20) | v1.1 |
| v1.0 design (2026-03-20) | v1.1 |

Implementation plans for v0.1–v1.0 are in [`/archive/plans/`](../../../archive/plans/);
the early "MCS" research notes are in [`/archive/research/`](../../../archive/research/).
