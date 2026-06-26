# Subjective Logic fusion operators (van der Heijden et al.) (arXiv:1805.01388)
**Venue / access:** arXiv (FUSION 2018 pre-print). HTML body read via ar5iv; abstract confirmed via arxiv.org. Full text read — formulas and section structure extracted.
**Source:** https://arxiv.org/abs/1805.01388

## What it is about

Subjective Logic (SL) defines several operators for combining beliefs from two sources. This paper asks: what happens when you have three or more sources? The answer is non-trivial because some SL operators are not associative — applying them pairwise in different orders gives different results. The authors give rigorous multi-source definitions for all four main SL fusion types: Cumulative Belief Fusion (CBF), Averaging Belief Fusion (ABF), Weighted Belief Fusion (WBF), and Consensus & Compromise Fusion (CCF). They also correct division-by-zero errors in prior CBF and ABF formulations. The result is a complete, well-defined multi-source fusion framework for SL.

## Key topics and concepts

- **Subjective Logic opinions** — each opinion is a tuple (belief mass b, uncertainty u, base rate a) over a frame of discernment X; must satisfy b(x) ≥ 0, u ≥ 0, Σb(x) + u = 1
- **Multinomial vs. hyper opinions** — multinomial: each singleton gets a belief mass; hyper: subsets can also hold mass
- **Dirichlet evidence PDF** — bijective mapping between SL opinions and Dirichlet distributions via evidence count r(x) = W·b(x)/u, W = 2 (non-informative prior weight)
- **Cumulative Belief Fusion (CBF)** — pools all evidence; models independent observers of the same phenomenon
- **Averaging Belief Fusion (ABF)** — averages opinions; models consensus without evidence accumulation
- **Weighted Belief Fusion (WBF)** — weights each source by its confidence (1 − u); reduces to ABF as a special case
- **Consensus & Compromise Fusion (CCF)** — extracts the minimum shared belief (consensus), then merges residual belief through intersection/union (compromise), then normalizes
- **Belief Constraint Fusion (BCF)** — SL analogue of Dempster's combination rule; applies mass-function combination across all sources
- **Dogmatic opinions** — opinions with u = 0; require special-case handling (relative degrees of infinity)
- **Vacuous opinions** — opinions with u = 1, meaning total ignorance

## Main claims and findings

- **Correction to CBF/ABF (Jøsang et al.):** the prior binary formulas produce division by zero when some but not all sources hold dogmatic opinions (u = 0). Fix: in the dogmatic case, discard all non-dogmatic opinions and fuse only dogmatic ones; require all uncertainties = 0 to trigger Case I.
- **WBF multi-source definition (Definition 4):** three cases —
  - Case 1 (all non-vacuous, non-dogmatic): belief b_x = weighted sum of b^A(x)·Π_{B≠A} u^B, normalized; uncertainty u = product-like residual; base rate = confidence-weighted average a^A weighted by (1 − u^A)
  - Case 2 (≥ 1 dogmatic source): only dogmatic sources contribute; u = 0
  - Case 3 (all vacuous, u = 1): b = 0, u = 1, base rate = uniform average
- **Theorem 1 (WBF ↔ Dirichlet):** multi-source WBF is equivalent to confidence-weighted averaging of Dirichlet evidence parameters: r^fused(x) = Σ_A [r^A(x)·(1 − u^A)] / Σ_A (1 − u^A)
- **CCF multi-source definition (Definition 5):** three phases —
  - Phase 1 (consensus): b^cons(x) = min_{A} b^A(x) for each x
  - Phase 2 (compromise): residual beliefs combined via set intersection and union across all source subsets
  - Phase 3 (normalization): η = (1 − b^cons − u^pre) / b^comp ensures the output is a valid opinion
- **Remark 4:** CCF always produces a valid opinion (belief and uncertainty in [0,1], additivity satisfied) — this is proved, not assumed
- **BCF multi-source (Definition 3):** map each opinion to a Dempster-Shafer mass function, apply Dempster's rule across all sources simultaneously (not pairwise), map result back to SL; base rate = confidence-weighted average, or uniform if all vacuous
- **Main result:** with these definitions, multi-source fusion is now well-defined for all SL fusion types — no ordering ambiguity, no division-by-zero failures

---

## Comparison against the Epistemic Pipeline project

**We cite it for:** cumulative (CBF) vs averaging (ABF) fusion = add vs average opinion counts
**Verdict:** supports
**Support check:** The claim holds against this paper. On the opinion↔Dirichlet bijection (this file, "evidence count r(x) = W·b(x)/u"), CBF "pools all evidence" and ABF "averages opinions" — the add-vs-average contrast. The project's operator-decisions memo (`docs/research/2026-06-23-sl-operator-decisions-research.md`) states it precisely: D2 "cumulative fusion is `r⋄ = Σ r` over sources (van der Heijden et al., arXiv:1805.01388, 2018)"; D3 averaging = `(Σr)/N` as the equal-confidence special case of weighted fusion `r⋄ = Σ r(1−u)/Σ(1−u)`, attributed to "van der Heijden 2018, Thm 1." Both check out: this paper's Theorem 1 is exactly "multi-source WBF ↔ confidence-weighted averaging of Dirichlet evidence parameters," and line 16 records "WBF reduces to ABF as a special case." The Dezert adjudication memo's two direct quotes (non-associativity; division-by-zero "when at least one opinion has non-zero uncertainty, while at least two others have zero uncertainty") are consistent with this file's recorded CBF/ABF correction (dogmatic-source division-by-zero). No wrong number or fabricated quote found.
**Topical overlap:** State tuple R (Revision policy) and B (Beliefs) — the SL fusion mechanism in `encodings/worldview.py`; operator-choice decisions D2/D3 and the Dezert-Tchamova gate. Not the worldview-UI credibility layer (C1–C6), despite the task pointer naming the credibility file — that file does not cite this paper.
**Cautions:** Automated check, not human verification — the add-vs-average reading rests on the opinion↔Dirichlet bijection, which this understanding file records but I read via ar5iv HTML, not the original PDF. Single preprint (FUSION 2018); the corrected operators have no published adversarial replication (the project tracks this as the "monitored" Dezert gate). One self-corrected hazard on this same paper: `2026-06-23-belief-revision-formalism-research.md` (line 182) flags an earlier mis-attribution — "conflicting evidence is discarded" was wrongly pinned to arXiv:1805.01388 and reassigned to Sentz & Ferson / arXiv:2412.18024. That mismatch is already corrected in-repo; it does not affect the CBF/ABF-as-add/average claim, but a human re-checking citations to this paper should confirm no stale copy of the discard claim survives.
