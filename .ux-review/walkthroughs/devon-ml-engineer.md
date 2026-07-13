# Walkthrough — Devon, ML engineer evaluating the formalism

Environment: fresh eyes on `c:/Users/billy/source/repos/epistemic-pipeline`, local docs site up at `http://127.0.0.1:8123/epistemic-pipeline/`. Clock starts now.

Every claim about what the code does below was checked by running it, not by reading a docstring and assuming — commands and outputs are inline.

---

## Step 1 — README, first 30 lines

**Friction: 1/5**

```
# Epistemic Pipeline

> **Status: v1.1 implemented.** Five reasoning frameworks run on the full
> pipeline ... A sixth encoding, worldview, revises beliefs over a growing
> corpus using Subjective Logic; its revision rule has landed, with
> source-credibility grounding still to come.

A formal system for making reasoning explicit and auditable. It tracks four
things: the vocabulary of a problem, what has been observed, how confident
the system is in each hypothesis, and the rule it uses to update that
confidence.

**Who is this for?** Researchers and engineers who build systems that
reason — and need to inspect, replay, and evaluate that reasoning after the
fact.
```

> Okay. Status banner up top, stated as a claim with a stated gap ("source-credibility grounding still to come") instead of buried in a changelog. That's the first good sign — most repos hide what's not done. "Who is this for" names me by function, not by buzzword. Fine. I'll read the API example before I believe any of it.

The flagship code sample is a `BayesProblem` — priors, likelihoods, observations, `run_pipeline`. Clean, typed, runs top to bottom as shown. But this is the *general* pipeline, not the thing I actually came for. The worldview app — the "auditable belief revision over your documents" pitch — gets two sentences in the README and no code sample at all. I have to go find it myself.

> Not a deal-breaker. It tells me the maintainer's actual center of gravity is the five-framework pipeline, and worldview is the newest, least-finished limb. Consistent with the status banner. But it means my "5-minute runnable example" clock doesn't stop here — the README doesn't hand me one for the thing I'm evaluating.

## Step 2 — Install and test

**Friction: 1/5**

```
$ uv run pytest -q
........................................................................ [ 23%]
........................................................................ [ 47%]
........................................................................ [ 71%]
........................................................................ [ 95%]
...............                                                          [100%]
303 passed in 2.55s
```

> 303 passing, 2.5 seconds. No flakiness, no "works on my machine" ceremony. Good.

```
$ uv run pyright src/epistemic_pipeline/worldview_app
0 errors, 0 warnings, 0 informations
```

> Clean typecheck on the module I care about. That's must-have #2 off the list before I've written a line.

## Step 3 — Find the worldview app (README didn't point me there)

**Friction: 2/5**

```
$ find src/epistemic_pipeline -iname "*worldview*"
src/epistemic_pipeline/encodings/worldview.py
src/epistemic_pipeline/worldview_app/
```

Two things named "worldview," not one. `encodings/worldview.py` is the pure `(O, E, B, R)` math — plugs into the same generic `run_pipeline` the Bayes example used. `worldview_app/` is a separate, higher-level layer: a SQLite-backed `Store` plus three ingestion functions (`author_claim`, `ingest_document`, `NoteIngester`). The module docstring in `ingest.py` is the best piece of documentation in the whole tree — it states the three ingestion paths and their differences in four lines, no fluff.

> Two "worldview" things that don't obviously nest into each other is a naming smell — I had to open both files to confirm `worldview_app` *uses* `encodings/worldview.py` rather than duplicating it. It does (imports `WorldviewBeliefs`, `aggregate_beliefs` etc. directly). Fine once confirmed, but the README gave me zero help disambiguating; I did this by reading source, which is what I do anyway, so — friction is on the person who *doesn't* default to reading source.

## Step 4 — the LLM seam: is it a real extension point or a maze?

**Friction: 2/5**

```python
class RatingLLMInterface(LLMInterface, Protocol):
    def pick_tool(self, question, tools, evidence_summary) -> LLMResponse: ...
    def rate_confidence(self, question, hypotheses, evidence_summary) -> LLMResponse: ...
```

> A `Protocol`, not an ABC. Good — I don't need to inherit from anything, I just need an object with the right method shapes. `ingest_document` only ever calls `.rate_confidence(...)`, so at runtime I don't even need `pick_tool`. That's the "obvious extension point" must-have — obvious once I've read `llm_interfaces.py` end to end, which took a few minutes because the docstring on the module ("mock for testing") undersells what's actually exported.

Then I check the export surface:

```python
# src/epistemic_pipeline/llm/__init__.py
__all__ = ["LLMEvidenceAdapter", "LLMInterface", "LLMResponse", "MockLLM",
           "MockRatingLLM", "RatingLLMInterface"]
```

`MockRatingLLM` is a first-class package export, not a test fixture I'd have to import from `tests/`. That matters — the intake notes call this "mocks presented as a feature," and I want to be precise about what's actually true: it's *labeled* as a mock (the name says so, the docstring says "Test implementation"), it just also happens to be the only implementation the library ships. That's an honest mock, not a disguised one. My deal-breaker is "mock-only integrations *presented as* features" — this doesn't cross that line. It is, however, a real gap: there is no first-party adapter for any actual LLM API, and nothing in the docs site walks through wiring one. I'd file that as a "would help," not a "you lied to me."

## Step 5 — write the 5-minute example myself

**Friction: 2/5** (the code was easy; the fact that I had to write it myself is the friction)

```python
import json, time
from epistemic_pipeline.llm import LLMResponse, MockRatingLLM
from epistemic_pipeline.worldview_app.ingest import ingest_document
from epistemic_pipeline.worldview_app.store import Store

doc = "Fiscal Q4 2024 revenue was $2.1B. The CFO resigned in March."
llm = MockRatingLLM(responses={}, confidence_ratings=[LLMResponse(
    content=json.dumps({
        "Fiscal Q4 2024 revenue was $2.1B.": 0.8,
        "The CFO resigned in March.": 0.6,
    }),
    confidence=0.9,
)])

store = Store(":memory:")
moved = ingest_document(store, llm, "What happened at the company?", doc,
                         ts=time.time(), seed=1, model_id="mock-1", origin="doc-1")
print(moved)
```

```
$ uv run python devon_try.py
{'Fiscal Q4 2024 revenue was $2.1B.': 0.65, 'The CFO resigned in March.': 0.55}
```

> It ran on the first try. No hidden setup, no config file, no server. An 0.8-confidence rating against a totally uninformed prior (`u=1`, base rate 0.5) lands at 0.65 — pulled toward the base rate, not just copied. That's exactly the "first document doesn't get to skip the math" behavior the honesty docs claim (more on that below) — and I didn't have to trust the docs, I watched it happen.

Time from `git clone` (already done) to this working, non-mocked-away result: under 10 minutes, almost all of it spent locating `worldview_app` and reading `llm_interfaces.py`, not writing code. If the README had one working `ingest_document` snippet — even five lines — this drops under 5. As shipped, it doesn't clear the persona's own 5-minute bar; it clears it only because I read source fast. **This is the single concrete thing I'd file:** a runnable worldview snippet in the README or a `examples/` file, mirroring what the Bayes example already gets.

## Step 6 — try to break determinism

**Friction: 1/5**

```python
def run():
    store = Store(":memory:")
    return ingest_document(store, llm, "q", doc, ts=100.0, seed=1,
                            model_id="mock-1", origin="doc-1")
r1, r2 = run(), run()
assert r1 == r2  # True
```

> Byte-identical across two independent runs with a fixed timestamp. This is the actual must-have — "same evidence, same order, same belief" — and it holds. I went looking for the usual leaks (wall-clock timestamps, dict-ordering, unseeded anything) and the API forces you to *supply* the timestamp; you can't accidentally let `time.time()` leak in unless you pass it yourself, which I did on the first try and immediately regretted for reproducibility, which tells me the API's default affordance is the trap, not the fix. Worth naming precisely: determinism is real, but it's opt-in by discipline (pass a fixed `ts`), not enforced by the type system. A caller who reflexively writes `ts=time.time()` — which is the natural first instinct, as I just proved on myself — gets a non-reproducible trace with no warning.

## Step 7 — the thing that actually made me stop and frown: "replay"

**Friction: 4/5**

My other must-have is replay — the README's own pitch is "inspect, replay, and evaluate." The CLI is `epc`:

```
$ uv run epc --help
usage: epc [-h] {replay,diff,score} ...
```

`replay`, `diff`, `score` all operate on JSONL trace files written by `run_pipeline` (the generic Bayes/STRIPS/MDP/llm_agent path). `trace.py` does register `"worldview"` as a known encoding name for that serializer — so on paper `epc replay` *can* read a worldview trace. But `worldview_app.Store` — the thing that actually implements "drop in a document, watch beliefs update" — never calls into `trace.py` and never writes JSONL. Its own docstring says so outright:

```python
# store.py
"""
Deliberate simplification: no `traces` table. Full-trace replay lives in
trace.py as JSONL files; the drift timeline comes from evidence_links.
Two concerns, not one table.
"""
```

So the one public replay artifact `epc` understands and the one product surface I'd actually use (`worldview_app`) don't connect. The only way to rebuild `B` from the stored evidence trail is:

```python
from epistemic_pipeline.worldview_app.ingest import _replay_beliefs  # pyright: ignore[reportPrivateUsage]
```

Underscore-prefixed. Not exported. The maintainer's own comment on it: *"Nothing inside this module calls this now (only tests and belief-replay audits do), so pyright flags it unused... Keep the suppress until then."* Even the project's own test file imports it with a `pyright: ignore[reportPrivateUsage]` and a comment admitting it's reaching into the module's own guts.

> This is the gap I actually came here to find, and I found it. Not a lie — nobody told me `epc replay` works on worldview traces, I inferred that from the CLI's stated `{replay,diff,score}` scope plus `trace.py` listing `worldview` as a supported encoding, and then went and checked whether anything produces that JSONL for it. Nothing does. The replay *mechanism* for the document-corpus product is real (I proved it in step 6 by hand) but it is a private function with a name that starts with an underscore, that the codebase's own comments say nothing calls in production. If I want to build a "why does this belief sit here" view — which is the entire value proposition — I'm building it on top of an API the maintainer has flagged, in writing, as not meant to be called from outside. That's a precise, filable gap, not a vague one.

## Step 8 — docs site: does it admit any of this?

**Friction: 1/5** (relief, not frustration)

`/worldview/` page, "Status" section:

> "The server and browser UI (#9) — right now the app is a library you drive from Python."

That's true, and I just confirmed it the hard way. Good — the docs don't oversell a UI that doesn't exist.

`/worldview/honesty/` page — this is the best thing in the repo. It states, with an open GitHub issue number attached to each:

1. All ratings come from **one rater** — settledness measures document count under one model, not rater-independent evidence (#35).
2. **Claim identity** is exact-text-match — a paraphrase is a new, unrelated claim; two contradictory claims don't detect their contradiction (#33, called out as a one-way door because the store is append-only).
3. **Calibration is unmeasured** — "settledness 0.8 → right 80% of the time" is a design goal, not a verified property (#34).
4. **Credibility weighting is disabled**, labeled as such, not silently defaulted to 1.0 without comment.
5. Ingested evidence is **one-sided by construction** — nothing forces a search for disconfirming documents.
6. A **faithfulness gate** was measured, then explicitly deferred, with the measurement written up.

> This is the artifact that decides whether I adopt or bail, more than any code sample. It's a page that names its own worst-case failure modes with issue numbers attached — a claim can be "highly settled and false if every document you read about it happens to be wrong," in the docs' own words. That is exactly the sentence a marketing page never writes and an honest engineering team does. It also directly names the thing I found in step 7 as unmeasured/unenforced territory, which lines up — nothing here contradicts what I found by hand, it's consistent front-to-back.

The math itself: `beliefs.md` names Subjective Logic explicitly, cites Škorić et al. (arXiv:1402.3319) for the evidence-scaling discount operator, and states the *reason* it uses that operator over the naive belief-mass form — the naive form has "a documented pathology (a trusted high-evidence source's evidence can vanish)" that evidence-scaling avoids. That's a real citation with a real justification, not a rule pulled out of the air. Must-have #3, satisfied, with a margin — most repos in this space don't explain why they picked the operator they picked, only that they did.

## Verdict

**Would I adopt it?** Not yet, and not because the math is wrong — because the product I'd actually use (`worldview_app`) has no runnable example, no documented replay path, and a private function standing in for what should be a public one. That's a "come back in a few PRs" verdict, not a "this is snake oil" verdict.

**Would I file issues?** Yes, three, precise and short:

1. `worldview_app` has no runnable example anywhere (README, docs site, or `examples/`) — the Bayes encoding gets one, the actual pitched product doesn't. Costs a new evaluator ~10 minutes of source-reading to build their own first example; costs a non-coder the whole evaluation.
2. `_replay_beliefs` is the only way to rebuild belief state from the store, and it's private, unexported, and flagged in its own docstring as called only by tests. Either publish it as `replay_beliefs` or document the intended pattern if there is a different one.
3. `epc replay/diff/score` lists `worldview` as a supported encoding in `trace.py`, but nothing in `worldview_app` writes the JSONL those commands read. Either wire `Store` to emit a trace `epc` can consume, or the docs should say plainly that `epc` doesn't apply to the document-corpus product — right now a reader has to reverse-engineer that gap themselves.

**Would I bail entirely?** No. The determinism claim held under an actual adversarial test, the citations are real, and — this is the part that actually moved me — the project's own honesty page pre-empted most of what I'd have written up as findings. A project that names its own failure modes with issue numbers is doing the opposite of the demoware pattern I came in expecting. I'd rather build on a repo that tells me where it's weak than one that hides it and makes me find out in production.

---

## Friction summary

| Step | Moment | Friction |
|---|---|---|
| 1 | README first 30 lines | 1/5 |
| 2 | Install + test + typecheck | 1/5 |
| 3 | Locating `worldview_app` (two things named "worldview") | 2/5 |
| 4 | Understanding the LLM extension point | 2/5 |
| 5 | Writing the first working example myself | 2/5 |
| 6 | Determinism check | 1/5 |
| 7 | Replay: private function, no `epc` path for this product | 4/5 |
| 8 | Docs site honesty page | 1/5 (relief) |

Nothing here hits 5/5 — nothing made me close the tab. Step 7 is the ceiling: a stated capability (replay) that exists in the code but not as a supported, public, or `epc`-reachable surface for the actual product being pitched.
