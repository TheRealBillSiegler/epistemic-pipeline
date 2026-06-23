# Belief-Revision Formalisms for a Worldview Updater — Research & References

**Date:** 2026-06-23
**Status:** Research findings. Input to the worldview encoding design ([2026-06-23-worldview-subjective-logic-design.md](../superpowers/specs/2026-06-23-worldview-subjective-logic-design.md)).
**Method:** Multi-agent deep-research harness. Five search angles, run in parallel. 22 sources fetched, 106 candidate claims extracted, 25 claims adversarially verified (three independent skeptic votes each; a claim dies on 2 of 3 refutes). 24 confirmed, 1 killed.

---

## What this document is

A fair comparison of the main ways to represent and update beliefs, judged against one job: power a tool that revises a reader's worldview as documents arrive. It records what the literature actually supports, how strongly, and where it is silent. The design document turns these findings into a build. This document is the evidence the design rests on. Every load-bearing claim below links to a source.

One honesty rule governs this whole file: **claims are stated at the strength their sources warrant.** Where the evidence is one author's own corpus, we say so. Where the strongest counter-argument was not resolved, we say that too.

---

## The question

Which belief representation `B` and revision function `R` best support rigorous, evidence-proportioned reasoning for an automated worldview updater? The formalism must:

- **(a) Proportion confidence to evidence.** More and better evidence means a stronger belief; thin evidence means a weak one.
- **(b) Mark "unverified" as different from "balanced."** A claim with no evidence and a claim with equal evidence on both sides can both sit at probability 0.5. The formalism must tell them apart. A single number cannot.
- **(c) Weight evidence by source credibility.** A replicated peer-reviewed study must move belief far more than an unsourced social-media post.
- **(d) Not erase a belief just because the latest document is silent about it.** Absence of mention is not evidence of absence.
- **(e) Treat disconfirming evidence as first-class.** Evidence against a claim is represented directly, not discarded.

Plus one engineering constraint: `R` must be a **pure, deterministic, closed-form** function `R(B, e, O) → B'`. This is a hard invariant of the pipeline.

---

## The short answer

**Subjective Logic (SL).** Represent each belief as an *opinion* `(b, d, u, a)` — belief, disbelief, uncertainty, and a base rate — and update by accumulating evidence as pseudo-counts, scaled by source credibility. SL is the only candidate that meets all five requirements at once under the determinism constraint, and it dominates the closest runner-up (a bare Beta/Dirichlet model) by making uncertainty an explicit, first-class quantity.

**Confidence, stated honestly.** The *mathematical* claims behind this answer are high-confidence and independently corroborated (the Beta bijection, the Zadeh failure of Dempster's rule, the credal-set pathologies). The *normative* claim — that SL is the single best choice — is **medium** confidence. Most of the strongest SL evidence comes from the formalism's originator (Andrew Jøsang) and authors who build on him; that corpus is not adversarial to SL. The strongest published critique of SL (Dezert & Tchamova) was flagged but not resolved in this research pass. Treat "SL wins" as a well-supported working decision, not a closed question. See [Caveats](#caveats-read-before-relying-on-this).

---

## The candidates

| Formalism | One-line description |
|---|---|
| **Point-probability Bayes** | One probability distribution over hypotheses; update by Bayes' rule, renormalize. |
| **Beta / Dirichlet (pseudo-count)** | Each claim carries counts of supporting and contradicting evidence; belief is their ratio. |
| **Subjective Logic** | A re-parameterization of Beta/Dirichlet that adds an explicit *uncertainty mass* plus an operator algebra (fusion, trust-discounting). |
| **Dempster-Shafer (DS)** | Mass assigned to *sets* of hypotheses, including "don't know"; combine sources with Dempster's rule. |
| **Imprecise probability / credal sets** | A *set* of probability distributions; report bounds `[lower, upper]`. |
| **Log-odds / weight-of-evidence** | Belief as log-odds; each datum adds a weight (I.J. Good). |
| **AGM belief revision** | Beliefs as a set of accepted sentences; revise by minimal change. |

---

## Head-to-head

Verdicts are explained in the [Findings](#findings) and [Failure modes](#failure-modes-proven). "Subsumed" means the formalism is a special case of SL or collapses into the Beta/SL representation once made adequate.

| Formalism | (a) proportion | (b) unverified ≠ balanced | (c) credibility fusion | (d) non-erasure | (e) disconfirm | determinism / cost | Verdict |
|---|---|---|---|---|---|---|---|
| Point-probability Bayes | yes | **no** — 0.5 conflates | partial (likelihoods) | **no** — renormalize drops it | implicit | cheap, deterministic | **fails (b), (d)** |
| Beta / Dirichlet | yes | yes (concentration) | yes (pseudo-counts) | yes (additive) | yes (β count) | cheap, conjugate | viable; **subsumed by SL** |
| **Subjective Logic** | yes | **yes — explicit `u`** | yes (trust-discount) | yes (additive) | yes (`d` coord) | cheap, closed-form | **recommended** |
| Dempster-Shafer (rule) | yes | yes (mass on frame) | yes (discount) | n/a | discards conflict | exponential; **Zadeh failure** | **reject the rule** |
| Imprecise / credal sets | yes | **yes — ideal** | yes | yes | yes | **NP-hard; inertia + dilation** | reject as `R`; keep as yardstick |
| Log-odds / weight-of-evidence | yes | **no** — scalar | yes (additive weights) | n/a | yes (sign) | cheap | **subsumed** (→ Beta when augmented) |
| AGM | **no** — qualitative | partial | no | yes | yes | cheap | **reject** (cannot grade) |

---

## Findings

Each finding lists its confidence, the verification vote, sources, and the evidence. Vote notation like "3-0" means three independent skeptics tried to refute the claim and none could.

### F1 — Recommendation: Subjective Logic opinions as `B`; pseudo-count accumulation with trust-discounting as `R`
**Confidence: high (math) / medium (normative).** Synthesized from 5 unanimous (3-0) claims.

SL re-parameterizes the Beta/Dirichlet evidential model. A binomial opinion `(b, d, u, a)` maps bijectively to a Beta distribution: `b = r/(r+s+W)`, `d = s/(r+s+W)`, `u = W/(r+s+W)`, with `W = 2` the non-informative prior weight, and the inverse `r = W·b/u`. Beta-Bernoulli conjugacy makes the update closed-form and deterministic. SL **is** the Beta/Dirichlet model with an added uncertainty mass and an operator algebra — so it strictly dominates a bare Beta model on the requirements that need an explicit ignorance term and a credibility operator.

*Verifier caveat:* the bijection is exact only on the uncertain interior (`u > 0`); a dogmatic opinion (`u = 0`) is a limit (`r, s → ∞`). `W = 2` gives a clean uniform prior only for binary frames; larger ontologies need per-concept binomials or a dynamic `W`.

Sources: [Jøsang FUSION 2022], [arXiv:1805.01388], [arXiv:2502.12225], [arXiv:2412.18024].

### F2 — Satisfies (b): second-order uncertainty
**Confidence: high.** Synthesized from 7 unanimous (3-0) claims.

The uncertainty mass `u` separates *epistemic* uncertainty (ignorance, lack of evidence) from *aleatoric* uncertainty (balanced or conflicting evidence). A vacuous opinion (`u = 1`) and a balanced-but-evidenced opinion (`u ≈ 0`, `b = d`) both project to probability 0.5 but are distinct states. This is exactly the distinction a point probability collapses — the literature's "fair coin" (P = 0.5, well-evidenced) versus "was Oswald the lone gunman" (P = 0.5, near-total ignorance) example.

*Verifier caveat:* Jøsang's gloss of "aleatoric" as "balanced or conflicting" is idiosyncratic versus standard machine-learning usage (aleatoric = irreducible noise). The substance — two distinct states, one projected probability — is sound; the word choice is his.

Sources: [Jøsang FUSION 2022], [arXiv:2412.18024], [arXiv:2502.12225], [arXiv:1805.01388].

### F3 — Satisfies (c): credibility-weighted (discounted) fusion
**Confidence: high.** Synthesized from 3 unanimous (3-0) claims.

A trust-discounting operator (Shafer 1976 lineage) scales a source's belief mass by a reliability factor `P_R ∈ [0, 1]` and routes the lost mass into `u`: `b̂ = P_R · b`, `û = 1 − P_R · Σb`. At reliability 0 the opinion becomes fully vacuous (`u = 1`, source ignored); at reliability 1 it is unchanged. A low-credibility source therefore yields a *near-vacuous* opinion, not a confident wrong one. The discount can also be derived per-sample from a degree-of-conflict measure, so a source that conflicts with many others is discounted more.

*Verifier caveat:* the *binomial* "naive" discount operator has a documented pathology (a pure-disbelief source can resist uncertainty inflation). Use the *multinomial/Dirichlet* form, which routes discounted mass into `u` and avoids it.

Sources: [arXiv:2502.12225], [arXiv:2412.18024], [Jøsang FUSION 2022].

### F4 — Satisfies (e), and why to prefer cumulative/averaging fusion over Dempster's rule
**Confidence: high.** Synthesized from 4 unanimous (3-0) claims; one related claim was refuted (see [Refuted](#refuted-claim)).

In SL, disbelief `d` is its own tuple coordinate, so disconfirming evidence is represented natively. By contrast, Dempster's rule of combination (which SL exposes as *belief constraint fusion*) discards conflict by normalizing it away (dividing by `1 − K`). Under high conflict this produces the Zadeh counterexample (see [Failure modes](#failure-modes-proven)). So the SL *representation* keeps disconfirmation first-class, and the choice of *fusion operator* (cumulative or averaging, not Dempster's rule) keeps conflict from being erased.

Sources: [arXiv:2412.18024], [Sentz & Ferson].

### F5 — Dominant engineering risk: correlated / duplicate sources
**Confidence: high.** Synthesized from 4 unanimous (3-0) claims.

This is the hard part of requirement (c), and **the representation does not solve it.** Cumulative belief fusion (CBF) assumes *independent* sources and drives `u` monotonically toward zero as opinions are fused. Feed it N copies of one claim and it manufactures false confidence (a zero-variance Dirichlet). The correct operator for dependent sources is *averaging* or *weighted* belief fusion (ABF/WBF). **Operator choice, not the representation, encodes the independence assumption.**

*Key limitation:* CBF assumes *full* independence; ABF/WBF assume *full* dependence. Real sources (retweets, shared upstream, near-duplicates) are *partially* correlated and sit between the two. No retrieved source gives a clean operator for arbitrary correlation. The practical mitigation — deduplicate sources, and default to averaging when independence is unproven — is engineering judgment, not a sourced result.

Sources: [arXiv:2502.12225], [arXiv:2412.18024], [arXiv:1805.01388].

### F6 — Reject Dempster-Shafer combination as the primary `R`
**Confidence: high.** Synthesized from 2 unanimous (3-0) claims.

Given identical evidence and priors, DS yields belief bounds at least as tight as imprecise Bayesianism — sometimes tighter. But in a 1000-game agent-based simulation those tighter bounds did **not** produce better decisions, and DS updating does not by itself avoid the "ambiguity dilemma" (greater credal divergence → slower updating → worse short-run decisions). Combined with the Zadeh failure, DS combination buys little and costs robustness. Note SL's trust-discounting and cumulative fusion are *not* Dempster's rule; SL extends DS but lets you avoid the normalizing rule that fails.

*Caveat:* this finding is internal to one 2024 peer-reviewed agent-based model on Bernoulli tasks; the broader "ambiguity dilemma" framing is itself contested.

Sources: [OUP J. Logic & Computation 2024].

### F7 — Reject pure imprecise probability / credal sets as the working `R`
**Confidence: high.** Synthesized from 4 claims (three 3-0, one 2-1).

Credal sets represent ignorance correctly — the fair coin is `P(H) = {0.5}`, the unknown-bias coin is `P(H) = [0, 1]`. But they have two build-killing update pathologies:

- **Belief inertia.** A vacuous prior `[0, 1]` stays vacuous after conditioning. The agent *cannot learn from complete ignorance* (Levi 1980). This violates requirement (a).
- **Dilation.** Conditioning on apparently irrelevant evidence can *widen* a precise posterior `{1/2}` to `[0, 1]` (Seidenfeld & Wasserman 1993).

Also, total-uncertainty quantification over a credal set needs purpose-built, sometimes NP-hard, generalizations of entropy — violating the cheap/deterministic constraint.

**Build lesson:** do not initialize beliefs at full ignorance, and do not represent ignorance as a raw interval to be conditioned. SL's `u`-mass with a non-vacuous base rate sidesteps both pathologies, because the pseudo-count update always moves. Keep credal sets as the *conceptual yardstick* for requirement (b), not the implementation.

Sources: [Stanford Encyclopedia: Imprecise Probabilities], [Synthese 2011].

### F8 — Satisfies (d): omission is a no-op
**Confidence: medium.** Inferred from the pseudo-count mechanism (F1, F5) plus a direct reading of the current code; no single retrieved source states it verbatim.

SL's pseudo-count accumulation makes "the latest document didn't mention concept X" a no-op: X's counts `(r, s)` are unchanged, so its opinion is carried forward. This is the natural behavior of an additive accumulator. It is the **opposite** of the current `worldview.py` `R`, which renormalizes over only the latest vector and drops any concept the new document omits.

Sources: [arXiv:1805.01388], [Jøsang FUSION 2022], plus `src/epistemic_pipeline/encodings/worldview.py` (current behavior, lines ~12-22, ~147-160).

---

## Failure modes proven

These are the worked counterexamples that justify the rejections. They are arithmetic, not opinion.

### Zadeh's counterexample (kills Dempster's rule under conflict)
Two physicians each examine a patient. Physician 1: meningitis 0.99, brain tumor 0.01, concussion 0. Physician 2: concussion 0.99, brain tumor 0.01, meningitis 0. They agree the patient almost certainly does *not* have a brain tumor. Dempster's rule normalizes away the huge conflict (`K = 0.9999`) and concludes **brain tumor with belief 1.0** — the one diagnosis both doctors thought least likely. Reproduced in the SL literature as belief-constraint fusion yielding `b = 1.0, u = 0`. Sources: [Sentz & Ferson], [Counterexamples to Dempster's Rule], [arXiv:2412.18024].

### Belief inertia and dilation (kill credal sets as the update rule)
Inertia: a fully imprecise prior conditions to a fully imprecise posterior — no learning. Dilation: a sharp posterior can become *less* sharp after seeing evidence. Both are established results, not edge cases. Sources: [Synthese 2011], [Stanford Encyclopedia: Imprecise Probabilities].

---

## Caveats (read before relying on this)

1. **Source bias toward SL.** The strongest, most unanimous claims (the SL representation, the Beta bijection, trust-discounting, the cumulative-vs-averaging split) rest heavily on Jøsang's own corpus and papers that build on it. That is appropriate for *descriptive/mathematical* claims (the math is textbook and corroborated elsewhere) but is a **weak base for the normative claim that SL is best** — the SL literature is not adversarial to SL.
2. **The strongest counter-position was not adjudicated.** Dezert & Tchamova, *"Can we trust subjective logic for information fusion?"*, attacks SL's fusion rule and the opinion-to-Beta mapping at a foundational level. This research pass flagged it but did not retrieve and resolve it. **Read it before committing to SL in production.** It is the single biggest open risk to the recommendation.
3. **Operator fragility.** SL's cumulative/averaging operators are only semi-associative; naive multi-source fusion had a division-by-zero corner case later patched (van der Heijden et al.). Order-independence is not free — implement and test the corrected multi-source forms, not the pairwise originals.
4. **`W = 2` is binary-only.** The clean uniform-prior bijection holds exactly for binary frames. A growing multi-concept ontology should model each concept as an independent binomial opinion (recommended) or adopt a dynamic `W`.
5. **Determinism is about `R`, not the LLM.** All SL operators are closed-form and deterministic. The non-determinism lives upstream in the model that emits the confidence vector; the current code already records that vector as an Observation before `R` runs. Preserve that boundary.
6. **Partial correlation is unsolved in the retrieved evidence** (see F5).

---

## Open questions

1. **What operator handles *partially* correlated sources?** CBF (full independence) and ABF/WBF (full dependence) bracket the real case but neither fits. Candidate directions: source clustering/dedup before fusion, or a correlation-discount applied like a reliability factor.
2. **How is source credibility `P_R` grounded, non-circularly?** The discount operator is clean given a reliability number. Producing that number from source metadata ("peer-reviewed and replicated ≫ unsourced") without circularity is unsolved here. **If this input is ungroundable, the whole credibility layer rests on an unjustified prior.** This is the condition that would most weaken the recommendation.
3. **Does the Dezert & Tchamova critique undermine the cumulative/averaging operators specifically, or only the older consensus operator?** Unresolved; resolve before production.
4. **Per-concept independent binomials vs. one multinomial opinion over all concepts?** The former gives clean `W = 2`, natural carry-forward, and lets the renormalize be dropped. The latter needs a dynamic `W`. The choice affects requirement (d).

---

## Refuted claim

One verified-against claim, recorded for completeness: *"Belief constraint fusion ... the paper [arXiv:1805.01388] states plainly that conflicting evidence is discarded."* Vote **1-2 (refuted)**. The discard property of Dempster-style combination is real and well-sourced — but from [Sentz & Ferson] and [arXiv:2412.18024], **not** from arXiv:1805.01388. Cite the correct sources.

---

## Canonical references

Quality tags: **primary** (peer-reviewed paper, standards body, or original author), **secondary** (encyclopedia/survey), **blog** (practitioner write-up). Listed with what each one grounds.

### Subjective Logic (the recommended formalism)
- **[Jøsang FUSION 2022]** Jøsang, *Subjective Logic and Belief Fusion* (FUSION 2022 tutorial). primary. — Grounds: the opinion tuple, the Beta bijection, fusion operators, trust-discounting. `https://www.mn.uio.no/ifi/personer/vit/josang/sl/subjective-logic-fusion-2022.pdf`
- **[arXiv:1805.01388]** primary. — Grounds: SL representation, opinion↔Dirichlet map, cumulative-vs-averaging fusion. `https://arxiv.org/pdf/1805.01388`
- **[arXiv:2412.18024]** primary. — Grounds: binomial opinion definition, epistemic/aleatoric split, Zadeh reproduction in SL, discounting. `https://arxiv.org/pdf/2412.18024`
- **[arXiv:2502.12225]** primary. — Grounds: discount operator math, cumulative-fusion uncertainty collapse (F5), degree-of-conflict discount. `https://arxiv.org/html/2502.12225v2`

### Dempster-Shafer and its failure modes
- **[Sentz & Ferson]** Sentz & Ferson, *Combination of Evidence in Dempster-Shafer Theory* (Sandia/DOE report). primary. — Grounds: Zadeh counterexample arithmetic. `https://www.osti.gov/servlets/purl/800792/`
- **[Counterexamples to Dempster's Rule]** primary. — Grounds: high-conflict failures of Dempster's rule. `https://fs.unm.edu/CounterExamplesToDempstersRuleOfCombination.pdf`
- **[Wikipedia: Dempster-Shafer theory]** secondary. — Background only. `https://en.wikipedia.org/wiki/Dempster%E2%80%93Shafer_theory`

### Imprecise probability / credal sets
- **[Stanford Encyclopedia: Imprecise Probabilities]** secondary (authoritative survey). — Grounds: credal-set representation, ignorance, dilation, belief inertia. `https://plato.stanford.edu/entries/imprecise-probabilities/`
- **[Synthese 2011]** primary. — Grounds: dilation and belief-inertia results. `https://link.springer.com/article/10.1007/s11229-011-0042-2`

### Decision-quality comparison (DS vs imprecise Bayesianism)
- **[OUP J. Logic & Computation 2024]** primary. — Grounds: DS bounds tighter but not better decisions; ambiguity dilemma. `https://academic.oup.com/logcom/advance-article/doi/10.1093/logcom/exae069/7833415`

### Weight of evidence (log-odds baseline)
- **[Good, Weight of Evidence]** I.J. Good. primary. — Grounds: additive log-odds evidence weighting (the subsumed scalar baseline). `https://www.cs.tufts.edu/~nr/cs257/archive/jack-good/weight-of-evidence.pdf`

### The outstanding counter-position (must read before production)
- **Dezert & Tchamova**, *"Can we trust subjective logic for information fusion?"* primary. — The strongest published critique of SL's fusion rule and opinion-to-Beta mapping. **Not retrieved or adjudicated in this pass.** Full text to be located and read before committing. (Open question 3.)

### Additional sources consulted (correlated-source angle)
- Correlated/duplicate-source fusion literature: `https://pmc.ncbi.nlm.nih.gov/articles/PMC5676609/`, `https://www.sciencedirect.com/science/article/pii/S0004370207001063`, `https://isas.iar.kit.edu/pdf/Fusion17_Noack.pdf`, `https://www.stat.berkeley.edu/~aldous/Real_World/dempster_shafer.pdf`.

---

*Provenance: generated by the deep-research harness on 2026-06-23 (run `wf_1b6bc616-0c8`). 5 angles · 22 sources · 106 claims · 25 verified · 24 confirmed / 1 killed. Confidence levels and votes above are from the adversarial verification step, not asserted by the author.*
