"""SQLite belief store for the worldview app.

Holds the four things the app reasons over:

- claims: the accumulated belief archive. One row per claim, upserted by
  id and never deleted. A claim has a confidence in [0, 1] and a
  source_type recording where it came from (inferred / user / derived).
  This is a high-water archive, not one normalized distribution: the
  single normalized vector for the latest document is what
  worldview_update returns, and across documents that rate different
  claims the confidences here can sum past 1.0.
- observations: the evidence E. Append-only. Stores the Observation
  dataclass fields except `etype` (the app does not branch on evidence
  type yet); add that column when it does.
- concepts: the ontology O terms. Append-only set of names.
- evidence_links: which observation moved which claim by how much.
  Append-only. This is also the belief-drift timeline: the history of
  one claim is just its links ordered by time.

All timestamps are caller-supplied floats (epoch seconds), never wall
clock. The whole system is deterministic and replayable, so the store
must never invent a value that a replay could not reproduce.

Deliberate simplification: no `traces` table. Full-trace replay lives in
trace.py as JSONL files; the drift timeline comes from evidence_links.
Two concerns, not one table.
"""

from __future__ import annotations

import sqlite3
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

# source_type values for claims and concepts.
SOURCE_TYPES = ("inferred", "user", "derived")

_SCHEMA = """
CREATE TABLE IF NOT EXISTS claims (
    id           TEXT PRIMARY KEY,
    text         TEXT NOT NULL,
    confidence   REAL NOT NULL,
    source_type  TEXT NOT NULL,
    last_updated REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS observations (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    variable   TEXT NOT NULL,
    value      TEXT NOT NULL,
    source     TEXT NOT NULL,
    modality   TEXT,
    confidence REAL NOT NULL,
    timestamp  REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS concepts (
    name        TEXT PRIMARY KEY,
    source_type TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS evidence_links (
    claim_id       TEXT NOT NULL REFERENCES claims(id),
    observation_id INTEGER NOT NULL REFERENCES observations(id),
    delta          REAL NOT NULL,
    reason         TEXT NOT NULL,
    timestamp      REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_links_claim ON evidence_links(claim_id, timestamp);
"""


def _check_confidence(value: float) -> None:
    """Raise ValueError unless value is in [0, 1]."""
    if not 0.0 <= value <= 1.0:
        msg = f"confidence must be in [0, 1], got {value!r}"
        raise ValueError(msg)


class Store:
    """A SQLite-backed belief store. Owns one connection.

    Pass ``":memory:"`` for an ephemeral store (tests) or a file path to
    persist. The schema is created on connect, so a fresh file works with
    no setup step.
    """

    def __init__(self, path: str | Path = ":memory:") -> None:
        """Open (or create) the store at ``path`` and ensure the schema."""
        self.conn = sqlite3.connect(str(path))
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.conn.executescript(_SCHEMA)
        self.conn.commit()

    def close(self) -> None:
        """Close the underlying connection."""
        self.conn.close()

    def __enter__(self) -> Store:
        """Enter a context that closes the store on exit."""
        return self

    def __exit__(self, *_exc: object) -> None:
        """Close the store when leaving the context."""
        self.close()

    # --- claims (the accumulated belief archive) ---

    def put_claim(
        self,
        claim_id: str,
        text: str,
        confidence: float,
        source_type: str,
        ts: float,
    ) -> None:
        """Insert a claim, or update an existing one in place.

        On a repeat id, text, confidence, and source_type are all
        overwritten and last_updated tracks the change. source_type must
        be one of SOURCE_TYPES and confidence must be in [0, 1].
        """
        if source_type not in SOURCE_TYPES:
            msg = f"source_type must be one of {SOURCE_TYPES}, got {source_type!r}"
            raise ValueError(msg)
        _check_confidence(confidence)
        self.conn.execute(
            """INSERT INTO claims (id, text, confidence, source_type, last_updated)
               VALUES (?, ?, ?, ?, ?)
               ON CONFLICT(id) DO UPDATE SET
                   text = excluded.text,
                   confidence = excluded.confidence,
                   source_type = excluded.source_type,
                   last_updated = excluded.last_updated""",
            (claim_id, text, confidence, source_type, ts),
        )
        self.conn.commit()

    def get_claim(self, claim_id: str) -> sqlite3.Row | None:
        """Return the claim row, or None if it does not exist."""
        cur = self.conn.execute("SELECT * FROM claims WHERE id = ?", (claim_id,))
        return cur.fetchone()

    def claims(self) -> list[sqlite3.Row]:
        """Return all claims, highest confidence first (ties broken by id)."""
        cur = self.conn.execute("SELECT * FROM claims ORDER BY confidence DESC, id")
        return cur.fetchall()

    # --- observations (the evidence E, append-only) ---

    def add_observation(  # noqa: PLR0913
        self,
        variable: str,
        value: str,
        source: str,
        confidence: float,
        timestamp: float,
        modality: str | None = None,
    ) -> int:
        """Append an observation. Returns its auto-assigned id.

        confidence must be in [0, 1].
        """
        _check_confidence(confidence)
        cur = self.conn.execute(
            """INSERT INTO observations
               (variable, value, source, modality, confidence, timestamp)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (variable, value, source, modality, confidence, timestamp),
        )
        self.conn.commit()
        assert cur.lastrowid is not None  # noqa: S101  # autoincrement always sets this
        return cur.lastrowid

    def observations(self) -> list[sqlite3.Row]:
        """Return all observations in insertion order."""
        cur = self.conn.execute("SELECT * FROM observations ORDER BY id")
        return cur.fetchall()

    # --- concepts (the ontology O, append-only set) ---

    def add_concept(self, name: str, source_type: str) -> None:
        """Add a concept name. First write wins.

        Re-adding an existing name keeps its original source_type: no
        error, no update. source_type must be one of SOURCE_TYPES.
        """
        if source_type not in SOURCE_TYPES:
            msg = f"source_type must be one of {SOURCE_TYPES}, got {source_type!r}"
            raise ValueError(msg)
        self.conn.execute(
            "INSERT OR IGNORE INTO concepts (name, source_type) VALUES (?, ?)",
            (name, source_type),
        )
        self.conn.commit()

    def has_concept(self, name: str) -> bool:
        """Return True if the concept is in the ontology."""
        cur = self.conn.execute("SELECT 1 FROM concepts WHERE name = ?", (name,))
        return cur.fetchone() is not None

    def concepts(self) -> list[str]:
        """Return all concept names, sorted."""
        cur = self.conn.execute("SELECT name FROM concepts ORDER BY name")
        return [row["name"] for row in cur.fetchall()]

    # --- evidence_links (what moved what; append-only; the drift timeline) ---

    def add_link(
        self,
        claim_id: str,
        observation_id: int,
        delta: float,
        reason: str,
        ts: float,
    ) -> None:
        """Record that an observation shifted a claim's confidence by delta."""
        self.conn.execute(
            """INSERT INTO evidence_links
               (claim_id, observation_id, delta, reason, timestamp)
               VALUES (?, ?, ?, ?, ?)""",
            (claim_id, observation_id, delta, reason, ts),
        )
        self.conn.commit()

    def history(self, claim_id: str) -> list[sqlite3.Row]:
        """Return a claim's evidence links in time order (the drift timeline).

        Ties on timestamp are broken by insertion order, so the timeline
        is deterministic and replayable.
        """
        cur = self.conn.execute(
            "SELECT * FROM evidence_links WHERE claim_id = ? ORDER BY timestamp, rowid",
            (claim_id,),
        )
        return cur.fetchall()


def demo() -> None:  # pragma: no cover
    """Self-check: round-trip every table through a real on-disk file."""
    import tempfile  # noqa: PLC0415
    from pathlib import Path  # noqa: PLC0415

    with tempfile.TemporaryDirectory() as d:
        path = Path(d) / "w.db"
        s = Store(path)
        s.put_claim("c1", "fiscal Q4 = $2.1B", 0.5, "inferred", ts=1.0)
        oid = s.add_observation("revenue", "$2.1B", "10-K", 1.0, 1.0, modality="tool")
        s.add_link("c1", oid, delta=0.35, reason="10-K filing", ts=1.0)
        s.put_claim("c1", "fiscal Q4 = $2.1B", 0.85, "inferred", ts=2.0)  # update
        s.add_concept("revenue", "inferred")
        s.close()

        # Reopen: data must survive close/reopen.
        s2 = Store(path)
        c1 = s2.get_claim("c1")
        assert c1 is not None, "claim persisted"  # noqa: S101
        assert c1["confidence"] == 0.85, "confidence after update"  # noqa: S101, PLR2004
        assert len(s2.observations()) == 1, "one observation persisted"  # noqa: S101
        assert s2.has_concept("revenue"), "concept persisted"  # noqa: S101
        assert [r["delta"] for r in s2.history("c1")] == [0.35], "drift timeline"  # noqa: S101
        s2.close()
    print("ok")


if __name__ == "__main__":  # pragma: no cover
    demo()
