"""Fold the P3 backtest evidence both ways and apply the pre-registered rule.

Inputs (this directory): agents.json (11 blind reviews), channels.json
(per-hunk mechanical evidence), truth.json (revealed labels; byte-hash
must match truth_commitment.txt). Output: a markdown report on stdout.

Run: uv run python -X utf8 research/2026-07-15-p3-backtest/fold.py
"""

from __future__ import annotations

import hashlib
import itertools
import json
import sys
from pathlib import Path

from epistemic_pipeline.encodings.worldview import WorldviewOntology, aggregate_beliefs

HERE = Path(__file__).parent
IDS = [f"C{i:02d}" for i in range(1, 15)]

PYTEST_FAIL, PYTEST_PASS, PYRIGHT_FIRE = 0.95, 0.20, 0.90


def load() -> tuple[list[dict[str, object]], dict[str, dict[str, object]], dict[str, str]]:
    """Read the three inputs and check the truth commitment."""
    committed = (HERE / "truth_commitment.txt").read_text(encoding="utf-8").strip()
    actual = hashlib.sha256((HERE / "truth.json").read_bytes()).hexdigest()
    if committed != actual:
        msg = f"truth.json does not match pre-registered commitment: {actual} != {committed}"
        raise SystemExit(msg)
    agents = json.loads((HERE / "agents.json").read_text(encoding="utf-8"))["reviews"]
    channels = json.loads((HERE / "channels.json").read_text(encoding="utf-8"))
    truth = json.loads((HERE / "truth.json").read_text(encoding="utf-8"))["labels"]
    return agents, channels, truth


def evidence(agents: list[dict[str, object]], channels: dict[str, dict[str, object]],
             *, root_keyed: bool) -> list[tuple[str, dict[str, float]]]:
    """Build (root, vector) pairs under one of the two root maps."""
    pairs: list[tuple[str, dict[str, float]]] = []
    for a in agents:
        root = f"agent:{a['model']}" if root_keyed else f"agent:{a['model']}/{a['reviewer']}"
        pairs.append((root, {k: float(v) for k, v in a["ratings"].items()}))  # type: ignore[union-attr]
    pytest_vec = {h: (PYTEST_PASS if ch["pytest_pass"] else PYTEST_FAIL) for h, ch in channels.items()}
    pairs.append(("check:pytest", pytest_vec))
    pyright_vec = {h: PYRIGHT_FIRE for h, ch in channels.items() if ch["pyright_errors"]}
    if pyright_vec:
        pairs.append(("check:pyright", pyright_vec))
    return pairs


def fold(pairs: list[tuple[str, dict[str, float]]]) -> dict[str, float]:
    """Projected P(bug) per hunk from the production two-tier fuse."""
    beliefs = aggregate_beliefs(pairs, WorldviewOntology(concepts=frozenset(IDS)))
    return {h: beliefs.opinions[h].projected for h in IDS}


def auroc(scores: dict[str, float], truth: dict[str, str]) -> float:
    """Rank-based AUROC with average ranks on ties."""
    ordered = sorted(IDS, key=lambda h: scores[h])
    ranks: dict[str, float] = {}
    i = 0
    while i < len(ordered):
        j = i
        while j + 1 < len(ordered) and scores[ordered[j + 1]] == scores[ordered[i]]:
            j += 1
        for k in range(i, j + 1):
            ranks[ordered[k]] = (i + j) / 2 + 1
        i = j + 1
    pos = [h for h in IDS if truth[h] == "bug"]
    neg = [h for h in IDS if truth[h] == "safe"]
    u = sum(ranks[h] for h in pos) - len(pos) * (len(pos) + 1) / 2
    return u / (len(pos) * len(neg))


def main() -> None:
    agents, channels, truth = load()
    pa = fold(evidence(agents, channels, root_keyed=False))
    pb = fold(evidence(agents, channels, root_keyed=True))
    bugs = [h for h in IDS if truth[h] == "bug"]
    safes = [h for h in IDS if truth[h] == "safe"]

    # Decision-relevant movement: strict order inversions on bug/safe pairs.
    inversions = [
        (b, s) for b, s in itertools.product(bugs, safes)
        if (pa[b] - pa[s]) * (pb[b] - pb[s]) < 0
    ]
    auroc_a, auroc_b = auroc(pa, truth), auroc(pb, truth)
    top_a = sorted(IDS, key=lambda h: -pa[h])[: len(bugs)]
    top_b = sorted(IDS, key=lambda h: -pb[h])[: len(bugs)]
    fp_a, fp_b = [h for h in top_a if truth[h] == "safe"], [h for h in top_b if truth[h] == "safe"]

    if inversions and auroc_b >= auroc_a:
        verdict = "STRONG PASS" if (auroc_b > auroc_a or len(fp_b) < len(fp_a)) else "PASS"
    else:
        verdict = "FAIL"

    # Correlated-rater premise: mean pairwise Pearson within vs across models.
    def pearson(x: list[float], y: list[float]) -> float:
        n = len(x)
        mx, my = sum(x) / n, sum(y) / n
        cov = sum((a - mx) * (b - my) for a, b in zip(x, y, strict=True))
        vx = sum((a - mx) ** 2 for a in x) ** 0.5
        vy = sum((b - my) ** 2 for b in y) ** 0.5
        return cov / (vx * vy) if vx and vy else 0.0

    vecs = {a["reviewer"]: [float(a["ratings"][h]) for h in IDS] for a in agents}  # type: ignore[index]
    models = {a["reviewer"]: a["model"] for a in agents}
    within, across = [], []
    for r1, r2 in itertools.combinations(vecs, 2):
        (within if models[r1] == models[r2] else across).append(pearson(vecs[r1], vecs[r2]))

    print("## Verdict (pre-registered rule applied)\n")
    print(f"**{verdict}** — {len(inversions)} strict bug/safe order inversions; "
          f"AUROC naive {auroc_a:.3f} vs root-keyed {auroc_b:.3f}; "
          f"top-{len(bugs)} false positives {len(fp_a)} vs {len(fp_b)}.\n")
    print("| Hunk | truth | P naive | P root-keyed | shift |")
    print("|---|---|---|---|---|")
    for h in sorted(IDS, key=lambda h: -pb[h]):
        print(f"| {h} | {truth[h]} | {pa[h]:.3f} | {pb[h]:.3f} | {pb[h] - pa[h]:+.3f} |")
    print(f"\n- top-{len(bugs)} naive: {', '.join(top_a)}  (FP: {', '.join(fp_a) or 'none'})")
    print(f"- top-{len(bugs)} root-keyed: {', '.join(top_b)}  (FP: {', '.join(fp_b) or 'none'})")
    if inversions:
        shown = ", ".join(f"{b}>{s}" for b, s in inversions[:12])
        print(f"- inversions (bug reranked above safe, or vice versa): {shown}")
    print(f"- mean pairwise Pearson within-model {sum(within)/len(within):.3f} "
          f"vs across-model {sum(across)/len(across):.3f} "
          f"(the correlated-rater premise, measured)")
    sys.exit(0)


if __name__ == "__main__":
    main()
