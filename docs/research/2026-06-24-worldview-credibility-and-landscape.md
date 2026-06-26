# Worldview app: evidence-credibility grounding and prior-art landscape

**Status:** Researched — 2026-06-24. Load-bearing claims independently re-verified.
**Feeds:** the worldview UI design (in progress); the [SL design spec](../superpowers/specs/2026-06-23-worldview-subjective-logic-design.md) open item — `P_R` (source-reliability) grounding; the [UI plan](../superpowers/plans/2026-06-24-worldview-ui-plan.md).

This records two things. First, **how the worldview pipeline can weigh a piece of evidence by its credibility *auditably*** — the open item the SL design left as "`P_R` grounding." Second, **where the worldview app sits among existing tools.** Two deep-research passes gathered the findings (credibility grounding; prior-art landscape).

The deep-research harness's own verification step was rate-limited into abstention, so it falsely reported every claim "refuted." The 14 load-bearing claims below were therefore **re-verified** against their primary sources by a separate adversarial pass: **12 supported, 2 partial (corrected inline), 1 a citation mismatch (corrected).** Sources are cited by link; no paywalled PDFs are stored here.

**Read this first.** The law for this app is: *the app is a window; the pipeline applies the rigor.* The app never invents a judgment — it displays what the pipeline computed. These findings say *how* the pipeline can rank evidence by source quality without faking it. They also draw a hard line: **transparency is achievable now; correctness is not.** A weight that traces to (recorded type + quote + a fixed policy) is *auditable* today. Whether the weight is *right* is calibration — deferred, and the only real judge. This is the same stance as the [SL operator decisions](2026-06-23-sl-operator-decisions-research.md): pick the mechanism whose behavior is interpretable; let calibration decide if it earns its keep.

---

## Part A — Decisions: grounding stage 3 (evidence credibility)

The pipeline stores each belief as a Subjective-Logic opinion (evidence counts `r`/`s` plus an uncertainty mass). Before fusion, each source's evidence is discounted by a reliability in `[0, 1]`. These six decisions say where that reliability number comes from.

### C1 — Classify, then weight: the LLM names the evidence *type*; a fixed policy maps type → reliability. The LLM never emits the number.

**Decision.** An LLM reads an evidence item and assigns it a *type* from a fixed taxonomy, quoting the line that justifies the call. A separate, inspectable policy table maps each type to a reliability weight. The model contributes a category; the pipeline contributes the number.

**Why (experts).** Subjective Logic's discounting operator leaves the number open *by design*. EBSL defines discounting as `g(x)·y` with `g` a scalar in `[0, 1]`, and **explicitly defers how `g` is chosen** ("We postpone the precise details of how the function `g` can/should be chosen") — it even states "We are not claiming that `⊙` is the proper discounting operation" — `⊙` being one specific instance it disclaims, distinct from the generic operator `⊠` of Definition 12 ([EBSL, arXiv:1402.3319](https://arxiv.org/abs/1402.3319), *verified — supported; quote uses `⊙`, corrected 2026-06-26*). So an external policy table is not a hack; it fills a slot the formalism intentionally leaves blank. GRADE — medicine's evidence-grading standard — is the template: it sets a starting grade by evidence type, then adjusts by a *fixed list of named factors*, and does so expressly for transparency, conceding that "any discrete categorisation involves some degree of arbitrariness" but arguing "advantages of simplicity, transparency, and vividness outweigh these limitations" ([Guyatt et al. 2008, PMC2335261](https://pmc.ncbi.nlm.nih.gov/articles/PMC2335261/), *verified — supported*). That is the published defense of a class→weight table: the rigor is in the *enumerable transparency*, not in the numbers being measured.

**Honest standing.** This is defensible because auditable, not because it is correct (see C5, C6). The operator itself is a chosen one, not the truth.

**Would change it.** A worked case where a type→weight policy is provably miscalibrated and a data-driven grounding (e.g. internal conflict metrics, [Sciencedirect S0020025518301658](https://www.sciencedirect.com/science/article/abs/pii/S0020025518301658)) measurably beats it.

### C2 — Set the weights by *ranking* the types and applying a fixed formula, not by hand-picking numbers.

**Decision.** Do not assert "anecdote = 0.3." Assert an *ordering* of evidence types, then derive the numbers from it with a fixed formula.

**Why (experts).** Rank-order centroid (ROC) weights, from the SMARTER method, convert an ordinal ranking into cardinal weights via a closed form — "derived solely from a ranking of attribute importance" ([Barron & Barrett 1996](https://www.sciencedirect.com/science/article/abs/pii/0001691896000108), *verified — supported*; rank `r` of `K` gets weight `(Σ_{h=r}^{K} 1/h)/K`). You defend an ordering — arguable and auditable — and the formula yields the numbers. Even the numbers become principled given the ranking.

**Honest standing.** Minor nuance: ROC formally ranks *swing weights*, not bare "importance." For our use the ranked objects are evidence types, which is a faithful adaptation, not the original framing.

**Would change it.** Evidence that a flat or hand-tuned table calibrates better than the ROC weights for this domain.

### C3 — Use a coarse *source-type* taxonomy, not a study-design hierarchy.

**Decision.** Rank by broad source type (e.g. personal note < opinion < cites-a-source < primary source), or by Walton-style argument types — not by a medical hierarchy of study designs.

**Why (experts).** Evidence hierarchies are **question-type specific**. A hierarchy validated for therapy questions is "not appropriate for assessing studies addressing diagnostic accuracy, aetiology, prognosis or screening," and the same design does not hold the same rank across question types ([Merlin, Weston & Tooher 2009, PMC2700132](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC2700132/), *verified — supported*). A personal vault spans every question type at once, so a single clinical hierarchy would misweight most claims. A coarse source-type taxonomy degrades gracefully across claim kinds; Walton's 96 argumentation schemes are an inspectable alternative ([Walton, Reed & Macagno, *Argumentation Schemes*](https://www.cambridge.org/core/books/argumentation-schemes/9AE7E4E6ABDE690565442B2BD516A8B6)).

**Would change it.** A claim-type classifier good enough to switch among per-type rankings (GRADE's own answer was a separate ranking column per question type).

### C4 — The LLM classifies *type* only. Support direction comes from the SL `r`/`s` rating, never a separate LLM entailment verdict.

**Decision.** Use the LLM to tag *what kind* of evidence an item is. Do **not** ask it to judge "does this support the claim?" That direction is already carried by the confidence rating that splits into `r` (for) and `s` (against).

**Why (experts).** Type-tagging is the LLM's strength and can be made reproducible: zero-shot ChatGPT beats crowd workers by ~25 points on accuracy (against the gold-standard labels), and self-consistency rises to ~97% at temperature 0.2 ([Gilardi et al. 2023, PNAS](https://www.pnas.org/doi/10.1073/pnas.2305016120), *verified — supported*; caveat: "four of five tasks," 25 pts is an average; the 25-pt figure is the accuracy gap, distinct from intercoder agreement). But *stance/support* judgment is weak and unsafe zero-shot:
- Generative LLMs score far below fine-tuned encoders on stance — fine-tuned DeBERTa vs **GPT-3.5, GPT-4, Claude Opus** at **0.94 / 0.47 / 0.51 / 0.57 weighted-F1** (macro-F1 nearly identical: 0.93 / 0.48 / 0.51 / 0.57), a ~37-point gap ([arXiv:2406.08660](https://arxiv.org/html/2406.08660v1) Table 2, *verified against the table — partial: direction holds; the original "0.53–0.61" range was inflated and is corrected here*).
- LLM judges have positional bias large enough to flip aggregate verdicts — reordering let "Vicuna-13B beat ChatGPT on 66 of 80 queries" ([Wang et al. 2024, ACL](https://aclanthology.org/2024.acl-long.511/), *verified — supported*).
- LLM verifiers "rationalize incomplete evidence with internal knowledge," wrongly calling incomplete sets "entailment" instead of flagging the gap ([InteGround, arXiv:2509.16534](https://arxiv.org/pdf/2509.16534), *verified — supported*).

**Honest standing.** Run the type classifier at low temperature for reproducibility. If a harder support judgment is ever needed, prefer a fine-tuned classifier over a zero-shot LLM.

**Would change it.** A zero-shot LLM stance method that closes the gap to fine-tuned models with controlled order and gap-flagging.

### C5 — Ship uniform reliability first. It is a competitive baseline, not a cop-out.

**Decision.** v1 weighs all evidence equally (`DEFAULT_RELIABILITY = 1.0`). The graded policy (C1–C4) is an upgrade switched on only once it can be validated.

**Why (experts).** Bayesian models of source reliability hit a bootstrapping wall: without "a reference class of relevant past predictive success," no accurate reliability estimate is derivable, and "the credulous fixed-trust agent remains surprisingly competitive" ([Merdes, von Sydow & Hahn 2021, *Synthese*](https://link.springer.com/article/10.1007/s11229-020-02595-2), *verified — supported*). So uniform trust is a principled default, and graded weights without calibration data are guesses dressed up.

**Honest standing.** Proven for the two Bayesian models tested (Bovens–Hartmann, Olsson); the authors frame it as a deep structural gap, not a universal impossibility.

**Would change it.** Calibration data (C6) showing the graded policy beats uniform.

### C6 — Calibration is the judge. Validate weights by proper scoring on claims that later resolve.

**Decision.** Treat the credibility policy as unproven until measured. As claims resolve (or the user corrects them), score the system's past confidences with a proper scoring rule and check whether the graded weights improved accuracy.

**Why (experts).** Proper scoring rules (Brier, logarithmic) are minimized only by truthful probabilities. A proper score decomposes into uncertainty, resolution, and **reliability (calibration)** components computable from archived forecast–outcome pairs alone — no external labels (Murphy's decomposition; [Bröcker 2009, *QJRMS*, "Reliability, sufficiency, and the decomposition of proper scores"](https://www.researchgate.net/publication/227532520_Reliability_Sufficiency_and_the_Decomposition_of_Proper_Scores)). Expected Calibration Error bins predictions and compares confidence to outcome frequency.

**Verification catch.** The deep-research run attached the wrong citation here — arXiv:1212.0960 is Jung & Lease, *Evaluating Classifiers Without Expert Labels* (IR crowdsourcing), with no scoring-rule decomposition in it (*verified — refuted; citation corrected to Murphy 1973 / Bröcker 2009*). The result itself is standard and stands; only the auto-attached source was wrong.

**Would change it.** This *is* the change-condition for C1–C5. Until calibration runs, the graded policy stays labelled "transparent, not yet validated."

---

## Part B — Positioning: the open niche

No existing tool combines all four of the worldview app's ingredients. Each cousin has one or two.

| Category | What it has | What it lacks |
|---|---|---|
| Argument mapping — Kialo, [Argdown](https://argdown.org/) (markdown-native) | claim graph, pro/con (support/attack) | no per-claim confidence |
| Computational argumentation — epistemic graphs (graded belief), Carneades (per-claim proof standards), [ASPIC+](https://jair.org/index.php/jair/article/view/18404) | "stability/relevance" = *will a claim's acceptance survive new information* — the theory of the run-by/preview flow (*verified — supported*) | research formalisms, no personal-corpus product |
| Forecasting — [Fatebook](https://fatebook.io/), Metaculus | numeric confidence over time, proper-score calibration | operates on *user-stated future predictions*, not corpus-inferred beliefs; no evidence-to-claim, no contradiction detection (*Fatebook verified — supported*) |
| PKM / Obsidian — [VaultForge](https://github.com/Easonnotsing/VaultForge), [claude-obsidian](https://github.com/AgriciDaniel/claude-obsidian) | authored "contradiction" links + add-only suggest-don't-write (VaultForge); detected cross-note contradictions with cited callouts (claude-obsidian) | only coarse confidence; no explicit uncertainty mass; no replayable evidence trail (*both verified — supported*) |
| Truth-maintenance systems — [JTMS/ATMS](https://cse.buffalo.edu/~shapiro/Papers/br-overview.pdf) | a recorded justification/dependency trail | discrete labels (in/out), no graded uncertainty (*verified — partial: replayable holds for JTMS; ATMS keeps "no record of the intermediate assertions," and "true/false/unknown" is LTMS-specific*) |

**The niche we occupy:** a personal-corpus belief tracker that has *all four* — per-claim **graded uncertainty** (honest "unknown" vs "balanced"), a per-claim **replayable evidence trail**, beliefs **inferred from a corpus** (not hand-entered predictions), and a **deterministic preview** of how new information updates beliefs. Each piece is validated prior art; the combination is open.

**What to borrow:** GRADE (policy shape, C1), ROC (numbers from a ranking, C2), ASPIC+ stability (the preview's formal meaning), proper scoring (calibration, C6), VaultForge's add-only/suggest-don't-write stance (vault write-back).

---

## Still open

- **Vault write-back scope** — how aggressively the app reconciles the user's notes after a belief update. Recommend **additive-only** (save the new source as a note; suggest, never auto-write, annotations on challenged notes); VaultForge ships exactly this stance. Pending the user's call.
- **Credibility calibration (C6)** — the validation that turns the graded policy from "transparent" into "earned." Deferred; this is the project's trust-gate work.
- **The evidence-type taxonomy and its ranking (C2/C3)** — the exact category set and order are not yet fixed.

## Faithfulness audit (2026-06-25)

A later concept-misuse audit (verified) judged the borrowed instruments **defensible adaptations, not misuses** — with caveats that bound the borrowed authority. The pattern: borrowed *authority* does not transfer to *correctness*; each weight must be earned by calibration. See the [omission frontier](2026-06-25-honest-pipeline-omission-frontier.md).

- **GRADE (C1) — borrow the *shape*, not the warrant.** GRADE grades the certainty of a whole *body* of evidence for an *outcome*; several of its factors (inconsistency, publication bias) have no single-item analogue. So GRADE's published defensibility does **not** license a per-item reliability weight — only its transparent, type-anchored, auditable *structure* transfers. A per-item weight is earned by calibration (C6), not by GRADE's name.
- **ROC (C2) — not a neutral default.** ROC's numbers are the centroid of the ranking-constrained simplex — the expected weight under a *uniform prior* over all orderings-consistent weight vectors. That prior, and ROC's simulated edge over Rank-Sum, are conditional on the true-weight distribution (per surrogate-weight robustness studies — Danielson & Ekenberg, *A Robustness Study of State-of-the-Art Surrogate Weights for MCDM*, [10.1007/s10726-016-9494-6](https://link.springer.com/article/10.1007/s10726-016-9494-6)). Choosing ROC over Rank-Sum or a hand-tuned table is itself a modeling assumption to validate by calibration.
- **ECE (C6) — not the standalone judge.** ECE is not a proper score: it is binning-dependent, and a non-informative base-rate predictor drives it to ~0. Use the proper scores (Brier/log) and the Murphy *reliability* term as the primary calibration metric; treat ECE only as a supplementary, binning-disclosed diagnostic.

## Method

Two deep-research passes (evidence-credibility grounding; prior-art landscape), each: decompose → parallel web search → fetch sources → extract claims. The harness's adversarial-verify phase was rate-limited (every vote abstained → a false "all refuted" verdict), so a separate pass re-verified the 14 load-bearing claims against their primary sources, one skeptical agent per claim. Outcome: 12 supported, 2 partial (corrected inline: the stance F1 range; the TMS replay/label scope), 1 refuted-citation (the calibration source, corrected to Murphy/Bröcker). Provenance: workflow transcripts, 2026-06-24.

**Body-level quote check (2026-06-26, deterministic — fetch the paper body + string-match, no model):** the four corrections in this pass were re-verified against the paper bodies, not against any summary — EBSL's `⊙` disclaimer quote and its generic `⊠` operator (ar5iv full text), GRADE's "any discrete categorisation involves some degree of arbitrariness … advantages of simplicity, transparency, and vividness outweigh these limitations" (PMC), Bucher's Table-2 values 0.94 / 0.47 / 0.51 / 0.57 (arXiv HTML), and the "66 over 80" positional-bias figure (ACL). Gilardi's figures were then confirmed via the PMC mirror (PMC10372638), since PNAS blocks raw fetch: "about 25 percentage points on average" (the accuracy gap) and "97% for chatgpt with temperature = 0.2" (intercoder agreement) appear verbatim — which is exactly why the metric-label fix above is needed: the 25-pt figure is accuracy, the 97% is intercoder agreement, two different things. Tool, re-runnable: `tools/quote_check.py`.

## Sources

Credibility grounding:
- EBSL discounting, `g` left free — Škorić, de Hoogh, Zannone: [arXiv:1402.3319](https://arxiv.org/abs/1402.3319)
- GRADE evidence grading — Guyatt et al. 2008: [PMC2335261](https://pmc.ncbi.nlm.nih.gov/articles/PMC2335261/); [gradeworkinggroup.org](https://www.gradeworkinggroup.org/)
- Evidence hierarchies are question-type specific — Merlin, Weston, Tooher 2009: [PMC2700132](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC2700132/)
- Argumentation schemes (alternative taxonomy) — Walton, Reed & Macagno: [Cambridge](https://www.cambridge.org/core/books/argumentation-schemes/9AE7E4E6ABDE690565442B2BD516A8B6)
- ROC weights from a ranking — Barron & Barrett 1996: [ScienceDirect 0001691896000108](https://www.sciencedirect.com/science/article/abs/pii/0001691896000108)
- Bayesian source-reliability bootstrapping — Merdes, von Sydow & Hahn 2021, *Synthese*: [10.1007/s11229-020-02595-2](https://link.springer.com/article/10.1007/s11229-020-02595-2)
- Multi-criteria reliability (data-driven alternative) — [ScienceDirect S0020025518301658](https://www.sciencedirect.com/science/article/abs/pii/S0020025518301658)
- LLM annotation accuracy + temperature reproducibility — Gilardi et al. 2023, *PNAS*: [10.1073/pnas.2305016120](https://www.pnas.org/doi/10.1073/pnas.2305016120)
- LLM stance weakness vs fine-tuned — [arXiv:2406.08660](https://arxiv.org/html/2406.08660v1)
- LLM judge positional bias — Wang et al. 2024, ACL: [2024.acl-long.511](https://aclanthology.org/2024.acl-long.511/)
- LLM verifiers rationalize incomplete evidence — InteGround: [arXiv:2509.16534](https://arxiv.org/pdf/2509.16534)
- Proper-score decomposition for calibration — Bröcker 2009, *QJRMS*: [ResearchGate 227532520](https://www.researchgate.net/publication/227532520_Reliability_Sufficiency_and_the_Decomposition_of_Proper_Scores) (corrects the deep-research run's mis-cite of arXiv:1212.0960)

Landscape:
- ASPIC+ stability/relevance under incomplete information — [JAIR 18404](https://jair.org/index.php/jair/article/view/18404)
- Epistemic graphs (graded argument belief) — [arXiv:1802.07489](https://arxiv.org/abs/1802.07489)
- Carneades (per-claim proof standards) — [Argument & Computation 2012](https://www.tandfonline.com/doi/abs/10.1080/19462166.2012.661766)
- Fatebook (forecasting elicitation/calibration) — [fatebook.io](https://fatebook.io/)
- VaultForge (Obsidian, typed links + add-only) — [github.com/Easonnotsing/VaultForge](https://github.com/Easonnotsing/VaultForge)
- claude-obsidian (contradiction callouts) — [github.com/AgriciDaniel/claude-obsidian](https://github.com/AgriciDaniel/claude-obsidian)
- Truth-maintenance systems overview — Shapiro 1998: [br-overview.pdf](https://cse.buffalo.edu/~shapiro/Papers/br-overview.pdf)
