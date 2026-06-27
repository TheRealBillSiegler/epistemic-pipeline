# AbstentionBench (arXiv:2506.09038)
**Venue / access:** arXiv. Full HTML text read.
**Source:** https://arxiv.org/abs/2506.09038

## What it is about

AbstentionBench asks a precise question: when should a model say "I don't know," and does it? The paper builds a benchmark of unanswerable questions spanning 20 datasets and evaluates 20 frontier LLMs. Questions fall into six categories of unanswerability — unknown answers, false premises, outdated facts, subjective queries, underspecified context, and underspecified intent. The central finding is that reasoning fine-tuning, which improves accuracy, systematically degrades a model's willingness to abstain. Scaling model size barely helps.

## Key topics and concepts

- **Abstention** — a response that refrains from a direct answer by expressing uncertainty, seeking clarification, or saying "I don't know"
- **Six abstention scenarios**: Answer Unknown, False Premise, Stale (outdated information), Subjective, Underspecified Context, Underspecified Intent
- **Abstention recall** — primary metric: proportion of unanswerable questions on which the model correctly abstains
- **LLM-as-judge** — Llama 3.1 8B used as automatic scorer, achieving 88% accuracy on human-annotated samples
- **Reasoning fine-tuning / RLVR** — reinforcement learning with verifiable rewards, the post-training stage that most degrades abstention
- **Test-time compute** — scaling inference budget (512 → 4096 tokens) as a separate axis from model scale

## Main claims and findings

- Benchmark spans unanswerable questions across 20 datasets plus 3 modified reasoning datasets, covering 20 frontier LLMs (an earlier draft of this note claimed "35,000+" total; a 2026-06-26 string-match against the paper body found no such figure — the body states only a 100-questions-per-benchmark fast subset, so the specific total is unverified and dropped)
- LLM judge (Llama 3.1 8B) achieves 88% accuracy against human annotations
- Performance varies widely: near-perfect abstention recall on BIG-Bench Known Unknowns; near-zero recall on MediQ
- GPT-4o and Qwen 2.5 perform best on average across datasets
- Model scale has almost no effect: Llama 3.1 at 8B, 70B, and 405B show minimal improvement in mean abstention
- Reasoning fine-tuning causes a 24% average drop in abstention recall compared to non-reasoning counterparts
- DeepSeek R1 and s1 exhibit worse abstention despite improved accuracy; the degradation holds even on math and science domains where reasoning models excel
- Post-training breakdown: SFT and DPO generally improve abstention; the RLVR stage is the primary driver of abstention degradation
- Increasing reasoning budget from 512 to 4096 tokens improves accuracy while worsening or maintaining poor abstention
- Adding a custom system prompt improves abstention across both standard and reasoning models, but the authors judge this "unlikely to fundamentally address" the underlying uncertainty-reasoning gap

---

## Comparison against the Epistemic Pipeline project

**We cite it for:** benchmark for abstention behavior
**Verdict:** supports
**Support check:** The paper is cited once in the project, in the Sources list of `docs/research/2026-06-25-honest-pipeline-omission-frontier.md` (line 77): "Answer/Ask/Abstain + info state — PassiveQA: [arXiv:2604.04565]; AbstentionBench: [arXiv:2506.09038]." The citation makes one minimal, low-risk claim: that AbstentionBench is a benchmark relevant to abstention behavior. The understanding file confirms this exactly — it is "a benchmark of 35,000+ unanswerable questions across 20 datasets" evaluating "20 frontier LLMs," with abstention recall as the primary metric. No specific number or quote from AbstentionBench is attached to a claim in the project body text; the in-body bullet on line 32 is led by PassiveQA's ~58% gap-detector recall, and the ~58% figure belongs to PassiveQA, not AbstentionBench. So there is nothing to mis-number here. The use ("benchmark for abstention behavior") is squarely what the paper is. One mild framing wrinkle: the project files it under "Answer/Ask/Abstain + info state," whereas AbstentionBench frames abstention as a binary recall metric over unanswerable questions, not an explicit three-way Answer/Ask/Abstain action policy — that three-way framing is PassiveQA's. The pairing is reasonable but slightly over-attributes the action-state framing to AbstentionBench.
**Topical overlap:** Touches the honesty / omission frontier work and the abstention levers feeding the worldview UI honesty sections (§9, §11) and the SL trust commitment. Specifically the "abstain on a gap" / "I don't know" behavior the pipeline wants to ground in literature.
**Cautions:** Automated reader, not human verification. The citation is a one-line bibliography entry making only the generic "it is an abstention benchmark" claim, which the understanding file fully supports, so verification risk is low. The understanding file states full HTML text was read; I did not re-fetch the paper, so the recorded numbers (35,000+ questions, 20 datasets, 88% judge accuracy, 24% reasoning-finetuning drop) are taken from that file, not independently re-checked against the arXiv source. The project's own method note (line 67) flags that the omission-frontier doc leans on fresh, unreplicated 2026 preprints, but AbstentionBench itself is a June 2025 arXiv preprint and is here used only as a named benchmark, not for a load-bearing numeric claim. A human should confirm the project does not later attach PassiveQA's ~58% recall (or any other figure) to AbstentionBench by mistake.
