# Faithfulness gate — what the attribution literature directs (issue #26)

**Status:** Researched — 2026-07-01.
**Feeds:** the forthcoming #26 faithfulness-gate design spec; sibling to root-keyed fusion ([#25 design](../superpowers/specs/2026-06-26-shared-source-root-keyed-fusion-design.md)).
**Method:** one deep-research pass — 5 search angles, 21 sources fetched, 92 claims extracted, 25 adversarially verified at 3 votes each (kill on 2/3 refutes). Result: 24 confirmed, 1 refuted, 0 unverified. Provenance: workflow `wf_fd60c41f-951`, 2026-07-01. Sources cited by link; no paywalled PDFs stored.

**Read this first.** Two axes, not one. *Faithfulness* asks "does the cited source contain the claim?" *Truth* (factuality) asks "is the source right?" A claim can be faithful and false, or true and unfaithful. #26 gates faithfulness only. The app never issues a truth verdict (project stance). The literature below confirms this split is standard, and tells us exactly where a deterministic check can sit and where it cannot.

## The finding that decides the design

> **You cannot get both faithfulness-by-construction and standalone claims from a single mechanical copy.**

The confirmed sources converge on one trade-off:

- A **verbatim span** gives faithfulness for free. It is trivially in the source, so a copy cannot fabricate. A string match catches any invented quote with certainty.
- But **~70% of verbatim spans are not self-contained** (Choi et al. 2021). "It grew 10%" (grew *what*? *when*?) is faithful but useless as a belief handle.
- Making a span standalone is **inherently abstractive**. The best abstractive extractor measured (Claimify) reaches **99% entailment, never 100%**. Rewriting to add context is where fabrication re-enters.
- A **pure string match** catches fabricated quotes but is **silent on entailment** (does the quote support the belief you attached?) **and silent on truth** (AIS, GopherCite both: support does not imply truth).

**Design consequence.** Put the mechanical guarantee on the **verified quote (the grounding), not the claim text (the belief handle)**. The two cannot be collapsed into one mechanical step. Turning a verbatim span into a standalone, cross-document-bucketable concept is non-mechanical and stays a deferred residual (the same cross-document clustering problem #25 left open in §10).

This also sharpens the project's working position, "extracting a claim is a mechanical process":

- **True for the faithfulness half.** The copy is mechanical and gives a deterministic 100% gate. The instinct is right, and the literature backs it.
- **False for the belief-handle half.** The worldview app buckets beliefs by concept id, so "the same" claim must match across documents. Two documents never emit byte-identical spans for one claim, so verbatim chunks do not cluster on their own. That step is not mechanical.

## Confirmed findings (each 3-0 verified against primary sources)

### F1 — FActScore and SAFE are abstractive, and they check factuality, not faithfulness

FActScore (Min et al., EMNLP 2023) and SAFE (Wei et al., NeurIPS 2024) both use an **LLM to generate** atomic facts — they resolve pronouns and inject subjects ("He was born" → "Barack Obama was born"), which is generative, not verbatim copying. Both then verify each fact against an **external** knowledge source: FActScore against Wikipedia, SAFE against Google Search. Neither has a *cited* document to check against. So they answer "is this supported *somewhere*?" (factuality), not "does *this* source say it?" (faithfulness). That gap is exactly what #26 fills.

- Sources: [FActScore (ACL)](https://aclanthology.org/2023.emnlp-main.741/), [arXiv 2305.14251](https://arxiv.org/abs/2305.14251), [repo](https://github.com/shmsw25/FActScore); [SAFE arXiv 2403.18802](https://arxiv.org/abs/2403.18802), [NeurIPS 2024](https://proceedings.neurips.cc//paper_files/paper/2024/hash/937ae0e83eb08d2cb8627fe1def8c751-Abstract-Conference.html).

### F2 — Claimify targets extraction faithfulness, but reaches 99%, not 100%

Claimify (Metropolitansky & Larson, Microsoft, ACL 2025) is an **LLM-based** claim extractor. It explicitly requires each claim to be **entailed** by the source and **decontextualized** (understandable on its own), and reports **99% of extracted claims are entailed by their source sentence**. This proves the extraction-faithfulness *problem* is real (LLM extraction can introduce unsupported content) and that measurement mitigates it — but 99% is not the 100%-by-construction a verbatim gate gives.

- Sources: [arXiv 2502.10855](https://arxiv.org/abs/2502.10855), [ACL 2025](https://aclanthology.org/2025.acl-long.348/), [MS blog](https://www.microsoft.com/en-us/research/blog/claimify-extracting-high-quality-claims-from-language-model-outputs/).

### F3 — Verbatim spans are often not self-contained (Choi et al.)

Choi, Palomaki, Lamm, Kwiatkowski, Das & Collins (TACL 2021) define decontextualization as "taking a sentence together with its context and rewriting it to be interpretable out of context, while preserving its meaning." They state plainly: "Taking excerpts of text can be problematic, as key pieces may not be explicit in a local window." About **70% of sentences need edits** to stand alone. This is the empirical core of the trade-off above.

- Sources: [TACL 2021](https://aclanthology.org/2021.tacl-1.27/), [arXiv 2102.05169](https://arxiv.org/abs/2102.05169).

### F4 — GopherCite pairs answers with verbatim verified quotes and can abstain

GopherCite (Menick et al., 2022, DeepMind) trains a model to answer *with* a verbatim supporting quote drawn from retrieved documents, and it can decline to answer. It also states the wall directly: "not all claims supported by evidence are true." So a quote check is a support check, never a truth check.

- Source: [arXiv 2203.11147](https://arxiv.org/abs/2203.11147). See correction C1 on the abstention trigger.

### F5 — AIS separates attribution from truth

The AIS framework — Attributable to Identified Sources (Rashkin et al., arXiv 2021 / *Computational Linguistics* 2023) — defines attribution operationally: a pair is attributable to source parts P if a generic hearer would affirm "According to P, s." The paper is explicit that "this definition of attribution is distinct from truth," and that judging truth needs a *separate* source-quality evaluation. A statement can be attributable yet false. This grounds the faithfulness-vs-truth split #26 is built on.

- Sources: [CL 2023](https://aclanthology.org/2023.cl-4.2/), [arXiv 2112.12870](https://arxiv.org/abs/2112.12870). See correction C4 on what the test measures.

## Corrections to the pre-research characterization

The verifier caught five places where the initial framing was loose or wrong. Recorded here so the spec does not inherit the errors.

- **C1 — GopherCite's abstention is a confidence threshold, not a "no quote found" trigger.** It abstains when a reward-model score falls below a threshold (selective prediction). The reward model scores plausibility *and* quote-support jointly, so they correlate, but the trigger is confidence. **The abstain-on-missing-verbatim-span rule (`g=0`) is our design choice, not GopherCite precedent.**
- **C2 — Claimify *adds* context to make claims standalone; it does not "decontextualize from the source."** And its faithfulness is achieved by measurement (99%), not guaranteed by construction.
- **C3 — Choi et al. do not call decontextualization a "faithfulness risk."** They frame it as conservative, meaning-preserving editing. The "rewriting reintroduces hallucination risk" reading is *our* inference (defensible, but ours). "Abstractive" is also a loose label for their minimal edits (pronoun swaps, name completion), not summarization-style abstraction.
- **C4 — AIS is a support/entailment test, not a verbatim-string test.** It asks whether a hearer would affirm "According to P, s." So AIS grounds the faithfulness/truth *split*; it is **not** precedent for verbatim string matching.
- **C5 — FActScore/SAFE verify against external knowledge, not a cited document.** They are factuality checks, structurally unable to be faithfulness checks (folded into F1).

The one refuted claim (0-3): a skeptic argued Claimify is "confidence-gated, not entailment-checking." Refuted — entailment is confirmed from the blog and full paper. The refutation *confirms* F2.

## Not adjudicated — do not treat as confirmed

Three of the eight fact-check targets did not survive into the 25-claim verify batch (budget), so they are neither confirmed nor refuted:

- **#6 ClaimBuster (Hassan et al., KDD 2017) / CLEF CheckThat!** — check-worthiness as a *learned* task, not a deterministic rule. Source-corroborated at fetch (KDD'17 paper frames it as supervised classification), but not adversarially verified. Bearing: a deterministic gate still needs a *selection* step ("which spans are claims?"), and if selection is inherently learned, one non-deterministic component re-enters the pipeline.
- **#7 sub-sentence "atomic" claims beat sentence-level chunking for verification** — open, not adjudicated.
- **#8 ALCE (Gao et al., EMNLP 2023) evaluates citations by NLI entailment, not string match** — source-corroborated (the repo runs an NLI model: premise = passage, hypothesis = claim), but not verified. Bearing: ALCE is the closest published analogue to the entailment step a gate would need *after* verbatim extraction.

## Two load-bearing sources, read in full (2026-07-01)

I fetched the full text of the two most design-relevant leads. Primary source, direct-read — but note: read by me, not run through the workflow's 3-vote gate.

### F6 — Worledge et al.: the spectrum gives us the design vocabulary and a verifiability curve

The paper names **five operating points** from extractive to abstractive. They map almost exactly onto our fork:

1. **Extractive** — raw source snippets; citation is inherent (the span *is* the source).
2. **Quoted** — word-for-word quotes inline, clearly demarcated, minimal connective text.
3. **Paraphrased** — reworded, same content, nothing added or removed.
4. **Entailed** — removal / contraction / rewording allowed, no new claims (source ⇒ output).
5. **Abstractive** — may contain uncited claims.

Human study: 31 annotators, 480 queries, 7 systems; metrics for fluency, perceived utility, citation precision, citation coverage, and time-to-verify. **Citation coverage by operating point: Quoted 97%, Paraphrased 96%, Entailed 85%, Abstractive 43%.** So faithfulness holds near-perfectly through Paraphrased, loses ~11 points at Entailed, and collapses at Abstractive.

Per-domain recommendation: **high-stakes, dispersed-information tasks → Extractive / Quoted** (verifiability prioritized, minimal model transformation). That is our app's category.

The cost of pure Extractive, quantified: **lowest** fluency and utility — 91.4% of quoted outputs were rated below top fluency, "source snippets often contain irrelevant information," they cannot synthesize across sources, and they cannot reformulate for reading level. This is Choi's "not standalone" problem, measured in a human study.

**Design mapping.** Gate the *grounding* at Quoted (verbatim, demarcated). Allow the human-readable *belief handle* to sit at Paraphrased (96% coverage, far more usable). Never let anything faithfulness-bearing reach Entailed or Abstractive. The 97/96/85/43 curve is the citation for that boundary.

### F7 — Wanner et al. (DnDScore): decontextualization is consequential, in both directions

DnDScore verifies an atomic subclaim while *showing the verifier the decontextualized form as context*, so "which part do I check?" is unambiguous (prompt gives reference doc + subclaim + its decontextualized form; asks true/false on the subclaim). The load-bearing number: across decomposed vs decontextualized subclaims, **19.11% of verification judgments change** —

- **16.25% flip false → true**: a bare span was wrongly rejected because it was not self-contained (missing subject/pronoun). Example: "She has appeared in several television series" → false; "Susan Sarandon has appeared in several television series" → true.
- **3.26% flip true → false**: decontextualization *added wrong context* and broke a true claim.

Both directions bear on us. The 16.25% is the cost of checking bare verbatim spans — they get unfairly rejected for lack of context, which is exactly why a raw span is a poor belief handle. The 3.26% is corrections C2/C3 quantified: making a claim standalone introduced a fresh error about 3 times in 100. The paper's fix: never verify a decontextualized claim in isolation — pair the atomic span with its decontextualized form, and deduplicate redundant context (decontextualize-then-decompose inflates scores).

**Design mapping.** This is the empirical case for keeping the two layers separate. String-match the verbatim span for the deterministic faithfulness gate. Do NOT run the decontextualized concept-handle through the same faithfulness check as if it were verbatim — by these numbers it would falsely reject ~16% (missing context) and falsely flip a further ~3% (added context). If an entailment layer is ever added above the string match, DnDScore's paired-verification recipe is the method to copy.

## Remaining leads (abstract-only, unverified)

ID-verified (title / authors / year confirmed 2026-07-01) but read only at abstract depth; claims not verified.

- **VeriFastScore: Speeding up long-form factuality evaluation** — Rajendhran, Zadeh, Sarte, Li & Iyyer, 2025 ([arXiv 2505.16973](https://arxiv.org/abs/2505.16973)). Fine-tunes one model to *jointly* extract and verify claims.
- **VeriFact: Enhancing Long-Form Factuality Evaluation with Refined Fact Extraction and Reference Facts** — Liu, Zhang, Munir, Gu & Wang, 2025 ([arXiv 2505.09701](https://arxiv.org/abs/2505.09701)). Refined fact extraction checked against reference facts.
- **A Question Answering Framework for Decontextualizing User-facing Snippets from Scientific Documents** — Newman, Soldaini, Fok, Cohan & Lo, **2023** ([arXiv 2305.14772](https://arxiv.org/abs/2305.14772)). QA-based decontextualization: rewrite a snippet to stand alone via question generation → answering → rewriting. Note the year — contemporaneous with Choi et al., not recent work.

## Design-validation pass (2026-07-01, run wf_5add7979)

A second deep-research pass stress-tested the proposed #26 design (D1–D7) adversarially — 5 angles, 21 sources, 94 claims, 25 verified (19 confirmed, 6 refuted). **Verdict: the design holds only as a cheap fabrication screen, not as a faithfulness guarantee. Calling it a "faithfulness gate" overreaches what a presence check delivers.** Five confirmed problems:

**V1 — Value ceiling (the big one; multiple claims 3-0).** A presence-only check catches only fabricated/nonexistent quotes — the *rarest* attribution error. The dominant failures are a real, present quote that does **not** support the claim (entailment failure) and cherry-picking. ALCE (Gao et al., EMNLP 2023, [arXiv 2305.14627](https://arxiv.org/abs/2305.14627)): even the best models "lack complete citation support 50% of the time" on ELI5, where the cited passages *exist* — presence is trivially satisfied, entailment fails. "Cited but Not Verified" ([arXiv 2605.06635](https://arxiv.org/abs/2605.06635); corporate preprint, indicative only): present-and-relevant citations fail factual support 23–76%. D7 already concedes the gate skips entailment, so this is self-consistent — but the gate screens the rarest class while most attribution errors survive.

**V2 — Feasibility / brittleness (3-0).** Free-form LLMs do not reproduce source text verbatim by default; they silently fix typos, capitalization, and factual errors (Semin et al., "Strategies for Span Labeling with LLMs," [arXiv 2601.16946](https://arxiv.org/abs/2601.16946); single source). D5's normalization (whitespace + smart-quotes/dashes) neither case-folds nor tolerates edits, so exactly those deviations become false negatives — a strict substring gate rejects valid claims at a punishing rate. Production quote/citation/plagiarism systems normalize then use fuzzy/fingerprinting (Winnowing, SIGMOD 2003); exact matching detects only exact copies. GopherCite needed constrained decoding to *guarantee* verbatim quotes.

**V3 — Architecture / SOTA (3-0).** State-of-the-art grounding verification is NLI/entailment-based, not string matching. ALCE verifies support with a fine-tuned NLI model (TRUE, T5-11B); entailment-based AutoAIS correlates best with human judgment (ROC-AUC ~92.6%, [arXiv 2406.15264](https://arxiv.org/abs/2406.15264)). The 2023–2026 literature treats surface string matching as the fabrication-prone shortcut and "does the source *support* it" (entailment) as the floor — the layer D7 declines.

**V4 — Post-rationalization (3-0 on mechanism).** Requiring a quote per claim risks the LLM stating a claim from priors, then attaching a topically-aligned quote it did not derive from ("Correctness is not Faithfulness in RAG Attributions," Wallat et al., [arXiv 2412.18004](https://arxiv.org/abs/2412.18004); named "prevalent" — a specific 57% figure was refuted in verification, do not cite it). So requiring quotes does not by itself guarantee genuine grounding.

**V5 — Drop bias (3-0, single source, medium confidence).** Dropping (g=0) ungrounded claims biases the belief set: some true claims need multiple pieces of evidence plus a logical argument, so a single-span gate excludes valid multi-sentence inferences (GopherCite limitations, [arXiv 2203.11147](https://arxiv.org/abs/2203.11147)). D6's intra-document scope aggravates it.

**Single most-strengthening change (per the pass):** add an entailment check that the verbatim span actually supports the belief handle — the layer D7 declines, the field's SOTA implements, and it stays inside faithfulness-not-truth (entailment ≠ truth). Constrained decoding was explicitly *down-voted* (0-3) as the top fix.

Caveats: most V1/V3/V4 evidence studies RAG generation citing document-IDs, not ingest-time span extraction; the failure modes transfer by analogy, and the core critique rests on D7's own concession. [arXiv 2605.06635](https://arxiv.org/abs/2605.06635) is a non-peer-reviewed corporate preprint. V2 and V5 rest on single primary sources (both 3-0). Refuted over-claims not relied on: the 57% post-rationalization figure, constrained-decoding-as-top-fix, "every production scheme lowercases," the LLMQuoter semantic-judge claim.

## What a deterministic verbatim check can and cannot catch

- **Can:** a fabricated or nonexistent quote — with certainty. This is a sound *lower bound* on attribution.
- **Cannot:** whether the quote actually entails the belief attached to it (needs NLI / a support judgment); whether the source is true (never — the truth axis); a semantic restatement that carries no explicit quote (the dependence information was destroyed upstream — the same residual as #25 §10).

## Measurement — path A probe (2026-07-01)

To decide whether the deterministic screen earns its place before building it, I ran a one-off probe (`scratchpad/measure/`): 5 sample documents (factual news, scientific abstract, informal note, an inference-inviting argument, and one with smart quotes / dashes / a hyphen-linebreak), 5 blind subagents acting as the extraction LLM — each emitting `{claim, confidence, verbatim quote}` per the proposed D2 contract — and a stdlib checker scoring each quote as strict-present / lenient-present / fuzzy / absent.

**Result (n = 34 claim/quote pairs):**

- Fabrication (quote absent from source under any normalization): **0 / 34 (0%)**.
- Strict-gate false negatives (a real quote the original D5 would wrongly reject): **0 / 34 (0%)** — strict D5 admitted all 34; the smart-quote / en-dash / em-dash cases in the messy doc were handled by the fold step.
- The deterministic gate would therefore have **rejected nothing** and **added nothing** in this regime.

**What it shows.** A capable model, explicitly asked for verbatim quotes, on clean digital text, does not fabricate quotes. Per the project's evidence-triggered build rule (root-keyed spec §8), a fabrication gate is premature in this regime.

**Caveats — this is a lower bound, not a clearance:**

- n = 34, one capable model, clean digital text. Weaker / cheaper extraction models plausibly fabricate more.
- The PDF hyphen-linebreak stress never fired (no quote crossed it), so strict-vs-lenient brittleness is **untested on real PDF-extracted text** — the one place strict matching could still hurt (V2).
- Presence ≠ support, visible in-sample: doc 4's claim "nuclear can operate safely at scale over the long term" rests on a quote only about France's record — a mild over-reach the presence gate would admit. The dominant failure mode (V1) shows up even here, and the gate is blind to it.

**Triggers that would revive the gate:** deploying a weaker extraction model, or ingesting real PDFs (re-measure fabrication + strict-false-negatives on those first).

## Sources

- FActScore — Min et al., EMNLP 2023: [ACL](https://aclanthology.org/2023.emnlp-main.741/), [arXiv 2305.14251](https://arxiv.org/abs/2305.14251), [repo](https://github.com/shmsw25/FActScore)
- SAFE / Long-form factuality — Wei et al., NeurIPS 2024: [arXiv 2403.18802](https://arxiv.org/abs/2403.18802), [proceedings](https://proceedings.neurips.cc//paper_files/paper/2024/hash/937ae0e83eb08d2cb8627fe1def8c751-Abstract-Conference.html)
- Claimify — Metropolitansky & Larson, ACL 2025: [arXiv 2502.10855](https://arxiv.org/abs/2502.10855), [ACL](https://aclanthology.org/2025.acl-long.348/), [blog](https://www.microsoft.com/en-us/research/blog/claimify-extracting-high-quality-claims-from-language-model-outputs/)
- Decontextualization — Choi et al., TACL 2021: [ACL](https://aclanthology.org/2021.tacl-1.27/), [arXiv 2102.05169](https://arxiv.org/abs/2102.05169)
- AIS — Rashkin et al., CL 2023: [ACL](https://aclanthology.org/2023.cl-4.2/), [arXiv 2112.12870](https://arxiv.org/abs/2112.12870)
- GopherCite — Menick et al., 2022: [arXiv 2203.11147](https://arxiv.org/abs/2203.11147)
- ALCE — Gao et al., EMNLP 2023 (*corroborated, unverified*): [ACL](https://aclanthology.org/2023.emnlp-main.398/), [repo](https://github.com/princeton-nlp/ALCE)
- ClaimBuster — Hassan et al., KDD 2017 (*corroborated, unverified*)
- Extractive-Abstractive Spectrum — Worledge et al., 2024 (*full text read 2026-07-01; not 3-vote verified*): [arXiv 2411.17375](https://arxiv.org/abs/2411.17375)
- DnDScore — Wanner, Van Durme & Dredze, 2024 (*full text read 2026-07-01; not 3-vote verified*): [arXiv 2412.13175](https://arxiv.org/abs/2412.13175)
- VeriFastScore — Rajendhran et al., 2025 (*lead; ID verified 2026-07-01*): [arXiv 2505.16973](https://arxiv.org/abs/2505.16973)
- VeriFact — Liu et al., 2025 (*lead; ID verified 2026-07-01*): [arXiv 2505.09701](https://arxiv.org/abs/2505.09701)
- QA decontextualization — Newman et al., 2023 (*lead; ID verified 2026-07-01*): [arXiv 2305.14772](https://arxiv.org/abs/2305.14772)
