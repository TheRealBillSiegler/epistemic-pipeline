# Uncertainty-based abstention filters unsafe outputs (Tomani et al.) (arXiv:2404.10960)
**Venue / access:** arXiv. Full text read via HTML view (v1).
**Source:** https://arxiv.org/abs/2404.10960

## What it is about

LLMs fail in three ways: wrong answers, hallucinated answers, and unsafe answers. This paper asks whether uncertainty signals — computed over the model's own outputs — can trigger abstention before those failures reach the user. The authors test both statistical uncertainty (computed over token probabilities) and verbalized uncertainty (hedge words in the response) across correctness, hallucination, and safety tasks. They find that each failure mode responds best to a different kind of uncertainty signal. The approach adds almost no compute cost.

## Key topics and concepts

- **Abstention / selective prediction:** the model refuses to answer when its uncertainty exceeds a threshold, rather than outputting a low-confidence response
- **Negative log-likelihood (NLL):** single-pass token-level uncertainty; sum of `-log p(token)` over the generated sequence
- **Predictive entropy:** multi-sample uncertainty; average log-likelihood over N sampled sequences
- **Semantic entropy:** multi-sample uncertainty clustered by meaning (bi-directional entailment via DeBERTa), not by token string
- **In-Dialogue Uncertainty (InDU):** count of hedge words ("perhaps," "maybe," "I don't know") in the response as a verbalized uncertainty proxy
- **AUROC / Accuracy-Rejection Curve (ARC) / AUARC:** evaluation framework measuring how well uncertainty ranks failures above successes and how accuracy improves as uncertain samples are rejected
- **RLHF finetuning effects:** RLHF reduces output diversity and raises confidence, yet preserves or sharpens the uncertainty signal for abstention
- **Safety datasets:** AutoDAN and AttaQ (adversarial prompts designed to elicit harmful outputs)
- **Hallucination dataset:** SelfAware (paired answerable vs. unanswerable questions)

## Main claims and findings

- **Correctness:** statistical uncertainty (semantic entropy) achieves average AUROC of 0.69 on RLHF-finetuned models; predictive entropy AUROC ranges 0.57–0.82 across datasets
- **Correctness (TriviaQA):** rejecting the top 5% most uncertain samples raises accuracy from 84.4% to 86.0%; rejecting the top 25% raises it to 92.6%
- **Hallucination:** InDU achieves AUROC of 0.75 on RLHF models for detecting unanswerable questions; statistical measures score only 0.48–0.60 on the same task
- **Hallucination (InDU filter):** correctly flags ~50% of unanswerable questions while incorrectly refusing only ~10% of answerable ones; responses to unanswerable questions contain roughly 2x the hedge words of responses to answerable ones
- **Safety (AutoDAN):** RLHF model reaches AUROC of 0.78 (predictive entropy) and 0.99 (NLL); rejecting the top 10% uncertain samples raises safe-response rate from 92.5% to 99.4%
- **Safety (AttaQ):** AUROC of 0.78 (predictive entropy); safe-response rate rises from 92.1% to 95.1% with 10% rejection
- **Baseline safe-response rates by model type:** pretrained 7.4–9.0%; instruction-tuned (Vicuna) 11.5–54.1%; RLHF-finetuned 92.1–92.5% — uncertainty abstention is only effective on top of RLHF; pretrained and instruction-tuned models show AUROC ≈ 0.50 for safety
- **Overall pattern:** statistical uncertainty suits correctness and safety; verbalized uncertainty (InDU) suits hallucination detection; no single signal dominates all three tasks

---

## Comparison against the Epistemic Pipeline project

**We cite it for:** abstention can filter unsafe outputs
**Verdict:** supports
**Support check:** The project cites this paper in exactly one place: the Sources list of `docs/research/2026-06-25-honest-pipeline-omission-frontier.md` (line 74), labeled "abstention filters unsafe — Tomani et al." No specific number is attached to Tomani in the project prose, so there is no number to mismatch. The directional claim is fully backed by this understanding file: on AutoDAN, rejecting the top 10% uncertain samples raises the safe-response rate from 92.5% to 99.4%; on AttaQ, 92.1% to 95.1% with 10% rejection (lines 27-28). The claim wording ("abstention *can* filter unsafe outputs") is a possibility claim and is appropriately modest — it does not overstate the result.
**Topical overlap:** Abstention / "I don't know" mechanisms — a design candidate for the pipeline's honesty layer (the omission-frontier research on calibration/abstention). Adjacent to the SL uncertainty/ignorance mass and the three-axis abstain lever, though Tomani is one supporting cite, not a load-bearing pillar of the doc.
**Cautions:** Automated reader, not human verification. (1) Scope condition the project's one-line cite drops: per this understanding file (line 29), uncertainty abstention for safety is "only effective on top of RLHF" — pretrained and instruction-tuned models show AUROC ≈ 0.50 for safety. The project does not overclaim because its claim is a bare possibility, but a human should note the result is RLHF-conditional. (2) The cited safety numbers (92.5%→99.4%, 92.1%→95.1%) live in this understanding file's summary; I did not re-read the arXiv body to confirm the figures or that the quoted framing appears verbatim there. (3) arXiv preprint — unreplicated.
