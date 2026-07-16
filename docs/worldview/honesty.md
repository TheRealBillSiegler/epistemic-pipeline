# What the numbers mean

**Settledness is `1 − u`: how much distinct, recorded evidence backs a belief. It is not truth, and it is not confidence that the claim is right — it only says how much independent evidence you have looked at.** The system computes settledness from evidence you can inspect, by a rule you can replay. It does not compute whether that evidence adds up to something true. This page draws that line precisely, then lists every place reality has not caught up to the design yet — each with an open issue, so "known limit" never quietly becomes "forgotten limit."

## What settledness is

Every claim in the store carries an [opinion](../beliefs/index.md): belief `b`, disbelief `d`, uncertainty `u`. Settledness is `1 − u` — the share of the opinion that is *not* uncertainty.

`u` shrinks only when evidence accumulates from a **new, distinct root**. Ten mentions of one document do not shrink it ten times — [root-keyed fusion](store.md#provenance-knowing-where-evidence-came-from) collapses repeats of one source before they reach the belief. So settledness answers one question: *how much independent, recorded evidence have you looked at, on this claim?*

It does not answer: *is the claim true?* A claim can be highly settled and false — if every document you read about it happens to be wrong. A claim can be barely settled and true — if it is correct but you have only read one source on it. Settledness measures your evidence, not the world.

## The three commitments settledness rests on

These are the guarantees the number is allowed to lean on. Each is pinned by tests today; making the pipeline itself enforce them at every step is tracked in [#36](https://github.com/TheRealBillSiegler/epistemic-pipeline/issues/36).

- **Traceable.** Every opinion links back to the observations that built it — see [the drift timeline](store.md#the-drift-timeline). You can always ask "why does this claim sit here?" and get the evidence chain, not a shrug.
- **Replayable.** The revision rule `R` is [pure and deterministic](../concepts/state.md#r-revision-policy). Replaying the same evidence, in the same order, reproduces the same beliefs, byte for byte.
- **Deduplicated by root.** [Root-keyed two-tier fusion](https://github.com/TheRealBillSiegler/epistemic-pipeline/blob/main/docs/superpowers/specs/2026-06-23-worldview-subjective-logic-design.md#72-correlated-and-duplicate-sources) averages repeats of one canonical source and accumulates only across distinct ones. Re-importing one article twice does not make it look like two sources.

Traceable and replayable are structural — they hold by how the pipeline is built. Deduplication is a measured fix, not a structural guarantee: it closes the *exact-duplicate* case, and its own design spec names the *partially*-correlated case — a paraphrase with no machine-readable origin — as unclosed residue.

## The known walls

Six places where settledness means less than a bare "`1 − u`" reading suggests. None are hidden; each has an open issue.

### 1. One rater

Every confidence number in the store comes from one rating LLM. Its stated confidence mixes two things: what the document says, and the model's own prior belief about the claim. Ten documents rated by that one model do not give you ten independent opinions — they give you ten readings filtered through one shared judge.

Root-keyed fusion cannot see this, because it keys on the *document's* origin, not the rater. The rater rides along in the provenance string, invisible to the dedup logic. This is the meme-farm problem one level up: instead of one source repeated, it is one *judge* repeated across many sources. Settledness today reflects document count under one rater — not rater-independent evidence. [#35](https://github.com/TheRealBillSiegler/epistemic-pipeline/issues/35) tracks measuring the rater's prior contribution, by rating a fixed corpus with a second model family, and the structural fixes that could bound it.

### 2. Claim identity

A claim's id is its own sentence. `"Fiscal Q4 2024 = $2.1B"` and a paraphrase of the same fact are, to the store, two unrelated claims. Nothing in the pipeline asks "are these the same thing said two ways?"

Two failures follow. A paraphrase fragments one belief's evidence into several weak opinions, deflating settledness below what the total evidence supports. And a claim and its direct contradiction — "X is safe" and "X causes harm" — are unrelated coordinates that can each settle high, with no signal raised that they conflict.

[#33](https://github.com/TheRealBillSiegler/epistemic-pipeline/issues/33) tracks this. It is a one-way door: the belief store is append-only, so a wrong claim-identity design cannot be quietly patched later without a migration.

### 3. Calibration is unmeasured

"Settledness 0.8 predicts the claim is right 80% of the time" is the design's goal for the *projected probability* `P`, not a measured property of the system today. Calibration needs a reliability diagram: bucket beliefs by `P`, check how often the bucket is actually right, against ground truth the system never touched.

That measurement has real prerequisites the design had not stated until [#34](https://github.com/TheRealBillSiegler/epistemic-pipeline/issues/34) named them: a comparison baseline (so credit doesn't go to the LLM's raw confidence instead of the pipeline), labels from a source outside the app (the app's own stance is never-a-verdict, so it cannot label its own test set), and claim identity settled first (a calibration score computed per-string inherits problem 2 above). Nothing in the codebase runs this measurement today. Until it does, "0.8" is a number the formalism is built to make meaningful — not one that has been checked against reality.

### 4. Credibility weighting is disabled

The [Subjective Logic design](https://github.com/TheRealBillSiegler/epistemic-pipeline/blob/main/docs/superpowers/specs/2026-06-23-worldview-subjective-logic-design.md#71-grounding-the-credibility-number-the-biggest-open-risk) calls for scaling each source's evidence by a reliability number `P_R` — a replicated study should move belief further than an unsourced post. Grounding that number without circularity is unsolved: an LLM guessing "credibility: 0.9" is as manipulable as the source it is judging.

So `P_R` is fixed at `1.0` for every source — [the code names this explicitly](https://github.com/TheRealBillSiegler/epistemic-pipeline/blob/main/src/epistemic_pipeline/encodings/worldview.py): credibility weighting is a documented no-op, not a working feature. A meme and a meta-analysis currently move a claim by the same amount. This is production gate 2 in the design spec (§10) — the spec permits shipping without grounding *only if the gap is disabled and labeled*, which is the current state. [#34](https://github.com/TheRealBillSiegler/epistemic-pipeline/issues/34) tracks what a real measurement of this would need.

### 5. The input is one-sided by construction

If you feed the app your own notes, you get a quantified account of *what convinced you* — not an independent check on whether you should have been convinced. A personal note vault already reflects what you chose to read and save, so the evidence base is confirmation-biased before the app ever sees it. Settledness on a claim built from that vault says "you have accumulated this much evidence, from your own reading" — not "the world is this settled."

This is not a bug the pipeline can fix. It is a property of any evidence base built by one person choosing what to feed in. The honest fix is knowing which claim the number supports.

### 6. The faithfulness gate: measured, then deferred

A cited source can be quoted correctly and still not say what the claim attributes to it — misquoted, fabricated, or a wrong number, weighed exactly as honestly as a real citation. [#26](https://github.com/TheRealBillSiegler/epistemic-pipeline/issues/26) proposed a deterministic gate: before a claim's evidence counts, check that its quoted source text is actually present in the document.

The gate was [researched against the literature](https://github.com/TheRealBillSiegler/epistemic-pipeline/blob/main/docs/research/2026-07-01-faithfulness-gate-literature-research.md), then measured, then re-checked. Three passes, each narrowing what it can actually do:

- **The literature** (FActScore, GopherCite, AIS, and the Worledge et al. extractive-to-abstractive spectrum) confirms *faithfulness* — does the source contain the claim — is a separate question from *truth* — is the source right. A presence check can only ever answer the first. It also found presence-checking catches the *rarest* failure: on one citation benchmark (ALCE, on the ELI5 task), even the best models failed to fully support cited claims about half the time — and the cited passages **existed**. Presence was satisfied; the quote just didn't entail the claim. A string-match gate is blind to that failure, which the same research names as the dominant one.
- **The measurement**: 5 documents, 34 extracted claim-and-quote pairs, checked deterministically. Zero fabricated quotes. The first read of that number: a capable model, asked for a verbatim quote, doesn't invent one, so a gate that only catches invented quotes would reject nothing — don't build it.
- **The re-check**, run ten days later against that same reasoning, corrected it: 34 trials is too few to call the fabrication rate "zero." The statistics of small samples say a true rate as high as roughly 9% is still consistent with seeing zero fabrications in 34 tries. The re-check also found the measurement's own corpus and scoring script were never saved, so it cannot be rerun or checked against a future one.

The decision to defer stands, but not for the reason first given. It does not rest on fabrication being rare — that claim was overstated. It rests on the literature finding above: presence-only checking has a ceiling regardless of the fabrication rate. It catches a fabricated quote; it cannot catch a real, present quote that fails to support the claim it's attached to, which is the dominant way a citation goes wrong.

One more gap survives every pass. This gate — designed, measured, and re-checked, never built — only ever covered quotes *within* one document. The case that opened this issue was different: a fabricated statistic and a quote misattributed to an *external* source, never checked against that source at all. That surface was set aside early in the design and is still unguarded.

!!! warning "Honest status"
    No faithfulness gate runs today. A citation can be wrong in the source, wrong about the source,
    or attributed to the wrong source entirely, and the pipeline weighs it the same as a verified one.
    [#26](https://github.com/TheRealBillSiegler/epistemic-pipeline/issues/26) carries the full record,
    including the measurement's own re-examined limits.

## Why this page exists

A number that cannot say what it does not mean is not honest, no matter how carefully it is computed. Every wall above is a wall the system knows about and states plainly — not a gap discovered by a user after trusting the number too far. That is the standard this project holds itself to: the process can be shown, checked, and replayed, even where the result cannot yet be proven right.

## Where next

- [When the model is wrong](model-error.md) — hallucination, flawed training, and who is allowed to judge evidence
- [The belief store](store.md) — where the evidence behind every number actually lives
- [Beliefs as numbers](../beliefs/index.md) — the Subjective Logic math that turns evidence into `u`
- [The Subjective Logic design](https://github.com/TheRealBillSiegler/epistemic-pipeline/blob/main/docs/superpowers/specs/2026-06-23-worldview-subjective-logic-design.md) — §2 for the trust commitment, §7 for the hard parts, §10 for the production gates
