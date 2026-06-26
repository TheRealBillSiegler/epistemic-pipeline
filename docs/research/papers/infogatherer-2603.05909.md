# InfoGatherer (Taranukhin et al.) (arXiv:2603.05909)
**Venue / access:** arXiv (2026 preprint). Full HTML text read.
**Source:** https://arxiv.org/abs/2603.05909

## What it is about

LLM systems often give overconfident answers when the input is incomplete. InfoGatherer fixes this in high-stakes domains (medicine, law) by combining Dempster-Shafer evidential reasoning with document retrieval and strategic follow-up questioning. The system builds a directed acyclic graph of domain variables, extracts Basic Belief Assignments (BBAs) from retrieved documents instead of point probabilities, and fuses those beliefs using Yager's combination rule. It then selects each follow-up question by maximizing expected reduction in Deng entropy — a measure that separates ambiguity from hypothesis conflict. The result is a principled dialogue agent that converges on a correct hypothesis while asking fewer questions than competing approaches.

## Key topics and concepts

- Dempster-Shafer Theory (DST): assigns mass to *sets* of hypotheses, not single values; supports explicit ignorance
- Basic Belief Assignments (BBAs): the DST analog of probability distributions over a power set
- Yager's rule of combination: fuses BBAs while routing conflict to ignorance rather than normalizing it away
- Deng entropy: decomposes uncertainty into nonspecificity (large focal sets) and discord (competing singletons)
- Evidential network: a DAG where nodes are domain variables and edges carry BBA-weighted beliefs
- Shenoy-Shafer belief propagation: local computation of marginal beliefs over the network
- Strategic question selection: greedy policy — reduce nonspecificity first, then discord
- Retrieval-grounded reasoning: LLM proposes network variables and extracts BBAs from retrieved documents, not from parametric memory
- Information-seeking dialogue: the system decides *when* to ask vs. predict, and *what* to ask next

## Main claims and findings

- InfoGatherer outperforms all baselines on both domains with GPT-5-nano:
  - Medical (MedQA, 1,273 instances): **69.3% success in 7.4 turns** vs. UoT 63.8% / 7.6 turns, MediQ 59.1% / 10.7 turns, AoP 41.6% / 2.1 turns
  - Legal (BarExamQA, 211 instances): **66.5% success in 5.9 turns** vs. UoT 32.8% / 4.9 turns, MediQ 27.2% / 9.4 turns, AoP 17.1% / 2.6 turns
- Results hold on Qwen3 32B: medical 68.1% / 7.1 turns, legal 64.3% / 5.4 turns
- Replacing BBAs with point probabilities (IG Bayesian ablation) drops legal success from 66.5% → 61.3% and medical from 69.3% → 67.5%, showing that preserving set-valued uncertainty matters most when evidence is hedged or contradictory
- Removing retrieval and using model-generated references drops legal success from 66.5% → 64.1% and raises turns from 5.9 → 8.2
- Network construction validated on QUITE / ASIA benchmark: mean Structural Hamming Distance 1.4 ± 0.9 edges, edge precision 0.91 ± 0.06, edge recall 0.88 ± 0.08

---

## Comparison against the Epistemic Pipeline project

**We cite it for:** Dempster-Shafer explicit ignorance mass + value-of-information question policy (reduce vagueness first, then break ties, abstain on budget)

**Verdict:** partial

**Support check:** The cite lives in `docs/research/2026-06-25-honest-pipeline-omission-frontier.md` §1, in two bullets (lines 24-25) and the Sources line (line 78). No numbers are attached to InfoGatherer in those bullets, so there is no figure to mis-state.

- "Keep an explicit ignorance mass" — directly supported. This file records "DST assigns mass to *sets* of hypotheses, not single values; supports explicit ignorance" and Yager's rule "routing conflict to ignorance rather than normalizing it away." So mass-on-an-ignorance-set when evidence is vague or conflicting is faithful.
- "reduce vagueness first, then break ties" — directly supported and a faithful rename of this file's "greedy policy — reduce nonspecificity first, then discord" (Deng entropy splits uncertainty into nonspecificity/large focal sets ≈ vagueness, and discord/competing singletons ≈ ties). The "value-of-information" framing matches "selects each follow-up question by maximizing expected reduction in Deng entropy."
- "abstain if a confidence threshold isn't met within a turn budget" / "abstain on budget" — only PARTLY supported by what this understanding file records. The file states the system "decides *when* to ask vs. predict, and *what* to ask next" and that it asks "fewer questions" with reported turn counts (e.g., 7.4 turns). That establishes a predict-vs-ask switch and a bounded number of turns, but the file does NOT explicitly record an abstain rule keyed to a confidence threshold plus a turn/budget cutoff. The cite's abstain-on-budget phrasing is a reasonable inference from the ask-vs-predict + bounded-turns design, not a verbatim mechanism this file captured. Hence partial, not full support.

**Topical overlap:** Honesty / omission frontier (the doc's §1, "honest about the evidence it HAS"). Maps to the pipeline's Subjective-Logic uncertainty mass (the SL `u` term is the explicit-ignorance kin of a DST ignorance set) and to the Evidence (E) component plus a future active evidence-gathering loop in the Revision policy (R). Not a credibility-classifier (C1-C6) or verdict-stance claim.

**Cautions:** Automated reader check, not human verification. (1) The strongest caveat is intrinsic and already flagged in the citing doc's Method note: InfoGatherer is a fresh, unreplicated 2026 arXiv preprint — treat its numbers as provisional and its mechanisms as candidates. (2) The abstain-on-budget element is partly inferred; a human should confirm against the paper body that abstention is actually triggered by a confidence threshold within a turn/budget limit, since this understanding file records only the ask-vs-predict switch and turn counts, not that explicit rule. (3) This comparison was done against the understanding file, not a fresh full-text read, so any body detail not captured in the file is unverified here.
