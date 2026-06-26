"""Mechanical quote check for PDF-only sources. Uses a real PDF parser (pypdf),
which decodes FlateDecode streams a naive tag-strip cannot. Companion to
quote_check.py (which handles HTML/text). No LLM in the loop.

Run: uv run --with pypdf python tools/pdf_quote_check.py

Current target: the Heuer ACH process-vs-verdict quote. Our docs use the
*handout's* wording; the 1999 *book* states the same point in different words —
this script confirms both, so the attribution stays honest.
"""

import io
import re
import sys
import time
import urllib.request

from pypdf import PdfReader

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
UA = {"User-Agent": "epistemic-pipeline-citation-check/1.0 (mailto:billsiegler@outlook.com)"}


def pdf_text(url: str) -> str:
    data = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=90).read()
    r = PdfReader(io.BytesIO(data))
    return re.sub(r"\s+", " ", " ".join(p.extract_text() or "" for p in r.pages))


def fetch(urls: list[str]) -> tuple[str | None, str]:
    for u in urls:
        try:
            t = pdf_text(u)
            if len(t) > 1000:
                return u, t
            print(f"   (too short from {u}: {len(t)})")
        except Exception as e:  # noqa: BLE001
            print(f"   (failed {u}: {type(e).__name__}: {e})")
        time.sleep(0.5)
    return None, ""


def show(text: str, needle: str, window: int = 120) -> bool:
    t, n = text.lower(), needle.lower()
    i = t.find(n)
    if i < 0:
        print(f"   [*** NOT FOUND ***] {needle!r}")
        return False
    print(f"   [FOUND] {needle!r}")
    print(f"        …{text[max(0, i - window):i + len(needle) + window]}…")
    return True


# (name, [urls], [needles], note)
TARGETS = [
    ("Heuer HANDOUT — our docs' verbatim wording lives here",
     ["https://www.pherson.org/wp-content/uploads/2013/06/Improving-Intelligence-Analysis-with-ACH.pdf"],
     ["obviously no guarantee", "fallible human judgment", "ach does, however, guarantee an appropriate process",
      "diagnostic", "disconfirming"]),
    ("Heuer BOOK (1999) — same point, DIFFERENT words (mirror; CIA URL is dead)",
     ["https://www.ialeia.org/docs/Psychology_of_Intelligence_Analysis.pdf"],
     ["no guarantee that ach", "fallible intuitive judgment",
      "analysis of competing hypotheses does, however, guarantee an appropriate process"]),
]

print("=" * 92)
print("MECHANICAL PDF QUOTE CHECK (pypdf decodes FlateDecode) — no model")
print("=" * 92)
for name, urls, needles in TARGETS:
    url, text = fetch(urls)
    print(f"\n[{name}]")
    if url is None:
        print("   *** could not fetch any source — needs a human read ***")
        continue
    print(f"   source: {url}  ({len(text):,} chars)")
    for nd in needles:
        show(text, nd)
    time.sleep(1.0)
