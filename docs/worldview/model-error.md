# When the model is wrong

**Every number in the store depends on one LLM reading a document. This page says what happens when that reading is wrong — split by the kind of wrongness, because each kind meets a different defense.** The short version: the system cannot stop the model from being wrong. It can bound the damage, keep the receipts, make retraction cheap, and measure the error in aggregate. Nothing here detects falsehood; that limit is stated, not hidden.

## Three senses of "correct"

"Does the pipeline produce a correct result" splits into three claims that must not be blurred:

1. **Correct arithmetic — provable, and proved.** Downstream of the LLM, everything is deterministic, tested, and replayable. Given its inputs, the output is exactly what the stated rule produces.
2. **Correct about your documents — exactly as correct as the LLM.** The claims, stances, and confidences are one model call. Nothing downstream repairs an upstream misreading; the math faithfully aggregates whatever the model said.
3. **Correct about the world — never claimed.** See [What the numbers mean](honesty.md).

The LLM is the only epistemic organ; everything else is bookkeeping. The design's job is to make sure the bookkeeping never launders the model's judgment into more than it is.

## Hallucination: contain, attribute, retract

A hallucination in ordinary LLM use becomes your belief in one step. Here it meets three mechanisms:

- **Containment.** One source lands a claim at 0.65, not 0.9 — settledness accumulates only across distinct roots. A fabricated claim enters as a weak, single-source, fully-receipted belief, and repeating the lie moves nothing ([fusion](../beliefs/fusion.md)). Its blast radius is bounded by arithmetic.
- **Attribution.** Every claim traces to its document, model, and prompt. When a fabrication is discovered, every belief it touched is a query, not a hunt.
- **Retraction** ([#42](https://github.com/TheRealBillSiegler/epistemic-pipeline/issues/42), designed, not built). Because beliefs are a pure fold over the evidence trail, removing a discredited observation's influence is cheap: mark the row discredited (the trail stays append-only — the lie *and* its retraction are both on record), re-derive beliefs without it, and log the retraction in the drift timeline. The same move works one level up: quarantine every observation from a model version later found flawed.

None of this is detection. The system does not notice a fabrication; someone holding a receipt does. That division is deliberate — see the ladder below.

## Flawed training: the error class above hallucination

A bias baked into the model's weights defeats the easy defenses:

- **Retry detects nothing.** A trained-in bias is perfectly consistent — consistency is what training does.
- **A second model helps less than you'd hope.** Model families share training corpora, so shared misconceptions are correlated. Disagreement between models catches quirks, not consensus errors.
- **Deterministic checks pass.** The quote is present, the DOI resolves; the model read a real document and *misweighed* it.
- **Even a human with receipts mostly misses it.** A systematic skew spreads small errors across thousands of ratings; no single receipt looks wrong.

Two mechanisms survive, and both are designed into this project:

1. **Calibration measurement is the detector** ([#34](https://github.com/TheRealBillSiegler/epistemic-pipeline/issues/34)). Trained-in bias *is* miscalibration: if a model's 0.8-rated claims resolve true only 60% of the time, the flaw becomes a measured curve. Invisible per claim; visible in aggregate against resolved ground truth.
2. **The discount operator is the repair.** A rater's measured track record can set its reliability `P_R` — discounting that model's evidence by exactly its measured miscalibration ([credibility](../beliefs/credibility.md)). A track record on resolved claims is also non-circular: it is grounded in outcomes, not in any model's self-report. This is the most principled grounding for `P_R` the project has found.

## The ladder of judges

Who is allowed to decide that evidence is bad? Ordered from most to least trustworthy — and from narrowest to widest coverage:

| Judge | Can catch | Cannot catch | Circularity risk |
|---|---|---|---|
| Deterministic check (string present, DOI resolves) | Fabricated quotes, broken references | A real quote that doesn't support the claim | None |
| Cross-model disagreement | One model's quirks and flukes | What every model believes | Low, but shared corpora correlate errors |
| A human holding a receipt | Anything they actually check | Distributed bias; more than they have time for | None — the only judge fully outside the loop |
| An LLM re-checking itself | Little: it re-samples the prior that made the error | Its own trained-in beliefs | **Total — this rung is excluded by design** |

The model never adjudicates the standing of its own outputs. Asking it to would inherit the bottom row: the fabrications most likely to survive re-checking are exactly the ones the model believes. The project's own verification research found the same circularity in LLM verifiers generally — they rationalize from internal knowledge — and self-error-detection recall has been measured at 13.7% ([prior-art record](https://github.com/TheRealBillSiegler/epistemic-pipeline/blob/main/docs/research/2026-07-12-parametric-knowledge-encoding-prior-art.md)).

!!! warning "The floor nothing reaches"
    A bias shared by all models, your corpus, *and* you — a whole community's blind spot — is
    invisible to every rung of the ladder. No mechanism inside the system detects it.
    This is the same wall as [input one-sidedness](honesty.md#5-the-input-is-one-sided-by-construction),
    one level deeper, and it stays stated rather than solved.

## Where next

- What the numbers mean and every other known wall: [What the numbers mean](honesty.md)
- The ideas this page feeds into, including auditing a model's own knowledge: [Directions](../project/directions.md)
- How evidence is weighed once admitted: [Fusing evidence](../beliefs/fusion.md)
