"""Generate diff.md: the review artifact shown verbatim to every reviewer.

For each hunk: the file, a before block and an after block, each with
three lines of surrounding context. Contains no ground-truth labels.
Regenerate with: uv run python research/2026-07-15-p3-backtest/gen_diff.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from hunks import HUNK_FILES, HUNKS  # noqa: E402

REPO = Path(__file__).parents[2]
CONTEXT = 3


def block(hid: str, fkey: str, old: str, new: str) -> str:
    """Render one hunk as before/after with context lines."""
    text = (REPO / HUNK_FILES[fkey]).read_text(encoding="utf-8")
    assert text.count(old) == 1, hid
    lines = text.split("\n")
    start_char = text.index(old)
    start_line = text[:start_char].count("\n")
    old_n = old.count("\n") + 1
    pre = "\n".join(lines[max(0, start_line - CONTEXT) : start_line])
    post = "\n".join(lines[start_line + old_n : start_line + old_n + CONTEXT])
    return (
        f"### {hid} — `{HUNK_FILES[fkey]}`\n\n"
        f"Before:\n\n```python\n{pre}\n{old}\n{post}\n```\n\n"
        f"After:\n\n```python\n{pre}\n{new}\n{post}\n```\n"
    )


def main() -> None:
    parts = [
        "# Changes under review\n",
        "One proposed cleanup PR, fourteen independent changes (C01-C14).\n",
    ]
    parts.extend(block(hid, *h) for hid, h in HUNKS.items())
    out = REPO / "research" / "2026-07-15-p3-backtest" / "diff.md"
    out.write_text("\n".join(parts), encoding="utf-8", newline="\n")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
