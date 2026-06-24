# Subjective Logic operator decisions (SL Unit 1)

**Status:** Decided — 2026-06-23.
**Feeds:** [design spec](../superpowers/specs/2026-06-23-worldview-subjective-logic-design.md), `src/epistemic_pipeline/encodings/_subjective_logic.py` (PR #19).

This records four operator and representation choices in the SL math module, the expert literature behind each, and what would change them. Two deep-research passes plus a 2019–2025 recency sweep back these. Sources are cited by link; no paywalled PDFs are stored here.

**Read this first.** Trust in the output rests on *measured calibration*, not on any operator being "true" (design §2, §8). These choices pick the operator whose behavior is interpretable and whose failure modes are known. Calibration is the judge.

## D1 — Discount by scaling evidence counts, not belief mass

**Decision.** `discount(opinion, P_R)` multiplies the evidence counts: `r' = P_R·r`, `s' = P_R·s`. It does **not** scale belief mass (`b' = P_R·b`).

**Why (experts).** This is Evidence-Based Subjective Logic's evidence-scaling operator (Škorić, de Hoogh & Zannone, [arXiv:1402.3319](https://arxiv.org/abs/1402.3319), peer-reviewed *Int. J. Information Security* 2016). The rejected belief-mass operator has a documented failure: it is **not distributive over fusion**, so appraising sources separately versus fused gives different answers, and a trusted high-evidence source's evidence can be lost (EBSL §3.2, Examples 2–4). Evidence-scaling preserves the evidence cleanly. EBSL Theorem 3 proves the two operators are genuinely different — they agree only at `P_R = 0` and `P_R = 1`.

**Properties.** Evidence-scaling is **non-associative** but **right-distributive over cumulative fusion**: `x ⊠ (y ⊕ z) = (x⊠y) ⊕ (x⊠z)`. Precise point, easy to get backwards: the *rejected* operator's pathology is **non-distributivity**, not non-associativity — belief-mass discounting is in fact associative. Order-independence in our pipeline comes from cumulative fusion (count addition), because each source is discounted *before* it is fused.

**Honest standing — a justified minority choice, not the field default.** Recent ML practice mostly uses belief-mass discounting: Vasilakes et al. ([arXiv:2502.12225](https://arxiv.org/abs/2502.12225), 2025) and Bezirganyan et al. "DBF" ([arXiv:2412.18024](https://arxiv.org/abs/2412.18024), AISTATS 2025). We diverge on purpose. Our pipeline is discount-then-cumulative-fusion, where right-distributivity is exactly the property that pays off; and our per-concept binomials sit in the regime where the belief-mass pathology bites (those papers are multinomial Dirichlet classifiers that route discounted mass to uncertainty, the safe regime). Neither paper tests count-scaling, so neither is evidence against this choice — they are counter-*practice*, not counter-*argument*.

**Would change it.** A worked case showing count-scaling miscalibrated where belief-mass is not, in a discount-then-cumulative-fusion binomial pipeline.

## D2 — Fuse independent sources by adding counts (corrected CBF)

**Decision.** Cumulative belief fusion = addition of evidence counts, using the corrected multi-source operator.

**Why (experts).** On the Dirichlet evidence representation, cumulative fusion is `r⋄ = Σ r` over sources (van der Heijden et al., [arXiv:1805.01388](https://arxiv.org/abs/1805.01388), 2018).

**Attribution.** The division-by-zero defect was in the *multi-source* extension by Jøsang–Wang–Zhang (FUSION 2017), **not** the 2016 Jøsang book, which defines only two-source fusion. van der Heijden 2018 diagnosed it; the corrected formulas live in the revised JWZ 2017. No 2019–2025 work re-corrects or supersedes them.

**Foundational critique (Dezert & Tchamova 2014).** Adjudicated separately: [dezert memo](2026-06-23-dezert-tchamova-sl-critique-adjudication.md). It does not block this design. The critique's fusion objection targets Jøsang's superseded *consensus operator*, which predates the corrected CBF/ABF we use by four years; its mapping objection is the *non-isomorphism* point, which this system already concedes (we treat the opinion↔Beta map as a parameterization, not an isomorphism), so it costs us nothing. **Residual gap (honest):** the corrected operators have never faced a published Dezert-style adversarial test. Our calibration gate (design §8, §10) is the net designed to catch that empirically. **Gate: monitored.**

## D3 — Average dependent sources by mean of counts (a WBF special case)

**Decision.** `fuse_averaging` = arithmetic mean of counts. Keep it, with a caveat.

**Why (experts).** This equals canonical weighted/averaging belief fusion *only when sources carry equal evidence*. Weighted belief fusion weights counts by confidence `(1−u)`: `r⋄ = Σ r(1−u) / Σ(1−u)`, which reduces to `(Σr)/N` at equal confidence (van der Heijden 2018, Thm 1). Independently re-derived, with a citable non-associativity proof, by DBF 2025 (Prop. 1). This is the **strongest-supported** of the four decisions.

**Caveat.** Arithmetic averaging does *not* raise uncertainty under confident conflict — two confident, opposed, low-`u` sources fuse to low `u`. Fine for the duplicate / meme-farm guard (near-duplicates carry similar evidence). For general unequal-evidence dependent sources, confidence-weighted fusion or deduplicate-then-cumulative is the literature's answer.

## D4 — Base rate belongs to the concept, not the opinion

**Decision.** Store `base_rate` once per concept (proposition), shared by every opinion about it.

**Why (experts).** The base rate is a frame-level prior, normally shared across opinions about the same proposition (JWZ 2017: "the argument base rate distributions are normally equal"; confirmed by Vasilakes 2025 and DBF 2025). No source relocates it onto the individual opinion.

**Note.** Subjective Logic *syntactically permits* a per-opinion base rate, so this is the *normal/intended* choice, not a theorem — and it deliberately forgoes the rarely-used unequal-base-rate fusion. A separate knob: the prior weight `W` (we fix `W = 2`) is a tunable frame-level parameter distinct from the base rate (argued by R-EDL, ICLR 2024). The `W = 2` choice is a binary-frame convention (design §4.1).

**Status (code).** `base_rate` is currently a field on `Opinion`, guarded by `_check_same_base_rate` in fusion (fail-loud on mismatch). Move it onto the concept in Unit 2 (`worldview.py`); the guard is the placeholder until then.

## Still open (not closed by this research)

- **`P_R` grounding** — how the credibility number is produced without circularity (design §7.1). Unchanged.
- **Partial-correlation fusion** — no SL operator exists for the middle between independent (cumulative) and fully-dependent (averaging) sources. Confirmed still open by the recency sweep. Mitigation stays dedup + default-to-averaging.
- **Dezert 2014 primary** — one retrieval pass reported obtaining it and confirmed the consensus-operator target by text search; the result is **unreplicated** (earlier passes were auth-walled), and nothing above depends on it.
- **Coarsening→pignistic non-invariance** (Dezert §III) — a real internal-consistency gap, but in the *opinion-construction* layer, not fusion. Bites only if base rates are ever derived via SL "normal" coarsening rather than fixed exogenously. Separate watch item.

## Method

Two deep-research passes (operator math; critique retrieval) and a 2019–2025 recency sweep, each with adversarial verification of load-bearing claims. The recency sweep found nothing superseded; it corrected the D2 attribution (book → JWZ 2017) and the D1 framing (deliberate minority choice, not field consensus). Provenance: workflow transcripts, 2026-06-23.

## Sources

- EBSL evidence-scaling discount — Škorić, de Hoogh, Zannone: [arXiv:1402.3319](https://arxiv.org/abs/1402.3319)
- Corrected multi-source fusion (CBF/ABF/WBF) — van der Heijden et al.: [arXiv:1805.01388](https://arxiv.org/abs/1805.01388)
- Discounted Belief Fusion (DBF), AISTATS 2025 — Bezirganyan et al.: [arXiv:2412.18024](https://arxiv.org/abs/2412.18024)
- SL annotation encoding (belief-mass discount in practice), 2025 — Vasilakes et al.: [arXiv:2502.12225](https://arxiv.org/abs/2502.12225)
- R-EDL (prior weight `W` as a tunable knob), ICLR 2024
- Base Subjective Logic / base-rate semantics — Jøsang: [arXiv:0712.1182](https://arxiv.org/abs/0712.1182); UAI 2016 tutorial
- Dezert, Tchamova, Han, Tacnet, *"Can we trust subjective logic for information fusion?"*, FUSION 2014 — IEEE Xplore 6916194; HAL `hal-01070401` (paywalled)
- Jøsang, *Subjective Logic: A Formalism for Reasoning Under Uncertainty* (Springer 2016) — canonical reference (paywalled)
