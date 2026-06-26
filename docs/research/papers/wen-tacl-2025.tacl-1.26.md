# Know Your Limits: A Survey of Abstention in LLMs (Wen et al.) (TACL 2025.tacl-1.26)
**Venue / access:** TACL (open). Full text read via arXiv HTML (arxiv.org/html/2407.18418v3).
**Source:** https://aclanthology.org/2025.tacl-1.26/

## What it is about

Abstention is when an LLM refuses to answer rather than generating a wrong or harmful response. This survey maps the entire abstention literature through one unified framework. The framework has three dimensions: whether the query is answerable, whether the model is confident, and whether the response aligns with human values. The authors cover methods across the full model lifecycle — pretraining, alignment, and inference — and review the benchmarks and metrics used to evaluate them. They close by naming what the field still gets wrong: binary abstention decisions, single-turn evaluation, and no standardized cross-domain benchmarks.

## Key topics and concepts

- **Three-perspective framework**: query answerability `a(x) → [0,1]`, model confidence `c(x,y) → [0,1]`, and human value alignment `h(x) → [0,1]` / `h(x,y) → [0,1]`; the refusal function `r` combines them — full abstention if any component equals 0
- **Lifecycle stages**: pretraining (no existing abstention research — a documented gap), alignment (SFT and preference optimization), inference (input-processing, in-processing, output-processing)
- **Uncertainty estimation methods**: token-likelihood, verbalized confidence, Maximum Softmax Probability, temperature scaling, Monte-Carlo Dropout, consistency-based multi-sample aggregation
- **Over-abstention**: heavy safety training causes models to refuse benign queries; excessive safety instructions make models "overly defensive"
- **Calibration failures**: aligned LLMs show poorly calibrated logits and over-confident verbalized scores even when incorrect
- **Bias in abstention**: disproportionate refusal across demographic groups (e.g., African American English queries refused more than White American English equivalents in toxicity-mitigated systems)
- **Partial abstention**: hedged answers and graded uncertainty instead of binary refuse/answer — identified as underexplored
- **Key evaluation metrics**: Abstention Accuracy `ACC = (N₁+N₅)/total`; Reliable Accuracy `R-Acc = N₁/(N₁+N₂+N₄)`; Effective Reliability `ER = (N₁-N₂-N₄)/total`; Abstention Precision `= N₅/(N₃+N₅)`; Abstention Recall/Prudence `= N₅/(N₂+N₄+N₅)`; URUP `= 1 − Recall_abs`; over-abstention rate `ARSP = N₃/(N₁+N₂+N₃)`; Coverage@Accuracy; AURCC; AUACC

## Main claims and findings

- No existing work addresses abstention during pretraining; the authors call this a significant gap and recommend abstention-aware data distribution, curriculum learning, and regularization as open problems
- SFT on abstention-aware data improves refusal capability but risks over-abstention; conflicting findings exist on whether this generalizes across domains
- Parameter-efficient methods (LoRA) act as regularization, reducing both over-refusal and capability degradation
- DPO reduces over-abstention by distinguishing answerable from unanswerable queries and lowers URUP rates relative to SFT baselines
- Verbalized confidence scores demonstrate systematic over-confidence despite explicit prompting to express uncertainty
- Few-shot exemplars of abstained responses and instruction hints ("Answer only if answerable") each show measurable improvements in abstention behavior
- Multi-LLM systems (2+ models) outperform single-model approaches for abstention decisions
- Finetuning with safe datasets can paradoxically undermine safety alignment — the survey documents this as a known vulnerability
- Perplexity-based malicious query detection identifies suspicious content through token-level analysis at inference time
- Abstention mechanisms are vulnerable to prompt engineering, persona attacks, and low-resource language attacks
- The survey covers pages 529–556 of TACL Vol. 13 (2025); arXiv preprint is 2407.18418, latest version v3 (February 12, 2025)
- Key benchmark datasets: SQuAD 2.0 (unanswerable questions), AmbigQA (multiple valid answers), RealTimeQA (current events), PUQA (questions beyond training cutoff), POPQA (long-tail entities), Do-Not-Answer (14 hazard categories), WildGuard (refusal as safety component)
- Major open problem: disagreement persists on whether abstention is a transferable meta-capability across domains or a task-specific behavior

---

## Comparison against the Epistemic Pipeline project

**We cite it for:** abstain on three axes (query under-specification, model confidence, human values), not one threshold
**Verdict:** supports
**Support check:** The project's one usage is in `docs/research/2026-06-25-honest-pipeline-omission-frontier.md` line 22: "the decision to say 'I don't know' depends on *query under-specification*, *model confidence*, and *human values* — and these do not collapse into a single confidence number." The paper's unified framework defines exactly three perspectives: a query perspective (ambiguous/incomplete/insufficient-context = under-specification), a model-knowledge perspective ("insufficiently confident about the correctness of output" = model confidence), and a human-values perspective. The refusal function `r` combines the three components `a(x)`, `c(x,y)`, `h(x,y)` — full abstention if any equals 0 — rather than thresholding one score. The paper states "questions of whether a query is aligned with human values or is answerable at all are difficult to model in terms of model confidence," which directly backs "do not collapse into a single confidence number." No number or quote is attached to this paper in the citing doc, so there is nothing numeric to mismatch. The three-axis reading matches the understanding file (this same file, line 11). No overclaim found: the project uses the paper only for its taxonomy of abstention triggers, which is the survey's central contribution.
**Topical overlap:** Honesty/omission frontier — specifically the abstain-trigger design ("when does the pipeline say 'I don't know'?"). Maps to the Revision policy (R) and Norms layer: distinct abstain triggers for a vague question (O/query under-specification), a thinly-backed belief (low SL confidence mass), and a values/safety conflict. Not directly tied to the C1–C6 credibility-weighting scheme.
**Cautions:** Automated reader, not human-verified. I confirmed the three-perspective framework and the combine-don't-threshold structure via the arXiv HTML (v3) of the same paper the understanding file cites; I did not page-verify the TACL camera-ready (pp. 529–556). The match is on taxonomy/framing, which is robust; a human should still confirm the project's looser gloss "query under-specification" is an acceptable rendering of the paper's broader "query perspective" (which also includes knowledge conflicts and unknowable questions, not only under-specification). This is a peer-reviewed TACL survey, not a preprint, so replication risk is low.
