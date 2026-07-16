# Credibility

**Every piece of evidence is scaled down by how much its source can be trusted, before it counts toward a belief.** The scaling factor is a number from 0 (ignore this source) to 1 (trust it fully) — the spec and code call it *reliability*, `P_R`; this page uses the site's term, *credibility*, for the same number. The scaling operator is settled math, chosen for a specific structural reason. Where `P_R` comes from is not settled — today it is a constant `1.0` for every source, and that gap is the honest content of this page.

## The discount operator

*Discounting* multiplies a source's evidence by its reliability, before that evidence joins a belief. An [opinion](opinions.md) stores two counts: `r` (evidence for a claim) and `s` (evidence against it). Discounting scales both by the same factor:

$$
r' = P_R \cdot r \qquad s' = P_R \cdot s
$$

Example: a document confidently rates a claim true, contributing `Opinion(r=2, s=0)` — two units of evidence for, none against. Discount it by a replicated, peer-reviewed source's reliability, `P_R = 0.95`, and it becomes `r' = 1.9`: almost the full two units land. Discount the same two units by an unsourced meme's reliability, `P_R = 0.02`, and it becomes `r' = 0.04`: the claim is registered, but barely moves anything.

## Why this operator was chosen

There are two ways to discount an opinion. Ours scales the *evidence counts* above. The other scales *belief mass* directly (`b' = P_R · b`) — and it is what most recent machine-learning work on Subjective Logic uses (Vasilakes et al. 2025, [arXiv:2502.12225](https://arxiv.org/abs/2502.12225); Bezirganyan et al., DBF, AISTATS 2025, [arXiv:2412.18024](https://arxiv.org/abs/2412.18024)). This project picked the minority option, on purpose.

The pipeline's own shape decides it. Discount runs once per source; then [cumulative fusion](fusion.md) adds the discounted counts together, across sources. Evidence-count scaling is *right-distributive* over that addition — discounting a source and then fusing it with others gives the same counts as fusing the sources first and discounting the combined total by the same factor:

$$
x \boxtimes (y \oplus z) = (x \boxtimes y) \oplus (x \boxtimes z)
$$

Belief-mass scaling has no such guarantee. Run source-by-source before fusion — the order this pipeline uses — it can make a trusted, evidence-heavy source's contribution partly vanish once fused with others: a documented failure of that operator (Škorić, de Hoogh & Zannone, [arXiv:1402.3319](https://arxiv.org/abs/1402.3319), §3.2, Examples 2–4). In a pipeline that discounts *then* fuses, that is exactly the failure to avoid. Full comparison of both operators: [SL operator decisions research, decision D1](https://github.com/TheRealBillSiegler/epistemic-pipeline/blob/main/docs/research/2026-06-23-sl-operator-decisions-research.md).

## Where `P_R` comes from: unsolved

The operator above is clean *given* a reliability number. Producing that number, without cheating, is not solved yet.

The tempting shortcut — ask the LLM to rate its own source's credibility — is rejected in the design. An LLM's credibility guess is exactly as manipulable as the claim it is judging, so it would move the trust problem instead of closing it.

So today `P_R` is a hardcoded constant, `1.0`, for every source ([`DEFAULT_RELIABILITY`](https://github.com/TheRealBillSiegler/epistemic-pipeline/blob/main/src/epistemic_pipeline/encodings/worldview.py)). At `1.0` the discount is a no-op: every source is treated as fully trusted, and the code labels this state plainly.

The design spec names three paths that would ground `P_R` in something checkable instead of a guess: traceable provenance, an independent-reproduction signal, or an explicit source-tier policy — ranking source types the way the spec already contrasts them ("replicated peer-reviewed" versus "unsourced meme") and reading `P_R` off the rank. None of the three is built. The work is gated: it cannot start until one of them is picked and specified.

!!! warning "Honest status"
    Credibility weighting is explicitly disabled: `P_R` is a hardcoded constant, so every source currently counts in full. The grounding problem is [design spec §7.1](https://github.com/TheRealBillSiegler/epistemic-pipeline/blob/main/docs/superpowers/specs/2026-06-23-worldview-subjective-logic-design.md#71-grounding-the-credibility-number-the-biggest-open-risk); progress is tracked on the [status page](../project/status.md).

## Where next

- The counts `P_R` scales: [Opinions and uncertainty](opinions.md)
- What happens after discounting: [Fusing evidence](fusion.md)
- The full operator record: [SL operator decisions research](https://github.com/TheRealBillSiegler/epistemic-pipeline/blob/main/docs/research/2026-06-23-sl-operator-decisions-research.md)
