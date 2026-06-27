# Root-keyed two-tier fusion — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Stop "how settled" from inflating when one source is counted twice, by grouping each concept's evidence by a canonical root id and fusing averaging-within-root, cumulative-across-roots.

**Architecture:** Each observation gains a `root_id` (the canonical origin it traces to). Belief replay changes from "fold every observation cumulatively" to "bucket increments by `(concept, root_id)`, average within a root, accumulate across roots." All structure is still derived from append-only evidence on replay, so `R` stays pure and replay stays byte-identical. No graph store, no source→source DAG, no EBSL flow (all deferred per spec §8).

**Tech Stack:** Python 3.14+, `uv`, `pytest`, `pyright`, `ruff`, SQLite (stdlib `sqlite3`), frozen dataclasses. Source of truth spec: `docs/superpowers/specs/2026-06-26-shared-source-root-keyed-fusion-design.md`. Resolves issue #25.

## Global Constraints

- Run everything via `uv`: `uv run pytest`, `uv run pyright`, `uv run ruff check`. Never bare `python`/`pip`.
- Core library is zero-dependency. This feature uses only the stdlib (`sqlite3`, `urllib.parse`, `re`, `hashlib`).
- State is immutable: `EpistemicState`/`Opinion`/`WorldviewBeliefs` stay frozen dataclasses. `R` is pure and deterministic. `E` (the observation trail) is append-only. The full belief state is always reconstructable by replaying `R` over `E`, byte-identically.
- Writing style (specs, docstrings, comments): graduate-level ideas in 8th-grade sentences. Short, active, lead with the point. Define each term once, follow an abstract definition with a concrete example.
- Commit messages end with: `Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>`.
- Work on a feature branch off `main` (not the default branch). Suggested: `feat/root-keyed-fusion`.

---

## File Structure

- **Create** `src/epistemic_pipeline/worldview_app/provenance.py` — `canonicalize_origin(origin) -> str`. One responsibility: turn a raw origin string into a stable, canonical root id. The spec calls this the load-bearing component (§10), so it gets its own file and focused tests.
- **Modify** `src/epistemic_pipeline/worldview_app/store.py` — add a nullable `root_id` column to the `observations` table (with a migration for existing DBs); `add_observation` gains a `root_id` parameter.
- **Modify** `src/epistemic_pipeline/encodings/worldview.py` — add the pure two-tier aggregation (`two_tier_fuse`, `aggregate_beliefs`). `worldview_update` is left unchanged.
- **Modify** `src/epistemic_pipeline/worldview_app/ingest.py` — `_replay_beliefs` uses `aggregate_beliefs`; new `_ratings_from_store` helper; `ingest_rating` threads a `root_id`; `ingest_document` gains an `origin` parameter and canonicalizes it; `NoteIngester.ingest` passes the note path as the origin.
- **Create** tests: `tests/worldview_app/test_provenance.py`, `tests/encodings/test_two_tier_fusion.py`, and additions to `tests/worldview_app/test_ingest.py`.

Build order and dependencies: Task 1 (provenance), Task 2 (store column), Task 3 (fusion math) are independent. Task 4 (replay) depends on 2 + 3. Task 5 (origin capture) depends on 1 + 4.

---

### Task 1: Canonicalize origins

**Files:**
- Create: `src/epistemic_pipeline/worldview_app/provenance.py`
- Test: `tests/worldview_app/test_provenance.py`

**Interfaces:**
- Produces: `canonicalize_origin(origin: str) -> str` — maps a raw origin (URL, DOI, arXiv id, or vault path) to a stable canonical root id. URLs differing only by tracking params, host case, fragment, or trailing slash map to the same id.

- [ ] **Step 1: Write the failing test**

```python
# tests/worldview_app/test_provenance.py
from epistemic_pipeline.worldview_app.provenance import canonicalize_origin


def test_urls_differing_only_by_tracking_and_case_collapse():
    a = canonicalize_origin("https://Blog.com/x?utm_source=tw&id=7#frag")
    b = canonicalize_origin("https://blog.com/x?id=7")
    assert a == b


def test_trailing_slash_is_normalized():
    assert canonicalize_origin("https://blog.com/x/") == canonicalize_origin("https://blog.com/x")


def test_doi_variants_collapse():
    assert canonicalize_origin("doi:10.1145/2700475") == canonicalize_origin("DOI:10.1145/2700475")
    assert canonicalize_origin("10.1145/2700475") == canonicalize_origin("doi:10.1145/2700475")


def test_vault_path_is_left_alone_and_distinct_sources_differ():
    assert canonicalize_origin("notes/ai-risk.md") == "notes/ai-risk.md"
    assert canonicalize_origin("notes/a.md") != canonicalize_origin("notes/b.md")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/worldview_app/test_provenance.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'epistemic_pipeline.worldview_app.provenance'`

- [ ] **Step 3: Write minimal implementation**

```python
# src/epistemic_pipeline/worldview_app/provenance.py
"""Turn a raw source origin into a stable, canonical root id.

A "root" is where a piece of evidence ultimately comes from. Two records
that trace to the same root must produce the same id, so belief fusion can
group them and not double-count one source. This is deterministic by
design: it normalizes ids the caller supplies (a URL, a DOI, a vault
path); it never guesses provenance from a document's contents.
"""

from __future__ import annotations

import re
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

# Query parameters that identify a click, not the resource. Dropped so the
# same article shared two ways collapses to one root.
_TRACKING = frozenset(
    {"utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
     "fbclid", "gclid", "ref", "ref_src"}
)
# A bare DOI, e.g. "10.1145/2700475".
_DOI = re.compile(r"^10\.\d{4,9}/\S+$")


def canonicalize_origin(origin: str) -> str:
    """Return a stable root id for ``origin``.

    Example: ``https://Blog.com/x?utm_source=tw&id=7#frag`` and
    ``https://blog.com/x?id=7`` both return ``https://blog.com/x?id=7``.
    """
    o = origin.strip()
    low = o.lower()
    if low.startswith(("http://", "https://")):
        parts = urlsplit(o)
        path = parts.path.rstrip("/") or "/"
        kept = sorted((k, v) for k, v in parse_qsl(parts.query) if k.lower() not in _TRACKING)
        return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), path, urlencode(kept), ""))
    if low.startswith("doi:"):
        return "doi:" + o[4:].strip().lower()
    if low.startswith("arxiv:"):
        return "arxiv:" + o[6:].strip().lower()
    if _DOI.match(low):
        return "doi:" + low
    return o
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/worldview_app/test_provenance.py -v`
Expected: PASS (4 tests)

- [ ] **Step 5: Lint, type-check, commit**

```bash
uv run ruff check src/epistemic_pipeline/worldview_app/provenance.py tests/worldview_app/test_provenance.py
uv run pyright src/epistemic_pipeline/worldview_app/provenance.py
git add src/epistemic_pipeline/worldview_app/provenance.py tests/worldview_app/test_provenance.py
git commit -m "feat: canonicalize source origins to stable root ids (#25)"
```

---

### Task 2: `root_id` column on observations

**Files:**
- Modify: `src/epistemic_pipeline/worldview_app/store.py` (the `_SCHEMA` string, `Store.__init__`, and `add_observation`)
- Test: `tests/worldview_app/test_store.py` (add to the existing file; create it if absent)

**Interfaces:**
- Consumes: nothing new.
- Produces: `Store.add_observation(variable, value, source, confidence, timestamp, modality=None, root_id=None) -> int`. The `observations()` rows now carry a `root_id` key (None for legacy rows).

- [ ] **Step 1: Write the failing test**

```python
# tests/worldview_app/test_store.py  (append; imports may already exist)
from epistemic_pipeline.worldview_app.store import Store


def test_observations_table_has_root_id_column():
    with Store(":memory:") as store:
        cols = [row["name"] for row in store.conn.execute("PRAGMA table_info(observations)")]
        assert "root_id" in cols


def test_add_observation_round_trips_root_id():
    with Store(":memory:") as store:
        store.add_observation("confidence_vector", "{}", "src", 1.0, 1.0, root_id="blog-A")
        row = store.observations()[0]
        assert row["root_id"] == "blog-A"


def test_add_observation_root_id_defaults_to_none():
    with Store(":memory:") as store:
        store.add_observation("confidence_vector", "{}", "src", 1.0, 1.0)
        assert store.observations()[0]["root_id"] is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/worldview_app/test_store.py -v`
Expected: FAIL — `sqlite3.OperationalError: table observations has no column named root_id` (and the column-presence test fails).

- [ ] **Step 3: Add the column to the schema**

In `store.py`, add `root_id` to the `observations` table in `_SCHEMA`:

```python
CREATE TABLE IF NOT EXISTS observations (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    variable   TEXT NOT NULL,
    value      TEXT NOT NULL,
    source     TEXT NOT NULL,
    modality   TEXT,
    confidence REAL NOT NULL,
    timestamp  REAL NOT NULL,
    root_id    TEXT
);
```

- [ ] **Step 4: Migrate existing databases in `__init__`**

In `Store.__init__`, after `self.conn.executescript(_SCHEMA)` and its `commit()`, add a forward migration so a pre-existing observations table (created before this column) gains it:

```python
        # Forward-migrate stores created before root_id existed. On a fresh
        # schema the column already exists, so the ALTER raises and we ignore
        # it; on an old store it adds the column. Either way both converge.
        try:
            self.conn.execute("ALTER TABLE observations ADD COLUMN root_id TEXT")
            self.conn.commit()
        except sqlite3.OperationalError:
            pass
```

- [ ] **Step 5: Thread `root_id` through `add_observation`**

Replace `add_observation` with:

```python
    def add_observation(  # noqa: PLR0913
        self,
        variable: str,
        value: str,
        source: str,
        confidence: float,
        timestamp: float,
        modality: str | None = None,
        root_id: str | None = None,
    ) -> int:
        """Append an observation. Returns its auto-assigned id.

        confidence must be in [0, 1]. ``root_id`` is the canonical source
        the evidence traces to; belief fusion groups by it. None means the
        origin was not recorded (legacy rows; replay falls back to source).
        """
        _check_confidence(confidence)
        cur = self.conn.execute(
            """INSERT INTO observations
               (variable, value, source, modality, confidence, timestamp, root_id)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (variable, value, source, modality, confidence, timestamp, root_id),
        )
        self.conn.commit()
        assert cur.lastrowid is not None  # noqa: S101  # autoincrement always sets this
        return cur.lastrowid
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `uv run pytest tests/worldview_app/test_store.py -v`
Expected: PASS (the 3 new tests, plus any pre-existing store tests).

- [ ] **Step 7: Lint, type-check, commit**

```bash
uv run ruff check src/epistemic_pipeline/worldview_app/store.py tests/worldview_app/test_store.py
uv run pyright src/epistemic_pipeline/worldview_app/store.py
git add src/epistemic_pipeline/worldview_app/store.py tests/worldview_app/test_store.py
git commit -m "feat: record a root_id per observation (#25)"
```

---

### Task 3: Two-tier fusion math (pure)

**Files:**
- Modify: `src/epistemic_pipeline/encodings/worldview.py` (add two functions + imports; leave `worldview_update` untouched)
- Test: `tests/encodings/test_two_tier_fusion.py`

**Interfaces:**
- Consumes: `Opinion`, `discount`, `fuse_cumulative`, `fuse_averaging` from `_subjective_logic`; `_evidence_increment`, `WorldviewOntology`, `WorldviewBeliefs` already in `worldview.py`.
- Produces:
  - `two_tier_fuse(by_root: Mapping[str, Sequence[Opinion]]) -> Opinion` — average increments within each root, then accumulate across roots.
  - `aggregate_beliefs(ratings: Sequence[tuple[str, Mapping[str, float]]], ontology: WorldviewOntology) -> WorldviewBeliefs` — bucket each concept's increments by root id and two-tier-fuse them. Concepts outside the ontology are skipped.

Reference (for the implementer): `_evidence_increment(1.0)` returns `Opinion(2.0, 0.0)` (reliability is 1.0, a no-op), whose `uncertainty` is `2/(2+0+2) = 0.5`. Averaging three identical `Opinion(2,0)` gives `Opinion(2,0)` (mean of counts). Cumulative-fusing two `Opinion(2,0)` gives `Opinion(4,0)`, uncertainty `2/6 ≈ 0.333`.

- [ ] **Step 1: Write the failing test**

```python
# tests/encodings/test_two_tier_fusion.py
import math

from epistemic_pipeline.encodings.worldview import (
    WorldviewOntology,
    aggregate_beliefs,
    two_tier_fuse,
)
from epistemic_pipeline.encodings._subjective_logic import Opinion


def test_within_root_averages_then_across_roots_accumulates():
    inc = Opinion(2.0, 0.0)  # one fully-confident increment
    one_root = two_tier_fuse({"A": [inc, inc, inc]})        # 3 restatements of A
    assert math.isclose(one_root.uncertainty, 0.5)          # counted once
    two_roots = two_tier_fuse({"A": [inc], "B": [inc]})     # 2 distinct roots
    assert math.isclose(two_roots.uncertainty, 2 / 6)       # accumulated


def test_aggregate_collapses_one_root_but_distinct_roots_settle_more():
    onto = WorldviewOntology(concepts=frozenset({"c"}))
    same = aggregate_beliefs([("A", {"c": 1.0}), ("A", {"c": 1.0}), ("A", {"c": 1.0})], onto)
    distinct = aggregate_beliefs([("A", {"c": 1.0}), ("B", {"c": 1.0}), ("C", {"c": 1.0})], onto)
    assert math.isclose(same.opinions["c"].uncertainty, 0.5)       # one root's worth
    assert distinct.opinions["c"].uncertainty < same.opinions["c"].uncertainty


def test_aggregate_skips_concepts_outside_the_ontology():
    onto = WorldviewOntology(concepts=frozenset({"known"}))
    beliefs = aggregate_beliefs([("A", {"known": 1.0, "unknown": 1.0})], onto)
    assert set(beliefs.opinions) == {"known"}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/encodings/test_two_tier_fusion.py -v`
Expected: FAIL — `ImportError: cannot import name 'aggregate_beliefs'`

- [ ] **Step 3: Add `fuse_averaging` and typing imports**

In `worldview.py`, extend the `_subjective_logic` import and add a typing import near the top:

```python
from epistemic_pipeline.encodings._subjective_logic import (
    Opinion,
    discount,
    fuse_averaging,
    fuse_cumulative,
)
```

And under the existing `from __future__ import annotations`, add (or extend) a TYPE_CHECKING block:

```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence
```

- [ ] **Step 4: Implement the two functions**

Add to `worldview.py` (place them after `_evidence_increment`):

```python
def two_tier_fuse(by_root: Mapping[str, Sequence[Opinion]]) -> Opinion:
    """Average increments within each root, then accumulate across roots.

    Restatements of one source (same root) are averaged, so N copies count
    as one. Distinct roots are cumulatively fused, so independent sources
    each lower uncertainty. ``by_root`` must be non-empty and every
    increment must share a base rate (they do: all come from
    ``_evidence_increment``).
    """
    per_root = [fuse_averaging(list(incs)) for incs in by_root.values()]
    return fuse_cumulative(per_root)


def aggregate_beliefs(
    ratings: Sequence[tuple[str, Mapping[str, float]]],
    ontology: WorldviewOntology,
) -> WorldviewBeliefs:
    """Build beliefs from (root_id, confidence-vector) pairs: the pure R fold.

    Each pair is one recorded rating: the root it came from, and that
    rating's concept -> confidence map. Group every concept's increments by
    root id, then two-tier-fuse (average within a root, accumulate across
    roots). Concepts the ontology does not know are skipped. A concept with
    no increments gets no opinion (it stays vacuous on read).
    """
    buckets: dict[str, dict[str, list[Opinion]]] = {}
    for root_id, vector in ratings:
        for concept, confidence in vector.items():
            if concept not in ontology.concepts:
                continue
            by_root = buckets.setdefault(concept, {})
            by_root.setdefault(root_id, []).append(_evidence_increment(confidence))
    opinions = {concept: two_tier_fuse(by_root) for concept, by_root in buckets.items()}
    return WorldviewBeliefs(opinions=opinions)
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `uv run pytest tests/encodings/test_two_tier_fusion.py -v`
Expected: PASS (3 tests)

- [ ] **Step 6: Lint, type-check, commit**

```bash
uv run ruff check src/epistemic_pipeline/encodings/worldview.py tests/encodings/test_two_tier_fusion.py
uv run pyright src/epistemic_pipeline/encodings/worldview.py
git add src/epistemic_pipeline/encodings/worldview.py tests/encodings/test_two_tier_fusion.py
git commit -m "feat: two-tier fusion (average within root, accumulate across) (#25)"
```

---

### Task 4: Two-tier replay + thread `root_id` through `ingest_rating`

**Files:**
- Modify: `src/epistemic_pipeline/worldview_app/ingest.py` (`_replay_beliefs`, new `_ratings_from_store`, `ingest_rating`, imports)
- Test: `tests/worldview_app/test_ingest.py` (append)

**Interfaces:**
- Consumes: `aggregate_beliefs` (Task 3); `add_observation(..., root_id=...)` (Task 2).
- Produces:
  - `_ratings_from_store(store: Store) -> list[tuple[str, dict[str, float]]]` — read each confidence-vector observation as `(root_id_or_source, parsed_vector)`.
  - `ingest_rating(store, confidences, *, source_type, ts, model_id, prompt_hash, seed, reason, root_id=None) -> dict[str, float]` — same as before, plus an optional `root_id`, and it now fuses via `aggregate_beliefs`. When `root_id` is None it falls back to the observation's provenance `source` (the same fallback replay uses for legacy rows), so a caller that supplies no origin still counts as exactly one root. `ingest_document` supplies a real canonical root in Task 5; until then this keeps the document path working and leaves the tree green at the end of this task.

- [ ] **Step 1: Write the failing tests**

```python
# tests/worldview_app/test_ingest.py  (append)
import math

from epistemic_pipeline.worldview_app.ingest import _replay_beliefs, ingest_rating
from epistemic_pipeline.worldview_app.store import Store


def _rate(store, *, root_id, prompt_hash):
    return ingest_rating(
        store, {"c": 1.0}, source_type="inferred", ts=1.0, model_id="m",
        prompt_hash=prompt_hash, seed=0, reason="r", root_id=root_id,
    )


def test_same_root_does_not_inflate_settledness():
    with Store(":memory:") as store:
        _rate(store, root_id="blog-A", prompt_hash="h1")
        _rate(store, root_id="blog-A", prompt_hash="h2")  # same source, rated again
        beliefs = _replay_beliefs(store)
        assert math.isclose(beliefs.opinions["c"].uncertainty, 0.5)  # one root's worth


def test_distinct_roots_raise_settledness():
    with Store(":memory:") as store:
        _rate(store, root_id="blog-A", prompt_hash="h1")
        _rate(store, root_id="paper-B", prompt_hash="h2")
        beliefs = _replay_beliefs(store)
        assert beliefs.opinions["c"].uncertainty < 0.5  # two roots accumulate


def test_replay_is_deterministic():
    with Store(":memory:") as store:
        _rate(store, root_id="blog-A", prompt_hash="h1")
        _rate(store, root_id="paper-B", prompt_hash="h2")
        a = _replay_beliefs(store).opinions["c"]
        b = _replay_beliefs(store).opinions["c"]
        assert (a.r, a.s, a.base_rate) == (b.r, b.s, b.base_rate)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/worldview_app/test_ingest.py -v -k "root or deterministic"`
Expected: FAIL — `ingest_rating()` raises `TypeError: ... unexpected keyword argument 'root_id'`.

- [ ] **Step 3: Fix the imports in `ingest.py`**

In the `from epistemic_pipeline.encodings.worldview import (...)` block, add `aggregate_beliefs` and remove `worldview_update` (it is no longer used in this module). Keep `extraction_observation`, `WorldviewOntology`, `WorldviewBeliefs`, `DEFAULT_BASE_RATE`. Confirm `parse_confidence_vector` is already imported (it is — `ingest_document` uses it).

- [ ] **Step 4: Add `_ratings_from_store` and rewrite `_replay_beliefs`**

Replace the body of `_replay_beliefs` and add the helper above it:

```python
def _ratings_from_store(store: Store) -> list[tuple[str, dict[str, float]]]:
    """Read the trail as (root_id, confidence-vector) pairs.

    The root id is the recorded ``root_id``; legacy rows that predate it
    fall back to ``source`` so each still counts as its own root.
    """
    ratings: list[tuple[str, dict[str, float]]] = []
    for row in store.observations():
        if row["variable"] != "confidence_vector":
            continue
        root = row["root_id"] or row["source"]
        ratings.append((root, parse_confidence_vector(row["value"])))
    return ratings


def _replay_beliefs(store: Store) -> WorldviewBeliefs:
    """Rebuild opinions by replaying R (two-tier fusion) over the trail.

    Groups each concept's evidence by root id: averaging within a root,
    cumulative across distinct roots. The ontology is read here (the full,
    current concept set) so a stale ontology cannot silently drop concepts.
    """
    ontology = WorldviewOntology(concepts=frozenset(store.concepts()))
    return aggregate_beliefs(_ratings_from_store(store), ontology)
```

(Delete the old `_replay_beliefs` docstring/body and its per-row `worldview_update` loop. Keep the surrounding `_prompt_hash` / `author_claim` functions untouched.)

- [ ] **Step 5: Thread `root_id` through `ingest_rating`**

Add `root_id: str | None = None` to the signature (keyword-only, alongside the others) and document it: "the canonical source this rating traces to; None falls back to the provenance source, so an unrooted rating counts as one root." Replace the before/after computation and the `add_observation` call:

```python
    rated = {c: v for c, v in confidences.items() if math.isfinite(v)}
    if not rated:
        return {}
    for claim in rated:
        store.add_concept(claim, source_type)

    # Build the observation first: its provenance source doubles as the root
    # when the caller gives none. That is the same fallback replay uses for
    # legacy rows (row["root_id"] or row["source"]), so a direct rating still
    # counts as exactly one root, and the cached projected probabilities here
    # match what _replay_beliefs will later derive.
    obs = extraction_observation(rated, ts, model_id, prompt_hash, seed)
    root = root_id or obs.source

    ontology = WorldviewOntology(concepts=frozenset(store.concepts()))
    after = aggregate_beliefs([*_ratings_from_store(store), (root, rated)], ontology)

    moved = [c for c in rated if c in after.opinions]
    if not moved:
        return {}

    obs_id = store.add_observation(
        obs.variable,
        obs.value,
        obs.source,
        obs.confidence,
        obs.timestamp,
        modality=obs.modality,
        root_id=root_id,
    )
```

(Store the literal `root_id` — None when the caller gave none — so the column keeps its "None = origin not recorded" meaning and replay's `row["root_id"] or row["source"]` fallback resolves it to the same `root` used above. In-memory and replayed beliefs therefore agree.)

Leave the `for claim in moved:` link-writing loop below it unchanged (it computes drift from `store.get_claim`, not from beliefs).

- [ ] **Step 6: Run the new tests**

Run: `uv run pytest tests/worldview_app/test_ingest.py -v -k "root or deterministic"`
Expected: PASS (3 tests)

- [ ] **Step 7: Run the FULL suite — it must stay green**

Run: `uv run pytest -q`
Expected: **all green.** Because `root_id` defaults to the provenance `source`, `ingest_document`/`NoteIngester` and the direct `ingest_rating` call (`test_non_finite_rating_leaves_no_orphan_concept`, which passes no `root_id`) keep working untouched. Every existing test ingests **distinct** documents, so each gets a distinct fallback root and still accumulates exactly as before — including `test_replay_matches_incremental_build`, whose cumulative `expected` equals two-tier fusion over singleton roots. No existing test ingests the **same** document text twice expecting accumulation, so nothing should need flipping here; the re-ingest-after-edit collapse lands in Task 5 (where `NoteIngester` starts passing `origin=path`). If a test does turn red, do not weaken it: flip it to the no-inflation expectation only if it genuinely encoded the bug; otherwise it is a regression to fix.

- [ ] **Step 8: Lint, type-check, commit**

```bash
uv run ruff check src/epistemic_pipeline/worldview_app/ingest.py tests/worldview_app/test_ingest.py
uv run pyright src/epistemic_pipeline/worldview_app/ingest.py
git add src/epistemic_pipeline/worldview_app/ingest.py tests/worldview_app/test_ingest.py
git commit -m "feat: replay beliefs with root-keyed two-tier fusion (#25)"
```

---

### Task 5: Capture the origin at ingest

**Files:**
- Modify: `src/epistemic_pipeline/worldview_app/ingest.py` (`ingest_document`, `NoteIngester.ingest`, import)
- Test: `tests/worldview_app/test_ingest.py` (append)

**Interfaces:**
- Consumes: `canonicalize_origin` (Task 1); `ingest_rating(..., root_id=...)` (Task 4).
- Produces: `ingest_document(store, llm, question, document, *, ts, seed, model_id, origin, reason=None, source_type="inferred") -> dict[str, float]` — now takes the canonical `origin` of the document. `NoteIngester.ingest` passes the note `path` as the origin, so a note re-ingested after an edit keeps one root.

- [ ] **Step 1: Write the failing tests**

```python
# tests/worldview_app/test_ingest.py  (append)
from types import SimpleNamespace

from epistemic_pipeline.worldview_app.ingest import NoteIngester, ingest_document


class _StubLLM:
    """Rates every document with a fixed confidence vector."""

    def __init__(self, content: str) -> None:
        self._content = content

    def rate_confidence(self, question: str, known: tuple[str, ...], document: str):
        return SimpleNamespace(content=self._content)


def test_reingest_after_edit_does_not_inflate():
    with Store(":memory:") as store:
        ing = NoteIngester(store, _StubLLM('{"c": 1.0}'), "q", model_id="m")
        ing.ingest("notes/n.md", "version one", ts=1.0, seed=0)
        ing.ingest("notes/n.md", "version two — edited", ts=2.0, seed=0)  # same note, changed
        beliefs = _replay_beliefs(store)
        assert math.isclose(beliefs.opinions["c"].uncertainty, 0.5)  # one root


def test_same_article_two_urls_collapse_via_canonicalization():
    with Store(":memory:") as store:
        llm = _StubLLM('{"c": 1.0}')
        ingest_document(store, llm, "q", "doc", ts=1.0, seed=0, model_id="m",
                        origin="https://blog.com/x?utm_source=tw")
        ingest_document(store, llm, "q", "doc", ts=2.0, seed=0, model_id="m",
                        origin="https://blog.com/x")
        assert math.isclose(_replay_beliefs(store).opinions["c"].uncertainty, 0.5)


def test_resolver_miss_two_distinct_origins_over_count():
    # Distinct origins that do NOT canonicalize equal are two roots — proof
    # the dedup lives in the canonicalizer, not the fusion algebra.
    with Store(":memory:") as store:
        llm = _StubLLM('{"c": 1.0}')
        ingest_document(store, llm, "q", "doc", ts=1.0, seed=0, model_id="m", origin="notes/a.md")
        ingest_document(store, llm, "q", "doc", ts=2.0, seed=0, model_id="m", origin="notes/b.md")
        assert _replay_beliefs(store).opinions["c"].uncertainty < 0.5
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/worldview_app/test_ingest.py -v -k "reingest or canonical or resolver"`
Expected: FAIL — `ingest_document()` raises `TypeError: ... missing ... 'origin'` (and `NoteIngester` does not pass it yet).

- [ ] **Step 3: Import the canonicalizer**

In `ingest.py`, add:

```python
from epistemic_pipeline.worldview_app.provenance import canonicalize_origin
```

- [ ] **Step 4: Add `origin` to `ingest_document`**

Add `origin: str` as a keyword-only parameter (place it before `reason`), document it, and pass the canonicalized root to `ingest_rating`:

```python
def ingest_document(  # noqa: PLR0913
    store: Store,
    llm: RatingLLMInterface,
    question: str,
    document: str,
    *,
    ts: float,
    seed: int,
    model_id: str,
    origin: str,
    reason: str | None = None,
    source_type: str = "inferred",
) -> dict[str, float]:
```

Add to the docstring's Args: `origin: the canonical source the document came from (a URL, DOI, or note path). Resolved to a root id so re-imports of one source are not double-counted.` Then change the `return ingest_rating(...)` call to add:

```python
        root_id=canonicalize_origin(origin),
```

- [ ] **Step 5: Pass the note path as origin in `NoteIngester.ingest`**

In the `ingest_document(...)` call inside `NoteIngester.ingest`, add `origin=path` (the note's path is its stable entity id; editing the body does not change it):

```python
        result = ingest_document(
            self.store,
            self.llm,
            self.question,
            content,
            ts=ts,
            seed=seed,
            model_id=self.model_id,
            origin=path,
            reason=path,
            source_type="derived",
        )
```

(Match the existing keyword arguments already in that call; only `origin=path` is new. If `reason`/`source_type` are already passed, leave them.)

- [ ] **Step 6: Run the new tests**

Run: `uv run pytest tests/worldview_app/test_ingest.py -v -k "reingest or canonical or resolver"`
Expected: PASS (3 tests)

- [ ] **Step 7: Run the full suite, lint, type-check**

```bash
uv run pytest -q
uv run ruff check src/epistemic_pipeline/worldview_app/ingest.py tests/worldview_app/test_ingest.py
uv run pyright src/epistemic_pipeline/worldview_app/ingest.py
```

Expected: all green. The existing `tests/worldview_app/test_ingest.py` has ~14 `ingest_document` calls; each now raises a missing-`origin` `TypeError` until you add `origin=`. **CRITICAL:** give each *distinct* document its own origin (e.g. `origin="d1"`, `origin="d2"`, `origin=f"d{i}"`, or the existing doc-text string) so the multi-document tests keep **distinct** roots and their accumulation/delta assertions still hold. Tests relying on distinct-document accumulation include `test_grows_ontology_and_links_evidence`, `test_second_document_relinks_with_new_delta`, `test_unmentioned_claim_is_not_erased`, `test_nonoverlapping_documents_accumulate_above_one`, and `test_replay_matches_incremental_build`. Only a same-source scenario should share an origin. The lone production caller is `NoteIngester.ingest` (handled in Step 5); there are no other non-test callers.

- [ ] **Step 8: Commit**

```bash
git add src/epistemic_pipeline/worldview_app/ingest.py tests/worldview_app/test_ingest.py
git commit -m "feat: capture document origin and resolve it to a root id (#25)"
```

---

## Self-Review

**Spec coverage:**
- §2 / §4 D3 two-tier fusion → Task 3 (`two_tier_fuse`, `aggregate_beliefs`) + Task 4 (replay uses it). ✓
- §4 D1 identity ≠ content hash → Task 5 (`NoteIngester` passes the stable `path`, so an edit keeps one root); test `test_reingest_after_edit_does_not_inflate`. ✓
- §4 D2 canonicalize the supplied origin, no prose-scraping → Task 1 + Task 5. ✓
- §4 D4 fold lives in replay, R pure, byte-identical → Task 4 (`_replay_beliefs` → `aggregate_beliefs`, `worldview_update` untouched); test `test_replay_is_deterministic`. ✓
- §4 D5 citing-source own-credit zero / no DAG / no graph store → nothing builds them; replay only sees roots. ✓ (Deferred per §8.)
- §4 D7 honest naming → `two_tier_fuse` docstring frames averaging as the duplicate-collapsing rule; no EBSL claim in code. ✓
- §7 gates → no-inflation (T4), calibration-dual (T3/T4), resolver-miss (T5), replay-determinism (T4). ✓
- §10 dedup correctness = canonicalization quality → `test_resolver_miss_two_distinct_origins_over_count` makes the boundary explicit. ✓

**Placeholder scan:** No TBD/TODO; every code and test step shows full code; commands have expected output. ✓

**Type consistency:** `canonicalize_origin(str)->str`, `add_observation(..., root_id: str|None=None)`, `two_tier_fuse(Mapping[str, Sequence[Opinion]])->Opinion`, `aggregate_beliefs(Sequence[tuple[str, Mapping[str,float]]], WorldviewOntology)->WorldviewBeliefs`, `_ratings_from_store(Store)->list[tuple[str,dict[str,float]]]`, `ingest_rating(..., root_id: str | None = None)`, `ingest_document(..., origin: str)` — names and signatures are consistent across tasks. ✓

**One known ripple (not a gap):** Task 4 Step 7 and Task 5 Step 7 call out that pre-existing tests/callers may need updating (tests that encoded inflation; callers of `ingest_document` that must now pass `origin`). These are handled in-task, not deferred.

## Out of scope (deferred per spec §8)

Source→source citation DAG, multi-hop EBSL flow, graded own-credit, automated similarity clustering, in-document citation parsing. Do not build these; the plan must stay the v1 root-keyed map.
