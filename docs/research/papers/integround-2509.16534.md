# InteGround (arXiv:2509.16534)
**Venue / access:** arXiv. Full text read via HTML view.
**Source:** https://arxiv.org/abs/2509.16534

## What it is about

InteGround is an evaluation framework for *integrative grounding* — the task of retrieving and verifying multiple interdependent pieces of evidence to support a hypothesis. The paper tests how well NLI models and LLMs verify claims under four evidence conditions: complete, redundant, incomplete, and uninformative. It also benchmarks five retrieval planning strategies. The central finding is that LLMs fill evidence gaps with internal knowledge rather than admitting incompleteness — a systematic reliability failure. Premise abduction is the only planning strategy that consistently improves retrieval over no planning at all.

## Key topics and concepts

- **Integrative grounding**: verifying a hypothesis against multiple interdependent evidence pieces retrieved from external sources
- **Evidence scenario types**: Informative (complete), Redundant (complete + distractors), Incomplete (strict subset), Uninformative (missing required premises)
- **NLI verification**: DeBERTa xlarge/xxlarge as precise but precision-biased verifiers
- **LLM rationalization**: LLMs compensate for missing evidence by filling gaps from parametric memory, not flagging incompleteness
- **Retrieval planning strategies**: query expansion (HyDE-style), atomic fact decomposition, proposition decomposition, premise abduction, self-reflection (history-aware)
- **Premise abduction**: generates the logical premises a hypothesis requires, then uses those to query retrieval — a directed, constraint-based expansion
- **Self-reflection**: iterative planning that uses retrieval history to steer subsequent queries
- **Benchmark datasets**: EntailmentBank (340 items), WiCE (285 items), HotpotQA (500 items), MuSiQue (500 items); 1,625 total

## Main claims and findings

- **NLI models are precise verifiers.** DeBERTa xlarge F1: 85.7% (EntailmentBank), 68.7% (WiCE), 85.8% (HotpotQA), 62.8% (MuSiQue). High precision (96.9% on WiCE, 93.6% on HotpotQA) but conservative recall.
- **LLMs rationalize incomplete evidence.** On incomplete EntailmentBank evidence: Llama 8B scored 18.8%, Claude 3 Sonnet 16.8%, GPT-4o 34.4% — described as "much worse than random performance."
- **LLMs are robust to redundancy.** Claude 3.5 Sonnet: 84.1% accuracy with redundant evidence vs. 85.3% on informative baseline — minimal degradation.
- **Combining LLM + NLI improves detection of incomplete/uninformative cases** but trades off accuracy on genuinely informative evidence.
- **Query expansion degrades retrieval.** Mean Recall@5 drops ~10 percentage points on WiCE vs. no planning (53.6 vs. 64.0 baseline); "almost always led to decreased performance."
- **Premise abduction is the best planning strategy.** Mean Recall@5 across LLMs: 68.3 (EntailmentBank), 61.7 (WiCE), 79.7 (HotpotQA), 73.7 (MuSiQue) — consistently at or above the no-planning baseline (67.7, 64.0, 80.1, 65.2 respectively).
- **Self-reflection rescues undirected methods.** Query expansion improved from ~53.6% toward ~64%+ on EntailmentBank after reflection, by introducing directed bias.
- **Fact and proposition decomposition show limited improvement** due to overly conservative query generation.

---

## Comparison against the Epistemic Pipeline project

**We cite it for:** LLMs rationalize/justify evidence gaps rather than flag them
**Verdict:** supports
**Support check:** The project cites this in `docs/research/2026-06-24-worldview-credibility-and-landscape.md` (C4, line 53) as: LLM verifiers "rationalize incomplete evidence with internal knowledge," wrongly calling incomplete sets "entailment" instead of flagging the gap. Both quoted strings are verbatim from the paper. The abstract reads "they tend to rationalize using internal knowledge when information is incomplete"; a section heading reads "LLM verifiers tend to rationalize incomplete evidence with internal knowledge"; and the results state "LLMs are prone to classify incomplete evidence sets (Inc.) as 'entailment', leading to much worse than random performance on EntailmentBank." The understanding file's numbers (Llama3.1 8B 18.8%, Claude 3 Sonnet 16.8%, GPT-4o 34.4% on incomplete EntailmentBank) are confirmed against Table 3, as is the "much worse than random" phrasing. The citation supports the exact use the project makes of it: justifying C4's rule that the LLM tags evidence *type* only and must not render a stance/support verdict, because LLM verifiers paper over evidence gaps rather than flag them.
**Topical overlap:** Stage-3 evidence credibility, decision C4 (the LLM classifies type, never stance/support). Indirectly reinforces the project's core honesty stance — surface gaps, never paper over them with a confident verdict.
**Cautions:** Automated reader; the body numbers and the "entailment" sentence were verified via the arXiv abstract plus the HTML full-text view, not a human read of the PDF. Unreplicated arXiv preprint (Sept 2025), no peer review. Minor non-load-bearing slip: the understanding file (line 14) glosses the mechanism as "parametric memory," but the word "parametric" does not appear in the paper — the paper says "internal knowledge." The project's actual citation uses "internal knowledge," so the cited claim is clean; only the understanding-file paraphrase overreaches on that one word.
