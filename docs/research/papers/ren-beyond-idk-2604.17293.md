# Beyond I Don't Know (Ren et al.) (arXiv:2604.17293)
**Venue / access:** arXiv (2026 preprint). Full text read via HTML view.
**Source:** https://arxiv.org/abs/2604.17293

## What it is about

LLMs today either answer or refuse with "I don't know." This paper argues that refusal is not enough: a reliable model must say *why* it can't answer. The authors split uncertainty into two types. Data uncertainty means the question itself lacks a unique answer (ambiguous input, missing information). Model uncertainty means the question is well-defined but the model lacks the capability to solve it. Those two cases call for different downstream actions (ask for clarification vs. invoke a tool), so conflating them is a real practical failure. The paper introduces UA-Bench, a 3,500-question benchmark across six datasets, tests 18 frontier LLMs on the discrimination task, and proposes a reinforcement-learning fine-tuning strategy that substantially improves attribution without hurting answer accuracy.

## Key topics and concepts

- **Data uncertainty vs. model uncertainty** — the two-way split that replaces generic "I don't know"
- **UA-Bench** — benchmark with >3,500 questions from six datasets (GAIA, MuSiQue, SelfAware for knowledge tasks; OlympiadBench-math, GSM8K-MiP, MATH-MiP for reasoning tasks)
- **DU-F1 / MU-F1 / AVG-F1** — three precision-recall metrics for evaluating uncertainty attribution separately for each type
- **GRPO reinforcement learning** — trained on 5,000 synthetic instances (answerable, model-uncertain, data-uncertain variants) with a +1/0/-1 reward scheme
- **Thinking-mode collapse** — extended chain-of-thought reasoning improves answer accuracy but can destroy model-uncertainty recognition (MU-F1 drops to 0%)
- **Failure modes** — systematic misclassification in both directions: data gaps labeled as model limits, and model gaps labeled as input ambiguity

## Main claims and findings

- No model reliably distinguishes data from model uncertainty; all 18 tested models show substantial gaps on at least one dimension.
- **GPT-4o** reaches the strongest knowledge-task score: 78.2% DU-F1, 66.6% MU-F1, AVG-F1 72.4%.
- **Claude Sonnet 4** scores 74.2% DU-F1 and 67.4% MU-F1 (AVG-F1 70.8%) on knowledge tasks; 62.5% accuracy and 86.6% MU-F1 (AVG-F1 84.4%) on reasoning tasks.
- **Qwen3-8B** shows extreme imbalance on knowledge tasks: 69.8% DU-F1 but only 4.0% MU-F1 (AVG-F1 36.9%).
- Thinking mode can collapse MU-F1: Qwen3-235B in thinking mode goes from 84.8% to 0.0% MU-F1 on reasoning tasks while raising accuracy to 80.0%.
- **RL-UA fine-tuning on Qwen3-4B-Instruct**: backbone 23.3% MU-F1 → RL-UA 53.5% MU-F1 (AVG-F1 45.9% → 61.0%), answer accuracy held at 72.3% → 73.4%.
- **RL-UA fine-tuning on Qwen3-8B thinking mode**: MU-F1 18.7% → 60.8% (+225%), AVG-F1 33.0% → 63.5%, accuracy essentially unchanged (77.7% → 77.9%).
- Metric definitions: DU-F1 precision = (TP_DU/N) / (TP_DU/N + FP_DU/M); MU-F1 precision = (TP_MU/M) / (TP_MU/M + FP_MU/N); where N = unanswerable set size, M = answerable-error set size.
- The paper concludes uncertainty attribution "remains a highly challenging open problem" with scores far from saturation across all tested models.

---

## Comparison against the Epistemic Pipeline project

**We cite it for:** data vs model uncertainty need different moves (ask vs abstain/fetch); models self-classify the gap poorly (we claim 4% F1 on model-uncertainty)
**Verdict:** supports
**Support check:** The project uses this paper in one place — `docs/research/2026-06-25-honest-pipeline-omission-frontier.md` §1 (line 23), with a back-reference in the source list (line 76). The cited sentence reads: *"data uncertainty (the question has no unique answer — ambiguous/missing input) and model uncertainty (an answer exists but is past the system's reach) demand different moves — ask vs abstain / go fetch. Critical caveat: models cannot reliably classify which they face (one model scored 4% F1 on model-uncertainty). So route on it, but do not trust the model to self-classify the gap."* Each sub-claim checks out against this understanding file:

> - Two-way split (data vs model uncertainty): matches the file's "What it is about" and key-concepts (data uncertainty = ambiguous/missing input; model uncertainty = well-defined question past the model's capability).
> - "Different moves — ask vs abstain / go fetch": the file records "different downstream actions (ask for clarification vs. invoke a tool)." The project's "ask vs abstain / go fetch" is a faithful paraphrase ("invoke a tool" ≈ "go fetch"; "abstain" is the project's added framing, consistent with the paper's overall thesis that refusal alone is not enough).
> - "4% F1 on model-uncertainty": matches exactly — the file records Qwen3-8B at 4.0% MU-F1 (model-uncertainty F1) on knowledge tasks (AVG-F1 36.9%). The project rounds "4.0%" to "4%" and correctly attributes it as a single model's score, not a paper-wide result.
> - "Models cannot reliably classify which they face": matches the file's headline finding that no model reliably distinguishes the two and all 18 show substantial gaps on at least one dimension. The project's stance ("do not trust the model to self-classify the gap") is properly hedged, not an overclaim.

**Topical overlap:** Honesty / omission frontier (the `2026-06-25-honest-pipeline-omission-frontier.md` research). Supports the design principle "don't trust the model's own gap-classification; route on missing-input vs beyond-evidence but get the signal from structure, not self-report." Tangentially touches the C1-C6 evidence-credibility stance (the LLM names a type, a fixed policy decides the move — here, the move is the ask/abstain/fetch routing rather than a weight).
**Cautions:** Automated reader, not human verification. I checked the project's claim against the *understanding file*, not the paper's body text directly, so this confirms internal consistency (project claim ↔ recorded summary), not that the understanding file faithfully captured the PDF. The understanding file itself notes full HTML was read, but the 4.0% MU-F1 figure and the "ask vs invoke a tool" framing are body-detail an automated pass cannot independently re-derive. Unreplicated 2026 arXiv preprint — the omission-frontier doc already flags this and treats its numbers as provisional. One minor framing note: the project's "abstain" is its own addition to the paper's "invoke a tool"; defensible, but the paper's literal second action is tool-use, not abstention.
