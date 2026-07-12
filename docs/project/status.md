# Project status

**The core pipeline is built and tested. One belief-quality fix has shipped. One proposed safety gate was measured, then deferred — and a later review found the measurement itself was too weak to justify that call. The remaining open issues mostly come from one internal review that went looking for ways the worldview app's numbers could lie.** This page is the ledger: what runs today, what was checked and set aside on purpose, and what is still undecided.

## Built

The **core pipeline** ([v1.1 design](https://github.com/TheRealBillSiegler/epistemic-pipeline/blob/main/docs/superpowers/specs/2026-05-14-epistemic-pipeline-v11-design.md)) ships six [encodings](../concepts/encodings.md) — Bayesian inference, STRIPS planning, forward-state search, MDP value iteration, an LLM-agent loop, and the worldview encoding. Every run keeps a full state trace, and the `epc` CLI replays, diffs, and scores a saved trace from the command line. The full test suite passes.

The worldview app's belief math — a [Subjective Logic opinion](../beliefs/index.md) per claim, and the revision rule that updates it — landed in two units: [#17](https://github.com/TheRealBillSiegler/epistemic-pipeline/issues/17) (the SL math itself) and [#18](https://github.com/TheRealBillSiegler/epistemic-pipeline/issues/18) (wiring it into the worldview `B`/`R`).

**Root-keyed fusion** ([#27](https://github.com/TheRealBillSiegler/epistemic-pipeline/issues/27)) fixed a real bug: settledness — how much the app treats a claim as backed by evidence — went up every time one source was counted twice, like a note re-ingested after an edit. The fix tags each piece of evidence with a canonical root id, then averages repeats of one root instead of adding them. Full account in [the belief store](../worldview/store.md#provenance-knowing-where-evidence-came-from).

Documents reach the store through **three ingestion paths** ([#8](https://github.com/TheRealBillSiegler/epistemic-pipeline/issues/8)): LLM extraction from a corpus, explicit authoring by a person, and a continuous path triggered on every note save.

## Measured, then deferred

[**#26**](https://github.com/TheRealBillSiegler/epistemic-pipeline/issues/26) asked a narrow question: before the pipeline weighs a claim's evidence, should it check that the claim's quoted source text is actually present in the document? A deterministic check can only prove *faithfulness* — the source contains the words — never *truth* — the source is right. That split is confirmed in the literature this issue researched (FActScore, GopherCite, AIS; full record in [the faithfulness-gate research](https://github.com/TheRealBillSiegler/epistemic-pipeline/blob/main/docs/research/2026-07-01-faithfulness-gate-literature-research.md)).

The team measured it anyway: 5 documents, 34 extracted claim-and-quote pairs, checked by a deterministic string match. Zero fabricated quotes. The gate was deferred — a check that fires on 0 of 34 trials looked like code that would never trigger.

!!! warning "Honest status — the deferral was re-examined and only partly holds"
    A 2026-07-11 review corrected the reasoning behind that call. Zero fabrications in 34 trials is not the same claim as "fabrication doesn't happen": by the rule of three, a true fabrication rate as high as roughly 8.8% per claim is still consistent with seeing zero in 34 tries. The measurement's own corpus and scoring script were never committed, so it cannot be rerun or compared against later. And the case that opened this issue — a fabricated statistic and a misattributed quote — was an *external*-citation failure; the 34-trial measurement only tested *intra-document* quoting, a different surface that was never itself measured. The decision to defer stands, but the evidence for it was weaker than the original writeup claimed. Full record in [the honesty page](../worldview/honesty.md#6-the-faithfulness-gate-measured-then-deferred) and on the issue.

## Open

Most of the issues below trace back to one internal review, run on 2026-07-11, that looked for ways the worldview app's settledness number could be wrong without anyone noticing. Its findings extend the settledness-honesty scope that epic [#28](https://github.com/TheRealBillSiegler/epistemic-pipeline/issues/28) tracks, alongside the dedup and faithfulness work above.

Deciding what to build next follows one rule, sized to how reversible the decision is:

- **Default: ship the simplest option.** Most calls need no separate write-up — build the plain version, defer the rest until a real case demands it. This is the project's evidence-triggered build rule; [#26](https://github.com/TheRealBillSiegler/epistemic-pipeline/issues/26)'s own gate followed it before the correction above.
- **Medium stakes: one measurement.** A call that's cheap to reverse gets a single check before shipping — the way #26's 34-trial measurement was meant to settle whether the gate was worth building, even though the check itself turned out too small.
- **One-way doors: literature review, then a memo.** [#33](https://github.com/TheRealBillSiegler/epistemic-pipeline/issues/33) and [#34](https://github.com/TheRealBillSiegler/epistemic-pipeline/issues/34) both invoke this explicitly as "Tier 2" — a literature pass, a design memo, and a stated falsifier, before any code lands. Both are one-way doors for the same reason: the belief store is append-only, so a wrong claim-identity or calibration design can't be quietly patched later, only migrated.

| Issue | What | State |
|---|---|---|
| [#5](https://github.com/TheRealBillSiegler/epistemic-pipeline/issues/5) | Worldview app tracking epic — closes when #9 and #10 land | Open |
| [#9](https://github.com/TheRealBillSiegler/epistemic-pipeline/issues/9) | FastAPI server and browser UI for the worldview app | Open |
| [#10](https://github.com/TheRealBillSiegler/epistemic-pipeline/issues/10) | README rewrite and demo corpus for the worldview app | Open |
| [#22](https://github.com/TheRealBillSiegler/epistemic-pipeline/issues/22) | A garbage LLM response silently marked a note as ingested | Fix in review ([PR #38](https://github.com/TheRealBillSiegler/epistemic-pipeline/pull/38)) |
| [#26](https://github.com/TheRealBillSiegler/epistemic-pipeline/issues/26) | Faithfulness gate | Deferred with recorded rationale (see above) |
| [#28](https://github.com/TheRealBillSiegler/epistemic-pipeline/issues/28) | Settledness-honesty epic (dedup + faithfulness) | Open |
| [#30](https://github.com/TheRealBillSiegler/epistemic-pipeline/issues/30) | Replaying a trace uses the old cumulative rule, not root-keyed fusion — replay can reproduce the inflation #27 fixed in the live store | Open |
| [#31](https://github.com/TheRealBillSiegler/epistemic-pipeline/issues/31) | Authoring a claim left no record in the drift timeline | Fix in review ([PR #38](https://github.com/TheRealBillSiegler/epistemic-pipeline/pull/38)) |
| [#32](https://github.com/TheRealBillSiegler/epistemic-pipeline/issues/32) | The agent loop cannot tell a malformed LLM rating from an empty one | Open |
| [#33](https://github.com/TheRealBillSiegler/epistemic-pipeline/issues/33) | Claim identity: two sentences that state one fact get two unrelated ids, so evidence for one belief can fragment or a claim and its contradiction can both look settled | Open |
| [#34](https://github.com/TheRealBillSiegler/epistemic-pipeline/issues/34) | The planned calibration check has no comparison baseline and no label source that isn't circular — it can't yet attribute a result to the pipeline | Open |
| [#35](https://github.com/TheRealBillSiegler/epistemic-pipeline/issues/35) | Every rating comes from one LLM, so many documents can share that model's prior instead of being independent evidence — root-keyed fusion can't see this | Open |
| [#36](https://github.com/TheRealBillSiegler/epistemic-pipeline/issues/36) | The `(O, E, B, R)` invariants are enforced by convention and tests, not checked by the pipeline itself | Open |
| [#37](https://github.com/TheRealBillSiegler/epistemic-pipeline/issues/37) | A docs site that explains the whole system with diagrams — this page is part of that site | Open |

## Where next

- [What the numbers mean](../worldview/honesty.md) — the full epistemic write-up of every wall on the settledness number, including #26, #33, #34, and #35
- [The encodings](../concepts/encodings.md) — what each of the six encodings proves
- [The belief store](../worldview/store.md) — where root-keyed fusion actually lives
