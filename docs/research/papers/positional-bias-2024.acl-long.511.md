# LLMs are not Fair Evaluators (positional bias) (ACL 2024.acl-long.511)
**Venue / access:** ACL Anthology (open). Abstract and landing page read in full; PDF binary was unreadable; quantitative details drawn from HuggingFace paper page (which matched the abstract claims).
**Source:** https://aclanthology.org/2024.acl-long.511/

## What it is about

LLM-as-judge pipelines compare two candidate responses and pick a winner. This paper shows that the winner depends heavily on which response appears first in the prompt. Simply swapping the order of candidates can flip the verdict. The authors call this positional bias. They propose three calibration strategies that reduce the bias and bring LLM verdicts closer to human judgments.

## Key topics and concepts

- **Positional bias**: LLM evaluators systematically prefer responses in a fixed slot (GPT-4 prefers the first slot; ChatGPT prefers the second)
- **LLM-as-judge / pairwise evaluation**: using a frontier LLM to score or rank outputs from smaller models
- **Conflict rate**: fraction of query pairs where swapping order reverses the verdict
- **Multiple Evidence Calibration (MEC)**: sample the evaluator k times, each time requiring a chain-of-thought rationale before the score, then aggregate
- **Balanced Position Calibration (BPC)**: evaluate each pair in both orderings and average the results
- **Human-in-the-Loop Calibration (HITLC)**: compute Balanced Position Diversity Entropy to flag high-uncertainty cases for human review
- **Vicuna Benchmark**: the 80-query benchmark used for experiments

## Main claims and findings

- Swapping candidate order changed ChatGPT's verdict on 82.5% of Vicuna-vs-ChatGPT queries and 52.5% of Vicuna-vs-Alpaca queries (conflict rates)
- GPT-4 conflict rates were lower but still substantial: 46.3% on Vicuna-vs-ChatGPT queries and 5.0% on Vicuna-vs-Alpaca queries
- Vicuna-13B's win rate against ChatGPT (evaluated by ChatGPT) ranged from 2.5% to 82.5% depending solely on which position Vicuna occupied — a 80-percentage-point swing
- The combined MEC+BPC calibration raised evaluator accuracy by +9.8% for GPT-4 and +14.3% for ChatGPT relative to uncalibrated baselines
- With HITLC routing 20% of cases to human review, ChatGPT reached "comparable or even better annotation alignment with average human performance"
- The HITLC approach reduced annotation costs by 39% compared to full human annotation while maintaining quality

---

## Comparison against the Epistemic Pipeline project

**We cite it for:** LLM-as-judge has order/positional bias; we cite a Vicuna-13B-beats-ChatGPT 66/80 result — verify it
**Verdict:** supports
**Support check:** The "66 of 80" number is verbatim from the abstract: "Vicuna-13B could beat ChatGPT on 66 over 80 tested queries with ChatGPT as an evaluator." The citing line in `docs/research/2026-06-24-worldview-credibility-and-landscape.md` (line 52, decision C4) quotes it as "Vicuna-13B beat ChatGPT on 66 of 80 queries" — accurate paraphrase, correct count. 66/80 = 82.5%, which is consistent with this understanding file's "up to 82.5% win rate" framing (line 23); the two are the same fact expressed as a count vs a percentage, not a contradiction. The paper's core finding — that pairwise LLM-as-judge verdicts can be flipped at the aggregate level by reordering candidates — directly supports the project's use: C4 invokes it as a reason to NOT let the LLM emit a stance/support judgment, only an evidence *type*. The framing is faithful to the paper; no overclaim found.
**Topical overlap:** Touches credibility decision C4 (LLM classifies type only; stance/support never comes from a zero-shot LLM verdict). Indirectly supports the project's core honesty-as-process stance: an order-sensitive judge is exactly the kind of unreliable verdict the pipeline refuses to issue.
**Cautions:** Automated check only — verified against the open ACL abstract, which states the 66/80 figure directly. The body-level claims in this understanding file (conflict rates 82.5%/52.5%, MEC+BPC +9.8%/+14.3%, HITLC 39% cost reduction) come from a HuggingFace paper page per the header note and were NOT re-verified against the PDF here (PDF binary was unreadable). Those secondary numbers are not the ones the project relies on, so the cited claim stands; a human should still confirm the body figures if they ever get cited. Published ACL 2024 long paper, not a preprint — replication risk is low.
