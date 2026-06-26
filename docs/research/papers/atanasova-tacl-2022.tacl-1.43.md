# Fact Checking with Insufficient Evidence (Atanasova et al.) (TACL 2022.tacl-1.43)
**Venue / access:** TACL (open). Abstract and metadata read from ACL Anthology page and arXiv listing; full body text not directly parseable (PDF binary; no HTML version available). Key numbers confirmed across multiple sources.
**Source:** https://aclanthology.org/2022.tacl-1.43/

## What it is about

Fact-checking (FC) models usually produce a verdict no matter how thin the evidence is. This paper asks: when should a model say "I don't have enough to decide"? The authors build a fluency-preserving method that removes specific pieces of evidence — at the constituent or sentence level — and then measures how well FC models notice what is missing. They also release SufficientFacts, a diagnostic dataset where human annotators label whether each omission matters for the verdict. Finally, they propose a data-augmentation strategy using contrastive self-learning with tri-training to teach models to detect insufficient evidence, and show that doing so improves downstream fact-checking accuracy.

## Key topics and concepts

- **Evidence sufficiency prediction** — a new sub-task: classify whether the retrieved evidence is complete enough to support a verdict
- **Fluency-preserving evidence omission** — a method that removes constituents or sentences from evidence passages without breaking grammaticality, used to create synthetic "missing evidence" examples
- **SufficientFacts dataset** — human-annotated diagnostic set; annotators rated whether each omitted span was important for fact-checking
- **Contrastive self-learning + tri-training** — the augmentation strategy: use the omission method to generate contrastive pairs, then train with tri-training across three Transformer models
- **Three FC datasets** — the paper evaluates across three existing fact-checking benchmarks (names not recoverable from abstract-level fetch)
- **Three Transformer models** — experiments use three different Transformer-based architectures (specific model names not recoverable from abstract-level fetch)
- **Granularity of missing evidence** — adverbial modifiers vs. date modifiers vs. full sentences as distinct omission types with very different detection difficulty

## Main claims and findings

- FC models are poor at detecting missing adverbial modifiers: **21% accuracy** — the worst-performing omission type
- FC models are much better at detecting omitted date modifiers: **63% accuracy** — the best-performing omission type among those tested
- The contrastive self-learning augmentation strategy improves Evidence Sufficiency Prediction by **up to 17.8 F1 points**
- That improvement in evidence sufficiency prediction translates to **up to 2.6 F1 points** gain in downstream FC performance
- The paper is described as the first work to study what information FC models treat as sufficient for making a verdict
- Human annotators (SufficientFacts) and model behavior diverge: models are systematically insensitive to the absence of modifiers that humans judge as critical

---

## Comparison against the Epistemic Pipeline project

**We cite it for:** evidence-sufficiency is a distinct task from which-way-it-leans; detection is weak/uneven (we claim 21% vs 63% by omission type)
**Verdict:** supports
**Support check:** The paper's abstract (verified live against the ACL Anthology page, aclanthology.org/2022.tacl-1.43) backs every load-bearing element of our claim. It introduces Evidence Sufficiency Prediction as "a novel task" and says the authors "are the first to study what information FC models consider sufficient" — this grounds our "distinct task from which way it leans." The two numbers we attach are both exact: "models are least successful in detecting missing evidence when adverbial modifiers are omitted (21% accuracy)" and "it is easiest for omitted date modifiers (63% accuracy)." Our doc reproduces these as "21% accuracy for some omission types, 63% for others" — correct, and correctly framed as the worst-vs-best omission types, which is the paper's own framing of weak/uneven detection. The two F1 figures recorded in this understanding file (17.8 F1 for sufficiency prediction; 2.6 F1 downstream) also match the abstract exactly, though our citing doc does not lean on those. No fabricated quote or wrong number found.
**Topical overlap:** Honesty/omission frontier (omission-frontier doc §1, the only place we cite it). It supports the pipeline's "separate enough-evidence? signal" lever: a sufficiency signal on each belief, kept separate from the belief's lean — and the explicit caveat that such detection is a weak signal, not a guarantee. Adjacent to credibility grading (C1-C6) only loosely; the paper is about sufficiency of a verdict's evidence, not per-item credibility weighting.
**Cautions:** Automated check, not human verification. All numbers were confirmed only against the published abstract; the paper's full body (PDF only, no HTML) was not parsed, so the per-type accuracy table, the three FC datasets, and the three Transformer models behind the 21%/63% headline numbers were not independently inspected. TACL 2022 is peer-reviewed (low replication risk). The claim we draw is conservative — we use the paper as motivation for a sufficiency signal and as evidence that detection is hard, both of which the abstract directly supports. One framing nuance: the paper shows models are *bad* at sufficiency detection; our doc correctly presents this as "a signal, not a guarantee" and does not overclaim a working detector.
