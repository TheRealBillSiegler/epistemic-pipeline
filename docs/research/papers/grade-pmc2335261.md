# GRADE: rating quality of evidence (Guyatt et al.) (PMC2335261)
**Venue / access:** BMJ (PMC open access). Full text read via PMC HTML.
**Source:** https://pmc.ncbi.nlm.nih.gov/articles/PMC2335261/

## What it is about

GRADE is a system for grading the quality of evidence and the strength of clinical recommendations. It was developed by an international working group and adopted by over 25 organizations, including WHO and the Cochrane Collaboration. The paper is the first in a five-part series; it explains why formal grading systems matter and lays out GRADE's core structure. It separates two distinct judgments: how confident we are in the evidence, and how strongly we recommend acting on it. Subsequent papers in the series specify numerical thresholds and detailed criteria for each factor.

## Key topics and concepts

- **Quality of evidence**: confidence that an effect estimate is correct, rated on a four-tier scale
- **Strength of recommendation**: how strongly a guideline panel endorses an action, rated as strong or weak
- **Randomized controlled trials (RCTs)**: start at high quality; can be downgraded
- **Observational studies**: start at low quality; can be upgraded under specific conditions
- **Downgrading factors**: five reasons to lower a quality rating
- **Upgrading factors**: three conditions under which observational evidence earns a higher rating
- **Transparency**: GRADE requires explicit, documented rationale for every quality judgment

## Main claims and findings

- **Four quality tiers**, defined by confidence in effect estimates:
  - *High*: "Further research is very unlikely to change our confidence in the estimate of effect"
  - *Moderate*: "Further research is likely to have an important impact on our confidence in the estimate of effect and may change the estimate"
  - *Low*: "Further research is very likely to have an important impact on our confidence in the estimate of effect and is likely to change the estimate"
  - *Very low*: "Any estimate of effect is very uncertain"
- **RCTs start as high quality**; observational studies start as low quality
- **Five downgrading factors** (each can lower the rating by one or more levels): study limitations (risk of bias), inconsistency of results, indirectness of evidence, imprecision, and reporting (publication) bias
- **Three upgrading factors** for observational studies: (1) very large treatment effect (e.g., hip replacement for severe hip osteoarthritis), (2) evidence of a dose-response relationship, (3) all plausible biases would decrease the apparent treatment effect
- **Strong recommendation**: desirable effects clearly outweigh undesirable effects, or clearly do not
- **Weak recommendation**: trade-offs are uncertain — either because evidence quality is low or because desirable and undesirable effects are closely balanced
- **Adoption**: 25+ organizations use GRADE at time of publication; this article does not report accuracy or F1 metrics — it is a methodology paper, not an empirical study

---

## Comparison against the Epistemic Pipeline project

**We cite it for:** GRADE as a transparency-first evidence-grading template (C1/C3); grade the BODY of evidence, not each item
**Verdict:** supports
**Support check:** The project uses GRADE as the published defense of a class→weight table: set a starting grade by evidence type, then adjust by a fixed list of named factors, expressly for transparency. The paper backs this. Confirmed verbatim against the full PMC text: "advantages of simplicity, transparency, and vividness outweigh these limitations" — matches the citation file exactly. RCTs-start-high / observational-start-low and the five downgrading + three upgrading factors are all confirmed. One quote-accuracy flag: the citation file (worldview-credibility doc, C1) puts `"partly arbitrary"` in quotation marks, but that two-word phrase is NOT verbatim in the paper. The paper says "any discrete categorisation involves some degree of arbitrariness" (and, for recommendations, "Some arbitrariness will therefore be associated with placing particular recommendations in categories"). The meaning is faithful; the quoted wording is a paraphrase mis-presented as a literal quote. On "grade the BODY of evidence, not each item": GRADE does grade the certainty of a body of evidence for an outcome, and the project is explicit and honest about this — its faithfulness audit states GRADE's defensibility does NOT license a per-item reliability weight, and that a per-item weight must be earned by calibration (C6), not by GRADE's name. No overclaim found; the project under-claims if anything. Caveat: this first paper of the five-part series states the per-outcome/across-studies framing implicitly; an automated full-text scan did not surface an explicit "for each outcome" sentence here (that detail lives in later papers in the series).
**Topical overlap:** Stage-3 evidence credibility — decisions C1 (classify-then-weight; LLM names type, fixed policy maps type→reliability) and C3 (coarse source-type taxonomy). Maps to the (O,E,B,R) Evidence component and the Norms layer (the fixed, inspectable policy table). Supports the core honesty-as-process stance: rigor lives in enumerable transparency, not in the numbers being measured.
**Cautions:** Automated reader, not human-verified. The `"partly arbitrary"` quote should be corrected in the citation file to the paper's actual wording, or de-quoted as a paraphrase. The "grade the body, not each item" claim is correct for GRADE overall but is implicit in THIS paper; a human should confirm whether the project means to cite the series rather than just part 1 for the explicit per-outcome methodology. The paper is a methodology/consensus statement, not an empirical study — no accuracy/F1 numbers to verify (and none are claimed). Open-access BMJ via PMC, low retraction/replication risk.
