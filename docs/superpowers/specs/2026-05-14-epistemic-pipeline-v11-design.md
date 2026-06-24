# Epistemic Pipeline v1.1 Design Specification

**Date:** 2026-05-14
**Status:** Implemented (current baseline).
**Delta from v1.0:** LLM-agent encoding (fifth expressiveness demonstration), trace persistence as JSONL, `epc` command-line interface (replay/diff/score), and a named use case for agent debugging.

> **Partial supersession.** The worldview encoding's revision function described here — renormalize over the latest confidence vector, and drop any concept a new document omits — is **superseded** by [Worldview Encoding — Subjective Logic Design](2026-06-23-worldview-subjective-logic-design.md) (2026-06-23). That design does *not* erase a belief on omission. Everything else in this spec (LLM-agent encoding, JSONL traces, `epc` CLI) is current.

---

## Motivation

v1.0 ships four academic encodings — Bayesian inference, STRIPS planning, state-space search, and MDP value iteration. None of those is what most engineers use day-to-day. Most engineers run LLM agents. An LLM agent is a program that calls a language model in a loop, often with tools, to answer a question or complete a task. v1.1 adds an LLM-agent encoding so the architecture speaks to the work most users actually do.

v1.0 also keeps every reasoning trace in memory. When the process exits, the trace is gone. "Auditable reasoning" is hollow if no one can read yesterday's run. v1.1 adds a persistence format so traces survive process exit.

v1.0 ships a library with no command to type. v1.1 adds a small command-line tool called `epc` so a normal user can run, replay, diff, and score traces without writing Python.

These three changes are the minimum needed to turn the v1.0 library into something a working engineer can install on Monday and use on Tuesday. The formal core — pure transformations, immutable state, the (O, E, B, R) tuple — is unchanged.

---

## Part 1: LLM-Agent Encoding

### 1.1 What it encodes

The LLM-agent encoding treats one run of an LLM agent loop as a single (O, E, B, R) reasoning system. The agent is given a closed set of hypotheses and a closed set of tools. Each step, the agent picks a tool, the tool returns evidence, and the agent re-rates its confidence across the hypotheses.

- **O (Ontology):** the fixed set of named hypotheses the agent must rank, plus the registry of tools the agent may call. O also carries a flag `inadequate` that the pipeline sets when the agent proposes a hypothesis outside the closed set.
- **E (Evidence):** the full sequence of tool results and LLM self-reports. Each item is one `Observation` with `modality="tool"` or `modality="llm"`.
- **B (Beliefs):** a dict from hypothesis name to confidence in [0, 1]. Confidences sum to 1.0 within float tolerance, the same invariant Bayes uses.
- **R (Revision):** reads the latest LLM observation, which contains a JSON confidence vector, filters out unknown hypotheses, renormalizes, and returns the new beliefs.

### 1.2 Conditional determinism

R must be pure. But the LLM is not deterministic. v1.0 already names this gap and resolves it: the LLM response is recorded as an `Observation` *before* R runs. R reads the recorded text and applies a deterministic parse-and-renormalize step. The randomness is captured in E, not in R.

In live mode, the pipeline calls the LLM through an `LLMInterface` and records each response as evidence. In replay mode, the pipeline reads recorded responses from a trace file and produces the same state sequence. The hard invariant "R is pure" holds because R only ever reads from E.

### 1.3 Types

```python
@dataclass(frozen=True)
class LLMAgentOntology:
    """Hypotheses and tools the agent operates over.

    hypotheses: mutually exclusive hypothesis names.
    tools: tool names the agent may call.
    inadequate: True if the agent has proposed a hypothesis outside
        the closed set. Set by the Test stage, not by R. When True,
        the meta layer should trigger REFRAME.
    """

    hypotheses: tuple[str, ...]
    tools: tuple[str, ...]
    inadequate: bool = False

    def adequate(self, evidence: tuple[Observation, ...]) -> bool:
        return not self.inadequate


@dataclass(frozen=True)
class LLMAgentBeliefs:
    """Confidence distribution over hypotheses.

    confidences: maps each hypothesis to confidence in [0, 1].
    Invariant: sum equals 1.0 within float tolerance.
    """

    confidences: dict[str, float]
```

### 1.4 Revision policy

`llm_agent_update(beliefs, evidence, ontology) -> LLMAgentBeliefs`

Steps:

1. Parse `evidence.value` as a JSON object mapping hypothesis name to confidence.
2. Drop entries whose name is not in `ontology.hypotheses`.
3. If the filtered map is empty, return `beliefs` unchanged.
4. Renormalize the filtered map so values sum to 1.0.
5. Return `LLMAgentBeliefs(confidences=...)`.

R never sees the LLM. R reads the recorded `Observation`. R is a pure function from (B, e, O) to B'.

### 1.5 Pipeline stages

- **Frame:** Build `LLMAgentOntology` from the problem spec. Set uniform priors unless custom priors are given. Store the LLM interface, tool registry, max-steps budget, and confidence threshold in metadata.
- **Decompose:** No-op for v1.1.
- **Model:** No-op. R is set in Frame.
- **Select:** No-op for v1.1. Tool selection happens inside Test.
- **Test:** Outer loop, one iteration per agent step. Each iteration:
  1. Ask the LLM which tool to call given the current state. Record the answer as `Observation(modality="llm", variable="tool_choice")`.
  2. Call the chosen tool with arguments parsed from the LLM response. Record the result as `Observation(modality="tool")`.
  3. Ask the LLM for a fresh confidence vector given the new evidence. Record as `Observation(modality="llm", variable="confidence_vector")`.
  4. Apply R to the recorded confidence vector. Update B.
  5. If the LLM response mentions a hypothesis not in `ontology.hypotheses`, append `"ontology_inadequate"` to anomalies and set the new ontology's `inadequate` flag via the standard `replace` pattern (this is a pipeline-stage action, not R).
  6. Stop when (a) the top hypothesis has confidence ≥ `confidence_threshold`, (b) the step budget is exhausted, or (c) the meta layer returns ESCALATE.
- **Integrate:** Extract the argmax hypothesis as the answer. Compute the confidence margin (top1 − top2). Store both in metadata.

### 1.6 Toy problem: revenue Q&A with fiscal-vs-calendar trap

The toy problem must show one realistic agent failure mode that the trace can catch. We choose the fiscal-versus-calendar Q4 confusion because it is concrete, common in finance work, and produces a clean trace.

Question: *"What was Q4 2024 revenue for FakeCo?"*

Tools:

- `lookup_financials(company, period)` — returns the value from FakeCo's internal records. FakeCo's fiscal year ends in June, so Q4 FY2024 = $2.1B (April–June 2024). The tool returns $2.1B when asked for "Q4 2024" because that is how FakeCo's records are indexed.
- `lookup_recent_news(query)` — returns recent press releases. Returns "FakeCo reports $2.4B Q4." for "FakeCo Q4 revenue." The press release uses calendar Q4 (October–December 2024).

Hypotheses (closed set):

- `"$2.1B"` — fiscal Q4 ending June 2024.
- `"$2.4B"` — calendar Q4 ending December 2024.

Expected trace:

1. Agent calls `lookup_financials("FakeCo", "Q4 2024")`. Tool returns $2.1B. Belief in $2.1B rises to about 0.85.
2. Agent calls `lookup_recent_news("FakeCo Q4 revenue")`. Tool returns $2.4B. Belief flips: $2.4B rises to about 0.70.
3. Belief flips back when agent re-reads the first result.
4. Oscillation detector trips on the third flip. Anomaly `"oscillation"` appended.
5. Meta layer reads norm scores, triggers `SWITCH_STRATEGY` or `ESCALATE`.

The point of the trace is that a user reading it can immediately see *which evidence flipped which belief* and *why the run failed*. That is the audit story v1.0's encodings cannot tell because none of them invoke an LLM.

### 1.7 LLMAgentProblem

```python
@dataclass(frozen=True)
class LLMAgentProblem:
    """Full specification of an LLM-agent reasoning problem.

    question: the natural-language task to solve.
    hypotheses: closed set of candidate answers.
    tools: name -> ToolInterface registry.
    llm: an LLMInterface for live mode.
    max_steps: outer-loop budget.
    confidence_threshold: stop when top hypothesis exceeds this.
    priors: initial confidence distribution. Uniform if None.
    """

    question: str
    hypotheses: tuple[str, ...]
    tools: dict[str, ToolInterface]
    llm: LLMInterface
    max_steps: int = 10
    confidence_threshold: float = 0.9
    priors: dict[str, float] | None = None
```

### 1.8 Provider adapters

Real LLM providers live behind optional extras. The core package stays zero-dep. Adapters wrap a provider client into the `LLMInterface` protocol.

```python
# epistemic_pipeline/llm/providers/openai_adapter.py
class OpenAIAdapter:
    """Wraps openai.OpenAI client into LLMInterface."""
    def __init__(self, client: Any, model: str) -> None: ...

# epistemic_pipeline/llm/providers/anthropic_adapter.py
class AnthropicAdapter:
    """Wraps anthropic.Anthropic client into LLMInterface."""
    def __init__(self, client: Any, model: str) -> None: ...
```

`pyproject.toml` gains:

```toml
[project.optional-dependencies]
openai = ["openai>=1.0"]
anthropic = ["anthropic>=0.20"]
```

The `LLMInterface` protocol gains one method `rate_confidence(question, hypotheses, evidence) -> LLMResponse` that returns a JSON confidence vector. To preserve backward compatibility with v1.0's `MockLLM`, this method is added as a separate sibling protocol `RatingLLMInterface(LLMInterface, Protocol)`. Code paths that only need v1.0 capabilities continue to accept `LLMInterface`. The LLM-agent encoding requires `RatingLLMInterface`.

### 1.9 Tests

A `tests/test_llm_agent.py` file exercises:

- Pure-R behavior under recorded evidence (no live LLM).
- Renormalization correctness when LLM returns partial coverage.
- Unknown-hypothesis detection sets `ontology_inadequate`.
- Step-budget exhaustion ends Test cleanly.
- Confidence-threshold early stop.
- The full fiscal-vs-calendar toy problem produces the expected anomaly.

---

## Part 2: Trace Persistence

### 2.1 Goal

Save a `PipelineResult.trace` to disk so it can be replayed, diffed, scored, and shared. The format must be human-readable enough to grep and small enough that thousands of traces per day are practical.

### 2.2 Format: JSONL

One line per state in the trace. Each line is one JSON object. The first line carries a header with the encoding name and the problem spec. Header schema:

```json
{
  "kind": "header",
  "encoding": "llm_agent",
  "version": "1.1",
  "problem": { ... }
}
```

State-line schema:

```json
{
  "kind": "state",
  "step": 0,
  "ontology": { ... },
  "evidence": [ ... ],
  "beliefs": { ... },
  "metadata": { ... }
}
```

The revision policy R is not serialized. R is reconstructed at load time from the `encoding` field through a registry of named encodings. Each encoding registers a `(serialize, deserialize, revision_policy)` triple.

### 2.3 API

```python
# epistemic_pipeline/trace.py
def dump_trace(result: PipelineResult, path: str | Path) -> None: ...
def load_trace(path: str | Path) -> PipelineResult: ...

def register_encoding(
    name: str,
    serialize: Callable[[EpistemicState], dict],
    deserialize: Callable[[dict], EpistemicState],
    revision_policy: Callable[..., Any],
) -> None: ...
```

v1.1 ships four built-in encodings: `bayes`, `strips`, `mdp`, and `llm_agent`. They register themselves inside `trace.py` at import time. The `search` encoding is excluded because `SearchOperator` carries Python callables that cannot be serialized without naming a global symbol; v1.2 may add this through importlib-based callable resolution.

### 2.4 Limits

- Tool results must be JSON-serializable. v1.1 ships native support for `str`, `int`, `float`, `bool`, `list`, `dict`, and `None`. Custom result types require a `to_json` / `from_json` pair on the wrapping `ToolResult`.
- MDP value functions can grow large. v1.1 dumps them in full. v1.2 may add compaction.
- Search traces are not supported in v1.1 (see above).

### 2.5 Invariant

`load_trace(dump_trace(result))` returns a `PipelineResult` whose `trace` equals `result.trace` element-by-element under structural equality. This is asserted in `tests/test_trace.py` for each of the four supported encodings.

---

## Part 3: `epc` Command-Line Interface

### 3.1 Commands

`epc run` is deferred. Portable serialization of LLM and tool callables is out of scope for v1.1. Users build problems through the Python API, then run `epc replay`, `epc diff`, or `epc score` on the resulting JSONL trace.

```text
epc replay <trace.jsonl>
    Walk the evidence list and print beliefs after each
    observation. Anomalies are surfaced inline.

epc diff <a.jsonl> <b.jsonl>
    Print the first step where two traces diverge. Show both
    evidence and beliefs side-by-side.

epc score <trace.jsonl> [--truth <hypothesis>]
    Print the NormScore. With --truth, also reports reliability
    and calibration. Exit 2 on score failure.
```

### 3.2 Entry point

```toml
[project.scripts]
epc = "epistemic_pipeline.cli:main"
```

### 3.3 Replay output

```text
Step 0   B: {$2.1B:0.50, $2.4B:0.50}
Step 1   B: {$2.1B:0.85, $2.4B:0.15}   <- tool(lookup_financials)
Step 2   B: {$2.1B:0.30, $2.4B:0.70}   <- tool(lookup_recent_news)
Step 3   B: {$2.1B:0.62, $2.4B:0.38}   <- llm(confidence_vector)
Anomalies: oscillation
```

Each line shows the step number, the beliefs after that step, and the evidence item that caused the change. Anomalies are surfaced inline.

### 3.4 Diff output

```text
First divergence at step 2.

  a evidence:
    tool:lookup_recent_news=$2.1B
  b evidence:
    tool:lookup_recent_news=$2.4B

  a beliefs: {$2.1B:0.90, $2.4B:0.10}
  b beliefs: {$2.1B:0.30, $2.4B:0.70}

  Cause: different tool query at step 2.
```

### 3.5 Exit codes

- `0`: success.
- `1`: bad input (missing file, malformed JSON, unknown encoding).
- `2`: scoring failure (a norm fell below threshold, or contradictions are present in the trace).

Exit code 2 makes `epc score` directly usable in CI: a regression in trace quality fails the build.

### 3.6 Tests

`tests/test_cli.py` covers each command with a recorded fixture trace for each of the five encodings. CLI tests use `pytest`'s `capsys` and the `click.testing.CliRunner` pattern, but with `argparse` (no new dependency).

---

## Part 4: Use-Case Narrative

`research/USECASE-agent-debugging.md` is the first file in `research/` written from a single named persona's point of view. Existing research files are written as academic positioning. This file is written as a story about one engineer doing one task.

### 4.1 Persona

Maya, ML engineer at FakeCo. Owns the customer-support agent. On call this week.

### 4.2 Story arc

1. **Tuesday morning.** Customer-success Slack pings: a customer was quoted the wrong Q4 revenue figure in a support chat. The agent said $2.1B; the customer expected $2.4B.
2. **The old workflow.** Maya pulls the session log. Twelve thousand tokens of chain-of-thought. She scrolls. She guesses. Three hours later, she has a hypothesis: the agent confused fiscal Q4 with calendar Q4. She cannot prove it from the log.
3. **The new workflow.** Maya runs `epc replay sessions/2026-05-13-customer-bot.jsonl`. The trace shows belief flipped at step 3 because the agent's confidence vector dropped $2.4B from 0.70 to 0.20 after one re-read of `lookup_financials`. The oscillation anomaly was recorded. Maya has the proof in 90 seconds.
4. **The fix.** Maya adds a fiscal-vs-calendar disambiguation hypothesis to the agent's ontology. She re-runs `epc score` against the day's traces. Calibration recovers.
5. **The daily ritual.** Every agent run now writes a JSONL trace. A nightly job runs `epc score` over the day's traces. A Slack alert fires when reliability drops more than 10%. Maya checks the alert each morning. Most days, no alert. The day there is one, she has the trace in her terminal in under five minutes.

### 4.3 Construction rule

The story is written from a real captured trace, not from imagination. The exact step numbers, confidence values, and tool names in section 4.2 are placeholders until v1.1 ships an LLM-agent encoding and one trace has been recorded against the fiscal-vs-calendar toy problem. After that trace exists, the prose is updated to match.

This rule keeps the use case from being marketing copy. If the encoding cannot produce the trace, the story is wrong and must change.

---

## Out of Scope for v1.1

- Web UI. The CLI is sufficient.
- OpenTelemetry export. Scheduled for v1.2.
- Distributed trace store. Local files only.
- Streaming traces during execution. The trace is dumped at the end of the run.
- New norms beyond v1.0.
- Learning from traces (RLHF, distillation, replay buffers).
- Cross-trace clustering or anomaly detection across many runs.

---

## Invariants Preserved

- `EpistemicState` is immutable per pipeline step.
- R is pure: `R(B, e, O) -> B'` reads recorded evidence and returns new beliefs deterministically.
- E is append-only within a pipeline run.
- O is static within a pipeline run; only the meta layer can re-frame.
- The full state trace is preserved and now persistable.
- Existing tests (140 from v1.0) continue to pass.

---

## Acceptance Criteria

- `tests/test_llm_agent.py` exercises the fiscal-vs-calendar toy problem end-to-end with a `MockLLM` and produces the expected oscillation anomaly.
- `dump_trace` and `load_trace` round-trip every existing toy problem.
- `epc run`, `epc replay`, `epc diff`, and `epc score` each have at least one integration test against a recorded trace.
- `research/USECASE-agent-debugging.md` references step numbers from a captured trace stored in `research/traces/`.
- All v1.0 tests still pass.
- `uv run pyright` and `uv run ruff check` pass.
