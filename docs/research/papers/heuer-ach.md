# Improving Intelligence Analysis with ACH (Heuer/Pherson) (ACH PDF)
**Venue / access:** pherson.org (free PDF). **Update 2026-06-26:** now decoded with a real PDF parser (`pypdf`) — FlateDecode is decodable, just not by a naive tag-strip. The body is confirmed at source, including the full process-vs-verdict quote, diagnosticity, and disconfirmation-first scoring. **Correction to the comparison section below:** the quote our docs use is the **handout's** verbatim wording ("obviously… fallible *human* judgment… *ACH* does, however"), NOT misattributed — the 1999 *book* states the same point with different words ("no guarantee… *intuitive* judgment… *Analysis of Competing Hypotheses* does, however"). See `tools/pdf_quote_check.py`. (Original note, now superseded: abstract-only, reconstructed from Wikipedia/secondary sources.)
**Source:** https://www.pherson.org/wp-content/uploads/2013/06/Improving-Intelligence-Analysis-with-ACH.pdf

## What it is about

ACH is a structured analytic technique developed by Richards J. Heuer Jr. during his time at the CIA (1970s–1980s). It forces analysts to evaluate all plausible hypotheses simultaneously rather than building a case for one favored explanation. The core move is to seek disconfirmation: the winning hypothesis is the one with the fewest inconsistencies against the evidence, not the most confirming data. This inverts the natural confirmatory bias of human reasoning. The technique is taught as a practical worksheet method for intelligence analysts and has since spread to law enforcement, cybersecurity, and business intelligence.

## Key topics and concepts

- **Hypothesis-first discipline:** start by listing all plausible explanations before collecting evidence, to avoid anchoring on one story
- **Evidence-hypothesis matrix:** a grid with hypotheses as columns and evidence items as rows; each cell is labeled Consistent (C), Inconsistent (I), or Not Applicable (N/A)
- **Diagnosticity:** the property of an evidence item that makes it useful — diagnostic evidence discriminates between hypotheses (rules some in, others out); non-diagnostic evidence is consistent with all hypotheses and should be down-weighted or removed
- **"Work across" not "work down":** evaluate one piece of evidence against all hypotheses before moving to the next, preventing hypothesis-first tunnel vision
- **Inconsistency focus:** the conclusion favors the hypothesis with the fewest I marks, not the most C marks — a deliberate asymmetry drawn from falsificationist reasoning
- **Sensitivity analysis:** after a tentative conclusion, test whether removing or reinterpreting the most critical evidence items changes the result; if one item flips the conclusion, that item demands extra scrutiny
- **Cognitive biases addressed:** confirmation bias, premature closure, groupthink
- **Auditability:** the matrix is a traceable artifact; another analyst can reconstruct the reasoning path
- **SACH (Structured ACH):** a refinement that allows hypotheses to be subdivided (e.g., "WMD in Baghdad" vs. "WMD in Mosul") for more granular estimates
- **Software implementations:** PARC ACH 2.0 (developed with Heuer by Palo Alto Research Center); Excel-based templates; open-source variants
- **Formalized extensions:** Bayesian integration (Valtorta et al.), subjective logic treatment (Pope & Jøsang), collaborative Bayesian communities (CACHE)

## Main claims and findings

- The primary claim is normative, not empirical: ACH reduces analytic error by forcing systematic consideration of alternatives and centering disconfirmation over confirmation.
- **No original quantitative findings are reported in this document.** It is a 5-page instructional handout, not an empirical study. It does not report accuracy rates, F1 scores, or controlled-trial results.
- The 8-step process (some sources consolidate to 7) is: (1) identify hypotheses, (2) list evidence and arguments, (3) build the matrix, (4) refine by diagnosticity, (5) draw tentative conclusions from inconsistency counts, (6) run sensitivity analysis, (7) report all hypotheses with rejection rationales, (8) identify future indicators that would revise the conclusion.
- The matrix produces numerical totals (inconsistency counts per hypothesis), but the paper explicitly states these totals "must not overrule analysts' own judgments" — the matrix is a cognitive scaffold, not a decision rule.
- The broader ACH literature (not this document) notes "a lack of strong empirical evidence" that ACH measurably reduces confirmation bias in controlled studies — the technique's value rests on theoretical and practitioner grounds, not randomized trials.
- Critics (notably philosopher Tim van Gelder) argue ACH forces too many discrete judgments, misconceives evidence-hypothesis relationships as binary consistent/inconsistent, and cannot represent subordinate argumentation — concerns the document does not address.

---

## Comparison against the Epistemic Pipeline project

**We cite it for:** disconfirmation-first scoring, diagnosticity, MECE precondition; a sound PROCESS can be guaranteed but a correct VERDICT cannot (verify the quoted sentence)

**Verdict:** partial

**Support check:**
- *Disconfirmation-first scoring* — SUPPORTED. The understanding file records the core ACH move as "the winning hypothesis is the one with the fewest inconsistencies against the evidence, not the most confirming data" and "the conclusion favors the hypothesis with the fewest I marks." The omission-frontier doc's "rank a hypothesis by how little evidence is *against* it" matches.
- *Diagnosticity* — SUPPORTED. The file defines it as evidence that "discriminates between hypotheses (rules some in, others out)." The cite's "weight each evidence item by how well it discriminates" matches.
- *MECE precondition* — PARTIAL / INFERRED. The omission doc claims "diagnosticity is only meaningful if the hypothesis set is collectively exhaustive (MECE): a missing true hypothesis makes the scores misleading." The understanding file records "list all plausible hypotheses" but does NOT use the term MECE or state the collective-exhaustiveness precondition verbatim. This is a sound and standard reading of ACH, not a fabrication, but it is the project's framing rather than a recorded quote from this handout.
- **Process-can-be-guaranteed / verdict-cannot — QUOTE MISATTRIBUTED TO THE WRONG SOURCE.** The omission doc and the UI spec carry the verbatim quote: "There is obviously no guarantee that ACH or any other procedure will produce a correct answer... ACH does, however, guarantee an appropriate process of analysis." That sentence is from Heuer's 1999 CIA book *Psychology of Intelligence Analysis* (the doc attributes it correctly to that book). But this catalogued paper is a DIFFERENT work — the Pherson pherson.org 5-page course handout "Improving Intelligence Analysis with ACH." The handout's body could NOT be decompressed (abstract-only access), so the quote cannot be confirmed against THIS document at all. The idea (sound process, no guaranteed verdict) is consistent with ACH's stance, and the understanding file's "totals must not overrule analysts' own judgments... a cognitive scaffold, not a decision rule" supports the same spirit. But the specific quoted sentence belongs to a different Heuer text and is unverified here.
- *Empirical-limits caveat* — the omission doc cites "Mandel et al. 2018; Dhami et al. 2019" for ACH not reducing confirmation bias. The understanding file records the limit ("a lack of strong empirical evidence") but names Tim van Gelder, not Mandel/Dhami. Those two citations are not corroborated by this file; treat them as drawn from the broader literature, not this handout.

**Topical overlap:** Honesty frontier — the omission-frontier research (§1 implementable levers and §3 "the walls") and the UI design spec §9.1 honesty ceiling. ACH is the named scaffold for disconfirmation-first scoring + diagnosticity, and the source of the project's central "honesty-as-process, not verdict" stance. It does NOT touch the C1–C6 credibility scheme or the SL operators directly.

**Cautions:** Automated check, not human verification. Two real issues a human should resolve: (1) the load-bearing process-vs-verdict QUOTE is from *Psychology of Intelligence Analysis* (1999), NOT from the pherson.org handout this file catalogues — either re-cite the quote to the 1999 book or add that book as a separate source; the quote could not be verified against either text by the tool. (2) The understanding file itself is reconstructed from Wikipedia and secondary sources because the PDF's FlateDecode body could not be read, so every "the paper says X" claim about this specific handout is second-hand. MECE and the Mandel/Dhami citations are reasonable but not grounded in this document. The substantive claims (disconfirmation-first, diagnosticity) are well-established ACH facts and low-risk; the misattributed quote is the thing to fix.
