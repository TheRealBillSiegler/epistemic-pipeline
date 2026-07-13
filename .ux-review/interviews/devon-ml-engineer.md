# Interview — Devon, ML engineer evaluating the formalism

Pre-registered before touching the tool. These are my expectations, must-haves, and deal-breakers going in, so I can check afterward whether contact with the real thing changed my mind — and where it didn't.

## What "auditable belief revision over your documents" has to mean

I've seen this pitch before, usually attached to a RAG demo with a vector DB and zero math. For me to take it seriously it has to mean:

- There's a revision rule `R`, and I can see its source, not just its output.
- The same evidence in the same order always produces the same belief. If two runs of the same input diverge, the "auditable" claim is dead on arrival.
- Every number traces back to specific evidence, not to an LLM's vibes dressed up as a probability.
- The system tells me when it doesn't know something, instead of quietly defaulting to 0.5 and calling that neutral.

## Expectations walking in

- A staff-eval-harness person's prior on any tool claiming "auditable AI reasoning": 90% marketing, 10% math. I expect to find the 10% or bail within 15 minutes.
- I expect the README to oversell relative to what's implemented — that's the norm for this genre. I will diff the claims against the code, not against the prose.
- I expect "auditable" to mean a trace file I can diff, not a design intention. If there's no artifact I can `git diff` or `jq` through, it isn't audited, it's aspirational.
- Given the project is "spec is publishable, code is pip-installable," I expect the spec to over-promise slightly ahead of the code. That's fine *if the repo says so itself*. It's not fine if I have to find the gap myself.

## Must-haves (from the persona brief, stated as checks)

1. **A working example, runnable in under 5 minutes.** Not "should work" — I will time it. Clock starts at `git clone`.
2. **Type hints on the public surface.** I judge Python maturity by whether `pyright --strict`-adjacent tooling passes clean, not by docstrings.
3. **Math traceable to literature.** A named algorithm, a citation, ideally a link to a paper or a spec with a proof sketch. "We use a fusion rule" with no reference is a red flag.
4. **An obvious extension point for a real LLM.** If the only shipped LLM integration is a mock, I need to see — within a few minutes, not by reverse-engineering the whole call graph — exactly which method to implement and what shape it returns. A `Protocol` with a clear docstring earns real credit here; an ABC buried three modules deep does not.

## Deal-breakers

- **Claims in docs the code doesn't back.** If a doc says "the app rates the claims" and there's no app — just a library function I have to wire up myself — that's a deal-breaker for "app," not for the underlying claim, and I will say so precisely, not vaguely.
- **Hidden nondeterminism.** Wall-clock timestamps baked into the belief state, unseeded randomness, dict ordering leaking into output — anything that makes replay non-reproducible without the docs admitting it.
- **Mock-only integrations presented as features.** "LLM-powered" in the pitch, `MockLLM` in the only code path that runs, and no visible seam for a real one — that's a demoware pattern, and I've been burned by it enough to bail on sight.

## What would make me adopt vs. file an issue and move on

Adopt: the revision rule is pure and I can prove it (run it twice, diff the output), the honesty gaps are stated by the project itself rather than found by me, and there's a real extension point even if no first-party LLM adapter ships.

File an issue and move on: the core math is sound but the surrounding experience (README, quickstart, CLI) doesn't reflect what the library actually does — e.g., a flagship CLI feature (`epc replay`) that doesn't actually apply to the product being pitched.

Bail without filing anything: the "auditable" claim is decorative — no trace artifact, no determinism, or the fusion rule turns out to be ad hoc arithmetic with no cited basis.

## What I will NOT do

I will not run anything that requires a real API key, a network call, or a UI — if the app promises "drop in a document" and that requires infrastructure I can't stand up in this session, I'll say so and evaluate what's left (the library) instead of pretending I ran the whole thing.
