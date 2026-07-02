# Worldview: root-keyed two-tier fusion (kill settledness inflation)

**Status:** Designed — 2026-06-26. Resolves [#25](https://github.com/TheRealBillSiegler/epistemic-pipeline/issues/25). Sibling: [#26](https://github.com/TheRealBillSiegler/epistemic-pipeline/issues/26) (faithfulness gate). Supersedes the discarded provenance-DAG + EBSL-flow direction.
**Feeds:** the [SL design](2026-06-23-worldview-subjective-logic-design.md) §7.2, which already names correlated/duplicate sources as the open residue. This closes it.
**Reviewed by:** a five-lens expert panel (Subjective Logic, data-provenance, graph algorithms, Bayesian aggregation, YAGNI), 2026-06-26. The panel's verdict drove this design; see §9.

---

## 1. The problem

The worldview app reports **"how settled"** a belief is. That number is `1 − u`, where `u` is the Subjective-Logic uncertainty mass: `u = W / (r + s + W)`, `W = 2`. It depends only on the **total** evidence `r + s`, not its direction.

Today `worldview_update` fuses every recorded confidence vector with `fuse_cumulative` (count addition), and nothing groups evidence by its underlying source. So one source counted twice raises settledness as if it were independent confirmation. Two paths inflate it right now:

- **Re-ingest after an edit.** `NoteIngester` skips only byte-identical re-saves. Edit a note and re-ingest, and its claims fuse a second time — the same note reads as two sources.
- **Re-import of one source.** The same article ingested from two paths (or one note re-saved under a new name) produces two increments; cumulative fusion adds both. (Ten *distinct* notes that merely paraphrase one blog in prose are a harder, partly-residual case — see §10.)

This overstates the one honesty number the app exists to report.

## 2. The fix in one sentence

Give every evidence increment a **root id** (the canonical origin it traces to), then fuse **averaging within a root** and **cumulative across distinct roots**. Settledness then tracks the count of *distinct roots*, so re-ingests and re-imports of one source count once.

## 3. Posture

- **Independence is earned, not assumed.** Settledness rises only when a new, distinct, verifiable root is added. Ambiguity fails toward *not* inflating.
- **The belief math moves only on deterministic root identity.** Any fuzzy signal (content similarity) is advisory and human-adjudicated; it never moves a number.
- **Derived on replay, no graph store.** All structure is rebuilt from append-only evidence `E` on each replay, so `R` stays pure and replay stays byte-identical. No mutable graph is a source of truth.

## 4. Decisions

### D1 — Root identity = stable entity id, separate from content version.

A root's `root_id` is a canonical origin id: a normalized URL, DOI, or arXiv id; a vault note's stable path; a dataset id. A **content hash is a version tag, not an identity.** A note re-ingested after an edit is a new *version* of the same root, not a new root.

This is the highest-priority correctness point. Keying identity on `doc-hash` (the naive choice) would make every edit a brand-new root and *re-manufacture* the bug in §1.

*Example.* `notes/ai-risk.md` edited three times → one `root_id` (`notes/ai-risk.md`), three versions. `https://blog.com/x?utm_source=tw` and `http://www.blog.com/x` → one `root_id` after canonicalization.

### D2 — Root resolution at ingest (v1 scope).

`root_id = canonicalize(origin)`, where `origin` is the canonical source the ingestion caller supplies:

- a vault note's stable path (`NoteIngester` already knows it),
- the URL / DOI / arXiv id the document was fetched from, or
- a structured `source:` the note declares in frontmatter.

Canonicalization normalizes the id: strip URL tracking params and fragments, lowercase the host, resolve DOI/arXiv to canonical form; a vault path is used as-is.

v1 does **not** scrape free-form body links or infer provenance from prose. So it collapses the cases where the *origin itself* is the same — a note re-ingested after an edit, or one article imported under two paths — but not ten distinct notes that merely paraphrase one blog. Inferring a shared upstream from in-document citations (the citation DAG) is deferred (§8); a paraphrase that names no machine-readable source is the residual case (§10). Keeping root resolution to a supplied, canonicalized origin keeps it fully deterministic.

### D3 — Two-tier fusion replaces unconditional cumulative.

Per concept, collect every evidence increment, tagged by its `root_id`. Then:

- **Within a root:** `fuse_averaging` the increments. N restatements of one root count once.
- **Across distinct roots:** `fuse_cumulative` the per-root opinions. Independent roots accumulate.

Apply each root's reliability `g` as a scalar `discount()` **before** the across-root step (reliability is uniform until C6 calibration, so this is a no-op today, but the seam is there).

### D4 — The two-tier fold lives in the replay aggregation, not in `worldview_update`.

Averaging-within-root needs *all* of a root's increments together, which the per-observation `worldview_update` cannot see. So `_replay_beliefs` changes from "fold each observation cumulatively" to "gather all increments per `(concept, root_id)`, then two-tier fuse." `worldview_update` and the purity of `R` are unchanged; only the aggregation that builds `B` from the full trail changes. Replay stays a pure function of `E`, so it stays byte-identical.

### D5 — Citing-source own-credit = zero (a pinned leaf).

A citing source contributes only its root's evidence; its own restatement adds no settledness. Frame this honestly as a citing source's *own leaf observation pinned at zero*, not a "conservative dial" — graded credit (a review earning its own increment over its roots) is a *different graph*, deferred to §8. v1 pins it at zero because v1 cannot verify that a citing source independently assessed the claim. No source→source citation DAG is built in v1.

### D6 — Content similarity is advisory only.

Near-verbatim overlap (deterministic shingling) and reworded-but-similar content (fuzzy) may **raise a flag** — "these two roots may share an origin; confirm?" — but never collapse roots automatically. Only a **human-confirmed** root-equivalence, recorded as its own append-only evidence item, merges two roots (and may legitimately *lower* settledness). This keeps the math deterministic and replayable.

### D7 — Name the mechanism honestly: it is the Beta/Dirichlet evidence model, not EBSL flow.

The dedup comes from the **group-by-canonical-root rule**, which has no Subjective-Logic theorem behind it; it is the project's own duplicate-collapsing rule. The `discount` operator is legitimately EBSL evidence-scaling (keep that in-module citation), but the *system-level* algebra is reliability-weighted count-scaling over a Beta/Dirichlet evidence model. Do not claim EBSL right-distributivity dedups this — it dedups a shared *conduit*, not a shared *source* (panel finding, §9). `fuse_averaging` (mean-of-counts) is a duplicate-collapsing **heuristic**; it equals canonical averaging fusion only when a root's increments carry equal evidence, and the code docstring already says so.

## 5. Data model changes

- **`observations` table:** add a nullable `root_id TEXT` column. The replay groups on it.
- **`store.add_observation`:** add a `root_id` parameter.
- **`ingest_document` / `ingest_rating`:** add an `origin` parameter — the caller's canonical id for where this document came from (`NoteIngester` passes the note path; a document ingest passes the parsed URL/DOI). Root resolution (D2) turns `origin` + parsed citations into the `root_id`.
- **The generic `Observation` dataclass in `state.py` does NOT change.** `root_id` is a worldview-store concern; putting it on the shared state type would be information leakage into every other encoding. The replay reads `root_id` from the row, where the two-tier fold needs it.

## 6. Algorithm (replay)

```text
beliefs = {}
buckets: dict[concept, dict[root_id, list[Opinion]]]   # nested, default empty
for row in store.observations() where variable == "confidence_vector":
    root = row["root_id"]                               # set at ingest, D2
    for concept, p in parse(row["value"]) if concept in O:
        buckets[concept][root].append(increment(p))     # one increment
for concept, by_root in buckets:
    per_root = [ discount(fuse_averaging(incs), g[root]) # within-root, D3
                 for root, incs in by_root ]
    beliefs[concept] = fuse_cumulative(per_root)         # across-root, D3
```

`O(E)`. No DAG traversal, no fixpoint, no graph store. Reuses `discount` / `fuse_cumulative` / `fuse_averaging` with zero new primitives. The drift preview in `ingest_rating` uses the same aggregation over (existing trail) vs (trail + new observation).

## 7. Tests / gates

1. **No inflation from one source.** Re-ingesting one note after an edit → settledness unchanged. The same source imported under N origins that canonicalize to one `root_id` → one root's worth, not N.
2. **Calibration dual (the panel's missing test).** N observations resolving to N *distinct* roots → settledness rises with N. Guards against the opposite failure: under-counting genuine independent corroboration. Document that v1-zero-credit carries a deliberate downward bias here (§4 D5), and that this test is the trip-wire for upgrading to graded credit.
3. **Resolver-miss regression.** The same real root recorded under two `root_id`s must over-count — proving the dedup lives in the canonicalizer, not the algebra. Make this risk visible in CI.
4. **Replay determinism.** Same `E` → same derived buckets → byte-identical beliefs. Extends the existing replay-determinism test.

## 8. Deferred behind a YAGNI gate

Build only when a *measured* case demands it:

- **Source→source citation DAG + multi-hop flow** (a review citing a primary you also hold). Needed only for multi-level chains where root-set dedup gives visibly wrong settledness.
- **Graded own-credit** (a citing source earning its own increment), modeled as a leaf attached to the citing node. Trigger: the calibration-dual test (§7.2) shows v1-zero under-credits independent expert corroboration enough to matter.
- **Automated similarity clustering** beyond the advisory flag (D6).

At that point, *real* EBSL (trust-opinion `g`, the τ-bound, the matrix fixpoint) becomes the correct engine. Until then it is speculative generality for a personal corpus whose citation depth is 1–2.

## 9. Why not the provenance-DAG + EBSL flow (panel record)

A five-lens panel, grounding claims against arXiv:1402.3319 and the code, converged:

- **EBSL does not solve this.** Right-distributivity `x⊠(y⊕z)=(x⊠y)⊕(x⊠z)` dedups a shared *conduit* reached via multiple paths. The inflation case is `(R1⊠P)⊕(R2⊠P)` — a shared *source* P — which needs *left*-distributivity, **which EBSL explicitly lacks**. In real ingestion each restatement is its own evidence edge; cumulative fusion adds them; only group-by-root dedups them. (5/5 agreed the claim is mis-scoped.)
- **No graph database.** Derived-on-replay DAG only; a mutable graph store would break byte-identical replay. (5/5.)
- **Over-built for v1.** With own-credit zero and shallow depth, the EBSL flow computes a set-union — the bipartite root-keyed map computes the same thing in ~10× less code with no determinism risk. (5/5 lean simpler.)
- **The one dissent** (Bayesian lens) argued zero-credit "fails biased," under-counting independent corroboration. Adjudicated: ship zero for v1 (it never over-counts; v1 can't verify independence), but adopt the pinned-leaf framing (D5) and the calibration-dual test (§7.2) so the upgrade is evidence-triggered.

## 10. Honest boundaries

- **Dedup correctness = quality of root-id canonicalization**, not an algebraic theorem. A resolver miss over-counts; a resolver false-merge under-counts. The canonicalizer is the load-bearing component.
- **Semantic restatement without an explicit citation is undetectable deterministically.** A note that reworded blog B and stripped the link looks like a primary source and gets its own root. That dependence information was destroyed upstream; D6's advisory flag is the only (human-mediated) recourse. v1 accepts this residual.
- **This dedups *dependence structure*, never *truth*.** Grouping by root makes settledness honest about *how many independent sources* back a claim. It says nothing about whether those sources are correct — that remains the calibration question (C6) and the never-a-verdict stance.

## 11. Files touched

- `src/epistemic_pipeline/worldview_app/store.py` — `root_id` column; `add_observation` param.
- `src/epistemic_pipeline/worldview_app/ingest.py` — `origin` param on ingest; root resolution (D2); the two-tier fold in `_replay_beliefs`.
- `src/epistemic_pipeline/encodings/worldview.py` — the two-tier aggregation helper (pure); `worldview_update` unchanged.
- `tests/worldview_app/` — the four gates in §7.
- `docs/superpowers/specs/2026-06-23-worldview-subjective-logic-design.md` — fold the invariant into §7.2.
