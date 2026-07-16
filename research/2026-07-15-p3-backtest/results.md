# P3 ranking backtest — results

**Date:** 2026-07-15
**Rule:** locked in `decision_rule.md` before any reviewer ran. Truth labels match the pre-registered commitment (`fold.py` checks the hash).
**Panel:** 11 blind reviewers (5 sonnet, 3 haiku, 3 opus), no tools, plus per-hunk pytest and pyright channels. Zero reviewer errors, zero dropped reviews. Tool-call audit: ~4 calls per reviewer (three reads plus the output call), consistent with the no-execution rule.

## Verdict: FAIL

Zero strict bug/safe order inversions between the naive fold and the root-keyed fold. AUROC 1.000 under both. Top-7 false positives: none under either. Root-keyed fusion did not change which claims got trusted. Per the pre-committed consequence, the agent-verification reframe stops here.

| Hunk | truth | P naive | P root-keyed | shift |
|---|---|---|---|---|
| C12 | bug | 0.931 | 0.871 | -0.060 |
| C02 | bug | 0.908 | 0.856 | -0.052 |
| C09 | bug | 0.886 | 0.838 | -0.048 |
| C04 | bug | 0.856 | 0.821 | -0.035 |
| C08 | bug | 0.827 | 0.686 | -0.141 |
| C03 | bug | 0.641 | 0.565 | -0.076 |
| C07 | bug | 0.476 | 0.540 | +0.064 |
| C13 | safe | 0.084 | 0.161 | +0.077 |
| C11 | safe | 0.076 | 0.155 | +0.079 |
| C05 | safe | 0.071 | 0.151 | +0.080 |
| C10 | safe | 0.071 | 0.151 | +0.080 |
| C14 | safe | 0.068 | 0.150 | +0.082 |
| C01 | safe | 0.068 | 0.150 | +0.081 |
| C06 | safe | 0.066 | 0.148 | +0.082 |

## Why it failed

The panel was too good for the dataset. Every reviewer, in every model family, separated the bugs from the safe changes almost perfectly. With perfect separation there are no contested claims, and a correction that re-weights contested claims has nothing to do.

The correlated-error premise did not show up here. Mean pairwise Pearson within a model family was 0.952; across families it was 0.926. The models did not share family-specific blind spots on this diff. They shared the truth.

The one contested claim moved the right way. C07 (the migration-breaking index, which this experiment's own construction check had misjudged as safe) split the sonnet reviewers: two missed it, three caught it. Root-keying averaged that split into one voice and raised the claim from 0.476 to 0.540 — toward the truth. That is the P3 mechanism working as designed, on the only claim where anyone erred. It is one data point and it did not flip any bug/safe pair, so it does not soften the verdict.

The global shift pattern (bugs down, safes up under root-keying) is arithmetic, not signal: fewer roots means more retained uncertainty, which pulls every projected value toward the 0.5 base rate.

## What this does and does not establish

It establishes: on review tasks where frontier models already agree and are right, root-keyed fusion adds nothing that vote-counting lacks. Redundant same-model panels were simply redundant — five sonnets told us nothing three didn't. If the target domain is "2026 frontier models reviewing small, well-contexted diffs," the load-bearing pillar carries no decision weight, exactly as the falsifier feared.

It does not establish: that the correction is worthless where models actually err. The Apple "Nine Judges" result lives in subjective evaluation tasks with high error rates; this diff produced almost no errors to correlate. A harder dataset — subtle concurrency bugs, large diffs, ambiguous specs, weaker models — could still show the effect. Nothing here licenses assuming it would.

Named at construction time and confirmed: the diff was author-built from standard mutation operators, n=14, one repo. The bugs (contradicted comments, transposed tuples, boundary flips) were evidently too detectable for this panel.

## Consequence

Per the pre-registered rule: stop. No Tier-2 design memo. The agent-verification reframe reverts from "conditional yes" to "not justified on current evidence." Reviving it requires a new pre-registered test on claims where the panel's error rate is materially above zero — that is a new decision, not a continuation of this one.
