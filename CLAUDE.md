# CLAUDE.md — Epistemic Pipeline

## Project

A universal reasoning architecture. Formal spec in `docs/spec/`, Python reference implementation in `src/epistemic_pipeline/`. See `docs/superpowers/specs/2026-03-19-epistemic-pipeline-v01-design.md` for the full v0.1 design.

## Writing Style

All prose in this project — specs, docstrings, comments, READMEs — must be **graduate-level ideas in 8th-grade sentences**.

Rules:
- Short sentences. Under 20 words on average.
- Define every technical term the first time it appears, in one plain sentence.
- Follow abstract definitions immediately with a concrete example.
- No sentence should require re-reading to parse. If it does, the sentence is the problem, not the idea.
- Active voice. Say who does what.
- No filler. No throat-clearing. Lead with the point.

This applies equally to the formal spec and the code. Rigor lives in the structure and the math, not in complex sentences.

## Architecture

Two orthogonal views of one system:
- **5-layer stack** (architecture): Tool/Environment, Cognitive Process, Pipeline, Norms, Meta-Epistemic
- **`(O, E, B, R)` tuple** (state): Ontology, Evidence, Beliefs, Revision policy

Each layer reads/writes different state components. The stack is vertical. The tuple is horizontal.

## Development Workflow

Interleaved: spec section → code → tests, for each component. Never implement without a spec. Never spec without implementing immediately after.

## Code Conventions

- Python 3.12+
- Pure functions for pipeline stages
- Frozen dataclasses for state (immutability is a hard invariant)
- Generic type parameters on `EpistemicState` so framework encodings can specialize O, E, B, R
- No external dependencies for v0.1
- `pytest` for tests, `mypy` for type checking

## Key Invariants

- `EpistemicState` is immutable per pipeline step
- R is pure: `R(B, e, O) → B'` — no side effects, deterministic
- E is append-only within a pipeline run
- O is static within a pipeline run (only meta-layer can re-frame)
- The state trace (list of all intermediate states) is always preserved
