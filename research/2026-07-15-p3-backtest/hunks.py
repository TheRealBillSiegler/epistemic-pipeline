"""The 14 changes under review, as (file, old, new) string replacements.

This file is public and committed BEFORE the review fan-out. It does not
say which changes are seeded bugs. The ground-truth labels live in a
separate truth.json whose salted SHA-256 is committed alongside this
file (truth_commitment.txt) and revealed only after all reviews are in.

ponytail: plain string replacement, not AST rewriting. Each `old` is
asserted unique in its file, which is all the precision this needs.
"""

from __future__ import annotations

HUNK_FILES = {
    "provenance": "src/epistemic_pipeline/worldview_app/provenance.py",
    "store": "src/epistemic_pipeline/worldview_app/store.py",
}

# id -> (file_key, old, new). Presented to reviewers in this order.
HUNKS: dict[str, tuple[str, str, str]] = {
    "C01": (
        "provenance",
        'path); it never guesses provenance from a document\'s contents.\n"""',
        'path); it never guesses provenance from a document\'s contents.\n'
        "\n"
        "Canonical ids are stable across releases: changing this normalization\n"
        're-keys fusion roots, so replays of old evidence logs would regroup.\n"""',
    ),
    "C02": (
        "provenance",
        '     "fbclid", "gclid", "ref_src"}',
        '     "fbclid", "gclid", "ref", "ref_src"}',
    ),
    "C03": (
        "provenance",
        '        path = parts.path.rstrip("/") or "/"',
        '        path = parts.path.rstrip("/")',
    ),
    "C04": (
        "provenance",
        '        return "doi:" + o[4:].strip().lower()',
        '        return "doi:" + o.removeprefix("doi:").strip().lower()',
    ),
    "C05": (
        "provenance",
        '        arxiv_id = re.sub(r"v\\d+$", "", o[6:].strip().lower())',
        '        raw_id = o[6:].strip().lower()\n'
        '        arxiv_id = re.sub(r"v\\d+$", "", raw_id)',
    ),
    "C06": (
        "store",
        "# source_type values for claims and concepts.\n"
        'SOURCE_TYPES = ("inferred", "user", "derived")',
        "# source_type values for claims and concepts. A tuple, not a set: the\n"
        "# order is stable so error messages read the same across runs.\n"
        'SOURCE_TYPES = ("inferred", "user", "derived")',
    ),
    "C07": (
        "store",
        "CREATE INDEX IF NOT EXISTS idx_links_claim ON evidence_links(claim_id, timestamp);\n"
        '"""',
        "CREATE INDEX IF NOT EXISTS idx_links_claim ON evidence_links(claim_id, timestamp);\n"
        "CREATE INDEX IF NOT EXISTS idx_obs_root ON observations(root_id);\n"
        '"""',
    ),
    "C08": (
        "store",
        "    if not 0.0 <= value <= 1.0:",
        "    if not 0.0 < value <= 1.0:",
    ),
    "C09": (
        "store",
        "               ON CONFLICT(id) DO UPDATE SET\n"
        "                   text = excluded.text,\n"
        "                   confidence = excluded.confidence,\n"
        "                   source_type = excluded.source_type,\n"
        '                   last_updated = excluded.last_updated""",',
        "               ON CONFLICT(id) DO UPDATE SET\n"
        "                   text = excluded.text,\n"
        "                   confidence = excluded.confidence,\n"
        '                   last_updated = excluded.last_updated""",',
    ),
    "C10": (
        "store",
        '        cur = self.conn.execute("SELECT * FROM claims WHERE id = ?", (claim_id,))\n'
        "        return cur.fetchone()",
        "        return self.conn.execute(\n"
        '            "SELECT * FROM claims WHERE id = ?", (claim_id,)\n'
        "        ).fetchone()",
    ),
    "C11": (
        "store",
        '        cur = self.conn.execute("SELECT * FROM claims ORDER BY confidence DESC, id")\n'
        "        return cur.fetchall()",
        '        return list(self.conn.execute("SELECT * FROM claims ORDER BY confidence DESC, id"))',
    ),
    "C12": (
        "store",
        "            (variable, value, source, modality, confidence, timestamp, root_id),",
        "            (variable, value, source, confidence, modality, timestamp, root_id),",
    ),
    "C13": (
        "store",
        '        cur = self.conn.execute("SELECT 1 FROM concepts WHERE name = ?", (name,))\n'
        "        return cur.fetchone() is not None",
        "        cur = self.conn.execute(\n"
        '            "SELECT count(*) FROM concepts WHERE name = ?", (name,)\n'
        "        )\n"
        "        row = cur.fetchone()\n"
        "        return row is not None and bool(row[0])",
    ),
    "C14": (
        "store",
        "        cur = self.conn.execute(\n"
        '            "SELECT * FROM evidence_links WHERE claim_id = ? ORDER BY timestamp, rowid",\n'
        "            (claim_id,),\n"
        "        )\n"
        "        return cur.fetchall()",
        "        cur = self.conn.execute(\n"
        '            """SELECT * FROM evidence_links\n'
        "               WHERE claim_id = ?\n"
        '               ORDER BY timestamp, rowid""",\n'
        "            (claim_id,),\n"
        "        )\n"
        "        return cur.fetchall()",
    ),
}
