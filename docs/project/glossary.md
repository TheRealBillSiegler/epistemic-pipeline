# Glossary

**Every term below is defined once, in one sentence, and links to the page that explains it in full — use this page to look a word up, not to learn the system.**

## averaging fusion

The fusion rule that averages evidence counts from several opinions about one claim, so restating one source many times counts as one restatement, not many. [Fusing evidence](../beliefs/fusion.md)

## base rate

The prior probability a claim gets before any evidence arrives, a number in [0, 1] that defaults to 0.5. [Opinions and uncertainty](../beliefs/opinions.md)

## belief mass

The share of an opinion's evidence that supports the claim, \( b = r / (r + s + W) \). [Opinions and uncertainty](../beliefs/opinions.md)

## claim

One sentence the system holds a belief about; the sentence's own text is its id, so `"Fiscal Q4 2024 = $2.1B"` names the claim and its stored belief at once. [The belief store](../worldview/store.md)

## concept

A name in the [ontology](#ontology) that a belief can attach to; in the worldview app every claim an LLM rates becomes a concept the moment it is rated. [The state tuple](../concepts/state.md)

## cumulative fusion

The fusion rule that adds evidence counts from several opinions, so independent confirmation lowers uncertainty — the right choice only when the sources are genuinely independent. [Fusing evidence](../beliefs/fusion.md)

## discount

Scaling an opinion's evidence counts by a source's reliability before it gets fused in, so a low-trust source loses influence instead of flipping the belief the other way. [Credibility](../beliefs/credibility.md)

## drift timeline

The ordered history of how much each observation moved one claim's belief, built from the append-only record of which observation moved which claim. [The belief store](../worldview/store.md)

## encoding

The plug-in that fits one reasoning framework — Bayes, planning, Subjective Logic — into the same `(O, E, B, R)` slots without changing the architecture around it. [The encodings](../concepts/encodings.md)

## epistemic state

The frozen snapshot `(O, E, B, R)` produced at one pipeline step — the whole system's memory at that instant, never edited after it is made. [The state tuple](../concepts/state.md)

## evidence increment

One document's contribution to one concept's opinion, tagged with the root it traces to before fusion groups it with others. [Fusing evidence](../beliefs/fusion.md)

## meme farm

The adversarial case where many near-duplicate, low-credibility sources restate one claim to manufacture false confidence; [averaging fusion](#averaging-fusion) is the defense against it. [Fusing evidence](../beliefs/fusion.md)

## observation

One recorded piece of evidence: what was measured, its value, its source, when it was seen, and how confident that source was. [The state tuple](../concepts/state.md)

## ontology

The set of concepts a belief can attach to; evidence about anything outside it can never move a belief. [The state tuple](../concepts/state.md)

## opinion

A belief about one claim, stored as supporting and disconfirming evidence counts `(r, s)` plus a base rate, from which belief, disbelief, and uncertainty are all derived. [Opinions and uncertainty](../beliefs/opinions.md)

## projected probability

The single number an opinion collapses to when one number is needed: belief plus base rate times uncertainty, \( P = b + \text{base\_rate} \cdot u \). [Opinions and uncertainty](../beliefs/opinions.md)

## provenance

The record of where a piece of evidence came from, used to derive its [root id](#root-id) and, eventually, its credibility. [The belief store](../worldview/store.md)

## replay

Rebuilding a belief state by re-running the revision policy over the recorded evidence trail; because R is pure this gives the same answer every time — provided the same R is reattached, which trace replay does not yet guarantee ([#30](https://github.com/TheRealBillSiegler/epistemic-pipeline/issues/30)). [The pipeline](../concepts/pipeline.md)

## revision policy

The pure rule \( R(B, e, O) \rightarrow B' \) that turns old beliefs plus one new observation into new beliefs — the only thing allowed to change B. [The state tuple](../concepts/state.md)

## root id

A stable, canonicalized id for where a piece of evidence ultimately comes from, so the same source counted twice collapses to one instead of inflating [settledness](#settledness). [The belief store](../worldview/store.md)

## settledness

How much recorded, deduplicated evidence backs a belief, computed as `1 - u`; it measures evidence gathered, never truth. [What the numbers mean](../worldview/honesty.md)

## trace

The full sequence of frozen states a pipeline run produces, kept so any past belief can be inspected and any run can be replayed. [The state tuple](../concepts/state.md)

## two-tier fusion

[Averaging fusion](#averaging-fusion) within one root, then [cumulative fusion](#cumulative-fusion) across distinct roots — so re-importing one source under two names no longer inflates settledness the way plain cumulative fusion would. [Fusing evidence](../beliefs/fusion.md)

## uncertainty mass

The share of an opinion that is neither belief nor disbelief, \( u = W / (r + s + W) \); it equals 1.0 when no evidence has arrived yet. [Opinions and uncertainty](../beliefs/opinions.md)

## vacuous opinion

An opinion with no evidence at all, `Opinion(r=0, s=0)`, which projects to its base rate and means "I don't know" — not "the evidence is balanced." [Opinions and uncertainty](../beliefs/opinions.md)
