# Use Case: Debugging an LLM Agent

This is a story about one engineer doing one task. It uses real output from `epc replay` against a real trace stored at `research/traces/2026-05-13-fakeco-q4.jsonl`. Step numbers and confidence values are not made up. If the encoding changes, this document must be regenerated from the new trace.

## Maya

Maya is an ML engineer at FakeCo. She maintains the customer-support agent. She is on call this week.

## Tuesday morning

A customer-success Slack thread pings her at 9:14am. A customer was quoted the wrong Q4 2024 revenue figure in a chat session the previous afternoon. The agent said **$2.1B**. The customer expected **$2.4B**. The press release matches the customer.

The agent has six tools. The session called two of them. Maya has the session log — twelve thousand tokens of LLM chain-of-thought interleaved with tool calls. She does not have a record of what the agent *believed* between calls.

## The old workflow

Maya re-runs the session in a notebook. She scrolls. She greps. She tries to reconstruct the agent's reasoning by reading the LLM's free-form text. Three hours later, she has a guess: the agent confused fiscal Q4 (FakeCo's fiscal year ends in June) with calendar Q4. She cannot prove this from the log. The log only shows what the agent *said*, not what the agent *believed*.

## The new workflow

Every agent run now writes a JSONL trace using `epistemic_pipeline.trace.dump_trace`. Maya runs:

```
epc replay sessions/2026-05-13-fakeco-q4.jsonl
```

She gets this:

```
Step 0   B: {$2.1B:0.50, $2.4B:0.50}
Step 1   B: {$2.1B:0.50, $2.4B:0.50}   <- llm(tool_choice={"tool": "lookup_financials", "args": {"company": "FakeCo"}})
Step 2   B: {$2.1B:0.50, $2.4B:0.50}   <- tool(lookup_financials={'period': 'Q4 FY2024', 'revenue': '$2.1B'})
Step 3   B: {$2.1B:0.85, $2.4B:0.15}   <- llm(confidence_vector={"$2.1B": 0.85, "$2.4B": 0.15})
Step 4   B: {$2.1B:0.85, $2.4B:0.15}   <- llm(tool_choice={"tool": "lookup_recent_news", "args": {"q": "FakeCo Q4"}})
Step 5   B: {$2.1B:0.85, $2.4B:0.15}   <- tool(lookup_recent_news={'headline': 'FakeCo reports $2.4B Q4'})
Step 6   B: {$2.4B:0.70, $2.1B:0.30}   <- llm(confidence_vector={"$2.1B": 0.3, "$2.4B": 0.7})
Step 7   B: {$2.4B:0.70, $2.1B:0.30}   <- llm(tool_choice={"tool": "lookup_financials", "args": {"company": "FakeCo"}})
Step 8   B: {$2.4B:0.70, $2.1B:0.30}   <- tool(lookup_financials={'period': 'Q4 FY2024', 'revenue': '$2.1B'})
Step 9   B: {$2.1B:0.80, $2.4B:0.20}   <- llm(confidence_vector={"$2.1B": 0.8, "$2.4B": 0.2})
Step 10  B: {$2.1B:0.80, $2.4B:0.20}   <- llm(tool_choice={"tool": "lookup_recent_news", "args": {"q": "FakeCo Q4"}})
Step 11  B: {$2.1B:0.80, $2.4B:0.20}   <- tool(lookup_recent_news={'headline': 'FakeCo reports $2.4B Q4'})
Step 12  B: {$2.4B:0.75, $2.1B:0.25}   <- llm(confidence_vector={"$2.1B": 0.25, "$2.4B": 0.75})
Anomalies: oscillation
```

Maya reads the trace top to bottom. She sees three things at a glance:

- Step 3, the top belief is **$2.1B at 0.85**. The agent has just read the fiscal-Q4 number and believes it.
- Step 6, the top belief flips to **$2.4B at 0.70**. The press release flipped it.
- Step 9, the top belief flips back to **$2.1B at 0.80**. The fiscal-Q4 number flipped it back.
- Step 12, the top belief flips again to **$2.4B at 0.75**. The press release flipped it again.

The trace recorded an `oscillation` anomaly. Maya now has proof — not a guess — that the agent could not decide between fiscal and calendar Q4. **Ninety seconds, not three hours.**

## The fix

Maya opens the agent's hypothesis set. It contains exactly two strings: `"$2.1B"` and `"$2.4B"`. There is no way for the agent to say "they are both right under different conventions." The ontology is inadequate for the question. The agent had to pick one, and the last tool call won.

She adds a third hypothesis: `"depends on FY-vs-CY"`. She updates the agent's prompt to flag fiscal-vs-calendar ambiguity when both numbers appear. She re-runs the session against the new agent and dumps a new trace.

```
epc diff sessions/2026-05-13-fakeco-q4.jsonl sessions/2026-05-14-fixed.jsonl
```

The first divergence is at step 6: instead of the old confidence vector flipping to $2.4B, the new agent assigns 0.50 to the new "depends" hypothesis. Maya now has a side-by-side diff showing exactly which step the fix changes.

## The daily ritual

Every agent run writes a JSONL trace under `sessions/`. A nightly job runs:

```
epc score sessions/<date>-*.jsonl --truth <expected>
```

across the day's labeled traces and reports four numbers per run: reliability, calibration, efficiency, justification. The job posts a Slack alert when the rolling mean of reliability drops more than 10% from the prior week. Most mornings, there is no alert. The morning there is, Maya opens the offending trace in her terminal within five minutes.

## What the trace gives you that a log does not

A log records what the agent **said**. A trace records what the agent **believed**, and which evidence produced each change. Two specific properties matter for audit work:

- **Per-observation belief replay.** `epc replay` walks the evidence list and re-applies the revision policy after each item. You see the belief flip on the line that caused it.
- **Anomaly tagging in the trace.** Oscillation, contradiction, and ontology-inadequacy are detected by the pipeline and written into the trace. You do not have to find them by inspection.

The trace file is JSONL. You can grep it. You can diff it. You can email it. It is not tied to any one observability vendor.

## When this approach falls down

The trace is only as good as the encoding's hypothesis set. If the agent answers a question whose right answer is not in `ontology.hypotheses` and never gets logged as `ontology_inadequate`, the trace will show high confidence in a wrong answer with no anomaly. That is the same failure mode as a logging system that does not log the right field — fixing it means adding the missing hypothesis, not abandoning the trace.

The trace also does not capture the *text* of the LLM's chain-of-thought. It captures the LLM's confidence vector and the tool calls. If the bug is in the chain-of-thought itself, you still need the raw transcript. The trace is complementary to logs, not a replacement.
