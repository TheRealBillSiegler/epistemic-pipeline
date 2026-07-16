# Could you be wrong? (Hills) (arXiv:2507.10124)
**Venue / access:** arXiv. Full text read via HTML view (https://arxiv.org/html/2507.10124v1).
**Source:** https://arxiv.org/abs/2507.10124

## What it is about

Hills asks whether a single metacognitive prompt — "could you be wrong?" — can surface biases and omitted evidence that LLMs suppress in their first response. The paper draws on human debiasing research (pre-mortems, prospective hindsight) and applies the same logic to transformer-based models. The core claim is that LLMs already hold the critical knowledge; they just do not volunteer it without an explicit invitation. Three bias categories are tested on ChatGPT-4o, with qualitative replication on Claude Sonnet 4, Gemini 2.5 Pro, and DeepSeek-R1.

## Key topics and concepts

- Metacognitive prompting — asking a model to reflect on its own output after the fact
- Discriminatory bias — stereotyped associations encoded during training (tested via the LLM Word Association Test)
- Metacognitive failure — confidently answering questions the model cannot actually know (fictional medical organ test)
- Evidence omission — initial responses that emphasize popular findings while burying contradictory ones
- Prospective hindsight / pre-mortem — the human psychology technique this prompt mirrors (Herzog & Hertwig)
- Iterative self-critique — exhausting a model's self-correction capacity through repeated metacognitive prompts
- Cognitive behavioral therapy techniques as a potential future debiasing toolkit

## Main claims and findings

- A single follow-up prompt ("could you be wrong?") consistently caused ChatGPT-4o to identify its own discriminatory word associations, explain their cause, and propose corrections — after an initial biased response.
- On the fictional-organ (Glianorex) metacognitive test, ChatGPT-4o identified the fictional nature of the question when asked if it could be wrong. Griot et al. had reported ChatGPT achieved this only **3.7% of the time** in standard multiple-choice format; the metacognitive prompt cleared this barrier in the author's runs.
- On the "too much choice effect," the initial response omitted a major meta-analysis finding **"virtually zero" mean effect size across 50 experiments**. The metacognitive prompt surfaced it immediately.
- Herzog & Hertwig found prospective hindsight improved human decision-making by **"approximately an order of magnitude"** compared to simple second judgments — cited as motivation for the approach.
- Qualitative consistency held across **10+ runs per case** and across all four tested models (ChatGPT-4o, Claude Sonnet 4, Gemini 2.5 Pro, DeepSeek-R1).
- The paper frames LLMs as attentional systems whose biases are latent in vector embeddings and attention heads, not absent — making prompt-based retrieval of counter-evidence structurally plausible rather than coincidental.

---

## Comparison against the Epistemic Pipeline project

**We cite it for:** metacognitive "could you be wrong?" SOMETIMES surfaces latent counter-evidence, NOT reliably (we explicitly refuted the reliable version)
**Verdict:** supports
**Support check:** The citing doc (`docs/research/2026-06-25-honest-pipeline-omission-frontier.md`) uses the paper in exactly the conservative way it claims. Line 50 lists "'Could you be wrong?' *reliably* surfaces counter-evidence" under §4 **Refuted** — kept only as "the model *sometimes* surfaces latent counter-knowledge — not reliably *(1–2)*". Line 54 demotes it to a "design candidate with motivation, not a proven mechanism." Line 80 cites the arXiv id. No number, quote, or finding is attached to the paper in the citing doc, so there is nothing numeric to mismatch — the only claim attributed is the qualitative "sometimes, not reliably." Notably, the project under-claims relative to the paper: the understanding file records that Hills frames the effect as strong ("consistently," "surfaced it immediately," "qualitative consistency held across 10+ runs per case" across all four models). The project deliberately downgraded that optimistic framing. That downgrade is well-warranted: the paper is single-author, small-N, qualitative, and reports no failure rate or controlled reliability statistic — so it cannot license "reliably," and "sometimes" is the honest reading. The citation neither fabricates nor overstates; it accurately resists the paper's own rhetoric.
**Topical overlap:** Honesty / omission frontier (§4 Refuted list and the "design candidates, not proven mechanisms" caveat). Touches the metacognitive-prompt mechanism that the pipeline might use to surface latent counter-evidence — kept as motivation only, never promised. Adjacent to the honesty-as-process stance.
**Cautions:** Automated reader, not a human verification. The understanding file is the only window onto the paper here; I did not re-read the arXiv HTML. The paper itself is an unreplicated single-author preprint with no quantitative reliability measurement (qualitative demonstrations on hand-picked cases, ~10 runs each), so its positive framing is itself weakly supported — which is precisely why the project's "not reliably" downgrade is safe rather than risky. A human should confirm the paper reports no failure-rate statistic before relying on the "sometimes, not reliably" reading as the paper's empirical ceiling.
