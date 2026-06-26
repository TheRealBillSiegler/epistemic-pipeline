# Epistemic Bias Injection (arXiv:2512.00804)
**Venue / access:** arXiv (2025/26 preprint). Full HTML text read.
**Source:** https://arxiv.org/abs/2512.00804

## What it is about

This paper studies a covert attack on retrieval-augmented generation (RAG) systems. The attack injects passages that are factually correct but perspectively biased into a knowledge base. Because the passages contain no false claims or obvious malicious structure, existing defenses miss them. The attack still shifts LLM outputs toward a target ideological direction. The authors also propose BiasDef, a post-retrieval filter that detects these passages by analyzing the joint distribution of relevance scores and polarization scores.

## Key topics and concepts

- RAG security: knowledge-base poisoning via factually-accurate but biased passages
- Bias injection attack: five-step workflow — generate synthetic passages, run PCA to find polarization axis, select seed, generate adversarial variants, inject
- Polarization Score (PS): each passage's projection onto the first principal component of the embedding space (the axis of maximum ideological variance)
- Similarity Score (SS): cosine similarity between query embedding and passage embedding
- BiasDef: post-retrieval filter using KL-divergence maximization over the SS-PS feature space to separate adversarial from benign passages, plus Mahalanobis-distance recovery for low-SS adversarial passages
- Three security properties for an effective adversarial passage: high retrieval relevance (Property 1), consistent perspective bias (Property 2), stealth / factual correctness (Property 3)
- Evaluation across three LLMs (Llama-3-8B, DeepSeek-R1-Distill-Qwen-14B, GPT-4.1) and three datasets (WIKI-BALANCE 452 questions / 4,662 passages, Reddit-Dialogues, HotpotQA)

## Main claims and findings

- **Attack success rate:** 74.7% of negative-bias injections and 78.0% of positive-bias injections satisfy both Property 1 (high retrieval) and Property 2 (perspective bias); ~90% satisfy at least one property.
- **Adversarial Recall (A-Recall@5) without defense:** at injection intensity 10, adversarial passages fill 98% of the top-5 retrieved slots.
- **Existing diversity defenses reduce A-Recall but crush benign Recall:** MMR and SMART drop A-Recall@5 to 0.23-0.29 at intensity 10 but also cut benign Recall@5 from 0.64 to 0.34-0.35 even in unattacked conditions.
- **BRRA** reduces A-Recall@5 to 0.20 at intensity 10 but drops benign Recall@5 to 0.01 under heavy attack — effectively returning no useful content.
- **Fact-checking is blind to the attack:** 68-69% of adversarial sentences are labeled "NOT ENOUGH INFO" (vs. 71% for benign); among verifiable claims, adversarial passages score 73-79% "SUPPORTS" vs. 63% for benign — appearing more factual, not less.
- **PS Shift in generated answers (No Defense):** 67-357% increase relative to baseline depending on injection intensity and direction; all three LLMs show comparable vulnerability. GPT-4.1 shifts 36-201%, smaller but still large.
- **Model scale does not help:** Llama-3-8B, DeepSeek-R1-14B, and GPT-4.1 show similar PS shifts under attack; the retrieval context, not the model, drives the bias.
- **BiasDef A-Recall@5:** 0.04-0.16 across intensities, beating the best baseline (BRRA: 0.04-0.20) by 15% on average.
- **BiasDef Recall@5:** 0.40-0.55 across conditions; 62% better than the best-performing baseline (SMART) at high injection intensities.
- **BiasDef worst-case A-Recall/Recall ratio:** 0.4 vs. 20 for BRRA and 98 for No Defense — a 2.1x improvement over the next best.
- **BiasDef PS Shift reduction:** 6.2x average reduction in answer PS shift versus undefended baseline; 6.1-8.8x across individual LLMs.
- **73% of queries** achieve complete adversarial filtering with BiasDef.
- **Overhead:** 465 ms average per query (negligible vs. multi-second LLM generation).
- **Theorem 1** (theoretical guarantee): if adversarial passages have strictly higher SS and fully separated PS from benign passages, the KL-maximizing threshold t_ss* guarantees complete adversarial separation.

---

## Comparison against the Epistemic Pipeline project
**We cite it for:** one-sided-but-TRUE evidence beats fact-checkers (we claim >86% attack success, fact-check not-enough-info 0.69 vs 0.71); omission != truth-checking

**Verdict:** partial

**Support check:**
- The qualitative core is well supported. The paper's whole premise is that factually correct but perspectively biased passages crowd out balance and steer the LLM, and that fact-checking is blind to them. The understanding file records adversarial sentences labeled "NOT ENOUGH INFO" at 68-69% vs 71% benign, and (when checkable) adversarial passages scoring *higher* SUPPORTS (73-79% vs 63%) — i.e. they look more factual, not less. So "a fact-checker cannot tell them from balanced ones" and "omission-honesty cannot be reduced to truth-checking" are warranted.
- The number "fact-check not-enough-info 0.69 vs 0.71" matches: adversarial 0.69 (top of the recorded 0.68-0.69 range), benign 0.71. Good match.
- The number ">86% attack success across several models" does NOT cleanly match the understanding file. The file records two attack-success framings: 74.7% (negative) / 78.0% (positive) satisfy *both* Property 1 (high retrieval) *and* Property 2 (perspective bias) — both **below** 86%; and ~90% satisfy *at least one* property — **above** 86%. So ">86%" is defensible only under the looser "at least one property" reading, and our citing sentence does not say which metric it means. This is a soft overclaim / ambiguous figure: under the stricter joint-property metric the real number is 75-78%; only the looser "at least one property" reading (~90%) clears 86%.

**Topical overlap:** The omission frontier — specifically the open "one-sidedness / viewpoint-coverage" gap in the honesty research (`docs/research/2026-06-25-honest-pipeline-omission-frontier.md` §2). It is the load-bearing source for the project's claim that honesty-as-process cannot be reduced to truth-checking, which in turn motivates the worldview app needing a separate coverage/one-sidedness check rather than a true/false verdict. Touches credibility grounding (a "true but cherry-picked" passage exposes why stance/support must not be trusted) and the never-verdict stance.

**Cautions:**
- Automated reader check only. I verified the cited numbers against the project's own understanding file, not against the arXiv body directly; the understanding file claims "Full HTML text read" but I did not re-open the source. A human should confirm the 0.69/0.71 fact-check figures and the attack-success definition in the paper itself.
- The ">86% attack success" figure should be tightened: either cite ~90% and say "satisfies at least one of high-retrieval / perspective-bias," or cite 75-78% for "satisfies both." As written it reads as a single headline number the paper does not state in that form.
- Unreplicated 2026 preprint (the omission-frontier Method section already flags this). The mechanism is a strong design motivation; the exact percentages are provisional.
- The paper is about RAG knowledge-base poisoning (an *attack* and its *detector*, BiasDef). The project uses it only for the negative result that fact-checking misses true-but-biased content. It does not use BiasDef or claim the pipeline has a working one-sidedness detector — consistent with the doc calling this "the open frontier."
