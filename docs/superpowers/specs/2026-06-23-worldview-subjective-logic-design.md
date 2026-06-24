# Worldview Encoding — Subjective Logic Design

**Date:** 2026-06-23
**Status:** Proposed. Next iteration of the worldview encoding. Supersedes the v1.1 "renormalize over the latest vector" revision function.
**Scope:** The belief representation `B` and revision function `R` for the worldview encoding. Grounded in [the formalism research](../../research/2026-06-23-belief-revision-formalism-research.md).
**Depends on:** [WorldviewRevision encoding (v1.1)](2026-05-14-epistemic-pipeline-v11-design.md), PR #14.

---

## At a Glance

The worldview encoding lets a reader's beliefs change as they read documents. v1.1 shipped a thin version: each document produces a confidence vector, and the revision function just renormalizes the newest one. That version forgets any concept a new document fails to mention, ignores how trustworthy a source is, and cannot tell "I have no evidence" apart from "the evidence is balanced."

This document replaces that revision function with **Subjective Logic (SL)**. A belief becomes an *opinion* that carries an explicit amount of ignorance. New evidence is *accumulated*, not overwritten, and each source's influence is *scaled by its credibility*. The math is closed-form and deterministic, so the pipeline's purity and replay guarantees still hold.

**What we claim, precisely.** We do **not** claim SL is the best possible formalism in the abstract. We claim something narrower and provable: *given the five requirements below and the determinism constraint, SL satisfies all of them and strictly dominates every alternative we considered, each of which fails a specific, named test.* The honest boundary of that claim is stated in [§7](#7-the-hard-parts-stated-honestly).

**Why a user can trust it.** Not because the math is infallible. Because every belief it reports is **calibrated, uncertainty-annotated, traced to its evidence, and deterministically replayable** — and because it says "I don't know" when it doesn't, instead of inventing a number. See [§2](#2-the-trust-commitment-read-this-first).

**Done when:** the validation plan in [§8](#8-validation-how-we-prove-trust-empirically) passes — calibration, replay, discounting ablation, and the adversarial "meme-farm" test — and the production gates in [§10](#10-gates-before-production) are cleared.

---

## 1. The requirements

A worldview updater must do five things. Each is stated plainly, with the failure it guards against.

- **(a) Proportion confidence to evidence.** A belief backed by ten replicated studies should be held more firmly than one backed by a single blog post. *Guards against:* overconfidence from thin evidence.
- **(b) Mark "unverified" as different from "balanced."** "I have no evidence about X" and "I have equal evidence for and against X" both land near probability 0.5, but they are not the same state. The first should be easy to overturn; the second should not. *Guards against:* mistaking ignorance for genuine uncertainty.
- **(c) Weight evidence by source credibility.** A replicated, peer-reviewed, independently verifiable result must move belief far more than an unsourced social-media claim. *Guards against:* a loud, low-quality source drowning out a careful one.
- **(d) Do not erase a belief on omission.** If today's document says nothing about X, the reader's belief about X should persist, not vanish. *Guards against:* amnesia — the v1.1 bug.
- **(e) Treat disconfirming evidence as first-class.** Evidence *against* a claim is recorded directly, never discarded or normalized away. *Guards against:* confirmation dynamics and the Zadeh failure (see research, "Failure modes").

Plus one hard engineering constraint, inherited from the pipeline:

- **(D) `R` is pure and deterministic.** `R(B, e, O) → B'` is a closed-form function with no side effects, and replaying it on a recorded trace reproduces the result byte-for-byte.

---

## 2. The trust commitment (read this first)

The goal is a tool a person trusts to update their worldview. That goal is dangerous if read as "an oracle that tells you what to believe." An oracle that asserts is precisely what a rigorous epistemic tool must not be — it is the failure mode this whole project exists to avoid.

So we make the trust concrete and *earnable*, not assumed. The pipeline is trustworthy to the exact degree that it is:

1. **Calibrated.** When it reports probability 0.8, the thing is true about 80% of the time. This is *measured*, not promised (see [§8](#8-validation-how-we-prove-trust-empirically)).
2. **Honest about ignorance.** Every belief carries its uncertainty mass `u`. When `u` is high, the system says "I don't have enough evidence," rather than fabricating 0.5. Requirement (b) is what makes this possible.
3. **Traceable.** Every belief links to the evidence that produced it and the credibility weights applied. The state trace is already preserved as a hard invariant. A user — or an auditor — can see *why* a belief moved.
4. **Replayable.** Because `R` is pure and deterministic, anyone can re-run the update and get the same answer. There is no hidden reasoning. Requirement (D).
5. **Even-handed.** Disconfirming evidence is represented, not suppressed. Requirement (e).

The system therefore does not "tell you what to believe." It **shows you a defensible belief, how much evidence stands behind it, where that evidence came from, and how confident you should be** — and you can inspect or override it. The trust lives in the *process*, which we can prove and measure. It does not live in the *verdict*, which is always provisional. This is the same standard the project's own reasoning rules demand of any careful agent: proportion confidence to evidence, mark the unverified as unverified, and never let easy assertion stand in for warrant.

---

## 3. The proof: why SL, and why not the others

This is a **dominance** argument, not a claim of absolute optimality. We fix the requirement set `{(a),(b),(c),(d),(e)}` and the determinism constraint `(D)`, fix the candidate set from the [research](../../research/2026-06-23-belief-revision-formalism-research.md), and eliminate each candidate by a specific, citable failure. SL is the survivor.

### Lemma 1 — A scalar belief cannot satisfy (b)

Requirement (b) demands that two states with the *same* point estimate but *different* evidential support be distinguishable. A representation that stores one real number per claim (a point probability, or a bare log-odds) has exactly one degree of freedom. It cannot encode both the estimate and the amount of evidence behind it. A function that maps every belief state to a single real number is not injective on the property (b) needs. **Therefore any scalar-belief representation fails (b).**
→ Eliminates **point-probability Bayes** and **bare log-odds / weight-of-evidence**. (Weight-of-evidence is excellent for (a), (c), and (e); but the moment you add the precision/count it needs to satisfy (b), it *becomes* the Beta `(r, s)` representation — i.e. it is subsumed, not separate.)

### Lemma 2 — AGM cannot satisfy (a)

AGM belief states are deductively closed *sets of accepted sentences*. Beliefs are in or out; there are no degrees. So AGM cannot proportion confidence to evidence strength at all. **Fails (a) by construction.**
→ Eliminates **AGM** for graded belief. (Its revision operators remain relevant one level up, at the meta-layer that reframes the ontology `O` — but that is not the belief updater.)

### Lemma 3 — Dempster's rule of combination is non-robust under conflict

Dempster's rule normalizes conflict away (divides by `1 − K`). Under high conflict this yields the **Zadeh counterexample**: two sources that agree a hypothesis is *unlikely* can combine to full belief in that very hypothesis (worked arithmetic in the research). This discards conflict rather than representing it — the opposite of requirement (e) — and the failure is catastrophic, not marginal.
→ Eliminates **Dempster's rule as `R`.** Note this rejects the *combination rule*, not the DS *representation*; SL is a descendant of DS that lets us pick a non-normalizing fusion operator instead.

### Lemma 4 — Credal sets fail (a) and (D) as the update rule

Credal sets represent ignorance ideally (intervals), so they are the right *yardstick* for (b). But as the working update they have two disqualifying pathologies: **belief inertia** (a vacuous prior stays vacuous after conditioning — the agent cannot learn from complete ignorance, violating (a)) and **dilation** (conditioning can *widen* a sharp posterior). And exact total-uncertainty quantification over a credal set is NP-hard, violating (D)'s "cheap and deterministic."
→ Eliminates **imprecise probability / credal sets as `R`.** Retained as the conceptual yardstick for (b) only.

### Lemma 5 — SL satisfies all five plus (D), and dominates bare Beta

Two candidates survive: **Beta/Dirichlet** and **SL**. SL opinions are bijective with Beta/Dirichlet distributions, so they share the same conjugate, closed-form, deterministic update — both satisfy (D). SL then satisfies each requirement:

- **(a)** belief is a function of accumulated pseudo-counts `(r, s)`; more evidence → lower `u`, firmer belief.
- **(b)** the uncertainty mass `u` is an explicit coordinate. Beta encodes the same information *implicitly* as concentration; SL surfaces it as a first-class number, which is exactly what auditability and the trust commitment ([§2](#2-the-trust-commitment-read-this-first)) require.
- **(c)** the trust-discounting operator scales a source's *evidence counts* by reliability `P_R` and routes the lost evidence into `u` — closed-form. This is Evidence-Based Subjective Logic's evidence-scaling discount (Škorić et al., arXiv:1402.3319), **not** the belief-mass form `b' = P_R·b`; the belief-mass form has a documented pathology — a trusted high-evidence source's evidence can vanish — that evidence-scaling avoids.
- **(d)** accumulation is additive, so a document silent on a concept contributes nothing and the concept is carried forward unchanged.
- **(e)** disbelief `d` is its own coordinate.

**Conclusion.** Under the fixed requirements and candidate set, **SL is the unique survivor that satisfies all five requirements with closed-form determinism, and it dominates bare Beta by making `u` explicit and supplying the credibility and fusion operators.** ∎

**The honest boundary of this proof.** It is dominance *relative to this candidate set and these requirements.* It rests on two unresolved external dependencies — how to ground the credibility number `P_R`, and how to handle partially correlated sources — and one unadjudicated foundational critique (Dezert & Tchamova). Those are not hidden; they are [§7](#7-the-hard-parts-stated-honestly) and [§10](#10-gates-before-production). The proof shows SL is the right *shape*; the gates decide whether it is production-ready.

---

## 4. The design

### 4.1 `B` — beliefs as per-concept opinions

Each concept the worldview knows gets its own **binomial opinion**, stored as evidence counts:

```python
@dataclass(frozen=True)
class Opinion:
    """A belief about one concept, as accumulated evidence.

    r: weighted evidence FOR the concept (supporting pseudo-count).
    s: weighted evidence AGAINST the concept (disconfirming pseudo-count).
    base_rate: prior probability before any evidence (default 0.5).
    """
    r: float
    s: float
    base_rate: float = 0.5
```

The Subjective-Logic view is derived, not stored (with `W = 2`):

- belief `b = r / (r + s + W)`
- disbelief `d = s / (r + s + W)`
- uncertainty `u = W / (r + s + W)`
- projected probability `P = b + base_rate · u`

`B` for the whole worldview is `dict[str, Opinion]` — one opinion per concept, **independent**, no shared normalization. We choose per-concept binomials over a single multinomial opinion deliberately (research, open question 4): it keeps `W = 2` exact, gives requirement (d) for free, and lets us **drop the renormalize entirely** — the thing that caused the v1.1 amnesia.

Why store counts `(r, s)` rather than the tuple `(b, d, u)`? Counts are the natural accumulator (addition is the update), they keep the bijection exact (no `u = 0` edge case), and `(b, d, u)` is one cheap formula away for display.

### 4.2 `R` — revision as discounted accumulation

`R(B, e, O) → B'` does four steps, all closed-form:

1. **Parse** the recorded confidence vector from `e` (the existing parser; unchanged trust boundary — the LLM already ran and its output is recorded as an Observation).
2. **Discount** by source credibility. Read the source's reliability `P_R ∈ [0, 1]` (from the observation's provenance — see [§7.1](#71-grounding-the-credibility-number-the-biggest-open-risk)). Scale the evidence this document contributes by `P_R`. A meme at `P_R ≈ 0` contributes almost nothing; a replicated study at `P_R ≈ 1` contributes fully. Discounted evidence becomes uncertainty, not false confidence (evidence/count scaling — EBSL's evidence-scaling operator, Škorić et al. arXiv:1402.3319; non-associative but right-distributive over fusion, and the form the code ships).
3. **Fuse** the discounted evidence into each mentioned concept's counts. Default operator: **cumulative** fusion (addition of counts) for independent sources; **averaging** fusion when independence is unproven ([§7.2](#72-correlated-and-duplicate-sources)).
4. **Carry forward** every concept the document did *not* mention, unchanged. (Falls out of step 3: no contribution, no change.)

`R` reads only the recorded observation and the current beliefs. It is pure and deterministic. The non-determinism stays upstream in the LLM, exactly as v1.1 already arranges.

### 4.3 Worked example

Ontology knows `{climate, vaccines}`. Reader starts vacuous: every opinion `Opinion(r=0, s=0)`, so `u = 1`, `P = 0.5` — *unverified*, and the system says so.

- **Doc 1** — a replicated meta-analysis (`P_R = 0.95`) rates `climate` strongly true. After discounting, it contributes `r ≈ 1.9` to `climate`. Now `climate`: `b ≈ 0.49, u ≈ 0.51` — believed, but still uncertain after one source. `vaccines` is untouched: still `u = 1`.
- **Doc 2** — a meme (`P_R = 0.02`) rates `vaccines` false. It contributes `s ≈ 0.04`. `vaccines` barely moves: `u ≈ 0.98`. The system has *registered* the claim without being *moved* by it.
- **Doc 3** — silent on `climate`. `climate` is **carried forward unchanged**. No amnesia.

Contrast v1.1: after Doc 3, `climate` would have vanished, and the meme and the meta-analysis would have counted the same.

---

## 5. How it fits the existing pipeline

| Pipeline part | Effect of this change |
| --- | --- |
| **Trace persistence** | Serialize `Opinion` as `{r, s, base_rate}`, sorted keys (the byte-identical-determinism fix from PR #14 carries over). Register as before. |
| **`justification` norm** | Still holds: `R` is pure, so replay reproduces beliefs. |
| **`calibration` norm** | Now meaningful and central — the projected probability `P` is what we score against ground truth (see [§8](#8-validation-how-we-prove-trust-empirically)). |
| **`power` norm** | Unchanged. Ontology adequacy still fires `REFRAME` when a document names an unknown concept. |
| **Meta-layer** | New signals it can raise: "belief rests mostly on low-credibility sources" and "belief rests on correlated sources" — both candidates for `REFRAME`/`ESCALATE`. |

The `(O, E, B, R)` shape is unchanged. Only `B` and `R` change. The encoding stays a pure, replayable expressiveness proof, consistent with the rest of the project.

---

## 6. What this replaces

The v1.1 `worldview_update` renormalizes the latest confidence vector over the known concepts and returns it as the new belief. PR #14 documented its three limits honestly: it ignores the prior, drops unmentioned concepts, and cannot mark ignorance. The module's own `ponytail:` note already named the fix — "switch B to per-claim Bernoulli and drop the renormalize." **This design is the principled version of that note**: per-claim Bernoulli *is* a binomial SL opinion, and accumulation *is* the dropped renormalize done right.

---

## 7. The hard parts (stated honestly)

These are the two places the formalism does **not** save us, plus the one critique we have not resolved. They are the reason [§3](#3-the-proof-why-sl-and-why-not-the-others) is a dominance proof and not a guarantee.

### 7.1 Grounding the credibility number (the biggest open risk)

The discount operator is clean *given* a reliability number. Producing that number — "replicated peer-reviewed ≫ unsourced meme" — from a real source, without circularity, is unsolved. If `P_R` is itself an LLM guess, we have moved the trust problem, not solved it, because an LLM "credibility: 0.9" is as manipulable as the meme it is judging. **Credibility must come from something checkable**: traceable provenance, an independent-reproduction signal, an explicit source-tier policy. The pipeline already carries the hooks (`Observation.confidence`, `etype`, `source`); they are currently hardcoded and must be populated by the ingestion layer with auditable inputs. **If this cannot be grounded, the credibility layer rests on an unjustified prior and the (c) claim weakens to "weighted by a guess."**

### 7.2 Correlated and duplicate sources

Cumulative fusion assumes independent sources and drives `u → 0`. Ten copies of one claim then manufacture false confidence. The operator, not the representation, encodes independence: use **averaging/weighted** fusion for dependent sources, and **deduplicate** before fusing. The unsolved residue: real sources are *partially* correlated (retweets, shared upstream), and no retrieved source gives a clean operator for that middle case. Mitigation is engineering judgment: dedupe, cluster, and default to averaging when independence is unproven. Treat this as the primary failure surface for any social-media ingestion.

### 7.3 The foundational critique

Dezert & Tchamova, *"Can we trust subjective logic for information fusion?"* (Fusion 2014), attacks SL's fusion rule and the opinion-to-Beta mapping at the foundations. **Adjudicated** in a separate memo: [Dezert & Tchamova adjudication](../../research/2026-06-23-dezert-tchamova-sl-critique-adjudication.md). Verdict: it does not block this design — we reject Dempster's rule on independent grounds, use the corrected fusion operators, and treat the opinion-to-Beta mapping as a parameterization validated by calibration rather than asserted truth. The primary full text was auth-walled at adjudication time, so the gate is **monitored, not closed**: confirm against the primary that the fusion-rule objection targets the superseded consensus operator ([§10](#10-gates-before-production)). A later retrieval and 2019–2025 recency pass corroborated this (consensus-operator target; no calibration counterexample) but the retrieval is **unreplicated**, so the gate stays monitored. See [SL operator decisions](../../research/2026-06-23-sl-operator-decisions-research.md).

---

## 8. Validation: how we prove trust empirically

Trust is a claim about behavior, so we test behavior. Each test is falsifiable; the design is not "done" until they pass.

- **Calibration.** On a labeled set, bucket beliefs by projected probability `P` and check that frequency matches (reliability diagram). Score with the pipeline's existing log-score `calibration` norm. *A trustworthy updater is calibrated; this is the central test.*
- **Replay / determinism.** Dump → load → dump is byte-identical (the PR #14 test, carried forward to the new `B`).
- **Discounting ablation.** Feed the *same* claim from a high-`P_R` and a low-`P_R` source. Assert the low-credibility one moves `b` less and leaves `u` higher.
- **Meme-farm adversarial.** Inject N near-duplicate low-credibility sources for one claim. Assert `u` does **not** collapse to 0 (with dedup + averaging). This is the [§7.2](#72-correlated-and-duplicate-sources) defense, tested.
- **Ignorance honesty.** On a concept with no evidence, assert the system reports high `u` / abstains — it does not report 0.5 as if it were knowledge.
- **Disconfirmation.** Contradicting evidence raises `s` (lowers `b`); it is never silently dropped.

---

## 9. Migration (decomposition with standalone value)

Four shippable units plus one verification gate. Each states what lands, what works after it alone, and what it needs.

**Unit 1 — SL opinion math.**

- *Ships:* `encodings/_subjective_logic.py` — the `Opinion` type, the count↔`(b,d,u)` formulas, cumulative and averaging fusion, multinomial trust-discounting, with unit tests.
- *Standalone value:* a tested, reusable SL module any encoding can use. No pipeline change yet.
- *Depends on:* nothing.

**Unit 2 — Worldview `B`/`R` on SL.**

- *Ships:* rewritten `worldview.py` (`B = dict[str, Opinion]`, `R` = discounted accumulation, renormalize removed), updated trace serializers, updated tests.
- *Standalone value:* the worldview encoding now carries uncertainty and stops forgetting unmentioned concepts; runnable and replayable. Requirements (a), (b), (d), (e) met with a constant `P_R`.
- *Depends on:* Unit 1.

**Unit 3 — Credibility grounding (gated).**

- *Ships:* a `credibility(observation) → P_R` function plus ingestion wiring of `Observation.confidence`/`etype`/`source`.
- *Standalone value:* discounting actually responds to source quality — requirement (c) becomes real, not constant.
- *Depends on:* Unit 2, **and** a resolution to [§7.1](#71-grounding-the-credibility-number-the-biggest-open-risk). Until then `P_R` defaults to a documented constant and (c) is explicitly marked "not yet grounded."

**Unit 4 — Correlation control.**

- *Ships:* source dedup + averaging-fusion default + the meme-farm test.
- *Standalone value:* resistance to manufactured consensus.
- *Depends on:* Unit 2.

**Unit 5 — Trust gate (verification, not feature).**

- *Ships:* a short decision memo adjudicating Dezert & Tchamova, plus calibration-validation results.
- *Standalone value:* go/no-go evidence for production trust.
- *Depends on:* Unit 2 (something to test).

---

## 10. Gates before production

Do **not** ship this as "trustworthy worldview updates" until:

1. **Calibration is measured and acceptable** ([§8](#8-validation-how-we-prove-trust-empirically)). An uncalibrated updater is not trustworthy regardless of its math.
2. **`P_R` is grounded in something auditable** ([§7.1](#71-grounding-the-credibility-number-the-biggest-open-risk)), or credibility weighting is explicitly disabled and labeled as such.
3. **The meme-farm test passes** ([§7.2](#72-correlated-and-duplicate-sources)).
4. **Dezert & Tchamova is adjudicated** ([memo](../../research/2026-06-23-dezert-tchamova-sl-critique-adjudication.md), [§7.3](#73-the-foundational-critique)) — done, status *monitored*. Re-raise to blocking only if the primary shows a counterexample against the *corrected* cumulative/averaging operators that yields miscalibrated belief; then revisit [§4.2](#42-r--revision-as-discounted-accumulation).

Until these clear, the encoding is a sound, well-grounded *research artifact* — the right shape, honestly bounded — not a finished product that "tells you what to believe."

---

## References

Full evidence base, citations, confidence levels, and the canonical reference list: [Belief-Revision Formalisms for a Worldview Updater — Research & References](../../research/2026-06-23-belief-revision-formalism-research.md).
