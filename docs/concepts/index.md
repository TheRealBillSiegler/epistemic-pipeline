# Core ideas

**Four pages explain the whole architecture.** One state tuple holds everything the system knows. Five layers divide the work of changing it. One pipeline moves a run from question to audited answer. Encodings let different reasoning frameworks — Bayes, planning, Subjective Logic — live inside the same four slots.

## Read in this order

1. **[The state tuple](state.md)** — the `(O, E, B, R)` state: ontology, evidence, beliefs, and the revision rule. Everything else reads or writes these four slots, so start here.
2. **[The five layers](layers.md)** — how the system splits work vertically, from tools at the bottom to the meta layer that may re-frame the problem.
3. **[The pipeline](pipeline.md)** — how one run flows through six stages, producing a frozen state at each step.
4. **[Encodings](encodings.md)** — how a framework like Bayesian updating or Subjective Logic specializes the tuple without changing the architecture.

The tuple is the horizontal view: what the state *is*. The layers are the vertical view: who touches it. The pipeline is the time view: when. Encodings are the plug-in view: in what vocabulary.

## Who this is for

Read this section if you want to understand *why* the system is auditable — not just what buttons the [worldview app](../worldview/index.md) has. No math is required here; the arithmetic of beliefs lives in [Beliefs as numbers](../beliefs/index.md).

These pages explain the design. The formal source of truth is the
[v1.1 design spec](https://github.com/TheRealBillSiegler/epistemic-pipeline/blob/main/docs/superpowers/specs/2026-05-14-epistemic-pipeline-v11-design.md).
