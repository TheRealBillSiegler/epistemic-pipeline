# How honest can the pipeline be? The omission frontier

**Status:** Researched — 2026-06-25. Verified (21 of 25 load-bearing claims confirmed by 3-vote adversarial check; 4 refuted, listed below).
**Feeds:** the [UI design spec](../superpowers/specs/2026-06-24-worldview-app-ui-design.md) honesty sections (§9, §11); the [SL design](../superpowers/specs/2026-06-23-worldview-subjective-logic-design.md) §2 trust commitment.

This answers one question: *can the pipeline be made fully honest?* The short answer the literature gives is sharp.

**Read this first.** The pipeline can be near-fully honest about the evidence it **has** — trace it, weigh it, show the uncertainty, refuse the verdict, replay it. It cannot be fully honest about what it **hasn't seen**. That gap — *omission* — is structurally harder and only ever partial. The deepest line is conceded by the founder of the method intelligence analysts use for exactly this problem: a sound **process** can be guaranteed; a correct **verdict** cannot.

> "There is obviously no guarantee that ACH or any other procedure will produce a correct answer. The result, after all, still depends on fallible human judgment applied to incomplete and ambiguous information. ACH does, however, guarantee an appropriate process of analysis."
> — Heuer, originator of Analysis of Competing Hypotheses (CIA, *Psychology of Intelligence Analysis*)

So the pipeline's honesty target is **honesty-as-process**, and it must *disclaim verdict-correctness*. Coherence with its own evidence is reachable. Correspondence with reality is not guaranteed by any internal process. This is the same stance the SL design already takes; the research below says it is not a modest choice but the actual ceiling.

---

## 1. Honest about the evidence it HAS — tractable, with concrete levers

These are implementable and (mostly) peer-reviewed.

- **A separate "enough evidence?" signal.** Whether the evidence is *sufficient* is a different question from *which way it leans*, and should be measured on its own. Atanasova et al., *Fact Checking with Insufficient Evidence* (TACL 2022) make Evidence-Sufficiency Prediction a distinct task with its own dataset and metric. *Lever:* a sufficiency signal on each belief, separate from the belief's lean. *Caveat:* detection is weak and uneven by what's missing (21% accuracy for some omission types, 63% for others) — so it is a signal, not a guarantee.
- **Abstain on three axes, not one threshold.** Wen et al., *Know Your Limits: A Survey of Abstention in LLMs* (TACL 2025): the decision to say "I don't know" depends on *query under-specification*, *model confidence*, and *human values* — and these do not collapse into a single confidence number. *Lever:* distinct abstain triggers for a vague question, a thinly-backed belief, and a values/safety conflict.
- **Tell apart "missing input" from "beyond my knowledge."** Ren et al., *Beyond I Don't Know* (arXiv:2604.17293, 2026): *data uncertainty* (the question has no unique answer — ambiguous/missing input) and *model uncertainty* (an answer exists but is past the system's reach) demand different moves — *ask* vs *abstain / go fetch*. *Critical caveat:* models cannot reliably classify which they face (one model scored 4% F1 on model-uncertainty). So route on it, but do **not** trust the model to self-classify the gap.
- **Keep an explicit ignorance mass.** InfoGatherer (Taranukhin et al., arXiv:2603.05909, 2026) grounds uncertainty in Dempster–Shafer, assigning mass to an explicit *ignorance* set when evidence is vague or conflicting — the direct kin of the pipeline's Subjective-Logic uncertainty mass. This validates representing the unknown as a first-class quantity rather than folding it into a probability.
- **A value-of-information question policy.** Same InfoGatherer work: decide what to ask/seek next by *reducing vagueness first, then breaking ties*, and abstain if a confidence threshold isn't met within a turn budget. *Lever:* a principled active-evidence-gathering loop with built-in abstain-on-gap.
- **Score by least-disconfirmed, weight by diagnosticity.** Heuer's ACH: rank a hypothesis by how little evidence is *against* it (not how much is for it), and weight each evidence item by how well it *discriminates* between hypotheses. *Lever:* a disconfirmation-first scoring scaffold that traces a belief to its few load-bearing items and the assumptions to recheck. *Caveat:* ACH has **not** been shown to reduce confirmation bias empirically (Mandel et al. 2018; Dhami et al. 2019) — use it as a process scaffold, not a proven accuracy improver. And diagnosticity is only meaningful if the hypothesis set is *collectively exhaustive* (MECE): a missing true hypothesis makes the scores misleading — the omission frontier again.

---

## 2. The omission frontier — harder, and where honesty stays partial

- **Detecting *absence* is structurally harder than detecting conflict.** Spotting that evidence *disagrees* is anomaly detection over what's present; spotting that relevant evidence is *missing* requires quantifying over what *could* have been present. PassiveQA (arXiv:2604.04565, 2026) names this directly and its own gap-detector reaches only ~58% recall — a design pattern, not a solved problem.
- **One-sided-but-TRUE evidence beats every falsehood check.** This is the sharpest result for us. *Epistemic Bias Injection* (arXiv:2512.00804, 2026): factually accurate but cherry-picked passages crowd out other views and steer the conclusion, and a fact-checker **cannot** tell them from balanced ones (>86% attack success across several models; fact-check "not enough info" rates 0.69 vs 0.71). **Omission-honesty cannot be reduced to truth-checking.** A belief can be fully sourced, every claim true, and still be a lie of selection. The pipeline needs an explicit *viewpoint-coverage / one-sidedness* check — and the literature offers no validated one yet. This is the open frontier.

---

## 3. The walls — proven, honesty here is only partial

State these in the product, don't paper over them.

- **The system's own confidence cannot find its worst blind spots.** *Unknown-unknowns* — confident-but-wrong — sit *far* from the decision boundary, so confidence-driven methods (active learning, uncertainty sampling) never query them. Analytic, not incidental (Google Research; Attenberg, Ipeirotis & Provost, *Beat the Machine*, ACM JDIQ 2015). **Consequence:** the pipeline's own uncertainty/ignorance mass will, by construction, miss the gaps where it feels most certain.
- **Conformal "I don't know" has a real bound but hard limits.** Conformal abstention (Abbasi-Yadkori et al., *Mitigating LLM Hallucinations via Conformal Abstention*, arXiv:2405.01563) bounds the error rate via self-consistency, but the bound is *marginal/in-expectation*, *fails under distribution shift*, and the paper concedes it "clearly cannot detect situations where the LLM is completely sure about an incorrect answer."
- **No internal process guarantees a correct verdict** over incomplete, ambiguous information (Heuer, above).

---

## 4. Refuted — do NOT claim these (killed in verification)

- Fine-tuning beats inference-time prompting for abstention. *(0–3)*
- "Could you be wrong?" *reliably* surfaces counter-evidence. Only that the model *sometimes* surfaces latent counter-knowledge — not reliably. *(1–2)*
- ACH *structurally* prevents one-sidedness by equal hypothesis treatment. *(0–3)*
- Multi-agent debate *measurably* reduces unsafe outputs vs a single model. *(0–3)*

So a metacognitive "could you be wrong?" pass and multi-agent red-team debate are **design candidates with motivation, not proven mechanisms.** Try them; don't promise them.

---

## 5. What this means for the design

- **Claim honesty-as-process, disclaim the verdict.** Already the SL stance; now backed as the actual ceiling. The UI must never present a belief as true/false.
- **Make omission-honesty an explicit, separately-measured, never-finished target** — not a property we tick off. Ship: a sufficiency signal, three-axis abstain, a disconfirmation-first scaffold, an active question/evidence-gathering loop, and (the frontier) a one-sidedness/coverage check.
- **Name the walls in the UI.** Say "I might be missing something," "this rests on a choice I made," and "I can be confidently wrong." The honesty is in admitting the blind spot, not hiding it.
- **Don't trust the model's own gap-classification.** Route on missing-input vs beyond-evidence, but get the signal from structure (coverage against a hypothesis set, novelty/density), not the model's self-report.

## Method

One deep-research pass (5 angles: omission/sufficiency · disconfirmation/one-sidedness · calibration/abstention · provenance · epistemic foundations), 25 sources → 119 claims → top 25 adversarially verified (3 votes each): 21 confirmed, 4 refuted. Caveat: the sharpest omission sources (InfoGatherer, PassiveQA, Ren et al., Epistemic Bias Injection) are fresh 2026 arXiv preprints, unreplicated — treat their numbers as provisional and their mechanisms as candidates. Peer-reviewed anchors (TACL 2022/2025, NeurIPS 2024, ACM JDIQ 2015, Heuer's ACH corpus) are solid. Provenance: workflow transcript, 2026-06-25.

## Sources

- Evidence sufficiency as a task — Atanasova et al., TACL 2022: [aclanthology.org/2022.tacl-1.43](https://aclanthology.org/2022.tacl-1.43/)
- Abstention survey (three axes) — Wen et al., TACL 2025: [aclanthology.org/2025.tacl-1.26](https://aclanthology.org/2025.tacl-1.26/); abstention filters unsafe — Tomani et al.: [arXiv:2404.10960](https://arxiv.org/abs/2404.10960)
- Unknown-unknowns — Google Research blog; Attenberg, Ipeirotis & Provost, *Beat the Machine*, ACM JDIQ 2015: [dl.acm.org/doi/10.1145/2700475](https://dl.acm.org/doi/10.1145/2700475)
- Data vs model uncertainty — Ren et al., *Beyond I Don't Know*: [arXiv:2604.17293](https://arxiv.org/html/2604.17293v1)
- Answer/Ask/Abstain + info state — PassiveQA: [arXiv:2604.04565](https://arxiv.org/html/2604.04565); AbstentionBench: [arXiv:2506.09038](https://arxiv.org/abs/2506.09038)
- DS ignorance mass + value-of-information question policy — InfoGatherer, Taranukhin et al.: [arXiv:2603.05909](https://arxiv.org/html/2603.05909v1)
- Disconfirmation-first + diagnosticity (and its empirical limits) — Heuer/Pherson, ACH: [pherson.org](https://pherson.org/wp-content/uploads/2013/06/Improving-Intelligence-Analysis-with-ACH.pdf)
- Metacognitive "could you be wrong?" — Hills: [arXiv:2507.10124](https://arxiv.org/abs/2507.10124)
- Multi-agent red-team debate — RedDebate, Asad et al.: [arXiv:2506.11083](https://arxiv.org/html/2506.11083)
- One-sided-but-true evidence — Epistemic Bias Injection: [arXiv:2512.00804](https://arxiv.org/html/2512.00804)
- Conformal abstention (bound + limits) — Abbasi-Yadkori et al., *Mitigating LLM Hallucinations via Conformal Abstention*: [arXiv:2405.01563](https://arxiv.org/abs/2405.01563) (this is the conformal paper; not to be confused with the same group's NeurIPS 2024 *To Believe or Not to Believe Your LLM*, arXiv:2406.02543)
