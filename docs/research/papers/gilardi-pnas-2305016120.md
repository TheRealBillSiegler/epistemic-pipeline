# ChatGPT outperforms crowd workers for text annotation (Gilardi et al.) (10.1073/pnas.2305016120)
**Venue / access:** PNAS (open). Full text read via PMC (PMC10372638).
**Source:** https://www.pnas.org/doi/10.1073/pnas.2305016120

## What it is about

This paper asks: can ChatGPT replace human crowd workers for annotating political text? The authors gave identical instructions to ChatGPT, MTurk workers, and trained political science students, then compared results on five annotation tasks across four tweet and news-article datasets (6,183 documents total). ChatGPT used the gpt-3.5-turbo API with zero-shot prompting — no task-specific training. The paper measures accuracy against a trained-annotator gold standard, plus inter-annotator agreement and cost.

## Key topics and concepts

- **Zero-shot text annotation**: labeling text with no task-specific fine-tuning; only a natural-language instruction
- **Crowd-sourcing baseline**: MTurk Masters (>90% approval rate, US-based) as the incumbent annotation method
- **Intercoder agreement**: percent agreement — the fraction of document pairs where two annotators in the same group chose the same label
- **Political text tasks**: relevance filtering, stance detection, topic classification, and frame detection (general and policy frames)
- **Cost efficiency**: per-annotation cost at scale, comparing LLM API to human labor markets
- **Temperature as consistency lever**: lower temperature (0.2 vs. 1.0) increases LLM self-consistency across repeated runs

## Main claims and findings

- ChatGPT's zero-shot accuracy exceeds MTurk workers' accuracy by about 25 percentage points on average across tasks.
- ChatGPT outperforms MTurk on four of five annotation tasks; it performs comparably or better on the fifth.
- Per-task accuracy (ChatGPT, relevance tasks only, vs. trained-annotator gold standard):
  - Content moderation tweets (2020–2021): 70%
  - Content moderation news articles (2020–2021): 81%
  - US Congressional tweets (2017–2022): 83%
  - 2023 content moderation tweets: 59%
- Intercoder agreement (percent agreement metric):
  - MTurk workers: ~56%
  - Trained annotators: ~79%
  - ChatGPT at temperature=1.0: ~91%
  - ChatGPT at temperature=0.2: ~97%
- ChatGPT achieves higher intercoder agreement than both crowd workers and trained annotators across all tasks.
- Correlation between ChatGPT's intercoder agreement and accuracy is positive (Pearson's r = 0.36), validating agreement as a proxy for quality.
- ChatGPT accuracy correlates positively with trained-annotator agreement (r = 0.46): the model does better where humans also agree.
- ChatGPT's advantage over MTurk is larger on harder tasks (r = −0.37 between outperformance and task difficulty).
- Cost: "the per-annotation cost of ChatGPT is less than $0.003—about thirty times cheaper than MTurk."
- The authors conclude LLMs have the potential to "drastically increase the efficiency of text classification."

---

## Comparison against the Epistemic Pipeline project

**We cite it for:** C4 — LLMs are reliable at labeling evidence TYPE/annotation
**Verdict:** supports
**Support check:** The project cites this paper once (credibility doc, C4, line 50) for: "zero-shot ChatGPT beats crowd workers by ~25 points on agreement with trained annotators, and self-consistency rises to ~97% at temperature 0.2." Every number checks out against this understanding file. The ~25-point figure matches "about 25 percentage points on average across tasks." The ~97% matches "ChatGPT at temperature=0.2: ~97%." Both inline caveats are accurate: "four of five tasks" matches the finding that ChatGPT beats MTurk on four of five tasks, and "25 pts is an average" matches "on average across tasks." No fabricated quote or wrong number. Two precision flags, neither fatal to the verdict: (1) The cite phrases the 25-point gap as "on agreement with trained annotators," but in the paper that 25-point figure is an *accuracy* gap (vs. the trained-annotator gold standard), while *intercoder agreement* is a separate metric where ChatGPT scores ~91–97%. The doc blends the two; both numbers are real and both support the point, but they measure different things. (2) The paper's five tasks include stance detection and frame detection — judgments the project deliberately walls off from the LLM under C4. So Gilardi supports the broad claim "LLMs are reliable annotators" but does not specifically isolate "type-tagging good, stance-tagging bad." That finer split is carried by the doc's other C4 citations (arXiv:2406.08660, Wang 2024, InteGround), and the doc pairs Gilardi with them correctly.
**Topical overlap:** Stage-3 evidence credibility, decision C4 (classify-then-weight: LLM names the evidence type, fixed policy maps type → reliability; LLM never judges stance/support). Supports the "LLM type-tagging is reproducible" half of C4.
**Cautions:** Automated reader check, not human verification — I confirmed numbers against this understanding file, not against the PNAS PDF directly, so a human should still confirm the file's recorded figures match the paper. Two scope notes above (accuracy-vs-agreement metric conflation; stance/frame tasks are in-scope for the paper but out-of-scope for the project's LLM role) mean this paper grounds the general reliability claim, not the precise type-only restriction. Paper is peer-reviewed PNAS (not preprint); model is gpt-3.5-turbo, so the absolute numbers are dated and frontier models likely differ.
