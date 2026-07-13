# Directions

**Everything on this page is designed, researched, and not built.** Each direction has an open issue and a recorded evidence base. The project's build rule applies: nothing here gets built until the evidence demands it, and nothing here should be read as a shipped capability.

## Audit the model itself: the parametric-knowledge encoding

*Issue [#41](https://github.com/TheRealBillSiegler/epistemic-pipeline/issues/41) · research record [2026-07-12](https://github.com/TheRealBillSiegler/epistemic-pipeline/blob/main/docs/research/2026-07-12-parametric-knowledge-encoding-prior-art.md)*

The idea: instead of only reading documents, have the model break **its own knowledge** down into claims — and run those through the same pipeline. Two rules make the existing machinery handle it honestly:

- **The model is the root.** However many times you re-ask, every self-emitted claim shares one origin: the model's weights. Root-keyed fusion then averages self-emissions instead of accumulating them, so a self-derived worldview stays honestly single-sourced — its settledness is capped, and that cap is the point. Repeated self-questioning must never look like independent confirmation.
- **Declared priors.** Elicit the model's stance on a claim *before* it reads anything, and record it as the claim's base rate. Document evidence then moves belief relative to a stated prior instead of a hidden one — turning the [one-rater problem](../worldview/honesty.md#1-one-rater) from an unmeasurable contamination into recorded data.

What it would yield: an auditable, diffable map of what a model believes ("what did the upgrade change its mind about" becomes a query); the cheapest path to measuring a rater's calibration; and cross-model diffing as hallucination triage.

**What the literature says** (deep-research pass, 105 agents, adversarially verified): the combination is novel. The closest prior art — the AI2 belief-store lineage (BeliefBank, Entailer, TeachMe, REFLEX) — externalizes model beliefs but revises them by consistency-solving, never by evidential fusion, and has no provenance, replay, or document-evidence stage. Two imports would make the design better: a claim-relation graph (so a claim and its negation can finally interact — the same gap as [#33](https://github.com/TheRealBillSiegler/epistemic-pipeline/issues/33)) and multi-channel confidence elicitation (a single verbalized prior is measurably weak; sampling-consistency and channel fusion beat it).

**Hard prerequisite:** claim identity ([#33](https://github.com/TheRealBillSiegler/epistemic-pipeline/issues/33)). Self-emitted claims paraphrase-fragment worse than document claims do.

## Retraction: un-believing with a receipt

*Issue [#42](https://github.com/TheRealBillSiegler/epistemic-pipeline/issues/42)*

Mark a discredited observation, re-derive beliefs without it, log the retraction as a timeline event — full mechanism on [When the model is wrong](../worldview/model-error.md#hallucination-contain-attribute-retract). Cheap because beliefs are a pure fold; honest because the judgment stays human.

## The measurement program

The trust story ends at claims that are measured, not argued. What remains unmeasured, in dependency order:

| Measurement | Issue | Why it gates everything |
|---|---|---|
| Claim identity design (one-way door) | [#33](https://github.com/TheRealBillSiegler/epistemic-pipeline/issues/33) | Calibration scored per-string is ill-posed until claims have stable identity |
| Calibration with baselines | [#34](https://github.com/TheRealBillSiegler/epistemic-pipeline/issues/34) | The only detector for trained-in model bias; also the test of whether the pipeline adds anything over the raw LLM |
| Rater-prior contribution | [#35](https://github.com/TheRealBillSiegler/epistemic-pipeline/issues/35) | Bounds how much of "settled" is one model's prior |
| Replay-rule fidelity | [#30](https://github.com/TheRealBillSiegler/epistemic-pipeline/issues/30) | Replay must use the rule that made the trace |

!!! note "Why the order keeps repeating"
    Every deep question asked of this project — hallucination, flawed training, auditing the model itself —
    has resolved to the same two prerequisites: claim identity (#33) and measured calibration (#34).
    That convergence is the strongest evidence the priority order is right.

## Where next

- What is built and open today: [Status](status.md)
- The walls that hold regardless of any direction here: [What the numbers mean](../worldview/honesty.md)
