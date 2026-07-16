# P3 ranking backtest — pre-registered design and decision rule

**Date locked:** 2026-07-15, committed before any reviewer ran.
**Question:** Does root-keyed independence fusion (P3) change which claims get trusted, compared to naive per-agent accumulation, on real multi-agent review output — and does the change point toward ground truth? This is the kill-test named in `docs/research/2026-07-15-agent-verification-prior-art.md` §5. If root-keying does not move rankings, the load-bearing pillar carries no decision weight and the agent-verification reframe stops here.

## Setup

Fourteen independent changes (C01–C14, see `diff.md` and `hunks.py`) to two real modules. Some are seeded bugs built from standard mutation operators; the rest are verified behavior-preserving. The split and labels are hidden behind a salted SHA-256 commitment (`truth_commitment.txt`) until all reviews are in. Construction was verified mechanically before lock: every safe change leaves the full test suite green, pyright clean, and a fixed behavior probe byte-identical; every bug is witnessed by a probe difference or a red suite.

Each change is one claim: "C*k* introduces a behavior-changing defect."

## Evidence channels

- **11 LLM reviewers**, blind, no tools, identical prompt except a reviewer number: 5× `claude-sonnet-5`, 3× `claude-haiku-4.5`, 3× `claude-opus-4-8`. Each returns P(bug) ∈ [0,1] for every change. Ratings are used exactly as returned.
- **check:pytest** — each change applied alone, full suite run. Fail → 0.95 on that change. Pass → 0.20 (the suite exercised it and saw nothing).
- **check:pyright** — strict mode on both files, per change. New errors → 0.90. Clean → no evidence emitted.

## The two folds

Identical ratings, identical operator (`aggregate_beliefs`, the production two-tier fuse). One variable changes — the root map:

- **Fold A (naive):** every reviewer instance is its own root (13 roots: 11 agents + pytest + pyright). This is vote-counting: five sonnets are five independent voices.
- **Fold B (root-keyed):** reviewers sharing a model are one root (5 roots: sonnet, haiku, opus, pytest, pyright). Five sonnets average into one voice.

Rank changes by projected P(bug), descending, under each fold.

## Decision rule (locked)

- **PASS** iff both hold:
  1. At least one bug/safe pair is ordered differently by A and B — the correction moves a decision-relevant ranking.
  2. AUROC(B) ≥ AUROC(A) against ground truth — the movement is not away from truth.
- **STRONG PASS** if additionally AUROC(B) > AUROC(A), or fold B has strictly fewer false positives among its top-7 (7 = number of true bugs, revealed with the labels).
- **FAIL** otherwise: rankings identical on all bug/safe pairs, or AUROC(B) < AUROC(A).

On FAIL, the pre-committed consequence is: stop the agent-verification reframe; no design memo.

## Threats to validity, named now

- The diff is author-constructed (standard mutation operators). Reviewer *ratings* are blind and not authored, which is the variable under test — but bug difficulty is not sampled from nature.
- n = 14 claims, one diff, one repo. A pass here is "the mechanism can matter," not "it matters everywhere."
- Same-model correlation is the hypothesized driver of A/B divergence. If sonnet reviewers happen to disagree with each other as much as with other models, folds converge and the test can fail for that reason. That outcome would itself be evidence against P3's importance, which is the point of running it.
