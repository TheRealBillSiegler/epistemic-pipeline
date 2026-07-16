# Deep-research record: prior art for the agent-verification niche

**Date:** 2026-07-15
**Question:** Does anything already occupy the "verification ledger for agent swarms" niche — the six-pillar combination (claim identity, SL-graded confidence, root-keyed independence fusion, append-only pure-fold replay, retraction propagation, per-channel calibration) applied to machine-generated engineering claims? This is the Tier-2 gate the 2026-07-12 dogfood record named and did not run.
**Method:** Workflow `wf_3b03d339-3ae`, 11 agents, ~886k tokens. Five parallel sweep angles (agent observability/eval platforms; software assurance and attestation; academic literature 2022–2026; spec-driven dev tooling; direct competitive search) found 50 distinct systems. The five closest candidates each got an adversarial verifier instructed to *prove the niche occupied* by direct fetch of primary sources. Result: 0/5 occupied. Synthesis below is the verifier-informed verdict, saved verbatim.
**Scope limit:** Web-search depth. Patents and internal enterprise tooling were not audited. Read the verdict as "open per public evidence."

---

# Prior-Art Verdict: Verification Ledger for Agent Swarms

## 1. VERDICT

**The niche is open.** The specific six-pillar combination — Subjective-Logic-graded belief, root-keyed independence fusion, append-only pure-fold replay, retraction propagation, and per-channel calibration, all over machine-generated engineering claims — was not found in any shipped product, standard, or research system in this sweep. Every candidate covers at most two or three pillars. The closest single artifact (an anonymous TDCommons defensive publication) survives adversarial scrutiny as a partial match on P1/P5 only, and fails the hardest pillar outright.

Confidence is moderate, not absolute. This is a web-search-depth sweep, not an exhaustive patent or enterprise-tooling audit. Absence of evidence here is not proof of absence — internal tooling at large labs was not inspectable. But five independent adversarial passes each tried to prove the niche occupied and each failed on the same pillar.

Pillar-by-pillar, commodity vs. unoccupied:

- **P1 (claim identity) — commodity.** Every argument-graph, spec-driven, and ledger tool has it (GSN/CAE, Jama/DOORS, Spec Kit, Pramāṇa, Zep). No defensibility here.
- **P2 (graded confidence) — partly commodity, SL-specific form rare.** Scalar confidence labels are everywhere (Devin, Cursor, Galileo, Patronus). The belief/disbelief/**uncertainty** triple derived from evidence counts is rare, and the assurance-case literature (Bloomfield & Rushby) explicitly *rejects* Subjective Logic on the grounds it "delivers implausible results." So the SL choice is contested, not just unbuilt — that is a design position you must defend, not a free moat.
- **P3 (root-keyed independence fusion) — genuinely unoccupied. This is the load-bearing pillar.** The problem is rigorously documented (Apple's "Nine Judges, Two Effective Votes": a 9-judge panel carries ~2 independent votes; aggregation math recovers at most 11% of the gap). The fusion math exists (Jøsang's cumulative/averaging operators). Nobody has wired same-root-averages / distinct-root-accumulates into a claim ledger for agent or code-review claims. Every adversarial pass confirmed this gap.
- **P4 (append-only provenance + pure-fold replay) — split.** Append-only logs are common (in-toto, SLSA, agent-ledger, Pramāṇa). Deterministic *pure-fold recompute-from-log* is rarely a stated design property; most systems update trust scores in place.
- **P5 (retraction propagation) — commodity in adjacent domains, absent for graded engineering claims.** Classical Truth Maintenance Systems (Doyle, de Kleer's ATMS) invented cascading invalidation decades ago. Shipped agent-memory systems do it now (Zep, XTrace). DARPA ARCOS/CertGATE does change-impact re-evaluation. But none combine it with graded-confidence fusion over agent-generated software claims.
- **P6 (per-channel calibration from resolved-claim track record) — single-channel commodity, multi-channel fused version unoccupied.** CI platforms score per-test flakiness from history (Datadog, Launchable, Allure). SkillAggregation learns per-judge weights. None fuse test + LLM-review + human channels into one claim-level reliability weight, and none key it by underlying model root.

The moat is not any single pillar. It is **P3 wired into P4/P5/P6 for engineering claims** — the assembly, not the parts.

## 2. NEAREST NEIGHBORS

| System | Category | Pillars covered | Gap | URL |
|---|---|---|---|---|
| Distributed Ledger Provenance (TDCommons defensive pub) | IP disclosure, unimplemented | P1, P5 (partial P4) | No P3 (raw attestation-count trust score), no SL, no P6 | https://www.tdcommons.org/dpubs_series/10744/ |
| Pramāṇa protocol | Agent claim-attestation standard | P1, partial P4 | Categorical-only by design (no P2), no fusion, no retraction cascade | https://arxiv.org/html/2605.20312 |
| XTrace | Agent-memory belief revision | P1, P5 | Discrete status not SL, no P3, no P6; wrong domain (memory, not eng. claims) | https://xtrace.ai/research/belief-revision-system |
| Zep (Graphiti) | Agent-memory provenance graph | P4, P5 | Validity-window retraction only; no SL, no fusion, no calibration | https://blog.getzep.com/how-zep-tracks-provenance-in-agent-memory/ |
| Assurance 2.0 / Eliminative Argumentation | Assurance-case confidence framework | P2-adjacent, partial P5 | Rejects SL; Fréchet-bounds independence is human-declared, not root-keyed; no P6 | https://www.csl.sri.com/users/rushby/papers/confidence24.pdf ; https://arxiv.org/abs/2604.00034 |
| DARPA ARCOS (RACK + CertGATE) | Automated certification suite | P1, P4, P5-adjacent | No graded SL confidence, no independence fusion | https://arcos-tools.org/tools/certgate ; https://github.com/ge-high-assurance/RACK |
| Multi-Review / SWRBench | Code-review benchmark | P3 (concept only) | Self-Agg vs Multi-Agg is a benchmark result, not a ledger | https://arxiv.org/abs/2509.01494 |
| "Nine Judges, Two Effective Votes" (Apple) | Empirical measurement | P3 (problem statement) | Diagnoses the gap; builds no system | https://arxiv.org/abs/2605.29800 |
| SkillAggregation | LLM-judge weight learning | P3, P6 | Per-judge not root-keyed; no ledger, no replay, no retraction | https://arxiv.org/abs/2410.10215 |
| in-toto / SLSA | Supply-chain attestation | P1, P4, coarse P3 | N-of-M threshold is binary, not graded fusion; no confidence, no retraction | https://github.com/in-toto/docs/blob/master/in-toto-spec.md ; https://slsa.dev/attestation-model |
| doxa | OSS Subjective Logic library | P2 (primitive) | Building block only — no claim identity, no provenance, no calibration | https://github.com/topics/subjective-logic |
| CI-intelligence (Datadog, Launchable, Allure) | Test-evidence dashboards | P6 (single-channel) | Test-history only; no cross-channel fusion, no retraction to dependents | https://docs.datadoghq.com/tests/flaky_tests/ |

## 3. IMPORTS

Adopt these rather than reinventing:

- **Subjective Logic operators — use `doxa` or port its math.** Belief/disbelief/uncertainty, Beta evidence mapping, and cumulative/averaging fusion are already implemented dependency-free in Python. Do not hand-roll the opinion algebra. Jøsang's TNA-SL papers are the reference for the discount and fusion operators.
- **Effective-sample-size math for P3.** Import the Kish design-effect formula (n_eff = n / (1 + ρ(n−1))) from the Apple paper as the honest way to report "how many independent voices this claim actually has." It is the rigorous version of your pitch and gives you a number to display.
- **Provenance relation vocabulary.** The survey arXiv:2606.04990 already defines the typed relations (Support, Contradict, Depend-on, Update, Invalidate). Use its schema for edge types instead of inventing your own; it also documents that no one has attached fusion/replay to these, which is your positioning evidence.
- **Truth Maintenance Systems for P5 semantics.** de Kleer's ATMS is the correct prior art for cascading invalidation — justification-based recompute is exactly pure-fold replay in disguise. Frame P4+P5 as "evidence-sourced TMS with graded justifications" rather than a novel invention.
- **GSN / Claims-Arguments-Evidence structure for P1.** If you ever need a human-readable argument view, adopt the standardized GSN node types (goal/strategy/solution/context) rather than a bespoke claim tree. Adelard ASCE and Eclipse OpenCert show the notation.
- **in-toto attestation envelope for P4 provenance records.** The signed-link metadata format is a mature, adopted wire format for "who produced this evidence." Reuse the envelope; don't design a new signed-record schema.
- **Per-channel calibration method.** SkillAggregation's learned per-source skill weights (and its Dawid-Skene baseline) is the published method for P6. Adopt it, then change the keying from per-judge to per-root.

## 4. THREATS

Who could add the missing pillars fastest, and what remains:

- **LLM eval/observability platforms (Braintrust, LangSmith, Langfuse, Arize) — highest threat, but blunted.** They already have per-run scores, human-label calibration, and multi-judge workflows. Langfuse's own community has *requested* retraction-triggered re-evaluation (P5) — it is a known unbuilt feature. They could add persistent claim identity and a re-fold in a quarter. What they would still lack: root-keyed SL fusion is a genuine conceptual leap, not a config toggle, and their entire data model is trace/run-centric, not claim-centric. Retrofitting a claim ledger under a trace store is a rearchitecture, not a feature.
- **DARPA ARCOS / assurance-case vendors — capable but mis-incentivized.** They could bolt on graded confidence. But that community *rejects* Subjective Logic on principle (Graydon & Holloway's negative results), so they are unlikely to build your P2/P3 — they would build Fréchet-bounds instead. Different bet, different product.
- **Agent-memory platforms (Zep, XTrace) — adjacent, wrong domain.** They have P4+P5 shipped. Pivoting from conversational-memory facts to engineering claims plus adding SL fusion and calibration is a domain change plus two new pillars. Plausible but not trivial.
- **A spec-driven IDE (Kiro, Spec Kit, Devin) — owns distribution, lacks the epistemics.** They have claim identity and the users. They ship scalar confidence today. They are the most dangerous distribution threat but the furthest from the fusion/calibration math.

**Remaining defensibility:** thin on any single pillar, real on the assembly. The durable moat is (a) the root-keyed fusion *arithmetic* correctly applied to correlated agents, and (b) the deterministic replay-from-log architecture that makes retraction propagation trustworthy rather than a flagged-for-human-review notice. Both are architecture-level commitments a trace-centric competitor cannot cheaply retrofit. None of this is patent-grade novel — the components are all published — so the defensibility is execution and integration, not IP.

## 5. RECOMMENDATION

**Conditional yes** — give the agent-verification reframe the design pass.

The reframe is justified because the core problem is real and independently confirmed (P3 is measured and unsolved), the target domain (agent-generated engineering claims) has no incumbent ledger, and the failure modes the pitch names are documented gaps in the literature, not solved problems. The build cost is bounded: the hard math (SL, effective sample size, calibration) is all importable, so the work is integration and the claim-ledger data model, not research.

The condition: the design pass must treat **P3 as the product**, not a feature. If P3 collapses to "we run different models and average," you have rebuilt Braintrust's multi-judge workflow with extra steps, and the moat is gone.

**The falsifier that kills it:** if a resolved-claim backtest shows that root-keyed fusion produces the *same claim rankings* as naive per-agent accumulation on real agent-swarm output — i.e., the correlation correction does not change which claims get trusted — then the load-bearing pillar carries no decision weight, and the whole ledger reduces to commodity provenance-plus-scalar-confidence that incumbents already approximate. Run that backtest early, before the full design pass, on a real multi-agent code-review dataset. If root-keying doesn't move the ranking, stop.

Secondary falsifier: if an enterprise-tooling or patent audit (out of scope for this sweep) surfaces a shipped system combining P3 with P4/P5, the openness verdict weakens — treat the current verdict as "open per public evidence," not "open, full stop."
