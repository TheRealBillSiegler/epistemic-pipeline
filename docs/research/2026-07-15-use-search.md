# Deep-research record: what is this good for? (use search)

**Date:** 2026-07-15
**Question:** After the P3 backtest failure, is there any use — any purpose — where the belief ledger fits a real, paying problem? Searched demand-first across six domain clusters.
**Method:** Workflow wf_2ee83f80-415, 15 agents, ~811k tokens. Six domain scouts (regulated assurance; data/knowledge infrastructure; scientific knowledge bases; security/intel; agent/LLM infra; wildcard) returned 28 candidate uses scored against an ideal profile. The top 8 each got an adversarial kill-panel agent applying the six proven walls (W1 human-maintenance, W2 verdict, W3 frontier-accuracy, W4 decomposition, W5 format graveyard, W6 surviving pillars) and fetching the cited demand evidence. Two load-bearing citations failed verification and their candidates were downgraded — the screen worked. Synthesis below is saved verbatim.

---

# Best Use for the Belief Ledger — Decision Synthesis

## 1. The Answer

**Best use:** When a clinical trial is retracted, automatically re-fold every Cochrane meta-analysis that included it, so the pooled result and its downstream guidelines carry a dated "contaminated, needs re-analysis" flag instead of silently citing dead evidence.

**Runner-up:** When a CVE is marked REJECTED/DISPUTED, automatically discount every scan finding, SBOM flag, and risk ticket that cited it — an audit trail of which vulnerability evidence came from which source and what changed.

These two are close. The medical use wins on *verified* evidence and cleanest fit to the one pillar this technology is actually strong at. The CVE use has the bigger paying market and cleaner claim identity, but its key differentiation claim did not survive source-checking.

## 2. Why — the Top Two, Honestly Graded

### Medical retraction re-fold (#1)

**Demand — verified at source, not scout-asserted.** All three citations were fetched and confirmed:
- VITALITY Study I (PMC12015725): 312 retracted trials contaminated 4,095 meta-analyses; dropping the retracted trial flipped effect *direction* in 8.4% of cases and *significance* in 16.0%. Self-correction was near zero. **Verified.**
- Clarivate stopped counting retracted-article citations toward Journal Impact Factor (May 2025). **Verified.**
- Crossref funds the Retraction Watch DB (~$120k/yr). **Verified.**

**Wall survival:**
- **W1 (human maintenance): clean pass.** A retraction is a filed fact, not a human rating. No one maintains anything.
- **W6 (pillars): best fit.** Retraction propagation is the literal headline mechanic. Audit receipt and staleness follow.
- **W3: not applicable.** No LLM panel to correct. Input is a database event.
- **W5: strong pass.** Payer, pain, and distribution all pre-exist.
- **W4 (decomposition): partial hit.** Trial→review linkage is mechanical (RevMan structured data, stable DOI/PMID). Review→*guideline* linkage is **not** shown to be mechanical — NICE had to build bespoke NLP for it. **Drop the "propagates into every guideline" claim until that graph is proven.**
- **W2 (verdict): framing risk.** Subjective Logic cannot recompute a pooled risk ratio — that's DerSimonian-Laird work. Ship a *dated staleness/contamination flag*, not a corrected number.

**Honest caveat (unprompted):** This use barely touches the SL confidence-fusion math — it's mostly retraction propagation plus audit log. That's a real "brand borrowed for the plumbing" pattern. Also, Cochrane is already building an in-house flagging feature (Retraction Watch confirms), so the entry point should be the *missing second half* (the re-fold), sold as an add-on — not a competing platform.

### SCA/SBOM CVE ledger (runner-up)

**Demand — mixed on verification.**
- NVD backlog of 10,000+ unanalyzed CVEs by May 2024. **Verified, widely corroborated.**
- The Endor Labs citation used to justify "incumbents treat disagreement as noise, don't reconcile evidence" — **misrepresented.** That article is about linking binaries to source CPEs, not about CVE-validity disagreement or retraction propagation. **The load-bearing differentiation claim has no support in its own cited source.**

**Wall survival:**
- **W4 (claim identity): the strongest of any candidate.** CVE IDs are textbook stable identity — zero decomposition cost.
- **W6: excellent.** REJECTED/DISPUTED status maps directly to retraction; KEV-exploited vs. disputed maps to conflicted-vs-unexamined.
- **W1: pass**, if calibration free-rides on triage actions engineers already take.
- **W2: real tension.** Security buyers want "do I patch this" — a verdict. Survives only if repositioned to compliance/audit buyers (FedRAMP, PCI, SOC2) who need provable process.
- **W3-cousin risk (untested):** if feeds rarely actually disagree on CVE status, fusion changes no decisions — same dead end as correcting accurate raters.

**Why #2, not #1:** bigger and already-paying market, cleaner claim identity — but the differentiation claim collapsed on verification, and the natural buyer wants the one thing this system can never give (a verdict).

## 3. The Rest — One Line Each

- **Cochrane pooled-effect recompute (0.75):** Same domain as #1, more aggressive framing; survives only if it stops at re-fold-and-flag and leaves the materiality call to a human (W1).
- **GSN living safety cases (0.72):** Real funded buyer (GM job posting verified) and a real active frontier gap (SL safety-argument paper verified); held back by W1 (root-grouping is new human judgment) and W2 (a confidence number becoming a life-safety go/no-go gate). One cited quote looked fabricated.
- **Vuln-management CVE variant (0.6):** Same as runner-up with EPSS/KEV detail; strong W6, but retraction claim rests on a Broadcom article that names "stale DB" not "non-propagation."
- **Agent-memory belief ledger (0.6):** Verified structural gap vs. MemGuard/AgenticMemory and three independent OSS builds converging; but no paying customer, and the cited pain is a temporal-indexing problem, not the multi-source-fusion problem this solves (W3).
- **GDPR/RAG erasure receipts (0.6): dead.** The cited proof-of-pain paper (Ghost Vectors) ships its own cheaper cryptographic fix; a "receipt" can't certify irreversible erasure (W2); 2 of 4 artifact types lack lineage (W4). One fine figure unverifiable.
- **FDA post-market surveillance (0.58): dead.** Both demand citations misread — "$120M" is projected IT *savings*, not spend; calibration needs resolved-cause labels that don't exist at volume (W1); the claim is causation (W2).
- **AML sanctions delisting propagation (0.58):** Real regulated spend and a named delisting-propagation failure, but the buyer needs a match verdict (W2) and incumbents own decision-time screening.
- **DO-178C / DARPA ARCOS traceability (0.55):** Crowded incumbents (Jama, Codebeamer, Ketryx) and binary pass/fail objectives sit close to the verdict wall (W2).
- **Living-guideline GRADE recompute (0.55):** GRADE certainty is a multi-domain human judgment with no clean map onto SL evidence counts (W1); evidence not mechanical.
- **SOC/TIP threat-intel IOC fusion (0.55):** MISP already ships decaying indicators and warninglists; the correlated-feed-dedup gap is real but narrow.
- **Bank model-risk management SR 26-2 (0.5):** Most crowded incumbent field; ValidMind/ModelOp already sell the audit-trail pillar.
- **RAG per-chunk confidence (0.5):** Documented failure numbers but no dedicated budget line; rides general RAG spend.
- **AI-governance decision audit trail, EU Art. 12 (0.5):** Real regulatory demand for logging, but no evidence anyone wants graded confidence over the procedural trail incumbents already sell (claims don't pre-exist, W4).
- **Insurance claims adjudication, NAIC (0.45):** Live regulatory pressure, but claim evidence is human-authored (W1) and retraction value undocumented.
- **Data observability trust score (0.4):** DQLabs/Collibra already ship composite trust scores; entrenched incumbents, no ask for the SL upgrade.
- **Scite citation-stance fusion (0.4):** Claim unit is a citation edge, not an identified claim (W4); no user asking for correlation-correction.
- **Disinfo/OSINT root corroboration (0.4):** Graphika/DFRLab already do root-tracing; freeform social claims hit the decomposition tax (W4).
- **Enterprise KG maintenance (0.35):** Lineage engines already do the simple deprecation-propagation; buyers are maintenance-averse (W1).
- **EU AI Act Art. 12/72 logging (0.33):** Satisfiable by generic logging; no claim identity, no retraction mechanism in the regulation (W4).
- **C2PA provenance confidence (0.32):** Real named gap, but format-adjacent tooling with no demonstrated buyer (W5).
- **Citation manager, claim-level (0.3):** Item-level flagging already free in Zotero/EndNote; claim-level needs a graph researchers won't maintain (W1+W4).
- **Long-horizon agent belief query (0.25):** No payer, and the literature shows the *opposite* failure — agents under-revise, not over-relitigate.
- **Wikidata SL-based deprecation (0.2):** No payer; community has deliberately chosen not to automate this governance call.
- **Cross-vendor APT attribution fusion (0.2):** Needs vendors to expose decomposed evidence they don't produce; reports are narrative (W4).
- **Fraud case management (0.15):** Buyer needs a same-day fraud verdict (W2); no retraction-pain evidence found.
- **LLM eval judge reliability (0.15):** Already bundled inside eval platforms; frontier judges agree ~80-85%, so the correction problem is small (W3).

## 4. Next Test — Top Pick Only (runnable this week)

Retrospective backtest against VITALITY's own published ground truth. No new data, no humans.

**Pre-register before pulling data (salted commitment):**
Sample 50 Cochrane reviews from VITALITY's 847 flagged set (25 known-contaminated, 25 known-clean). Extract included-trial DOIs/PMIDs from structured RevMan data. Match against the Crossref-hosted Retraction Watch DB by stable ID alone — no fuzzy title/author matching.

**Kill threshold, committed now:** if pure stable-ID lookup correctly classifies contamination status on fewer than **45/50** reviews (<90% precision+recall without human disambiguation), W4 kills the "claims pre-exist with stable identity" premise for this domain and the use dies as scoped.

**If it clears:** the trial→review layer is validated as mechanical. The next test applies the identical design one level up (review→guideline linkage) to decide whether the guideline-propagation claim survives or must be permanently dropped.

All inputs are free and public (VITALITY ground truth published, Retraction Watch DB Crossref-hosted, Cochrane review data public). Cost: a join script and an afternoon.

## 5. Honest Floor

A strong use *was* found — but the honesty bar matters here.

The top pick is strong on the axes that were actually verifiable: demand evidence confirmed at source, pain quantified with real percentages, payers already spending adjacent money, mechanical non-judgmental trigger. That is genuinely better-evidenced than the rest of the field.

But two caveats keep it short of a slam dunk:

1. **The top two both under-use the technology.** Neither the medical re-fold nor the CVE ledger leans hard on Subjective Logic fusion or channel calibration — the parts that make this more than a graph DB with a cascade-delete and an audit log. The consistently surviving value across the whole field is **retraction propagation + audit receipts + staleness** — not truth-finding and not fusion-correcting accurate raters. If those three pillars alone don't justify the build, the fuller machinery may not find a home.

2. **Every candidate that needed the fusion math to matter either hit W2 (buyer wants a verdict) or the W3-cousin (sources don't disagree enough to change decisions).** That is a pattern, not noise. The market pull is for the *ledger's bookkeeping*, not its *epistemics*.

Bottom line: build the medical retraction re-fold as a narrow flag-and-audit add-on to Cochrane's existing workflow, run the kill-test first, and price the honest scope — a dated contamination receipt, never a recomputed truth.