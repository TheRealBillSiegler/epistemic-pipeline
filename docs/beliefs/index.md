# Beliefs as Numbers

**A belief is an opinion with explicit uncertainty — belief `b` (likely true), disbelief `d` (likely false), uncertainty `u` (unknown), and a base rate.** Evidence arrives as counts; each source is scaled by credibility before fusion; the algebra is Subjective Logic, deterministic and replayable. The result is traceable, never claims truth, and can always be replayed.

## What an opinion is

*An opinion carries how much evidence backs a belief.*

A plain probability of 0.65 hides whether the number rests on strong evidence or almost none. An opinion carries that missing information as an explicit uncertainty mass `u`, which separates "I have no evidence" from "the evidence is balanced." That is what makes honesty possible — the system can say "unknown" instead of fabricating 0.5.

## Counts and fusion

Observations become counts. An LLM's rating of a claim, scaled by the LLM's credibility, contributes to belief; the portion not attributed goes to uncertainty. Multiple sources fuse by adding their (discounted) counts. Subjective Logic makes this closed-form: the same trace always rebuilds the same beliefs, no approximation needed.

## Credibility and discounting

Not all sources are equal. The revision rule applies a credibility weight to every source, scaling its counts before fusion, so a trusted, replicated study can move belief further than an unvetted claim. Today that weight is a constant `1.0` for every source — the weighting machinery exists but is deliberately switched off until it can be grounded. [Credibility](credibility.md) explains both the operator and the gap.

## Where next

- [Opinions](opinions.md) — the formal definition and the Beta/Dirichlet bijection
- [Fusion and discounting](fusion.md) — how counts combine under credibility
- [The Subjective Logic spec](https://github.com/TheRealBillSiegler/epistemic-pipeline/blob/main/docs/superpowers/specs/2026-06-23-worldview-subjective-logic-design.md) — the design and its proof
