# Changes under review

One proposed cleanup PR, fourteen independent changes (C01-C14).

### C01 — `src/epistemic_pipeline/worldview_app/provenance.py`

Before:

```python
that trace to the same root must produce the same id, so belief fusion can
group them and not double-count one source. This is deterministic by
design: it normalizes ids the caller supplies (a URL, a DOI, a vault
path); it never guesses provenance from a document's contents.
"""

from __future__ import annotations

```

After:

```python
that trace to the same root must produce the same id, so belief fusion can
group them and not double-count one source. This is deterministic by
design: it normalizes ids the caller supplies (a URL, a DOI, a vault
path); it never guesses provenance from a document's contents.

Canonical ids are stable across releases: changing this normalization
re-keys fusion roots, so replays of old evidence logs would regroup.
"""

from __future__ import annotations

```

### C02 — `src/epistemic_pipeline/worldview_app/provenance.py`

Before:

```python
# distinct sources. "ref_src" (Twitter) is unambiguous tracking, so it stays.
_TRACKING = frozenset(
    {"utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
     "fbclid", "gclid", "ref_src"}
)
# A bare DOI, e.g. "10.1145/2700475".
_DOI = re.compile(r"^10\.\d{4,9}/\S+$")
```

After:

```python
# distinct sources. "ref_src" (Twitter) is unambiguous tracking, so it stays.
_TRACKING = frozenset(
    {"utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
     "fbclid", "gclid", "ref", "ref_src"}
)
# A bare DOI, e.g. "10.1145/2700475".
_DOI = re.compile(r"^10\.\d{4,9}/\S+$")
```

### C03 — `src/epistemic_pipeline/worldview_app/provenance.py`

Before:

```python
        # page; if they rarely do not, merging under-counts settledness --
        # the safe direction (spec section 3: fail toward not inflating).
        host = parts.netloc.lower().removeprefix("www.")
        path = parts.path.rstrip("/") or "/"
        kept = sorted((k, v) for k, v in parse_qsl(parts.query) if k.lower() not in _TRACKING)
        return urlunsplit(("https", host, path, urlencode(kept), ""))
    if low.startswith("doi:"):
```

After:

```python
        # page; if they rarely do not, merging under-counts settledness --
        # the safe direction (spec section 3: fail toward not inflating).
        host = parts.netloc.lower().removeprefix("www.")
        path = parts.path.rstrip("/")
        kept = sorted((k, v) for k, v in parse_qsl(parts.query) if k.lower() not in _TRACKING)
        return urlunsplit(("https", host, path, urlencode(kept), ""))
    if low.startswith("doi:"):
```

### C04 — `src/epistemic_pipeline/worldview_app/provenance.py`

Before:

```python
        kept = sorted((k, v) for k, v in parse_qsl(parts.query) if k.lower() not in _TRACKING)
        return urlunsplit(("https", host, path, urlencode(kept), ""))
    if low.startswith("doi:"):
        return "doi:" + o[4:].strip().lower()
    if low.startswith("arxiv:"):
        # A version suffix (v1, v2, ...) is a content version, not a new
        # identity, so two versions of one preprint share a root.
```

After:

```python
        kept = sorted((k, v) for k, v in parse_qsl(parts.query) if k.lower() not in _TRACKING)
        return urlunsplit(("https", host, path, urlencode(kept), ""))
    if low.startswith("doi:"):
        return "doi:" + o.removeprefix("doi:").strip().lower()
    if low.startswith("arxiv:"):
        # A version suffix (v1, v2, ...) is a content version, not a new
        # identity, so two versions of one preprint share a root.
```

### C05 — `src/epistemic_pipeline/worldview_app/provenance.py`

Before:

```python
    if low.startswith("arxiv:"):
        # A version suffix (v1, v2, ...) is a content version, not a new
        # identity, so two versions of one preprint share a root.
        arxiv_id = re.sub(r"v\d+$", "", o[6:].strip().lower())
        return "arxiv:" + arxiv_id
    if _DOI.match(low):
        return "doi:" + low
```

After:

```python
    if low.startswith("arxiv:"):
        # A version suffix (v1, v2, ...) is a content version, not a new
        # identity, so two versions of one preprint share a root.
        raw_id = o[6:].strip().lower()
        arxiv_id = re.sub(r"v\d+$", "", raw_id)
        return "arxiv:" + arxiv_id
    if _DOI.match(low):
        return "doi:" + low
```

### C06 — `src/epistemic_pipeline/worldview_app/store.py`

Before:

```python
if TYPE_CHECKING:
    from pathlib import Path

# source_type values for claims and concepts.
SOURCE_TYPES = ("inferred", "user", "derived")

_SCHEMA = """
CREATE TABLE IF NOT EXISTS claims (
```

After:

```python
if TYPE_CHECKING:
    from pathlib import Path

# source_type values for claims and concepts. A tuple, not a set: the
# order is stable so error messages read the same across runs.
SOURCE_TYPES = ("inferred", "user", "derived")

_SCHEMA = """
CREATE TABLE IF NOT EXISTS claims (
```

### C07 — `src/epistemic_pipeline/worldview_app/store.py`

Before:

```python
    reason         TEXT NOT NULL,
    timestamp      REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_links_claim ON evidence_links(claim_id, timestamp);
"""


def _check_confidence(value: float) -> None:
```

After:

```python
    reason         TEXT NOT NULL,
    timestamp      REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_links_claim ON evidence_links(claim_id, timestamp);
CREATE INDEX IF NOT EXISTS idx_obs_root ON observations(root_id);
"""


def _check_confidence(value: float) -> None:
```

### C08 — `src/epistemic_pipeline/worldview_app/store.py`

Before:

```python

def _check_confidence(value: float) -> None:
    """Raise ValueError unless value is in [0, 1]."""
    if not 0.0 <= value <= 1.0:
        msg = f"confidence must be in [0, 1], got {value!r}"
        raise ValueError(msg)

```

After:

```python

def _check_confidence(value: float) -> None:
    """Raise ValueError unless value is in [0, 1]."""
    if not 0.0 < value <= 1.0:
        msg = f"confidence must be in [0, 1], got {value!r}"
        raise ValueError(msg)

```

### C09 — `src/epistemic_pipeline/worldview_app/store.py`

Before:

```python
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
```

After:

```python
        self.conn.execute(
            """INSERT INTO claims (id, text, confidence, source_type, last_updated)
               VALUES (?, ?, ?, ?, ?)
               ON CONFLICT(id) DO UPDATE SET
                   text = excluded.text,
                   confidence = excluded.confidence,
                   last_updated = excluded.last_updated""",
            (claim_id, text, confidence, source_type, ts),
        )
        self.conn.commit()
```

### C10 — `src/epistemic_pipeline/worldview_app/store.py`

Before:

```python

    def get_claim(self, claim_id: str) -> sqlite3.Row | None:
        """Return the claim row, or None if it does not exist."""
        cur = self.conn.execute("SELECT * FROM claims WHERE id = ?", (claim_id,))
        return cur.fetchone()

    def claims(self) -> list[sqlite3.Row]:
        """Return all claims, highest confidence first (ties broken by id)."""
```

After:

```python

    def get_claim(self, claim_id: str) -> sqlite3.Row | None:
        """Return the claim row, or None if it does not exist."""
        return self.conn.execute(
            "SELECT * FROM claims WHERE id = ?", (claim_id,)
        ).fetchone()

    def claims(self) -> list[sqlite3.Row]:
        """Return all claims, highest confidence first (ties broken by id)."""
```

### C11 — `src/epistemic_pipeline/worldview_app/store.py`

Before:

```python

    def claims(self) -> list[sqlite3.Row]:
        """Return all claims, highest confidence first (ties broken by id)."""
        cur = self.conn.execute("SELECT * FROM claims ORDER BY confidence DESC, id")
        return cur.fetchall()

    # --- observations (the evidence E, append-only) ---

```

After:

```python

    def claims(self) -> list[sqlite3.Row]:
        """Return all claims, highest confidence first (ties broken by id)."""
        return list(self.conn.execute("SELECT * FROM claims ORDER BY confidence DESC, id"))

    # --- observations (the evidence E, append-only) ---

```

### C12 — `src/epistemic_pipeline/worldview_app/store.py`

Before:

```python
            """INSERT INTO observations
               (variable, value, source, modality, confidence, timestamp, root_id)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (variable, value, source, modality, confidence, timestamp, root_id),
        )
        self.conn.commit()
        assert cur.lastrowid is not None  # noqa: S101  # autoincrement always sets this
```

After:

```python
            """INSERT INTO observations
               (variable, value, source, modality, confidence, timestamp, root_id)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (variable, value, source, confidence, modality, timestamp, root_id),
        )
        self.conn.commit()
        assert cur.lastrowid is not None  # noqa: S101  # autoincrement always sets this
```

### C13 — `src/epistemic_pipeline/worldview_app/store.py`

Before:

```python

    def has_concept(self, name: str) -> bool:
        """Return True if the concept is in the ontology."""
        cur = self.conn.execute("SELECT 1 FROM concepts WHERE name = ?", (name,))
        return cur.fetchone() is not None

    def concepts(self) -> list[str]:
        """Return all concept names, sorted."""
```

After:

```python

    def has_concept(self, name: str) -> bool:
        """Return True if the concept is in the ontology."""
        cur = self.conn.execute(
            "SELECT count(*) FROM concepts WHERE name = ?", (name,)
        )
        row = cur.fetchone()
        return row is not None and bool(row[0])

    def concepts(self) -> list[str]:
        """Return all concept names, sorted."""
```

### C14 — `src/epistemic_pipeline/worldview_app/store.py`

Before:

```python
        Ties on timestamp are broken by insertion order, so the timeline
        is deterministic and replayable.
        """
        cur = self.conn.execute(
            "SELECT * FROM evidence_links WHERE claim_id = ? ORDER BY timestamp, rowid",
            (claim_id,),
        )
        return cur.fetchall()


def demo() -> None:  # pragma: no cover
```

After:

```python
        Ties on timestamp are broken by insertion order, so the timeline
        is deterministic and replayable.
        """
        cur = self.conn.execute(
            """SELECT * FROM evidence_links
               WHERE claim_id = ?
               ORDER BY timestamp, rowid""",
            (claim_id,),
        )
        return cur.fetchall()


def demo() -> None:  # pragma: no cover
```
