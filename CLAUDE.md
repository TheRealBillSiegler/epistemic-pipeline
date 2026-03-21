# CLAUDE.md — Epistemic Pipeline

## Project

A general-purpose reasoning architecture. Formal specs in `docs/superpowers/specs/`, Python reference implementation in `src/epistemic_pipeline/`. v0.1 design spec: `docs/superpowers/specs/2026-03-19-epistemic-pipeline-v01-design.md`.

## Writing Style

All prose in this project — specs, docstrings, comments, READMEs — must be **graduate-level ideas in 8th-grade sentences**.

The test: if a smart 8th-grader can't follow the English, rewrite the English. The math and code stay at whatever level they need to be. Simple sentences, rigorous structures.

Rules:

- Short sentences. Under 20 words on average.
- Active voice. Say who does what.
- Lead with the point. No filler, no throat-clearing.
- Define every technical term the first time it appears, in one plain sentence.
- Follow every abstract definition immediately with a concrete example.
- No sentence should require re-reading. If it does, the sentence is the problem, not the idea.
- The formalism carries the rigor. The prose carries the clarity. Never confuse complexity of language with complexity of thought.

## Architecture

Two orthogonal views of one system:

- **5-layer stack** (architecture): Tool/Environment, Cognitive Process, Pipeline, Norms, Meta-Epistemic
- **`(O, E, B, R)` tuple** (state): Ontology, Evidence, Beliefs, Revision policy

Each layer reads/writes different state components. The stack is vertical. The tuple is horizontal.

## Development Workflow

Interleaved: spec section → code → tests, for each component. Never implement without a spec. Never spec without implementing immediately after.

## Code Conventions

- Python 3.14+
- Use `uv` for all Python execution (never bare `python` or `pip`)
- Pure functions for pipeline stages
- Frozen dataclasses for state (immutability is a hard invariant)
- Generic type parameters on `EpistemicState` so framework encodings can specialize O, E, B, R
- No external dependencies for v0.1
- `pytest` for tests, `pyright` for type checking, `ruff` for linting
- Run tools via `uv`: `uv run pytest`, `uv run pyright`, `uv run ruff check`

## Key Invariants

- `EpistemicState` is immutable per pipeline step
- R is pure: `R(B, e, O) → B'` — no side effects, deterministic
- E is append-only within a pipeline run
- O is static within a pipeline run (only meta-layer can re-frame)
- The state trace (list of all intermediate states) is always preserved
