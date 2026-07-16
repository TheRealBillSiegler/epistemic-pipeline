# RedDebate (Asad et al.) (arXiv:2506.11083)
**Venue / access:** arXiv. Full text read via HTML view (arxiv.org/html/2506.11083v1).
**Source:** https://arxiv.org/abs/2506.11083

## What it is about

RedDebate is a multi-agent framework for automated AI safety evaluation. It puts multiple LLMs in structured debate to find and fix unsafe model behaviors. The core insight: isolated agents cannot see their own unsafe blind spots, but adversarial dialogue forces those gaps into view. After each debate round, the system stores safety lessons in persistent memory so the same failure does not recur. The result is continuous, scalable red-teaming without human annotators.

## Key topics and concepts

- **Automated red-teaming:** generating adversarial prompts to surface unsafe model outputs
- **Multi-agent debate:** structured disagreement among LLMs as a reasoning and correction mechanism
- **Three debate strategies:**
  - *PReD (Peer Refinement Debate)*: parallel peer agents all respond to the same red-team prompt
  - *DAReD (Devil-Angel Refinement Debate)*: adds a skeptical "Devil" and a supportive "Angel" auxiliary agent
  - *SReD (Socratic Refinement Debate)*: a questioning agent probes each response for gaps and implicit assumptions
- **Four memory types:**
  - *TLTM (Textual Long-Term Memory)*: natural-language feedback in a vector DB, retrieved by similarity
  - *CLTM (Continuous Long-Term Memory)*: parametric memory via LoRA fine-tuning on accumulated feedback
  - *Unified LTM*: TLTM + CLTM combined
  - *GLTM (Guardrails LTM)*: unsafe patterns converted to executable Colang programmatic controls
- **HarmBench and CoSafe** benchmarks for measuring unsafe-output error rates
- **Agreement rate:** fraction of initially-unsafe responses that debate converts to safe responses

## Main claims and findings

- Baseline single-turn prompting produces a **38.7% error rate** on HarmBench and **7.4%** on CoSafe.
- PReD reduces HarmBench error to **28.8%** (−25.6% relative).
- SReD reduces HarmBench error to **21.0%** (−45.7% relative).
- SReD + Unified LTM reduces HarmBench error to **6.1%** (−84.2% relative).
- SReD + GLTM reduces HarmBench error to **3.6%** (−90.7% relative).
- On CoSafe: SReD alone reaches **4.5%** error (−39.2%); SReD + GLTM reaches **2.5%** (−66.2%).
- SReD achieves the highest unsafe-to-safe agreement rate: **17.0%** on HarmBench.
- LLaMA-based GLTM alone reaches **0.3% error rate** on HarmBench — the single best result reported.
- Debate alone reduces unsafe responses by **17.7%**; combined with memory, reductions exceed **23.5%** (paper's summary figures).
- Three debate rounds are optimal; five rounds show diminishing returns.
- Debate exposes latent vulnerabilities: agents that produce safe initial responses sometimes generate unsafe content when pressed in debate.
- Unified memory outperforms either TLTM or CLTM alone, suggesting the two memory types are complementary.

---

## Comparison against the Epistemic Pipeline project

**We cite it for:** multi-agent red-team debate as a design CANDIDATE; we refuted that it measurably reduces unsafe outputs vs a single model
**Verdict:** supports
**Support check:** The paper appears in exactly two places in the project: the source list of `2026-06-25-honest-pipeline-omission-frontier.md` (line 81) and §4 "Refuted — do NOT claim these," line 52: *"Multi-agent debate measurably reduces unsafe outputs vs a single model. (0–3)"*, reinforced at line 54: *"multi-agent red-team debate [is a] design candidate with motivation, not proven mechanism. Try [it]; don't promise [it]."* Both uses are honest. RedDebate IS a multi-agent red-team debate framework, so it is a valid source for the candidate idea. The "(0–3) refuted" tag is the project's OWN 3-vote verification verdict on whether the claim is a *proven mechanism the pipeline can rely on* — NOT an assertion that the paper's results are wrong. The project attaches NO specific number to this paper in the citing doc, so there is no number to mismatch-check there; all figures live only in this understanding file. The recorded figures are internally arithmetically consistent (PReD 38.7→28.8 = −25.6%; SReD →21.0 = −45.7%; SReD+ULTM →6.1 = −84.2%; SReD+GLTM →3.6 = −90.7%; CoSafe SReD 7.4→4.5 = −39.2%, →2.5 = −66.2% — all verified by local arithmetic).

One nuance a human must hold: the paper's own headline is the OPPOSITE of the project's tag — it reports that debate (PReD, debate-only) does reduce HarmBench error 38.7%→28.8%, and debate+memory cuts it far more. So the project is not contradicting the paper's experiments; it is declining to treat a single unreplicated June-2025 preprint as a proven mechanism, especially because (a) the claim is specifically "vs a single model" and the largest reductions come from memory/guardrails (GLTM, LTM), not debate in isolation — the debate-only effect is the modest 25.6% relative drop — and (b) the project's verification scored the general claim 0/3. This is a defensible, conservative use, not an overclaim.
**Topical overlap:** Honesty/omission frontier — specifically the "refuted claims / design candidates" register of the honest-pipeline research. It informs the omission-detection question (can adversarial dialogue surface a model's own blind spots?) and the meta-epistemic layer's self-critique mechanisms. It does NOT touch the (O,E,B,R) tuple, Subjective Logic weighting, or the C1–C6 credibility scheme.
**Cautions:** Automated reader, not human verification. I confirmed the citing sentences exist and that the recorded numbers are self-consistent; I did NOT re-read the paper body, so I cannot independently confirm the absolute error rates (38.7%, 3.6%, 0.3%, the 17.7%/23.5% summary figures) against arXiv:2506.11083 — they are taken on trust from this understanding file. Unreplicated June-2025 arXiv preprint with no peer review; treat all magnitudes as provisional. The "vs a single model" isolation is the load-bearing distinction — if a human reads the paper and finds debate-only gains are robust and well-isolated from the memory/guardrail confounds, the "refuted" tag would warrant softening to "not yet replicated" rather than "unsupported."
