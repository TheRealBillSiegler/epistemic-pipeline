# Merlin et al. — evidence hierarchies (PMC2700132)
**Venue / access:** PMC open access. Full text read via pmc.ncbi.nlm.nih.gov redirect.
**Source:** https://www.ncbi.nlm.nih.gov/pmc/articles/PMC2700132/

## What it is about

Merlin, Weston, and Tooher (2009) extended Australia's NHMRC evidence hierarchy beyond treatment interventions. The original 1999 hierarchy ranked only interventional study designs (Levels I–IV). This paper expands it to cover four additional question types: diagnostic accuracy, prognosis, aetiology, and screening. The authors reviewed 18 existing international evidence frameworks, identified the CEBM hierarchy as the most comprehensive model, and developed a revised five-column matrix. The revised hierarchy became the standard for Australian health technology assessment and clinical practice guideline development.

## Key topics and concepts

- Evidence hierarchies and study design rankings
- NHMRC evidence levels (I–IV): systematic reviews of RCTs at top, case series at bottom
- Five question-type columns: interventions, diagnostic accuracy, prognosis, aetiology, screening
- CEBM (Centre for Evidence Based Medicine) hierarchy as reference model
- GRADE and SIGN grading systems as compatible downstream frameworks
- Quality assessment via validated checklists (separate from level designation)
- Systematic reviews of lower-level evidence retain rank based on included studies
- Ethical feasibility as a factor in hierarchy placement
- Harms assessment and its variation by research context

## Main claims and findings

- The pre-revision NHMRC framework covered only interventional studies in four levels (I–IV); all other question types were unaddressed.
- The authors reviewed **18 existing international evidence frameworks** before selecting CEBM as the best base model.
- The revised hierarchy maintains Levels I–IV but adds **five separate research-question columns**: interventions, diagnostic accuracy, prognosis, aetiology, screening.
- Pilot testing ran from **November 2004 through February 2009**; approximately **a dozen public submissions** informed revisions.
- Six criteria guided the revision: covers all question types, consistency across research areas, supports individual study assessments, grounded in empirical evidence, removes subjective quality terminology, and accommodates feasibility constraints.
- Empirical evidence for design-related bias existed primarily for interventional studies; **only one diagnostic bias study** was identified during development.
- The hierarchy does **not** cover qualitative research or economic analysis.
- Distinguishing aetiological from prognostic questions is flagged as an unresolved challenge.
- Quality assessment requires validated checklists beyond the evidence level designation alone.
- The revised hierarchy is compatible with existing grading systems including GRADE and SIGN.

---

## Comparison against the Epistemic Pipeline project

**We cite it for:** evidence hierarchies are question-type specific
**Verdict:** supports
**Support check:** The claim lives in decision C3 of `docs/research/2026-06-24-worldview-credibility-and-landscape.md` (line 42) and is echoed in the UI spec `docs/superpowers/specs/2026-06-24-worldview-app-ui-design.md` (line 168). C3 attaches one direct quote: a therapy hierarchy is "not appropriate for assessing studies addressing diagnostic accuracy, aetiology, prognosis or screening." Verified verbatim against the PMC full text, which reads "...not appropriate for assessing studies addressing diagnostic accuracy, aetiology, prognosis or screening interventions" — the quote is accurate (C3 simply stops before the trailing word "interventions"). C3's second statement, "the same design does not hold the same rank across question types," is a paraphrase, not a quote, and is directly supported by the paper's "The study designs best suited to answer these types of questions are not always the same, or presented in the same order, as that given in the original NHMRC hierarchy." No number or quote mismatch. The understanding file's summary (five separate question-type columns; original hierarchy intervention-only) matches the source faithfully.
**Topical overlap:** Stage-3 evidence-credibility grounding (the C1–C6 classify-then-weight scheme), specifically C3 — the choice of a coarse source-type taxonomy over a study-design hierarchy. This is the `P_R` source-reliability grounding work, not the (O,E,B,R) core or the worldview app's read-only window.
**Cautions:** Automated reader, not a human verification. The full text was reachable via PMC (open access), so this is not abstract-only; the two load-bearing fragments were checked against the live page. One conceptual nuance a human should note: the project cites this finding to justify the *opposite* design move the paper prescribes. The paper's fix for question-type specificity is *more* granularity (a separate evidence column per question type); the project uses the same finding to defend a *coarse* taxonomy for a personal corpus that spans all question types at once. This is not an overclaim — C3's "Would change it" line explicitly concedes "GRADE's own answer was a separate ranking column per question type," so the divergence is disclosed, not smuggled. The cited fact is reported correctly; the prescription is deliberately not adopted.
