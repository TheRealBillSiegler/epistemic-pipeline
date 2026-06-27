"""Tests for the three worldview ingestion paths (#8)."""

import json
import math

import pytest

from epistemic_pipeline.encodings.worldview import (
    WorldviewBeliefs,
    WorldviewOntology,
    extraction_observation,
    worldview_update,
)
from epistemic_pipeline.llm.llm_interfaces import LLMResponse, MockRatingLLM
from epistemic_pipeline.worldview_app.ingest import (
    NoteIngester,
    _replay_beliefs,  # pyright: ignore[reportPrivateUsage]  # testing the module's own helper
    author_claim,
    ingest_document,
    ingest_rating,
)
from epistemic_pipeline.worldview_app.store import Store


@pytest.fixture
def store():
    s = Store(":memory:")
    yield s
    s.close()


def _llm(*ratings):
    """A mock LLM that returns the given dicts as confidence vectors, in order."""
    return MockRatingLLM(
        {},
        confidence_ratings=[LLMResponse(json.dumps(r), 1.0) for r in ratings],
    )


class TestAuthorClaim:
    def test_writes_user_claim_and_concept(self, store):
        author_claim(store, "the sky is blue", 0.95, ts=1.0)
        row = store.get_claim("the sky is blue")
        assert row is not None
        assert row["source_type"] == "user"
        assert row["confidence"] == 0.95
        assert store.has_concept("the sky is blue")

    def test_no_evidence_link_for_user_claim(self, store):
        author_claim(store, "c", 0.5, ts=1.0)
        assert store.history("c") == []


class TestIngestDocument:
    def test_inferred_claims_persisted_as_opinions(self, store):
        # Each claim is an independent opinion, not a normalized share.
        # p=0.6 -> Opinion(1.2, 0.8) -> P=0.55; p=0.2 -> Opinion(0.4, 1.6) -> P=0.35.
        llm = _llm({"A": 0.6, "B": 0.2})
        posterior = ingest_document(
            store,
            llm,
            "q",
            "doc text",
            ts=1.0,
            seed=0,
            model_id="m",
            origin="doc text",  # single-doc test
        )
        assert posterior["A"] == pytest.approx(0.55)
        assert posterior["B"] == pytest.approx(0.35)
        a = store.get_claim("A")
        assert a["source_type"] == "inferred"
        assert a["confidence"] == pytest.approx(0.55)

    def test_grows_ontology_and_links_evidence(self, store):
        llm = _llm({"A": 1.0})
        ingest_document(store, llm, "q", "d", ts=2.0, seed=0, model_id="m", origin="d1")  # single distinct doc
        assert store.has_concept("A")
        hist = store.history("A")
        assert len(hist) == 1
        # First document: A moves from vacuous (P=0.5) to believed (P=0.75).
        assert hist[0]["delta"] == pytest.approx(0.25)
        assert hist[0]["reason"].startswith("doc:")

    def test_first_document_on_empty_store_is_complete(self, store):
        # The empty-prior path: no setup, one doc yields usable beliefs.
        # p=0.9 -> P=0.7; the higher-confidence claim leads.
        llm = _llm({"claim x": 0.9, "claim y": 0.1})
        posterior = ingest_document(
            store,
            llm,
            "q",
            "d",
            ts=1.0,
            seed=0,
            model_id="m",
            origin="d",  # single-doc test
        )
        assert posterior["claim x"] > posterior["claim y"]
        assert store.get_claim("claim x")["confidence"] == pytest.approx(0.7)

    def test_empty_rating_writes_nothing(self, store):
        llm = _llm({})
        posterior = ingest_document(store, llm, "q", "d", ts=1.0, seed=0, model_id="m", origin="d")  # single-doc test
        assert posterior == {}
        assert store.claims() == []

    def test_second_document_relinks_with_new_delta(self, store):
        # Two documents rate claim A differently; the drift timeline records both.
        llm = _llm({"A": 1.0}, {"A": 0.5, "B": 0.5})
        ingest_document(store, llm, "q", "d1", ts=1.0, seed=0, model_id="m", origin="d1")  # distinct doc 1
        ingest_document(store, llm, "q", "d2", ts=2.0, seed=0, model_id="m", origin="d2")  # distinct doc 2
        hist = store.history("A")
        assert len(hist) == 2
        # A: vacuous(0.5) -> believed(0.75) [+0.25], then accumulates mixed
        # evidence Opinion(2,0)+Opinion(1,1)=Opinion(3,1), P=0.667 [-0.0833].
        assert hist[0]["delta"] == pytest.approx(0.25)
        assert hist[1]["delta"] == pytest.approx(2 / 3 - 0.75)

    def test_disconfirming_rating_does_not_touch_unrelated_claims(self, store):
        # Under Subjective Logic a 0.0 rating is disconfirmation, not a no-op:
        # it records a real opinion. But it must still leave a claim it never
        # mentioned completely alone.
        author_claim(store, "user claim", 0.8, ts=1.0)
        result = ingest_document(
            store,
            _llm({"unrated": 0.0}),
            "q",
            "d",
            ts=2.0,
            seed=0,
            model_id="m",
            origin="d",  # single-doc test
        )
        # 0.0 -> Opinion(0, 2) -> P=0.25: disconfirmation is recorded.
        assert result == {"unrated": pytest.approx(0.25)}
        assert store.get_claim("unrated")["confidence"] == pytest.approx(0.25)
        # The unrelated user claim is untouched.
        uc = store.get_claim("user claim")
        assert uc["source_type"] == "user"
        assert uc["confidence"] == pytest.approx(0.8)
        assert store.history("user claim") == []

    def test_document_rating_of_user_claim_reconciles_drift(self, store):
        # A document rating a claim the user authored takes over, and the
        # drift link reflects the change the user actually sees (0.8 -> 0.7),
        # not a change measured from the vacuous base rate.
        author_claim(store, "X", 0.8, ts=1.0)
        result = ingest_document(
            store, _llm({"X": 0.9}), "q", "d", ts=2.0, seed=0, model_id="m", origin="d"  # single-doc test
        )
        assert result["X"] == pytest.approx(0.7)  # p=0.9 -> Opinion(1.8,0.2) -> 0.7
        row = store.get_claim("X")
        assert row["confidence"] == pytest.approx(0.7)
        assert row["source_type"] == "inferred"  # document evidence takes over
        assert store.history("X")[-1]["delta"] == pytest.approx(0.7 - 0.8)

    def test_unmentioned_claim_is_not_erased(self, store):
        # The amnesia regression at the store level: a second document silent
        # on A must leave A's stored belief and history untouched.
        ingest_document(
            store, _llm({"A": 1.0}), "q", "d1", ts=1.0, seed=0, model_id="m", origin="d1"  # distinct doc 1
        )
        a_before = store.get_claim("A")["confidence"]
        ingest_document(
            store, _llm({"B": 1.0}), "q", "d2", ts=2.0, seed=0, model_id="m", origin="d2"  # distinct doc 2
        )
        assert store.get_claim("A")["confidence"] == pytest.approx(a_before)
        assert len(store.history("A")) == 1  # no new link for the silent doc

    def test_nonoverlapping_documents_accumulate_above_one(self, store):
        # ARCHIVE contract: store.claims() is a high-water per-claim archive,
        # not one normalized distribution. Two documents that rate disjoint
        # concepts both persist, and their confidences sum past 1.0 by design.
        ingest_document(
            store, _llm({"A": 1.0}), "q", "d1", ts=1.0, seed=0, model_id="m", origin="d1"  # distinct doc 1
        )
        ingest_document(
            store, _llm({"B": 1.0}), "q", "d2", ts=2.0, seed=0, model_id="m", origin="d2"  # distinct doc 2
        )
        rows = {r["id"]: r["confidence"] for r in store.claims()}
        assert set(rows) == {"A", "B"}  # neither concept dropped
        assert sum(rows.values()) > 1.0  # not normalized across docs, by design


class TestReplayAndOrphanFilter:
    def test_replay_matches_incremental_build(self, store):
        # _replay_beliefs rebuilds B from the stored evidence trail. That
        # rebuild must equal fusing the same ratings in memory -- the
        # "B is a pure function of E" invariant the no-schema-change design
        # rests on. Three overlapping documents exercise carry-forward,
        # accumulation, and a new concept arriving, all at once.
        ratings = [{"A": 0.6, "B": 0.2}, {"A": 0.9, "C": 0.4}, {"B": 0.5, "C": 1.0}]
        for i, r in enumerate(ratings):
            ingest_document(store, _llm(r), "q", f"d{i}", ts=float(i), seed=0, model_id="m", origin=f"d{i}")  # each doc distinct

        ont = WorldviewOntology(concepts=frozenset(store.concepts()))
        expected = WorldviewBeliefs({})
        for i, r in enumerate(ratings):
            obs = extraction_observation(r, float(i), "m", "h", 0)
            expected = worldview_update(expected, obs, ont)

        assert _replay_beliefs(store).opinions == expected.opinions

    def test_non_finite_rating_leaves_no_orphan_concept(self, store):
        # ingest_rating drops NaN/Inf before add_concept, so a non-finite value
        # cannot leave an orphan concept in O with no belief behind it. Called
        # directly: ingest_document's parser would strip the bad value first, so
        # only the direct path exercises this guard.
        result = ingest_rating(
            store,
            {"good": 0.8, "bad": float("inf")},
            source_type="inferred",
            ts=1.0,
            model_id="m",
            prompt_hash="h",
            seed=0,
            reason="r",
        )
        assert set(result) == {"good"}
        assert store.has_concept("good") is True
        assert store.has_concept("bad") is False
        assert store.get_claim("bad") is None


class TestNoteIngester:
    def test_unchanged_content_is_deduped(self, store):
        llm = _llm({"A": 1.0})  # only ONE rating queued
        ing = NoteIngester(store, llm, "q", model_id="m")
        first = ing.ingest("note.md", "same body", ts=1.0, seed=0)
        second = ing.ingest("note.md", "same body", ts=2.0, seed=0)
        assert first is not None
        assert second is None  # deduped, so the LLM was not called again
        assert len(store.history("A")) == 1

    def test_changed_content_reingests(self, store):
        llm = _llm({"A": 1.0}, {"B": 1.0})
        ing = NoteIngester(store, llm, "q", model_id="m")
        ing.ingest("note.md", "body v1", ts=1.0, seed=0)
        ing.ingest("note.md", "body v2", ts=2.0, seed=0)
        assert store.has_concept("A")
        assert store.has_concept("B")

    def test_derived_source_type(self, store):
        llm = _llm({"A": 1.0})
        ing = NoteIngester(store, llm, "q", model_id="m")
        ing.ingest("note.md", "body", ts=1.0, seed=0)
        assert store.get_claim("A")["source_type"] == "derived"

    def test_failed_ingest_is_retried_not_skipped(self, store):
        # Only one rating is queued. The first changed note consumes it; the
        # second raises (queue empty). Re-ingesting the second content must
        # retry (raise again), not dedupe-skip a note that never landed.
        ing = NoteIngester(store, _llm({"A": 1.0}), "q", model_id="m")
        ing.ingest("note.md", "v1", ts=1.0, seed=0)  # consumes the rating
        with pytest.raises(IndexError):
            ing.ingest("note.md", "v2", ts=2.0, seed=0)  # LLM call raises
        with pytest.raises(IndexError):
            ing.ingest("note.md", "v2", ts=3.0, seed=0)  # retried, not skipped


def test_all_three_paths_share_one_store(store):
    author_claim(store, "user claim", 0.8, ts=1.0)
    ingest_document(
        store, _llm({"inferred claim": 1.0}), "q", "d", ts=2.0, seed=0, model_id="m", origin="d"  # single-doc test
    )
    NoteIngester(store, _llm({"derived claim": 1.0}), "q", model_id="m").ingest(
        "n.md",
        "body",
        ts=3.0,
        seed=0,
    )
    by_source = {r["id"]: r["source_type"] for r in store.claims()}
    assert by_source == {
        "user claim": "user",
        "inferred claim": "inferred",
        "derived claim": "derived",
    }


def test_same_inputs_produce_same_stored_beliefs():
    # Determinism: two fresh stores, identical inputs -> identical beliefs.
    def run():
        s = Store(":memory:")
        ingest_document(
            s, _llm({"A": 0.6, "B": 0.4}), "q", "doc", ts=1.0, seed=0, model_id="m", origin="doc"  # single-doc test
        )
        result = {r["id"]: r["confidence"] for r in s.claims()}
        sources = {r["source"] for r in s.observations()}
        s.close()
        return result, sources

    assert run() == run()


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


from types import SimpleNamespace  # noqa: E402


class _StubLLM:
    """Rates every document with a fixed confidence vector."""

    def __init__(self, content: str) -> None:
        self._content = content

    def rate_confidence(self, _question: str, _known: tuple[str, ...], _document: str):
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
