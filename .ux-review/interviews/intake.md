# Intake — epistemic-pipeline worldview tool UX review

Date: 2026-07-12. Source: session context (memory, issues #5/#9/#10, specs, docs site). Not an interactive interview — assumptions flagged inline.

## App purpose

A quantified sense-making tool: drop in documents, watch beliefs update by an auditable rule, inspect why every number is what it is. Never issues truth verdicts; the product is the honest, replayable process. (Memory: project_worldview_app_identity.)

## Target users

1. Near-term: the developer himself (dogfooding a personal note vault) — demand validation is an open question.
2. Mid-term: researchers / PKM users (Obsidian-adjacent) managing a reading corpus.
3. Parallel audience: academics/engineers evaluating the formalism (the repo's original stated audience: "spec is publishable; code is pip-installable").

## Surfaces that exist today

- Fresh-clone experience: README (leads with formalism, not the app), `uv sync`, `uv run pytest`.
- `epc` CLI: run/replay/diff/score pipeline traces. Zero worldview commands.
- Python library: `epistemic_pipeline.worldview_app` (Store, ingest_document, author_claim, NoteIngester). **No real LLM adapter ships — only mocks** (`MockRatingLLM`); the "inferred" path requires the user to write their own `rate_confidence` implementation.
- Docs site (PR #39, local at http://127.0.0.1:8123/epistemic-pipeline/): the onboarding/explanation surface.

## Known pain points (from issues)

- No server/UI (#9); no quickstart or demo corpus (#10); README doesn't lead with the app (#10).
- NoteIngester dedupe is per-process (restart re-ingests).
- Honest-status walls are documented on the docs site (honesty page) — good — but the tool cannot yet be *experienced* without writing Python.

## Success criteria for this review

Findings concrete enough to feed #9 (what the UI must show/fix) and #10 (what the quickstart must contain). Special attention: first 10 minutes of a new user's contact; whether the honesty identity survives contact with real UX.

## Scope

Current surfaces only. The unbuilt UI is assessed as an absence (what its lack costs each persona), not speculated into existence.
