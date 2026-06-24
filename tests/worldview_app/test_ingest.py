"""Tests for the three worldview ingestion paths (#8)."""

import json

import pytest

from epistemic_pipeline.llm.llm_interfaces import LLMResponse, MockRatingLLM
from epistemic_pipeline.worldview_app.ingest import (
    NoteIngester,
    author_claim,
    ingest_document,
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
    def test_inferred_claims_persisted_and_normalized(self, store):
        llm = _llm({"A": 0.6, "B": 0.2})
        posterior = ingest_document(
            store,
            llm,
            "q",
            "doc text",
            ts=1.0,
            seed=0,
            model_id="m",
        )
        # 0.6 / 0.8 = 0.75, 0.2 / 0.8 = 0.25
        assert posterior["A"] == pytest.approx(0.75)
        assert posterior["B"] == pytest.approx(0.25)
        a = store.get_claim("A")
        assert a["source_type"] == "inferred"
        assert a["confidence"] == pytest.approx(0.75)

    def test_grows_ontology_and_links_evidence(self, store):
        llm = _llm({"A": 1.0})
        ingest_document(store, llm, "q", "d", ts=2.0, seed=0, model_id="m")
        assert store.has_concept("A")
        hist = store.history("A")
        assert len(hist) == 1
        # first document: delta is the full posterior (prior was 0)
        assert hist[0]["delta"] == pytest.approx(1.0)
        assert hist[0]["reason"].startswith("doc:")

    def test_first_document_on_empty_store_is_complete(self, store):
        # The empty-prior path: no setup, one doc yields usable beliefs.
        llm = _llm({"claim x": 0.9, "claim y": 0.1})
        posterior = ingest_document(
            store,
            llm,
            "q",
            "d",
            ts=1.0,
            seed=0,
            model_id="m",
        )
        assert sum(posterior.values()) == pytest.approx(1.0)
        assert store.get_claim("claim x")["confidence"] == pytest.approx(0.9)

    def test_empty_rating_writes_nothing(self, store):
        llm = _llm({})
        posterior = ingest_document(store, llm, "q", "d", ts=1.0, seed=0, model_id="m")
        assert posterior == {}
        assert store.claims() == []

    def test_second_document_relinks_with_new_delta(self, store):
        # Two documents rate claim A differently; the drift timeline records both.
        llm = _llm({"A": 1.0}, {"A": 0.5, "B": 0.5})
        ingest_document(store, llm, "q", "d1", ts=1.0, seed=0, model_id="m")
        ingest_document(store, llm, "q", "d2", ts=2.0, seed=0, model_id="m")
        hist = store.history("A")
        assert len(hist) == 2
        # A went 0 -> 1.0 (delta +1.0), then 1.0 -> 0.5 (delta -0.5)
        assert hist[0]["delta"] == pytest.approx(1.0)
        assert hist[1]["delta"] == pytest.approx(-0.5)

    def test_degenerate_rating_leaves_other_claims_untouched(self, store):
        # A non-empty all-zero rating filters to no mass, so the revision
        # policy echoes the prior. The ingest must not re-stamp, relink, or
        # observe the unrelated claim it never mentioned.
        author_claim(store, "user claim", 0.8, ts=1.0)
        result = ingest_document(
            store,
            _llm({"unrated": 0.0}),
            "q",
            "d",
            ts=2.0,
            seed=0,
            model_id="m",
        )
        assert result == {}
        uc = store.get_claim("user claim")
        assert uc["source_type"] == "user"  # not flipped to inferred
        assert uc["confidence"] == pytest.approx(0.8)
        assert store.history("user claim") == []  # no spurious zero-delta link
        assert store.observations() == []  # no dangling observation


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
        store, _llm({"inferred claim": 1.0}), "q", "d", ts=2.0, seed=0, model_id="m"
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
            s, _llm({"A": 0.6, "B": 0.4}), "q", "doc", ts=1.0, seed=0, model_id="m"
        )
        result = {r["id"]: r["confidence"] for r in s.claims()}
        sources = {r["source"] for r in s.observations()}
        s.close()
        return result, sources

    assert run() == run()
