# Opinions: the shape of a belief

**A Subjective Logic opinion is four numbers instead of one: belief `b`, disbelief `d`, uncertainty `u`, and a base rate `a`.** Splitting a belief this way lets the system say "I don't know" instead of guessing — because a single probability cannot tell "no evidence yet" apart from "the evidence is split down the middle," and an opinion can. The four numbers come from two counts, evidence-for and evidence-against, by one fixed formula: the Beta bijection.

## The four numbers

An **opinion** is a belief about one yes/no claim — "this study replicated," "vaccines are safe." A single probability squeezes everything you know about a claim into one number. An opinion reports four instead:

- **belief `b`** — how much evidence favors "yes"
- **disbelief `d`** — how much evidence favors "no"
- **uncertainty `u`** — how much you simply don't know
- **base rate `a`** — your best guess with zero evidence (the default is 0.5, a coin flip)

`b`, `d`, and `u` always add to 1. A claim you've seen nothing about: `b = 0, d = 0, u = 1` — pure ignorance. A claim ten agreeing sources back: `b ≈ 0.9, d ≈ 0, u ≈ 0.1` — firm belief.

## The key idea: "no evidence" is not "balanced evidence"

Two claims can both sit at probability 0.5 and mean opposite things.

A **fair coin**, flipped a thousand times, comes up heads half the time. You know a lot about it, and what you know says 50/50.

A coin of **unknown bias**, never flipped, might be fair, loaded, or two-headed. You also can't call it better than 50/50 — but this time because you know nothing.

A single probability reports both coins as "0.5" and throws away the difference. That is exactly requirement (b) in the [Subjective Logic design](https://github.com/TheRealBillSiegler/epistemic-pipeline/blob/main/docs/superpowers/specs/2026-06-23-worldview-subjective-logic-design.md): a formalism must mark "unverified" as different from "balanced," because a system that can't tell them apart treats a wild guess and a well-tested fact as the same kind of confidence. Uncertainty `u` is the number that tells them apart: the fair coin has `u` near 0 (heavily evidenced, genuinely balanced), the unknown coin has `u = 1` (no evidence at all).

## Where the numbers come from: the Beta bijection

An opinion is stored as two counts, not as `(b, d, u, a)` directly: `r`, the weighted evidence for the claim, and `s`, the weighted evidence against it. The four numbers are computed from those counts by a **bijection** — a two-way conversion that loses nothing, counts to opinion and back exactly. `W` is a fixed constant (2) standing for "the weight of knowing nothing":

$$
b = \frac{r}{r + s + W}, \qquad d = \frac{s}{r + s + W}, \qquad u = \frac{W}{r + s + W}
$$

The **projected probability** — the single number you'd bet on if forced to pick one — folds the uncertainty back in at the base rate:

$$
P = b + a \cdot u
$$

**Worked example.** One confident source rates a claim, contributing `r = 2, s = 0`:

$$
b = \frac{2}{2+0+2} = 0.5, \qquad d = 0, \qquad u = \frac{2}{2+0+2} = 0.5, \qquad P = 0.5 + 0.5 \times 0.5 = 0.75
$$

One source is enough to move belief to 0.5 — but it leaves half the opinion still uncertain. The projected probability, 0.75, is what you'd report if forced to pick a single number; the opinion `(0.5, 0, 0.5, 0.5)` is what actually happened.

## Four corner states

The same base rate (`a = 0.5`) can land on very different opinions, depending on how much evidence there is and which way it points.

| State | Evidence | `b` | `d` | `u` | `P` | What it means |
|---|---|---|---|---|---|---|
| Vacuous | `r=0, s=0` | 0.00 | 0.00 | 1.00 | 0.50 | No evidence at all |
| Confirmed | `r=8, s=0` | 0.80 | 0.00 | 0.20 | 0.90 | Strong evidence for |
| Disconfirmed | `r=0, s=8` | 0.00 | 0.80 | 0.20 | 0.10 | Strong evidence against |
| Conflicted | `r=9, s=9` | 0.45 | 0.45 | 0.10 | 0.50 | Heavy evidence, evenly split |

Look at *vacuous* and *conflicted*: both project to `P = 0.50`. A single probability would report them identically. `u` shows they are nothing alike — 1.00 (nothing known) versus 0.10 (extensively tested, still split).

## Settledness

**Settledness** is how much of an opinion's uncertainty has been resolved: `1 - u`. Vacuous settledness is 0. Confirmed and disconfirmed settledness is 0.80. Conflicted settledness is 0.90 — *higher* than confirmed, because contradiction from real evidence still counts as evidence.

!!! note "Settled is not correct"
    High settledness means a lot of evidence has been weighed. The conflicted row above is the clearest case: heavily settled (0.90) and evenly split at the same time. Whether the claim is *true* is a separate question, and settledness does not answer it — see [What the numbers mean](../worldview/honesty.md).

## Where next

- How opinions from more than one source combine: [Fusing evidence](fusion.md)
- How a source's trustworthiness scales its contribution: [Credibility](credibility.md)
- Where `B`, the belief component, fits in the wider state tuple: [The state tuple](../concepts/state.md)
- The full design and its proof: [Worldview Encoding — Subjective Logic Design](https://github.com/TheRealBillSiegler/epistemic-pipeline/blob/main/docs/superpowers/specs/2026-06-23-worldview-subjective-logic-design.md)
- The reference implementation: [`_subjective_logic.py`](https://github.com/TheRealBillSiegler/epistemic-pipeline/blob/main/src/epistemic_pipeline/encodings/_subjective_logic.py)
