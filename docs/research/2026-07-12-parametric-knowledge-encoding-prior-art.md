# Parametric-Knowledge Encoding — Prior Art & Superiority Analysis

**Date:** 2026-07-12
**Status:** Research findings. Input to a possible "parametric-knowledge encoding" design (model-as-root + declared priors).
**Method:** Deep-research harness. 5 search angles in parallel, 105 agents, adversarial 3-vote verification per claim (a claim dies on 2 of 3 refutes). Full-text greps against primary sources for every negative claim.

## The question

The proposed idea: have the model decompose its **own** knowledge into atomic claims with elicited confidences ("declared priors"), track each claim as a Subjective Logic opinion with the **model itself as the single provenance root** (so self-emissions never accumulate independence), then revise against external document evidence — with the store's usual replay and retraction. Four questions: does this exist, has it been asked, can it be better, and is there an "ultimate" solution?

## The short answer

**Novel as a combination. Redundant in no component. Improvable by two imports.** No located system combines decomposition + elicited priors + formal fusion + external-evidence revision + provenance/replay. The three pieces with **no located prior art anywhere** are exactly this project's core machinery: provenance-keyed single-root fusion, replay/retraction over a persistent store, and evidential revision against external documents.

## What exists (all verified against primary full texts)

| System | Year | Has | Stops short at |
|---|---|---|---|
| BeliefBank (AI2, EMNLP 2021) | 2021 | External, evolving belief memory over a frozen model; store-level correction predating ROME/MEMIT | Revision = weighted MaxSAT consistency repair (Z3), yes/no questions, hand-curated constraints. Zero fusion, zero provenance. |
| Entailer / TeachMe (EMNLP 2022) | 2022 | Self-verified entailment chains; user-correctable belief memory (+15% without retraining); chain-level auditability | Beliefs materialized per-question, not persistent; correction = context injection; no graded opinions, no replay. |
| REFLEX (2023) | 2023 | Question-conditioned belief graphs + "rational layer"; closest architecture class | Full-text grep: zero hits for Subjective Logic, Dempster-Shafer, fusion, provenance, external-document revision, retraction. |
| Atomic / Fact-Level Calibration (2024–25) | 2024 | Atomic decomposition + per-claim confidence elicitation (verbalized, logit, sampling-consistency) | Evaluation frameworks only. No store, no revision, no fusion, no provenance (grepped: zero hits). |
| ROME / MEMIT | 2022 | Weight-level knowledge editing | The alternative branch to store-level retraction; no audit trail, no graded belief. |

Every prior belief store revises by **consistency repair or context injection — never evidential fusion** (9-0 verified).

## The two imports that would make it better

1. **Claim-relation graphs + constraint repair** (from the AI2 line). Pure per-claim fusion has no mechanism relating claims to each other — a claim and its negation never interact. BeliefBank/REFLEX solve exactly this with entailment/XOR constraints and MaxSAT. This is the same coherence gap already tracked as [#33](https://github.com/TheRealBillSiegler/epistemic-pipeline/issues/33); the literature's answer is a graph layer, not better fusion.
2. **Multi-channel elicitation instead of one declared number.** A single verbalized prior is documented-weak: values cluster in 80–100% at multiples of 5; GPT-4 managed only 62.7% AUROC for failure prediction (others near random). Sampling-consistency (ECE 18.7% vs 25.0%) and fusing discriminative with generative elicitation (ECE 26.8% → 10.9%) measurably beat it. "Declared priors" should be elicited through several channels and fused — the machinery for weighted fusion already exists here.

Two more verified facts that shape the design:

- **Self-only revision has a measured ceiling.** Internal high-confidence-corrects-low-confidence (ConFix) *regresses* on uncalibrated models (6.76% improved vs 80.68% regressed on LLaMA-2-7B), and self-error-detection recall was 13.7%. External evidence is load-bearing, not optional — the collision with documents is where the value is.
- **Decomposition itself has an intrinsic tension**: atomic claims lose context; decontextualized claims lose atomicity (~19% of verification verdicts can flip). Known, reducible, not eliminable.

One encouraging verified positive: elicited confidences are calibratable in principle — larger models are well-calibrated on suitably-formatted questions and P(True) improves with scale (Kadavath 2022; replicated in the GPT-4 report). Caveat: RLHF degrades it, and it is format-sensitive.

## Is there an ultimate solution?

**No impossibility theorem and no ultimate architecture surfaced** — only measured empirical ceilings (P(IK) loses calibration out of distribution; 13.7% self-detection recall; decomposition context loss; ~10% residual ECE after the best elicitation fusion). Whether a principled ceiling exists is an open question this pass could not answer either way. Treat "no theoretical ceiling found" as absence of evidence, not evidence of absence (low confidence, by construction).

## Sources (primary)

- BeliefBank — Kassner et al., EMNLP 2021: `https://aclanthology.org/2021.emnlp-main.697/`
- Entailer — Tafjord et al., EMNLP 2022: `https://aclanthology.org/2022.emnlp-main.134/`
- TeachMe — Dalvi et al., 2022: `https://arxiv.org/abs/2204.13074`
- REFLEX — 2023: `https://arxiv.org/abs/2305.14250`
- Atomic Calibration — 2024: `https://arxiv.org/abs/2410.13246`
- Fact-Level Calibration / ConFix — 2024: `https://arxiv.org/abs/2411.13343`
- VeriFact — 2025: `https://arxiv.org/abs/2505.09701`
- Kadavath et al., *LMs (Mostly) Know What They Know*, 2022: `https://arxiv.org/abs/2207.05221`
- Xiong et al., ICLR 2024 (confidence elicitation): `https://arxiv.org/abs/2306.13063`

*Provenance: deep-research run `wf_843e043f-758`, 2026-07-12. 105 agents · 5 angles · 3-vote adversarial verification; vote tallies recorded per claim in the run journal. Confidence labels above are from the verification step, not asserted by the author.*
