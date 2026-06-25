# Worldview App — UI Design (a window on the pipeline)

**Date:** 2026-06-24
**Status:** Proposed. The browser app for the worldview encoding. Terminal artifact of the 2026-06-24 design brainstorm.
**Scope:** How a person uses the pipeline on their own notes — point it at a vault, see what they believe and how firmly, run a new article by it, and keep their notes coherent. Not the belief math (that is the [SL design](2026-06-23-worldview-subjective-logic-design.md)).
**Depends on:** [SL design](2026-06-23-worldview-subjective-logic-design.md); store (#6, PR #12); ingestion (#8, PR #16); [credibility + landscape research](../../research/2026-06-24-worldview-credibility-and-landscape.md). Supersedes the ordering in the [earlier UI plan](../plans/2026-06-24-worldview-ui-plan.md), which `writing-plans` will re-plan against this spec.

---

## At a Glance

You point the app at your notes — say, an Obsidian vault. The pipeline reads them, works out what you seem to believe and how firmly, and shows you that worldview honestly: where you are sure, where you only think you are sure, and where your own notes pull both ways. Then you hand it a new article and ask, *"what would this do to me?"* It tells you exactly which beliefs would move and why — before you commit — and offers to fold the source back into your notes so what you believe and what you have written stay in step.

**The law (read this first):** the app is a **window**; the **pipeline applies the rigor**. The app never judges, scores, or revises. It only shows what the pipeline computed. We make that a structural fact, not a promise: the app has no belief logic, so it *cannot* fake rigor. See [§2](#2-the-law-the-app-is-a-window-the-pipeline-applies-the-rigor).

**The hero interaction** is "run-by": drop one new thing and see its effect on your worldview before you commit. Once the app has *read* the new thing, that effect is exact — the revision rule `R` is pure, so the preview *is* the commit, bit-identical, no surprise. (Reading the article is the one step the app does fresh each time.) See [§5.2](#52-run-by--the-front-door).

**The headline only this architecture can show:** "I haven't looked into this" is *not* "my notes pull both ways." A single percentage hides that difference; Subjective Logic carries it as an explicit uncertainty. The whole UI is built to make it visible.

**Done when:** Unit 1 ([§10](#10-migration-decomposition-with-standalone-value)) ships a running window over the existing belief store, the run-by preview lands (Unit 2), and each later view appears only once the pipeline layer behind it genuinely computes its result.

---

## 1. What it is for

**Worldview is a sense-making tool for your data.** It turns what you've collected — notes, reports, tables — into the beliefs your data actually supports, shows how firmly each is supported, and is honest about what you've never really looked into. It helps you make sense of new information: what it means for what you already hold, and how you should update. And it turns that honesty on *you* — it exposes beliefs held more firmly than the evidence earns: the echo repeated without question, the conviction resting on one weak source, the claim your own data contradicts. **It never tells you what is true. It shows you what your evidence supports, and how sure you can honestly be — and you decide.**

The engine is **corpus-agnostic**: a personal vault is the first target, business/client data a later skin — same `(O, E, B, R)`. And data never speaks for itself, so the engine separates **measurement** (what the data literally says — "Q4 = $2.1B") from **interpretation** (the claim someone reads it to support — "growth is sustainable"). Interpretation is the sense-making step: a *recorded, uncertain, contestable* reading — proposed with its warrant and its alternatives, never asserted as fact. Over-reading the data is the number-one unjust belief, and separating the two is how the tool exposes it.

This combination is the open niche. The [landscape research](../../research/2026-06-24-worldview-credibility-and-landscape.md#part-b--positioning-the-open-niche) found no tool that has all four of:

- per-claim **graded uncertainty** that tells *unexamined* from *split*,
- a per-claim **replayable evidence trail**,
- beliefs **inferred from your data** (not hand-typed predictions), and
- a **deterministic, replayable update** over a recorded reading of the new information (the preview equals the commit).

Argument maps have the claim graph but no confidence. Forecasting tools have confidence-over-time but no corpus and no evidence links. Note tools detect some contradictions but carry only coarse confidence. We are the combination.

---

## 2. The law: the app is a window; the pipeline applies the rigor

The rigor must come from the pipeline, never from the app or a stray LLM call in the UI. We enforce that **structurally**, so it is an invariant, not a discipline:

- **Engine side (the pipeline).** Reads the corpus, runs the stack, and *persists* its results — beliefs, evidence links, contradictions, the whole state trace — to the store.
- **Window side (the app).** Read-only over that store. No belief math, no scoring, no model call of its own. It can ask the engine to *do* something (ingest, preview, commit) and render what comes back, but it has no faculty to judge.

So if a number is on screen, the pipeline computed it. The app *cannot* fake rigor because it has nothing to fake it with.

**The consequence for how we build.** You never "add a view." You make the pipeline **actually compute** a rigor stage and persist it; the window then reflects it. The work is pipeline depth, proven one stage at a time ([§7](#7-the-build-path-one-pipeline-layer-at-a-time)). And the corollary: **the window shows exactly the rigor the pipeline applies — never more.** No view claims a judgment the pipeline has not really made.

The alternative — an app that drives the pipeline and computes results inline — is rejected for exactly this reason: it hands the rigor back to the UI layer, where it can drift into a vibe.

---

## 3. Plain language (the terminology contract)

The user is not a Subjective-Logic mathematician. Every term on screen is plain. The formalism keeps the rigor; the words carry the clarity. This table is binding on the UI copy.

| What the pipeline calls it | What the screen says |
|---|---|
| corpus / vault | **your notes** — the body of notes the app reads |
| claim / concept | a **belief** (a single statement that can be true or false) |
| projected probability `P` | **how supported** — a percentage; the weight of claims for vs against, from named sources |
| uncertainty mass `u` | **how settled** — shown as `1 − u`, so plenty of agreeing evidence reads "well-settled" and none reads "you haven't looked into this" |
| vacuous opinion (`u = 1`) | "**you haven't looked into this**" |
| balanced (`u ≈ 0.5`, `P ≈ 0.5`) | "**your notes pull both ways**" — genuinely split, not unexamined |
| belief `b` / disbelief `d` | support **for** / support **against** |
| evidence / observation | "**what a note says**" / a **source** |
| the model / LLM | "**the reader**" — the AI that reads your notes |
| evidence link / `delta` | "**what moved it**" — the change one source made |
| ontology / concept set | "**the things you have beliefs about**" / your topics |
| revision `R` | **update** |
| reliability discount / `P_R` | "**how much a source counts**" |
| contradiction (meta layer) | "**your notes disagree here**" |
| ontology gap (Power norm) | "**new territory**" — a note raised something new |
| run-by / preview | "**try it out**" — see what this would change |
| state trace / replay | "**the history**" — how this belief got here |

Every term is defined once, on first use, in the UI itself.

---

## 4. What the user navigates: the claim dossier

The atomic object is **one belief** (one claim). Each note is broken into claims; each belief gets a small case file — the **dossier** — which is just its `(O, E, B, R)` slice, in plain words:

- **The belief** — the statement itself, plus *how supported* and *how settled* it is.
- **The evidence** — what your notes say for it and against it, each tagged with where it came from (`E`).
- **How it got here** — the history: every source that moved it, and by how much (`R` over the trail).
- **Where it sits** — its topic, and any flags: "your notes disagree here" or "new territory" (`O`, norms, meta).

The home screen is the list of beliefs; opening one shows its dossier. That is the pipeline made walkable, and it stays legible: *here is a thing you believe, here is why, here is what argues against it, here is how well your evidence supports it.*

---

## 5. Two ways information meets the pipeline

### 5.1 Sync (your standing notes)

Your notes are the standing evidence. Each note commits into `E`; beliefs settle into `B`. Ingestion already exists (#8): each note becomes a recorded source (a confidence-vector observation, in engine terms), and `R` accumulates it. The app reads the resulting beliefs.

### 5.2 Run-by (the front door)

This is the hero. You hand the pipeline **one candidate** — an article — and ask what it would do, *before committing*.

**Why the preview is exact, not a guess.** `R` is pure. The engine extracts the article into a *recorded candidate observation*, computes `B' = R(B, candidate, O)` against your real vault-derived state, and shows the diff **without appending it**. Because the same recorded candidate and the same pure `R` are used at commit, **what you preview is exactly what you commit.** Honest caveat: the LLM reading the article is the one non-deterministic step; once it has produced the recorded candidate, everything downstream is exact, and the preview you see and the commit you accept are bit-identical (they share that one candidate). Re-reading the same article fresh could extract slightly different claims — that is a separate run.

**The impact report**, in plain words, sorts the effect into the cases that matter:

- **Confirms** — "you already leaned this way; now you are more settled." (more evidence-for)
- **New territory** — "you had no belief about this yet; this opens one." (the candidate names concepts not yet in your worldview — a preview-time difference, computable here; *not* the Power norm, which is inert while the ontology auto-grows — see [§9](#9-the-hard-parts-stated-honestly))
- **Challenges** — "this pushes against something you hold; how supported it is should *drop*." (evidence-against)
- **Contradicts** — "this directly disagrees with your note from before." (the Meta layer)
- **Reverses** — "enough pushback to flip your lean."

You then **accept** (append the candidate to `E`; beliefs update for real) or **reject** (discard it). Mechanically, preview is just *"revise over a candidate observation and do not append it"* — nearly free given pure `R`.

### 5.3 Reconciling the vault (write-back) — additive-only

When your beliefs update but your notes still say the old thing, your notes and your evidence-weighted beliefs have drifted apart. Closing that loop is valuable — but the vault is the user's data, so the app is conservative. **Decision: additive-only.**

On accept, the app:

- **saves the new source as a note** (so the evidence is preserved in the vault), and
- **suggests** non-destructive annotations on challenged notes (e.g. a callout: "⚠ challenged by [new source] on 2026-06-24"), applied only on the user's confirmation.

It **never rewrites existing note content** and never auto-edits without confirmation. (Rejected: full reconciliation that edits stated confidences or claims — real data-loss risk, deferred.) This matches the only shipping precedent found — VaultForge's add-only, suggest-don't-write stance ([research](../../research/2026-06-24-worldview-credibility-and-landscape.md#part-b--positioning-the-open-niche)). The *belief* update is the pipeline's rigor; the vault suggestion is a derived convenience the user controls.

---

## 6. Architecture

A read-side and an engine-side, split so the window has no brain.

- **Engine** = the pipeline + the belief store (#6). It owns all computation: extraction, classification, revision, contradiction detection, the preview diff. It persists beliefs, evidence links, anomalies, and the trace.
- **Window** = a local read-only HTTP server (`worldview-server`) + a static page. It exposes the store over HTTP and triggers engine operations (ingest, preview, commit). It holds no belief logic.

Beliefs are read by replaying `R` over the recorded evidence (no store schema change), matching the SL design. One replay pass builds every concept's opinion in `O(evidence)`, so the belief list — including each belief's honest uncertainty — is cheap to render. The expensive `O(N·E)` case (one replay per ingest) is not on the read path; caching `(r, s)` on the claims row stays the documented upgrade path if a corpus ever makes the single replay slow.

The server spine, endpoints, and the app-factory-for-testability pattern are detailed in the [UI plan](../plans/2026-06-24-worldview-ui-plan.md); `writing-plans` will re-plan it against this spec (the run-by preview becomes Unit 2, ahead of passive before/after).

---

## 7. The build path: one pipeline layer at a time

Each unit makes a pipeline layer genuinely compute its result, then the window reflects it. The order, owned from the literature and the layer dependencies:

| Pipeline layer | What the window shows | Live in the worldview path today? |
|---|---|---|
| Tool / Environment | connect a vault, list notes | **new** (vault reader) |
| Cognitive Process | the claims found in a note | **partial** — LLM extraction exists, thin |
| Pipeline `(O,E,B,R)` | the belief + its dossier + honest uncertainty; the run-by preview | **live** |
| Meta-Epistemic | "your notes disagree here" | exists generically, **not wired** to worldview |
| Norms | "new territory" | the preview-time concept diff is live in run-by; the Power-norm check over committed notes is **inert** while the ontology auto-grows (deferred) |
| Credibility (stage 3) | "this counted more — it cites a source" | **deferred** (slot exists, off) |

Build order of the rigor-stage spine: the `(O,E,B,R)` window first, then the run-by preview, then the drift history, then real-LLM vault ingestion, then contradictions (wire the Meta layer), then evidence credibility, then calibration. Contradictions come before credibility because conflict is computable from the existing `r`/`s` counts with no new external signal, while credibility needs the grounding work in [§8](#8-stage-3--evidence-credibility-how-honestly). Two units sit off this spine and slot in by dependency, not sequence: write-back (Unit 7, after vault + accept) and scale (Unit 8, after the window). The contradictions-after-ingestion placement is a sequencing choice, not a dependency — contradictions are independent of vault ingestion and could land earlier (see [§10](#10-migration-decomposition-with-standalone-value)).

---

## 8. Stage 3 — evidence credibility (how, honestly)

"Rank the evidence" is the soul of the rigor and the easiest thing to fake. The [credibility research](../../research/2026-06-24-worldview-credibility-and-landscape.md#part-a--decisions-grounding-stage-3-evidence-credibility) settles how to do it without faking it. Summary of decisions C1–C6:

- **C1 — classify, then weight.** An LLM names the evidence *type* (with a quoted justification); a fixed, inspectable policy maps type → reliability. The LLM never emits the number. Subjective Logic leaves that number open by design (EBSL's discount `g` is a free function), so a policy table fills a slot the formalism intends to be filled externally. GRADE is the template, and its transparency is the published defense.
- **C2 — set the numbers by ranking, not by hand.** Rank the types; rank-order-centroid (ROC) weights convert the ranking into numbers by a fixed formula. You defend an ordering; the formula does the rest.
- **C3 — coarse source-type taxonomy**, not a study-design hierarchy (evidence hierarchies are question-type specific and do not transfer to general claims).
- **C4 — type only.** The LLM classifies *type*, which it does reliably (and reproducibly at low temperature). Support direction comes from the SL `r`/`s` rating, **never** a separate LLM "does this support the claim?" verdict — zero-shot stance detection is weak, order-biased, and prone to rationalizing gaps.
- **C5 — uniform reliability first.** v1 weighs all evidence equally; that is a literature-backed competitive baseline, not a cop-out (Bayesian bootstrapping). The graded policy is an upgrade.
- **C6 — calibration is the judge.** The graded policy stays labelled "transparent, not yet validated" until proper-scoring on resolved claims shows it improves accuracy.

In the dossier this reads plainly: each piece of evidence shows *its kind* and *why it counted what it counted* — "this counted more: it cites a source (here is the line); that counted less: it is a personal note."

---

## 9. The hard parts (stated honestly)

- **Credibility is auditable before it is correct.** A weight that traces to (recorded type + quote + fixed policy) is transparent today. Whether the weight is *right* is calibration, which is deferred (C6). The UI must not imply graded evidence is validated before it is.
- **Extraction quality.** Breaking a note into claims is an LLM step; it is non-deterministic and imperfect. The pipeline records its output so `R` stays pure and replayable, but a bad extraction yields a bad belief. Honest framing in the UI ("the reader read this as…") rather than false authority.
- **Scale.** A pre-existing vault can be 5000+ beliefs on day one. The answer is a ranked, searchable, windowed list — *not* hierarchical clustering, which has nothing to cluster on (concepts are flat strings with no taxonomy). Clustering stays an optional later enhancement.
- **Vault safety.** Write-back is additive-only and confirmation-gated ([§5.3](#53-reconciling-the-vault-write-back--additive-only)). Never auto-rewrite a user's notes.
- **User-authored beliefs sit outside the evidence trail.** A claim the user states directly has a stored confidence but no observation, so it does not replay and has no drift history until a document rates it. The UI shows these as a distinct kind ("you stated this") rather than pretending an evidence trail exists.

### 9.1 The honesty ceiling — omission, and the walls

The pipeline can be near-fully honest about the evidence it *has*. It cannot be fully honest about what it *hasn't seen*. Verified in the [honesty research](../../research/2026-06-25-honest-pipeline-omission-frontier.md). The ceiling is **honesty-as-process, not verdict**: coherence with its own evidence is reachable; correspondence with truth is not guaranteed by any internal process. The app claims the first and disclaims the second.

Three walls the UI must *name*, not hide:

- **The system's own confidence can't find its worst blind spots.** Confident-but-wrong beliefs sit far from the boundary, so the uncertainty mass misses unknown-unknowns by construction. "I can be confidently wrong" is a real state.
- **One-sided-but-true beats every falsehood check.** A belief can be fully sourced, every claim true, and still be a lie of selection. Truth-checking cannot catch it; it needs an explicit one-sidedness/coverage check — for which no validated method yet exists (the open frontier).
- **No internal process guarantees a correct verdict** over incomplete, ambiguous information.

So omission-honesty is an **explicit, separately-measured, never-finished target**, not a box to tick. The implementable levers — a sufficiency signal separate from the belief, three-axis abstain (vague query / thin belief / values), a disconfirmation-first scoring scaffold, an active question/evidence-gathering loop — are catalogued in the research and slated as the honesty track ([§12](#12-in-design-this-sessions-threads)).

---

## 10. Migration (decomposition with standalone value)

Each unit states what lands, what works after it alone, and what it needs. Independent unless a dependency is named.

**Unit 1 — The window spine.**
- *Ships:* read-only `worldview-server` + static page; the belief list and the claim dossier with honest uncertainty; the no-LLM write paths (state a belief; drop a direct rating).
- *Standalone value:* a running app where you watch how-supported **and** how-settled move, and see *unexamined* differ from *split*, with zero LLM setup.
- *Depends on:* store (#6), ingestion (#8) — both shipped.

**Unit 2 — Run-by / preview (the front door).**
- *Ships:* a preview endpoint that runs `R` over a *candidate observation* without appending it, returns the impact report, and an accept/reject control. Live cases: **confirms / new territory / challenges / reverses** (all computable from `R` plus a concept-set diff). The **contradicts** case is stubbed until Unit 5 wires the Meta layer.
- *Standalone value:* run a directly-entered candidate rating by your worldview and see the exact, reversible diff — keep it or not. (The headline experience of dropping a real *article* needs the extraction step in Unit 4; with Unit 1 alone the candidate is hand-supplied.)
- *Depends on:* Unit 1. Real-article input depends on Unit 4.

**Unit 3 — Drift history.**
- *Ships:* a per-belief timeline of confidence over time with a marker per evidence event, reconstructed by walking *backward* from the current cached confidence (correct for user-authored starts).
- *Standalone value:* the signature view — how a belief got here.
- *Depends on:* Unit 1.

**Unit 4 — Vault + real-LLM ingestion.**
- *Ships:* a vault-folder reader and a concrete real-model `RatingLLMInterface` (with key handling via env); the document→candidate extraction path for both sync and run-by.
- *Standalone value:* point at a real Obsidian vault, and complete the run-by hero — drop a real *article* and preview its effect (the article-input half of Unit 2).
- *Depends on:* Unit 1; completes Unit 2's article path.

**Unit 5 — Contradictions (wire the Meta layer to worldview).**
- *Ships:* worldview-specific anomaly detection (heavy `r` *and* `s` on one belief = conflict; sign reversal = flip), surfaced as "your notes disagree here."
- *Standalone value:* contradictions across your notes become actionable prompts.
- *Depends on:* Unit 1; independent of Units 2–4.
- *Note:* "new territory" is already covered at preview time in Unit 2 (a concept-set diff). The Power-norm adequacy check is **not** shipped here — it is inert while ingestion auto-grows the ontology (every rated claim becomes a concept before `R` runs), so it would surface a flag the pipeline never computes, which [§2](#2-the-law-the-app-is-a-window-the-pipeline-applies-the-rigor) forbids. A real adequacy signal needs a locked-ontology mode, deferred until a unit calls for it.

**Unit 6 — Evidence credibility (stage 3, C1–C4).**
- *Ships:* LLM evidence-type classification → ranked types → ROC weights → SL discount; the dossier shows "counted more/less, and why."
- *Standalone value:* graded evidence, every weight traceable to (type + quote + policy). Transparent, pre-calibration.
- *Depends on:* Unit 4 (LLM), Unit 1.

**Unit 7 — Vault write-back (additive-only).**
- *Ships:* on accept, save the source as a note and suggest non-destructive annotations on challenged notes, applied on confirmation.
- *Standalone value:* the belief↔notes coherence loop, safely.
- *Depends on:* Unit 4 (vault), Unit 2 (accept).

**Unit 8 — Scale.**
- *Ships:* server-side ranking/pagination + client search + windowed rendering for 5000+ beliefs.
- *Standalone value:* a full vault export stays navigable.
- *Depends on:* Unit 1.

**Unit 9 — Calibration (the judge; verification gate).**
- *Ships:* proper-scoring (Brier/log, Murphy decomposition) over claims that later resolve; the go/no-go for trusting graded credibility (C6).
- *Standalone value:* evidence that the credibility policy earns its keep — or does not.
- *Depends on:* Unit 6 (the graded policy to test), Unit 2 (the commit path that applies graded updates), and Unit 3 (the per-belief trajectory the scoring reads). Resolved-claim outcomes come from user resolution or the drift trail.

---

## 11. Gates before calling it "trustworthy"

The same standard as the SL design: trust lives in the process, not the verdict. Do not present the app as giving validated, credibility-weighted beliefs until:

1. **Uncertainty is shown honestly** — the *unexamined vs split* distinction is visible, not collapsed to one number (Unit 1).
2. **Graded credibility is labelled "not yet calibrated"** until Unit 9 measures it (C5, C6).
3. **The vault is never auto-rewritten** — write-back stays additive and confirmation-gated (§5.3).
4. **Every on-screen number traces to a pipeline computation** — the §2 law holds in code (no rigor in the window).
5. **Omission is named, not hidden** — the app surfaces "I might be missing something," "this rests on a choice I made," and "I can be confidently wrong," and never issues a true/false verdict ([§9.1](#91-the-honesty-ceiling--omission-and-the-walls)).

Until then the app is an honest window on a partially-built engine — the right shape, openly bounded — not a finished product that "tells you what to believe."

---

## 12. In design (this session's threads)

Settled in direction and being folded in; they extend, not replace, §§1–11. Each gets full unit treatment in the next plan pass — recorded here so the spec stays ahead of the build, honestly.

- **Validation = weigh and gather, never a verdict.** "Validate this" means: weigh new information against your evidence, optionally *gather more* (including external sources, as weighted evidence with their own credibility), and show the better-supported belief with honest uncertainty. The app never stamps a claim true or false. External evidence-gathering is a gated later unit.
- **Insights (expose-unjust) as a computed layer.** Structural observations over `(O, E, B, R)` + the trace — shared-source fragility, unnoticed tensions, confident-but-thin clusters, dependency chains — each a real query, never an LLM hunch. A unit alongside contradictions (§5).
- **Measurement → interpretation → belief** in the evidence model. Structured data (tables) needs an explicit, recorded, contestable interpretation step before it becomes a claim ([§1](#1-what-it-is-for)). This is the heavier ingestion front-end the business/data corpus needs; the personal/text path stays the lean first target.
- **The omission-honesty track** ([§9.1](#91-the-honesty-ceiling--omission-and-the-walls)): a sufficiency signal, three-axis abstain, disconfirmation-first scoring, an active evidence-gathering loop, and the (still-unsolved) one-sidedness detector. Each becomes a unit once its pipeline signal is real.

---

## References

- Belief math: [Worldview Encoding — Subjective Logic Design](2026-06-23-worldview-subjective-logic-design.md)
- Stage-3 grounding + niche: [Worldview app: evidence-credibility grounding and prior-art landscape](../../research/2026-06-24-worldview-credibility-and-landscape.md)
- Honesty ceiling / omission frontier: [How honest can the pipeline be?](../../research/2026-06-25-honest-pipeline-omission-frontier.md)
- Server spine detail: [Worldview Browser UI Implementation Plan](../plans/2026-06-24-worldview-ui-plan.md)
