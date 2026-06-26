"""Mechanical quote/number verification against paper BODIES. No LLM in the loop.

Fetches each source, strips tags, and string-matches the exact quotes and numbers
our docs attach to it. This eliminates the 'verified against the summary, not the
paper' weak link for everything that IS a verbatim string. Interpretive claims
(inferences, framings) are NOT string-checkable and are listed as such — honest
about the boundary.

Run: uv run python quote_check.py
"""

import html as _html
import re
import sys
import time
import urllib.request

sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # Windows console is cp1252

UA = {"User-Agent": "epistemic-pipeline-citation-check/1.0 (mailto:billsiegler@outlook.com)"}


def _raw(url: str) -> str:
    req = urllib.request.Request(url, headers=UA)
    return urllib.request.urlopen(req, timeout=60).read().decode("utf-8", "ignore")


def _text(url: str) -> str:
    h = _raw(url)
    h = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", h, flags=re.S | re.I)
    h = re.sub(r"<[^>]+>", " ", h)
    h = _html.unescape(h)
    return re.sub(r"\s+", " ", h)


def fetch(urls: list[str]) -> tuple[str | None, str]:
    """Try urls in order; return (winning_url, text) or (None, error)."""
    last = "no urls"
    for u in urls:
        try:
            t = _text(u)
            if len(t) > 500:  # a real body, not an error page
                return u, t
            last = f"too short ({len(t)} chars)"
        except Exception as e:  # noqa: BLE001
            last = f"{type(e).__name__}: {e}"
        time.sleep(0.5)
    return None, f"FETCH FAILED ({last})"


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip().lower()


def check(text: str, needle: str) -> tuple[bool, str]:
    n, t = _norm(needle), _norm(text)
    i = t.find(n)
    if i < 0:
        return False, ""
    s, e = max(0, i - 80), min(len(t), i + len(n) + 80)
    return True, "…" + t[s:e] + "…"


def arxiv(idv: str) -> list[str]:
    return [
        f"https://arxiv.org/html/{idv}v1",
        f"https://arxiv.org/html/{idv}v2",
        f"https://arxiv.org/html/{idv}v3",
        f"https://ar5iv.labs.arxiv.org/html/{idv}",
        f"https://ar5iv.org/abs/{idv}",
    ]


# (name, [urls], [(label, needle, kind)])  kind: q=verbatim quote, n=number/phrase
TARGETS = [
    # ---- weak-link papers (were compared file-vs-file) ----
    ("conformal 2405.01563 [re-confirm]", arxiv("2405.01563"), [
        ("'completely sure about an incorrect answer' quote",
         "cannot detect situations where the llm is completely sure about an incorrect answer", "q"),
    ]),
    ("epistemic-bias 2512.00804 [partial]", arxiv("2512.00804"), [
        ("both-properties 74.7", "74.7", "n"),
        ("both-properties 78.0", "78.0", "n"),
        ("headline '86'", "86", "n"),
        ("'perspective bias' phrase", "perspective bias", "n"),
    ]),
    ("passiveqa 2604.04565 [partial]", arxiv("2604.04565"), [
        ("abstain recall 58.1", "58.1", "n"),
        ("baseline 13.3", "13.3", "n"),
        ("'abstain' phrase", "abstain", "n"),
    ]),
    ("infogatherer 2603.05909 [partial]", arxiv("2603.05909"), [
        ("'Deng entropy'", "deng entropy", "q"),
        ("'ignorance'", "ignorance", "n"),
        ("'nonspecificity'", "nonspecificity", "n"),
        ("'abstain' rule", "abstain", "n"),
    ]),
    ("ren 2604.17293", arxiv("2604.17293"), [
        ("Qwen3-8B '4.0% mu-f1' (tight needle)", "4.0% mu-f1", "q"),
        ("AVG-F1 36.9 (table row)", "36.9", "n"),
        ("'model uncertainty'", "model uncertainty", "n"),
        ("'data uncertainty'", "data uncertainty", "n"),
    ]),
    ("tomani 2404.10960", arxiv("2404.10960"), [
        ("safe-rate 99.4", "99.4", "n"),
        ("base 92.5", "92.5", "n"),
        ("'RLHF' condition", "rlhf", "n"),
    ]),
    # cited only as "a benchmark" — no number is load-bearing in our docs, so just confirm topic
    ("abstentionbench 2506.09038", arxiv("2506.09038"), [
        ("'unanswerable questions' (topic)", "unanswerable questions", "n"),
        ("'abstention'", "abstention", "n"),
    ]),
    ("hills 2507.10124", arxiv("2507.10124"), [
        ("title phrase 'could you be wrong'", "could you be wrong", "q"),
    ]),
    ("reddebate 2506.11083", arxiv("2506.11083"), [
        ("PReD start 38.7", "38.7", "n"),
        ("'unsafe'", "unsafe", "n"),
    ]),
    ("sl-fusion 1805.01388 [medium]", arxiv("1805.01388"), [
        ("'weighted belief fusion'", "weighted belief fusion", "q"),
        ("'cumulative belief fusion'", "cumulative belief fusion", "q"),
        ("'averaging belief fusion'", "averaging belief fusion", "q"),
    ]),
    ("gilardi 2023 [via PMC mirror — PNAS blocks raw fetch]",
     ["https://pmc.ncbi.nlm.nih.gov/articles/PMC10372638/"], [
        ("'25 percentage points' (accuracy gap)", "25 percentage points", "q"),
        ("'97% for chatgpt with temperature = 0.2' (intercoder agreement)",
         "97% for chatgpt with temperature = 0.2", "q"),
        ("'intercoder agreement' (distinct from accuracy)", "intercoder agreement", "n"),
    ]),
    # ---- re-verify the 4 doc fixes just applied ----
    ("EBSL 1402.3319 [fix1: ⊙ quote]", arxiv("1402.3319"), [
        ("'We postpone the precise details'", "we postpone the precise details", "q"),
        ("'We are not claiming that'", "we are not claiming that", "q"),
        ("odot symbol ⊙ present", "⊙", "n"),
        ("otimes-box symbol ⊠ present", "⊠", "n"),
    ]),
    ("GRADE PMC2335261 [fix2: arbitrariness quote]",
     ["https://pmc.ncbi.nlm.nih.gov/articles/PMC2335261/"], [
        ("'some degree of arbitrariness'", "involves some degree of arbitrariness", "q"),
        ("'outweigh these limitations'",
         "advantages of simplicity, transparency, and vividness outweigh these limitations", "q"),
    ]),
    ("Bucher 2406.08660 [fix3: F1 table]", arxiv("2406.08660"), [
        ("DeBERTa", "deberta", "n"),
        ("0.94", "0.94", "n"), ("0.93", "0.93", "n"), ("0.57", "0.57", "n"),
        ("0.48", "0.48", "n"), ("0.47", "0.47", "n"), ("0.51", "0.51", "n"),
    ]),
    ("positional-bias 2024.acl-long.511 [abstract]",
     ["https://aclanthology.org/2024.acl-long.511/"], [
        ("'66 over 80' quote", "66 over 80", "q"),
    ]),
    ("atanasova 2022.tacl-1.43 [abstract]",
     ["https://aclanthology.org/2022.tacl-1.43/"], [
        ("21% accuracy", "21%", "n"),
        ("63% accuracy", "63%", "n"),
    ]),
]

print("=" * 100)
print("MECHANICAL QUOTE / NUMBER CHECK against paper bodies — no model")
print("=" * 100)
for name, urls, needles in TARGETS:
    url, text = fetch(urls)
    print(f"\n[{name}]")
    if url is None:
        print(f"   *** {text} ***  — cannot machine-verify; needs human read")
        continue
    print(f"   source: {url}  ({len(text):,} chars)")
    for label, needle, kind in needles:
        ok, ctx = check(text, needle)
        mark = "FOUND" if ok else "*** NOT FOUND ***"
        print(f"   [{mark:17s}] {label}")
        if ok:
            print(f"        {ctx}")
    time.sleep(1.0)

print("\n" + "=" * 100)
print("Boundary: this checks verbatim strings only. NOT machine-checkable (need a read):")
print("  - PassiveQA 'absence harder than conflict' (our synthesis; paper has no conflict task)")
print("  - InfoGatherer 'abstain on a confidence threshold within a turn budget' (inferred mechanism)")
print("  - conformal 'fails under distribution shift' (inference from the exchangeability assumption)")
print("  - Heuer process-vs-verdict quote (from the 1999 BOOK, not the handout; handout PDF body unreadable)")
print("=" * 100)
