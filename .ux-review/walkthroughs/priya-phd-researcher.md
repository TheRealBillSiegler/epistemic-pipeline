# Walkthrough — Priya, PhD researcher with a reading corpus

Persona: `.ux-review/personas/priya-phd-researcher.md`. Interview (pre-contact expectations): `.ux-review/interviews/priya-phd-researcher.md`.

Method: I inhabit Priya's actual, stated capabilities — reads notebooks and copy-paste quickstarts, does not read source code, does not write a class that implements someone else's interface. Where the tool requires something past that line, I stop and record that as where the road ends for her, rather than pretending she pushes through it.

Entry point (assumption, flagged): a labmate who does PKM/Obsidian stuff sent her the GitHub link with "this might do the thing you keep doing by hand in a spreadsheet." She opens the repo README first — that's the reflex for any GitHub link — then finds the docs site linked from it.

---

## Step 1 — README, first screen

**What she saw** (`README.md`, lines 1–11):

> **Status: v1.1 implemented.** Five reasoning frameworks run on the full pipeline — Bayesian inference, STRIPS planning, forward-state search, MDP value iteration, and an LLM-agent loop — each with norm scoring, an adaptive meta-layer, JSONL trace persistence, and the `epc` CLI. A sixth encoding, worldview, revises beliefs over a growing corpus using Subjective Logic; its revision rule has landed, with source-credibility grounding still to come.
>
> ...**Who is this for?** Researchers and engineers who build systems that reason — and need to inspect, replay, and evaluate that reasoning after the fact.

**Inner monologue:** "Five reasoning frameworks... STRIPS planning... MDP value iteration. Okay, this reads like a CS systems paper, not a tool for reading papers. 'Researchers who build systems that reason' — I read papers, I don't build reasoning systems. The thing my labmate meant — 'worldview,' 'revises beliefs over a growing corpus' — is one clause, sixth in line, and it's not even done yet ('source-credibility grounding still to come'). I'll give it a few more minutes because the word 'auditable' hasn't shown up yet and that's the word I actually care about."

**Friction: 2/5.** Not a wall, but the README's opening frame is aimed at people who evaluate reasoning architectures, not people who want a result. She almost bounces here; she doesn't, because a trusted person sent the link.

---

## Step 2 — Docs site homepage

She scrolls the README further, finds the docs site link, and lands on `http://127.0.0.1:8123/epistemic-pipeline/`.

**What she saw:**

> A reasoning system that shows its work. It reads evidence, updates beliefs by explicit rules, and keeps a replayable record of every change. You can always ask: what did it believe, when, and why? — and get a checkable answer.
>
> **Where to go** — ... **The worldview app** — The first application: drop in documents, watch beliefs update, audit every move.

**Inner monologue:** "There it is — 'drop in documents, watch beliefs update, audit every move.' That's the sentence I was waiting for. Clicking that."

**Friction: 1/5.** This is the strongest moment in the whole walkthrough. The pitch lands exactly as advertised.

---

## Step 3 — The worldview app page

`worldview/index.md`. She reads about the three ingestion paths (inferred / user / derived) and the first-upload invariant.

**What she saw:**

> **Inferred** — an LLM reads a document and rates the claims in it, one confidence per claim. This is the default path: paste in an article, get back ratings.
>
> A brand-new install has an empty belief store — no claims, no history. Drop in one document, and the app still produces a meaningful result. There is no setup step and no minimum corpus size.

**Inner monologue:** "'Paste in an article, get back ratings' — that's exactly my Tuesday. And no minimum corpus, no setup step, so I don't need to front-load anything before I see it work. This is starting to feel like the must-have list I wrote before I opened the tab."

**Friction: 1/5.** Matches her stated need almost exactly. She's now invested and reading for the how, not the what.

---

## Step 4 — The status line

Same page, further down.

**What she saw:**

> **Status** — The belief store, the Subjective Logic encoding, and all three ingestion paths are built and tested. What's open:
>
> - **The server and browser UI** (#9) — right now the app is a library you drive from Python. A local server and a UI for the before/after panel, conflict surfacing, and the belief-drift timeline are not built yet.
> - **README and demo copy** (#10) — a quickstart with a seed corpus, one per ingestion path, is not written yet.

**Inner monologue:** "'A library you drive from Python' — okay, I can do that, I run notebooks. But 'the quickstart... is not written yet,' in their own words. That's the tool telling me, honestly, that the thing I'm about to go looking for doesn't exist yet. I respect that they said it plainly instead of making me discover it. But it also means I'm about to go hunting."

**Friction: 3/5.** Not a stop — she can drive a Python library — but the honest admission raises real doubt about how far this session goes. Worth noting: this candor is itself a point in the tool's favor for a persona this audit-literate; it's costing friction points on capability, not trust.

---

## Step 5 — Hunting for a runnable example

She checks every place a working code sample could plausibly live.

**README "Quick Start"** (`README.md`, lines 233–239):

```bash
uv pip install -e .        # install the package locally
uv run pytest              # run the test suite
uv run pyright             # run the type checker
```

**Inner monologue:** "This is a contributor quickstart — install editable, run the tests, run the type checker. Nothing about ingesting a document. Also, 'install the package locally' — locally from *what*? The README never says to clone the repo first; it just assumes I already have the source tree on disk. I do, because I cloned it to read it, but if I hadn't, this line doesn't get me there."

She checks the three worldview docs pages for code.

**What she found:** `worldview/index.md`, `worldview/store.md`, and `worldview/honesty.md` contain two Mermaid diagrams and zero Python code blocks between them. No import line, no function call, nowhere.

**Inner monologue:** "Three pages about exactly the feature I want, and not one line of code I could paste into a cell. There's a flowchart of the three ingestion paths but not the three lines of Python that would actually run one."

**Friction: 4/5.** This is the first real wall. Her stated must-have #1 — "a copy-paste quickstart that produces a visible result on the first try" — does not exist anywhere in the docs for the feature she came for.

---

## Step 6 — The guess that fails

Out of options in the docs, she does the one thing a notebook user does when there's no example: guess the import from the module name mentioned in the prose (`epistemic_pipeline.worldview_app`) and see what happens.

```python
from epistemic_pipeline.worldview_app import Store
```

```text
ImportError: cannot import name 'Store' from 'epistemic_pipeline.worldview_app'
(...\src\epistemic_pipeline\worldview_app\__init__.py)
```

**Inner monologue:** "An ImportError with a file path in it. I don't know if `Store` lives somewhere else in this package or if I spelled something wrong. This is exactly the kind of error message I'd screenshot and paste into a chat window, not one I'd debug by opening the package and reading its `__init__.py` — that's reading source, and reading source isn't what I do."

This is where a stranger following only the documented surface stops. (For the record, since this review needs to be precise about where the tool's real capability ends versus where Priya's personal ceiling ends: the working import is `from epistemic_pipeline.worldview_app.store import Store` plus `from epistemic_pipeline.worldview_app.ingest import ingest_document, author_claim` — findable by opening `src/epistemic_pipeline/worldview_app/`, or by reading `tests/worldview_app/test_ingest.py`, which is the one place in the repository a complete, correct call sequence exists. Both are source. Neither is a thing this persona does.)

**Friction: 4/5.** A wall she cannot see past without doing something she's explicitly told us she doesn't do.

---

## Step 7 — What she'd hit next, if she got past Step 6

I checked this so the finding is grounded, not speculative — it's the honest answer to "and then what," even though Priya herself doesn't get here.

A correct call sequence runs cleanly:

```python
from epistemic_pipeline.worldview_app.store import Store
from epistemic_pipeline.worldview_app.ingest import ingest_document
from epistemic_pipeline.llm.llm_interfaces import MockRatingLLM, LLMResponse
import json

s = Store(":memory:")
llm = MockRatingLLM({}, confidence_ratings=[
    LLMResponse(json.dumps({"GLP-1 drugs reduce cardiovascular risk": 0.8}), 1.0)
])
result = ingest_document(s, llm, "does this paper support the claim",
                          "a fake paper", ts=1.0, seed=0, model_id="mock", origin="paper1")
```

This works — `uv run pytest` passes, 303 tests, and the hand-built script above ran clean. But `MockRatingLLM` is exactly what its name says: canned responses supplied at construction time, built for the test suite. It does not call any real language model. To rate an actual paper, Priya would need to write a class that implements `RatingLLMInterface.rate_confidence(question, hypotheses, evidence_summary)` — calling a real API and returning JSON in the exact shape the pipeline expects.

**Inner monologue (hypothetical, if she'd gotten this far):** "So the 'paste in an article, get back ratings' path — the one the docs called the default — needs me to write the part that does the actual rating. That's the adapter class. That's the thing I said in my own notes I won't do on a Tuesday night."

**Friction: 5/5.** This is her stated deal-breaker, verified against the actual code, not assumed from the docs' silence. `MockRatingLLM` is the *only* implementation of the rating interface that ships. There is no configure-with-an-API-key path.

---

## Step 8 — The citation check

Even setting the LLM question aside, she'd want to know whether a rated claim gives her something footnote-shaped.

**What exists:** `ingest_document` takes an `origin` argument (a URL, DOI, or note path), and `provenance.canonicalize_origin` explicitly normalizes DOI and arXiv prefixes and strips tracking parameters — so the plumbing for "this claim traces back to that source" is real and reasonably well thought through. A claim's evidence history (`Store.history(claim_id)`) is queryable and, per the docs, is literally the drift timeline.

**What's missing:** nothing in the codebase produces a citation string, a BibTeX entry, or anything Zotero-shaped. The "citation" is a raw `origin` string she'd have to have supplied herself, and getting it back out means a SQL-shaped call (`store.history(...)`), not an export button or a formatted string.

**Inner monologue:** "The bones are here — it does keep the source, and it does dedupe re-imports of the same DOI, which is more thought than I expected. But 'trace back to a DOI' and 'give me a footnote' are still two different tools apart. I'd be writing the last mile myself."

**Friction: 4/5.** Partial credit — closer to satisfying her must-have than the LLM gap is, but still short, and still Python-shaped rather than output-shaped.

---

## Where the road ends

For Priya specifically — copy-paste-quickstart user, no source reading, no interface implementation — the road ends at **Step 6**: an `ImportError` on the only import she could plausibly guess from the prose, for a feature the docs themselves admit has no quickstart yet (#10) and no UI yet (#9). She does not reach the LLM-adapter wall (Step 7) or the citation gap (Step 8) *by her own hand* — she stops before them. I traced those further because the review needs to know whether persevering would have paid off. It would not have: even a more stubborn version of Priya who found the right imports hits a harder wall two steps later, one that exactly matches the deal-breaker she named before she ever opened the tool.

**Time to abandonment:** under her own 30-minute budget — realistically 10–15 minutes from landing on the README to the failed import, because the docs site (Step 2–4) is good enough to keep her reading past the CS-systems framing of the README.

**What would change the outcome, concretely (for #9/#10):**

1. One runnable code block on `worldview/index.md` — the exact three-line `Store` / `ingest_document` / `author_claim` sequence, with real import paths. This alone clears Steps 5–6 entirely.
2. A demo corpus (a handful of short documents plus a rated question) that runs with the *mock* LLM out of the box, explicitly labeled as a demo — so "does the flow work at all" is answered before "do I trust a real rating."
3. A stated, upfront answer to "what do I use instead of `MockRatingLLM` for a real paper" — even if the honest answer today is "nothing ships; here is the five-line protocol to implement if you want to wire in a provider" — said once, early, instead of discovered by hitting the mock and wondering why the rating never changes. Saying it early lets a user self-select out in two minutes instead of thirty.
4. Something citation-shaped on top of `origin` / `history()` — even a `store.citation(claim_id) -> list[str]` that returns the recorded origins would close most of the gap in Step 8.

None of this requires the server/UI in #9 to exist first. All four are documentation and small library surface, gated only on #10.
