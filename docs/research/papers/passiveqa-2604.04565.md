# PassiveQA (arXiv:2604.04565)
**Venue / access:** arXiv (2026 preprint). Full text read via HTML view.
**Source:** https://arxiv.org/abs/2604.04565

## What it is about

LLM-based QA systems default to generating an answer even when they lack the information to answer correctly. PassiveQA trains a model to instead choose among three actions: Answer, Ask a clarifying question, or Abstain. The decision is grounded in a knowledge graph that tracks which variables a query requires versus which are actually present. A Mistral-7B planner is finetuned on 24,456 graph-grounded examples with structured XML reasoning chains. The core claim is that epistemic calibration must be built into the model's weights at training time — prompt-level or retrieval-level interventions plateau too early.

## Key topics and concepts

- Three-action decision framework: Answer / Ask / Abstain
- Information state model: S(q) = (V_known, V_missing, C) — known entities, missing variables, constraints
- Knowledge graph construction in three phases: entity/relation extraction, SBERT semantic validation (threshold τ = 0.50), decision-weighted reinforcement
- Supervised finetuning with LoRA (rank 32) on Mistral-7B-Instruct-v0.3
- Retrieval-augmented generation (RAG) as a baseline family, including hard-gated Decision-Aware RAG
- Hallucination measurement as a first-class metric alongside decision accuracy and macro F1
- Multi-turn QA degradation under short sequence limits
- Dataset fusion: ShARC, QuAC, HotpotQA, ContractNLI into a 61,000-sample unified schema

## Main claims and findings

- Baseline and Enhanced RAG both plateau at 34.0% decision accuracy and 26.7% macro F1, despite five enhancements in the Enhanced variant
- Enhanced RAG raised hallucination rate from 42.7% to 51.7%, showing that better retrieval without decision gates makes overconfidence worse
- Decision-Aware RAG (hard gating) improved macro F1 to 35.3% and cut hallucination to 33.8%, but Ask recall was only 40.0% and Abstain recall only 13.3%
- Finetuned planner achieved 55.6% macro F1 — a +20.3 percentage-point gain over the best RAG baseline
- Per-action F1: Answer 71.2%, Abstain 63.4%, Ask 32.6%
- Abstain recall rose from 13.3% (best RAG) to 58.1% after finetuning
- Single-turn accuracy 78.4% vs. multi-turn accuracy 25.6%; the gap is attributed to the 512-token sequence limit
- Structured output compliance (well-formed XML tags in every output) was 100% across the full 5,218-sample test set
- Knowledge graph shrinks from 27,189 nodes (Phase 1) to 15,468 (Phase 2 after semantic filtering), then grows to 19,763 (Phase 3 after variable injection); 4,295 variable nodes added (21.7% of final graph)
- Finetuning dataset: 34,831 samples at 57.1% yield after quality filtering, split 24,456 / 5,157 / 5,218 (train / val / test)
- Central conclusion: "decision behaviour must be internalised at training time" — parameter-level alignment, not prompt-level gating, is what moves the needle

---

## Comparison against the Epistemic Pipeline project

**We cite it for:** detecting ABSENCE is harder than detecting conflict; we claim its gap-detector reaches only ~58% recall
**Verdict:** partial
**Support check:** Cited in two places in `docs/research/2026-06-25-honest-pipeline-omission-frontier.md` — the load-bearing body claim (line 32) and the Sources list (line 77). The body sentence: "Detecting *absence* is structurally harder than detecting conflict... PassiveQA (arXiv:2604.04565, 2026) names this directly and its own gap-detector reaches only ~58% recall."

NUMBER CHECK — accurate. The "~58% recall" maps to the understanding file's recorded "Abstain recall rose from 13.3% (best RAG) to 58.1% after finetuning" (line 27). ~58% ≈ 58.1% is correct.

FRAMING CHECK — two overclaims, both subtle:

1. "names this directly" is too strong for the absence-vs-conflict *distinction*. The understanding file records PassiveQA framing the problem as Answer/Ask/Abstain over an information state S(q) = (V_known, V_missing, C). It names and quantifies the *absence/under-specification* problem. It does NOT, per the recorded findings, contain a "conflict detection" task or an explicit "absence is harder than conflict" comparison. That contrast is the project's own synthesis; the paper supplies only the absence half. So the paper supports "absence detection is hard and only ~58% solved," but does not itself "name" the comparison to conflict.
2. "only ~58%" inverts the paper's narrative. The paper frames 58.1% Abstain recall as a *success* (+44.8 pp over the 13.3% RAG baseline), not as a ceiling. The project legitimately reads 58% as mediocre in absolute terms — and the companion Ask action is worse (per-action F1 32.6%) — but the "only" is the project's editorial gloss, not the paper's claim. Calling it a "gap-detector at ~58%" also quietly picks the most favorable of the two gap actions (Abstain 58.1% recall vs. Ask 32.6% F1).

Net: the number is right and the qualitative point (absence detection is structurally hard, partially solved) is well-supported; the "names this directly" attribution of the conflict comparison is an overclaim. Hence partial, not supports.
**Topical overlap:** The honesty / omission frontier (omission-frontier doc §2), feeding the worldview UI honesty sections (§9, §11) and the SL design's trust commitment. Specifically the pipeline's "detect what evidence is missing" target — the open frontier where honesty stays partial.
**Cautions:** Automated reader, not human verification. (1) Numbers are taken from the understanding file, which states full HTML text was read; I did not re-fetch arXiv to confirm 58.1% appears in the body or that it is labeled "Abstain recall" there. A human should spot-check the 58.1% figure and confirm the paper truly lacks a conflict-detection comparison before relying on "names this directly." (2) PassiveQA is a fresh 2026 arXiv preprint, unreplicated — the omission-frontier doc's own Method note (line 67) already flags it as such and says to treat its numbers as provisional. (3) If anyone tightens the body sentence, the fix is to drop "names this directly" (keep the absence-vs-conflict contrast as the project's framing) and consider softening "only ~58%" to acknowledge it is the post-finetuning best, not a stated limit.
