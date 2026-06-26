"""Mechanical citation + formula check. No LLM. Metadata APIs + arithmetic only."""

import json
import re
import time
import urllib.parse
import urllib.request

UA = {"User-Agent": "epistemic-pipeline-citation-check/1.0 (mailto:billsiegler@outlook.com)"}


def _get(url):
    req = urllib.request.Request(url, headers=UA)
    return urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "ignore")


def _norm(s):
    return re.sub(r"\s+", " ", re.sub(r"&amp;", "&", s or "")).strip()


def arxiv(idv):
    d = _get(f"http://export.arxiv.org/api/query?id_list={idv}")
    titles = re.findall(r"<title>(.*?)</title>", d, re.S)
    title = _norm(titles[1]) if len(titles) > 1 else ""
    authors = [_norm(a) for a in re.findall(r"<author>\s*<name>(.*?)</name>", d, re.S)]
    return title, authors


def doi(idv):
    d = _get(f"https://api.crossref.org/works/{urllib.parse.quote(idv)}")
    m = json.loads(d)["message"]
    title = _norm((m.get("title") or [""])[0])
    authors = [_norm(a.get("family", "")) for a in m.get("author", [])]
    return title, authors


def pmc(idv):
    d = _get(f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pmc&id={idv}&retmode=json")
    rec = json.loads(d)["result"][idv]
    title = _norm(rec.get("title", ""))
    authors = [_norm(a.get("name", "")) for a in rec.get("authors", [])]
    return title, authors


# (kind, id, expected title keyword or None, expected author surname or None, what-we-cited-it-for)
CITES = [
    ("arxiv", "1402.3319", "evidence-based subjective logic", "korić", "EBSL g-free"),
    ("arxiv", "1805.01388", "fusion", "Heijden", "corrected SL fusion (CBF/ABF)"),
    ("arxiv", "2405.01563", "conformal abstention", "Yadkori", "conformal abstention"),
    ("arxiv", "2406.02543", "believe", None, "the *other* paper (NeurIPS24) — distinct?"),
    ("arxiv", "2406.08660", None, None, "LLM stance weak vs fine-tuned"),
    ("arxiv", "2509.16534", None, None, "InteGround / rationalize gaps"),
    ("arxiv", "2604.04565", None, None, "PassiveQA (2026 preprint)"),
    ("arxiv", "2603.05909", None, None, "InfoGatherer (2026 preprint)"),
    ("arxiv", "2604.17293", None, None, "Beyond I Don't Know (2026 preprint)"),
    ("arxiv", "2512.00804", None, None, "Epistemic Bias Injection (2025 preprint)"),
    ("arxiv", "2506.11083", None, None, "RedDebate"),
    ("arxiv", "2507.10124", "wrong", "Hills", "could you be wrong"),
    ("arxiv", "2506.09038", "abstention", None, "AbstentionBench"),
    ("arxiv", "1212.0960", None, None, "we FLAGGED this as mis-cited for calibration"),
    ("doi", "10.1073/pnas.2305016120", "annotation", "Gilardi", "ChatGPT > crowd annotation"),
    ("doi", "10.1007/s11229-020-02595-2", None, None, "Synthese source-reliability (author dispute: Merdes vs Henderson?)"),
    ("doi", "10.1145/2700475", None, None, "Beat the Machine / unknown-unknowns"),
    ("doi", "10.1007/s10726-016-9494-6", None, None, "cited around ROC weights"),
    ("pmc", "2335261", None, "Guyatt", "GRADE"),
    ("pmc", "2700132", None, None, "hierarchies question-type specific (Merlin)"),
]

print("=" * 100)
print("CITATION RESOLUTION  (real metadata from arXiv / Crossref / NCBI APIs — no model)")
print("=" * 100)
for kind, idv, tkw, akw, why in CITES:
    try:
        title, authors = {"arxiv": arxiv, "doi": doi, "pmc": pmc}[kind](idv)
        ok = bool(title)
        tmatch = "n/a" if not tkw else ("YES" if tkw.lower() in title.lower() else "*** NO ***")
        astr = ", ".join(authors[:4]) + (" …" if len(authors) > 4 else "")
        amatch = "n/a" if not akw else ("YES" if any(akw.lower() in a.lower() for a in authors) else "*** NO ***")
        print(f"\n[{kind} {idv}]  resolves: {'YES' if ok else '*** NO ***'}")
        print(f"   cited for : {why}")
        print(f"   REAL title: {title!r}")
        print(f"   authors   : {astr}")
        print(f"   title kw={tkw!r} -> {tmatch}    author kw={akw!r} -> {amatch}")
    except Exception as e:  # noqa: BLE001
        print(f"\n[{kind} {idv}]  *** FETCH FAILED: {type(e).__name__}: {e} ***  (cited for: {why})")
    time.sleep(0.4)

print("\n" + "=" * 100)
print("FORMULA RECOMPUTATION  (pure arithmetic — assert the doc's numbers)")
print("=" * 100)
W = 2.0


def op(r, s, a=0.5):
    t = r + s + W
    b, d, u = r / t, s / t, W / t
    return b, d, u, b + a * u


checks = []
for p, expP in [(0.6, 0.55), (1.0, 0.75), (0.0, 0.25), (0.5, 0.50)]:
    r, s = 2 * p, 2 * (1 - p)
    _, _, u, P = op(r, s)
    checks.append((f"p={p}->Opinion({r},{s})  P", P, expP))
    if p == 0.5:
        checks.append(("p=0.5 u", u, 0.50))
_, _, uv, Pv = op(0, 0)
checks.append(("vacuous u", uv, 1.0))
checks.append(("vacuous P", Pv, 0.5))
# fusion = add counts: Opinion(2,0) (+) Opinion(1,1) = Opinion(3,1)
_, _, _, Pf = op(3, 1)
checks.append(("fuse (2,0)+(1,1)=(3,1) P = 2/3", Pf, 2 / 3))

# ROC weights, K=4: w_r = (1/K) * sum_{h=r..K} 1/h
K = 4
roc = [(1 / K) * sum(1 / h for h in range(r, K + 1)) for r in range(1, K + 1)]
checks.append(("ROC K=4 w1", roc[0], 0.5208333))
checks.append(("ROC K=4 sum", sum(roc), 1.0))

allpass = True
for name, got, exp in checks:
    ok = abs(got - exp) < 1e-3
    allpass &= ok
    print(f"   [{'PASS' if ok else '*** FAIL ***'}] {name:38s} got={got:.4f}  expected={exp:.4f}")
print(f"\n   ROC K=4 weights = {[round(x, 4) for x in roc]}")
print(f"\n   FORMULAS: {'ALL PASS' if allpass else '*** SOME FAILED ***'}")
