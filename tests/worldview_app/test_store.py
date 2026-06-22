"""Tests for the worldview belief store."""

import sqlite3

import pytest

from epistemic_pipeline.worldview_app.store import Store


@pytest.fixture
def store():
    s = Store(":memory:")
    yield s
    s.close()


class TestClaims:
    def test_put_and_get(self, store):
        store.put_claim("c1", "the moon is cheese", 0.3, "user", ts=1.0)
        row = store.get_claim("c1")
        assert row["text"] == "the moon is cheese"
        assert row["confidence"] == 0.3
        assert row["source_type"] == "user"

    def test_get_missing_returns_none(self, store):
        assert store.get_claim("nope") is None

    def test_put_updates_confidence_in_place(self, store):
        store.put_claim("c1", "x", 0.3, "inferred", ts=1.0)
        store.put_claim("c1", "x", 0.9, "inferred", ts=2.0)
        row = store.get_claim("c1")
        assert row["confidence"] == 0.9
        assert row["last_updated"] == 2.0
        assert len(store.claims()) == 1  # update, not insert

    def test_claims_sorted_by_confidence_desc(self, store):
        store.put_claim("a", "a", 0.2, "user", ts=1.0)
        store.put_claim("b", "b", 0.8, "user", ts=1.0)
        assert [r["id"] for r in store.claims()] == ["b", "a"]

    def test_bad_source_type_rejected(self, store):
        with pytest.raises(ValueError, match="source_type"):
            store.put_claim("c1", "x", 0.5, "guessed", ts=1.0)

    def test_put_overwrites_text_and_source_type_in_place(self, store):
        store.put_claim("c1", "original", 0.3, "inferred", ts=1.0)
        store.put_claim("c1", "corrected", 0.9, "user", ts=2.0)
        row = store.get_claim("c1")
        assert row["text"] == "corrected"
        assert row["source_type"] == "user"
        assert row["confidence"] == 0.9
        assert row["last_updated"] == 2.0
        assert len(store.claims()) == 1  # update, not insert

    def test_claims_tie_broken_by_id(self, store):
        for cid in ("c", "a", "b"):
            store.put_claim(cid, cid, 0.5, "user", ts=1.0)
        # equal confidence -> deterministic order by id
        assert [r["id"] for r in store.claims()] == ["a", "b", "c"]

    @pytest.mark.parametrize("bad", [1.5, -0.1])
    def test_confidence_out_of_range_rejected(self, store, bad):
        with pytest.raises(ValueError, match="confidence"):
            store.put_claim("c1", "x", bad, "user", ts=1.0)


class TestObservations:
    def test_add_returns_id_and_is_append_only(self, store):
        i1 = store.add_observation("v", "1", "src", 1.0, 1.0, modality="tool")
        i2 = store.add_observation("v", "2", "src", 1.0, 2.0)
        assert i1 != i2
        rows = store.observations()
        assert len(rows) == 2
        assert rows[0]["modality"] == "tool"
        assert rows[1]["modality"] is None

    def test_confidence_out_of_range_rejected(self, store):
        with pytest.raises(ValueError, match="confidence"):
            store.add_observation("v", "1", "s", 1.5, 1.0)


class TestConcepts:
    def test_add_and_has(self, store):
        store.add_concept("revenue", "inferred")
        assert store.has_concept("revenue")
        assert not store.has_concept("ebitda")

    def test_add_is_idempotent(self, store):
        store.add_concept("revenue", "inferred")
        store.add_concept("revenue", "user")
        assert store.concepts() == ["revenue"]

    def test_readd_keeps_original_source_type(self, store):
        store.add_concept("revenue", "inferred")
        store.add_concept("revenue", "user")  # first write wins
        cur = store.conn.execute(
            "SELECT source_type FROM concepts WHERE name = ?", ("revenue",)
        )
        assert cur.fetchone()["source_type"] == "inferred"

    def test_bad_source_type_rejected(self, store):
        with pytest.raises(ValueError, match="source_type"):
            store.add_concept("x", "made-up")


class TestEvidenceLinks:
    def test_history_is_time_ordered(self, store):
        store.put_claim("c1", "x", 0.5, "inferred", ts=1.0)
        o1 = store.add_observation("v", "1", "s", 1.0, 1.0)
        o2 = store.add_observation("v", "2", "s", 1.0, 2.0)
        store.add_link("c1", o2, delta=0.2, reason="second", ts=2.0)
        store.add_link("c1", o1, delta=0.1, reason="first", ts=1.0)
        hist = store.history("c1")
        assert [r["reason"] for r in hist] == ["first", "second"]
        assert [r["delta"] for r in hist] == [0.1, 0.2]

    def test_link_requires_existing_claim(self, store):
        # claim_id foreign key is enforced
        with pytest.raises(sqlite3.IntegrityError):
            store.add_link("ghost", 1, delta=0.1, reason="x", ts=1.0)

    def test_link_requires_existing_observation(self, store):
        # observation_id foreign key is enforced (claim exists, observation does not)
        store.put_claim("c1", "x", 0.5, "inferred", ts=1.0)
        with pytest.raises(sqlite3.IntegrityError):
            store.add_link("c1", 999, delta=0.1, reason="x", ts=1.0)

    def test_history_tie_broken_by_insertion_order(self, store):
        store.put_claim("c1", "x", 0.5, "inferred", ts=1.0)
        o1 = store.add_observation("v", "1", "s", 1.0, 1.0)
        o2 = store.add_observation("v", "2", "s", 1.0, 1.0)
        # same timestamp -> insertion (rowid) order, deterministic
        store.add_link("c1", o1, delta=0.1, reason="first", ts=5.0)
        store.add_link("c1", o2, delta=0.2, reason="second", ts=5.0)
        assert [r["reason"] for r in store.history("c1")] == ["first", "second"]


def test_survives_close_and_reopen(tmp_path):
    path = tmp_path / "w.db"
    s = Store(path)
    s.put_claim("c1", "x", 0.7, "derived", ts=1.0)
    oid = s.add_observation("v", "1", "s", 1.0, 1.0)
    s.add_link("c1", oid, delta=0.2, reason="r", ts=1.0)
    s.add_concept("topic", "derived")
    s.close()

    s2 = Store(path)
    row = s2.get_claim("c1")
    assert row is not None
    assert row["confidence"] == 0.7
    assert len(s2.observations()) == 1
    assert s2.has_concept("topic")
    assert len(s2.history("c1")) == 1
    s2.close()


def test_fresh_store_is_empty():
    """No setup step: a brand-new store has empty tables, not an error."""
    s = Store(":memory:")
    assert s.claims() == []
    assert s.observations() == []
    assert s.concepts() == []
    s.close()
