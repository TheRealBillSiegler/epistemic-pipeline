# To Believe or Not to Believe Your LLM (arXiv:2406.02543)
**Venue / access:** NeurIPS 2024 / arXiv. Full HTML text read (v2).
**Source:** https://arxiv.org/abs/2406.02543

## What it is about

LLMs produce confident-sounding answers whether or not they actually "know" the answer. This paper builds an information-theoretic measure to tell the difference. It separates epistemic uncertainty (the model lacks knowledge) from aleatoric uncertainty (the question has multiple valid answers). The measure is mutual information computed from repeated, iterative LLM samples. When the measure exceeds a threshold, the system abstains rather than risks hallucinating. The approach works without access to model internals — only output probabilities.

## Key topics and concepts

- **Epistemic vs. aleatoric uncertainty** — epistemic = model ignorance, aleatoric = irreducible ambiguity in the question itself
- **Mutual information (MI) as uncertainty signal** — high MI between prompt and sampled responses indicates the model is sensitive to phrasing, a sign it is guessing
- **Iterative prompting** — each new sample is drawn by appending prior responses to the prompt, building a pseudo-joint distribution over response sequences
- **KL divergence lower bound** — DKL(Q̃, P̃) ≥ I(Q̃); MI is a computable lower bound on the true model-vs-ground-truth KL gap
- **Finite-sample estimator with guarantees** — Algorithm 1 estimates MI from k samples; Theorem 4.6 gives a high-probability lower bound
- **Semantic equivalence clustering** — Algorithm 2 groups responses by meaning before computing MI, handling paraphrase variation
- **Abstention policy** — abstain when Î ≥ λ, respond when Î < λ; λ is calibrated on a held-out set
- **Self-attention mechanistic analysis** — explains why repeated in-context text raises the probability of that text: repeated keys dominate the softmax

## Main claims and findings

- **Core inequality (Theorem 4.5):** For any pseudo-joint distribution P̃ satisfying the independence assumption, DKL(Q̃, P̃) ≥ I(Q̃). MI is therefore a valid lower bound on the gap between the LLM and ground truth.
- **Finite-sample bound (Theorem 4.6):** I(μ) ≥ (1 − ε_k) Î_k(γ₁, γ₂) − (1/k + (1 + n·ln(1 + k|𝒳|))·ε_k), where ε_k = 𝔼[U_k] + √(ln(1/δ)/k) and U_k is the missing mass.
- **Zipf convergence rate:** For Zipf-distributed responses with exponent α > 1, 𝔼[U_k] = O(k^(−(α−1)/α − β)) for any β > 0, meaning the estimator converges reliably on realistic Q&A distributions.
- **n = 2 samples suffices** in practice — two iterative draws are enough for effective hallucination detection on the tested benchmarks.
- **Effective support is small:** on Q&A datasets, the support covering μ(𝒳̃) ≥ 0.95 rarely exceeds ~100 distinct responses, making the estimator tractable.
- **Probability stability on known facts:** "London" as capital of UK holds ~96% probability even after 100 repetitions of a wrong answer; "George Washington" scores 0.999 vs. "Abraham Lincoln" at 3.1×10⁻⁶.
- **Probability collapse on uncertain facts:** for genuinely ambiguous queries (e.g., Irish national instrument), probabilities collapse rapidly under repetition of an incorrect answer — the model's "belief" is fragile.
- **Multi-label queries preserve proportions:** for questions with multiple correct answers (UK cities, yellow fruits), relative probabilities stay stable under perturbation ("London" 0.958, "Manchester" 0.041; "Banana" 0.715, "Lemon" 0.284).
- **Benchmark performance:** tested on TriviaQA, AmbigQA, and a WordNet-derived dataset; the MI method achieves significantly higher recall on high-entropy samples while maintaining similar error rates compared to likelihood-only baselines.
- **Self-attention mechanism:** repeated in-context token Y receives t-times increased weight in the key matrix when t copies appear in the prompt, eventually dominating the original query X — this explains the probability amplification effect.

---

## Comparison against the Epistemic Pipeline project

**We cite it for:** the DISTINCT sibling paper we are careful not to confuse with the conformal one (2405.01563)
**Verdict:** supports
**Support check:** The project cites this paper in exactly one place — the Sources list of `docs/research/2026-06-25-honest-pipeline-omission-frontier.md`, line 83, as a disambiguation footnote on the conformal-abstention entry: "(this is the conformal paper; not to be confused with the same group's NeurIPS 2024 *To Believe or Not to Believe Your LLM*, arXiv:2406.02543)." The cite makes three checkable claims: (1) it is a paper distinct from the conformal one (2405.01563); (2) it is NeurIPS 2024, titled *To Believe or Not to Believe Your LLM*; (3) it is by "the same group" as the conformal paper. Claim (2) matches this understanding file exactly — title (line 1) and "NeurIPS 2024" venue (line 2). Claim (1) is correct: this file records an information-theoretic / mutual-information method separating epistemic from aleatoric uncertainty with an MI-threshold abstention — a genuinely different method from conformal self-consistency calibration, with a different arXiv id and title. No paper-specific number or quote (e.g. the ~96% London figure, n=2, Î ≥ λ) is attached to any project claim; the citation is disambiguation-only, so there is nothing numeric to mis-state. The project's use does not lean on this paper's findings at all — it only needs the paper to exist and be the other paper. That is satisfied.
**Topical overlap:** Honesty/abstention and the omission-frontier research. The paper sits in the same neighborhood as the pipeline's "honesty-as-process, never a verdict" stance and its uncertainty-mass / abstain-on-gap machinery (epistemic-vs-aleatoric split maps loosely onto the project's missing-input-vs-beyond-knowledge routing). But the project does NOT actually use this paper's method; it appears only as a name-collision guard.
**Cautions:** Automated check, not human verification. (a) The "same group" authorship claim is NOT verifiable from this understanding file — the file records no author list for 2406.02543, and the conformal entry names "Abbasi-Yadkori et al." A human should confirm both papers share authors before relying on "same group" (in reality both are Abbasi-Yadkori-led DeepMind work, but that is outside what the recorded notes show). (b) This file states the full HTML (v2) was read, but as an automated reader I am trusting that record, not re-reading the source. (c) NeurIPS 2024 is peer-reviewed, so unreplicated-preprint risk is low for this specific paper — unlike the fresh 2026 arXiv sources elsewhere in the same omission-frontier doc.
