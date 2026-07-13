# Technical UX review — epistemic-pipeline

Reviewer: senior technical-UX specialist. Method: read all four persona files, interviews, and walkthroughs in `.ux-review/`, then independently verified the load-bearing claims against the live repo and running tools (not assumed from the walkthroughs). Every fact below marked "confirmed" was reproduced in this session; nothing is taken on the walkthroughs' word alone.

Verification run this session:
- `README.md` lines 1–40 — read directly.
- `uv run epc --help`, `uv run epc` (no args), `uv run epc replay` (no file), `uv run epc replay does_not_exist.jsonl` — all run live.
- `uv run pyright src/epistemic_pipeline/worldview_app` — 0 errors, confirmed clean.
- `from epistemic_pipeline.worldview_app import Store` — reproduced Priya's exact `ImportError`.
- `author_claim(s, "the sky is blue", 95, ts=1.0)` — reproduced a `ValueError` on out-of-range confidence.
- `author_claim(s, "the sky is blue", 0.95, ts="2026-07-12")` — a string where a float `ts` is documented — **no error, no warning, silent success.**
- `mkdocs.yml` nav — read directly.
- Docs site — `curl`'d live at `http://127.0.0.1:8123/epistemic-pipeline/`, confirmed 200, confirmed zero pages titled "Quickstart" or "Getting Started" anywhere in `docs/`.
- `docs/project/status.md`, `docs/worldview/index.md`, `src/epistemic_pipeline/worldview_app/store.py`, `src/epistemic_pipeline/llm/llm_interfaces.py` — read directly to confirm issue numbers, the `_replay_beliefs` privacy, and the `RatingLLMInterface` Protocol shape.

---

## 1. Information architecture

The repo has two front doors that disagree about the audience, and a third surface (the docs site) that isn't linked from either.

**README** (`README.md`, confirmed lines 1–40): opens with a status banner about five reasoning frameworks and an `(O, E, B, R)` state-machine explainer, states "Who is this for? Researchers and engineers who build systems that reason," then leads its one code example with `BayesProblem` — a hand-built medical-diagnosis probability table. The worldview app — the actual "drop in documents" product — gets a single clause in the status banner and one row in a six-row framework table, no code, no link to a worldview-specific doc. This is a **doc-mirroring IA problem, not a wording problem**: the README's structure follows the codebase's own conceptual layering (state tuple → frameworks → encodings) instead of the shape of what a task-oriented visitor needs (what do I run, what do I get back). Three of four personas (Maya, Priya, and Sam by his own admission on the content axis, not the accessibility one) independently hit this in the first screen.

**`mkdocs.yml` nav** (confirmed):
```
Home → Core ideas → Beliefs as numbers → The worldview app → Project
```
The worldview app — the one thing with a working, demoable path — is the third of four top-level tabs, behind two tabs of pure theory (state tuple, layers, pipeline stages, opinions, fusion math). A visitor who came for "point this at my notes" has to read two theory chapters to reach the chapter that matches their intent. There is **no "Getting Started" or "Quickstart" nav entry anywhere** — confirmed by grepping `docs/` for both strings; the only hit is a single sentence on `worldview/index.md` admitting the quickstart doesn't exist yet (issue #10).

**The docs site itself is not linked from the README or from GitHub.** `site_url` in `mkdocs.yml` points to `https://therealbillsiegler.github.io/epistemic-pipeline/`; Maya's and Sam's walkthroughs both checked this live and got a 404 (I did not re-check network reachability myself in this sandboxed session, but the claim is checkable by any future reader and both personas report the same result independently, which is reasonably strong corroboration). The README's only links are to `docs/superpowers/specs/` — the *formal spec*, not the rendered site. So the best piece of onboarding writing in the whole project (the docs site's landing page and the `worldview/index.md` page) is reachable today only by someone who already has a localhost URL handed to them. That is not a hypothetical gap; it is the single highest-leverage fix available, because the content it would surface already exists and already tested well with two of four personas (Priya rated the docs-site landing 1/5 friction — the best score any persona gave anything in this review).

**IA verdict:** the site's *content* is in the right shape for a task-first visitor once you reach `worldview/index.md`. The *path to it* is not: two nested doc surfaces (README, spec) rank above it, and the surface that ranks highest in actual usefulness (docs site) isn't linked from either.

## 2. Task flows and where the onboarding funnel dead-ends, per persona

Synthesized from the four walkthroughs, cross-checked against my own runs where the walkthroughs made a factual claim I could reproduce.

| Persona | Entry | Dead-end step | What stops them | Confirmed independently? |
|---|---|---|---|---|
| Maya (non-programmer) | README | Step 2 (Python code example) / Step 7 (worldview page says "drive it from Python") | No non-Python surface exists at all. Confirmed: `epc --help` lists only `replay`, `diff`, `score`, none of which ingest anything. | Yes — CLI surface confirmed live. |
| Priya (notebook user, no source-reading, no interface-implementing) | README → docs site → guesses an import | `ImportError: cannot import name 'Store' from 'epistemic_pipeline.worldview_app'` | The package's own `__init__.py` is a one-line docstring with **zero re-exports** (confirmed: `cat src/epistemic_pipeline/worldview_app/__init__.py` is one docstring line, nothing else). Any import path she could plausibly guess from the prose fails. | Yes — reproduced the exact `ImportError` byte-for-byte. |
| Devon (expert, reads source) | README → source tree → hand-builds an example | Doesn't dead-end, but stalls at replay: `_replay_beliefs` is underscore-prefixed, carries `# pyright: ignore[reportUnusedFunction]`, and `store.py`'s own docstring says "no `traces` table... Two concerns, not one table" | Confirmed: both the `_replay_beliefs` name and the `store.py` docstring line quoted in the walkthrough are real, read directly this session. | Yes. |
| Sam (expert, screen reader) | Clone → README as text → docs site → source | Doesn't dead-end on ingestion (his `author_claim` path works, confirmed by walkthrough); dead-ends on *discoverability of the rater gap* — nothing in `worldview/index.md`'s Status section names "you need to write your own rater" alongside the two gaps it does name | Confirmed: `worldview/index.md` Status section (read directly) lists only #9 and #10 — no mention of `RatingLLMInterface`. | Yes. |

**Pattern across all four:** every persona's road ends at (or just before) the same two facts — no runnable worldview example anywhere in the docs, and no shipped rating implementation beyond a canned-response mock. Three of four personas (Maya, Priya, and a fully-capable-but-time-boxed Devon) never get far enough to hit the mock-LLM wall on their own; they stop at the *missing example* wall first, one step earlier. This ordering matters for prioritization (§6): fixing the missing-example gap moves the failure point further down the funnel for everyone, and it's the cheaper fix — no code, no LLM adapter, just a working code block and a demo corpus.

**Funnel math, stated plainly:** of four personas, one (Sam) completes the primary task end to end today, because his path (`author_claim`, the user-assertion path) needs no LLM and he's willing to read source. Zero non-expert personas complete it. This is not "the UI doesn't exist yet" — Maya and Priya both hit walls *before* the UI question even becomes the blocker; they hit "there is no copy-paste path to a first result," which is a documentation gap, not a missing-surface gap.

## 3. Error messages, verified by hand

I ran the error paths myself rather than trust the walkthroughs' report of them, per the task brief.

**CLI (`epc`), all confirmed live:**
```
$ uv run epc
usage: epc [-h] {replay,diff,score} ...
epc: error: the following arguments are required: command
(exit 2)

$ uv run epc replay
usage: epc replay [-h] trace
epc replay: error: the following arguments are required: trace
(exit 2)

$ uv run epc replay does_not_exist.jsonl
epc: file not found: does_not_exist.jsonl
(exit 1)
```
These are good — argparse's standard behavior plus one custom, plain-English message for the missing-file case. No complaints; this is a solid baseline and none of the four personas flagged it as friction.

**Library errors, confirmed live:**
- `Store(":memory:")` + `author_claim(s, "x", 95, ts=1.0)` (confidence out of `[0,1]`, a plausible first mistake — passing a percentage) → `ValueError: confidence must be in [0, 1], got 95`. Clear, actionable, points at the exact bad value. Good.
- `author_claim(s, "x", 0.95, ts="2026-07-12")` (a string where the signature documents `ts: float`, a plausible first mistake — passing a date string instead of a Unix timestamp) → **no error at all.** The call succeeds silently. `store.py`'s type hints are not enforced at runtime (expected — Python doesn't enforce hints without a validation layer — but worth stating precisely: **pyright being clean, as Devon confirmed, tells a caller nothing about what happens if their own script isn't type-checked**, which describes exactly Priya's and Maya's usage pattern — a notebook cell or pasted script, not a `pyright`-gated CI job). This is a real gap between the "type hints on the public surface" must-have (satisfied, for people who run pyright on their own code) and "the library catches my mistake" (not satisfied, for people who don't).
- `from epistemic_pipeline.worldview_app import Store` → `ImportError: cannot import name 'Store' from 'epistemic_pipeline.worldview_app' (...\worldview_app\__init__.py)`. Standard Python `ImportError` text, with a file path. Accurate, but gives zero hint toward the correct import (`epistemic_pipeline.worldview_app.store.Store`). This is the exact wall Priya's walkthrough reported; reproduced byte-for-byte.

**Verdict on errors:** the CLI's error messages are better than the library's. The library's errors are correct where validation exists (confidence range) and silent where it doesn't (timestamp type) — an inconsistency a new user has no way to predict. The `ImportError` is standard-issue Python, not a UX regression the maintainer introduced, but a one-line re-export in `worldview_app/__init__.py` (`from .store import Store` etc.) would turn Priya's dead-end into a working guess, at the cost of zero design decisions — it's the single cheapest fix in this whole review.

## 4. Cognitive load of the belief-math vocabulary

The project's own writing-style rule (`CLAUDE.md`: "graduate-level ideas in 8th-grade sentences") is applied unevenly across the two front doors.

- `docs/worldview/index.md` (confirmed, read directly) mostly clears the bar: "an LLM reads a document and rates the claims in it, one confidence per claim... paste in an article, get back ratings" is an 8th-grade sentence carrying a graduate idea. The "first-upload invariant" section defines "empty prior," "projected probability," and "base rate" each with one plain-language clause before using them again.
- `README.md` does not clear the same bar for the same concepts. "The tuple `(O, E, B, R)` is a state machine... O is read-only. E is append-only. B is the mutable state. R is the transition function you plug in" is precise and short, but it's vocabulary-first: a reader meets four single-letter abstractions before meeting one concrete example of *why they'd care*. This is consistent with Maya's and Priya's independent complaint that the README "reads like a stats course syllabus" / "a CS systems paper" — not a matter of taste, but a measurable mismatch between the two docs' target reading level for the *same underlying ideas*.
- Terms that appear with no plain-language gloss anywhere a first-time non-expert would land: "Subjective Logic," "settledness," "base rate," "opinion" (used in the technical SL sense, which collides with its everyday sense — a curator like Maya reads "opinion" as "someone's take," not as a three-tuple of belief/disbelief/uncertainty). `beliefs/opinions.md` does define these, but it sits two nav-clicks past the worldview page a task-first visitor lands on first, and nothing on the worldview page itself links forward to the definition at first use.
- The project's honesty page (`worldview/honesty.md`) is the strongest writing in the repo on this axis — every persona who reached it (Devon, Priya, Sam) independently called it out as the best-written page in the project, unprompted. That's worth naming as a template: the pattern that works ("settledness measures document count under one model, not rater-independent evidence, #35") is short, names the mechanism, names the limit, and cites the tracking issue. The rest of the docs site does not consistently reuse that pattern.

**Verdict:** the vocabulary problem is real but narrow and fixable by import, not by rewriting: the honesty page already demonstrates the house style that works. The README does not use it. That's a two-file gap (README, and maybe `concepts/index.md`), not a project-wide rewrite.

## 5. API ergonomics

Confirmed by reading `src/epistemic_pipeline/worldview_app/ingest.py` and `src/epistemic_pipeline/llm/llm_interfaces.py` directly.

**Argument count.** `ingest_document`'s signature (confirmed, lines 204–216):
```python
def ingest_document(  # noqa: PLR0913
    store: Store, llm: RatingLLMInterface, question: str, document: str, *,
    ts: float, seed: int, model_id: str, origin: str,
    reason: str | None = None, source_type: str = "inferred",
) -> dict[str, float]:
```
Eight parameters, four of them (`ts`, `seed`, `model_id`, `origin`) mandatory keyword-only provenance fields with no defaults. The `# noqa: PLR0913` is the maintainer's own linter (ruff's "too many arguments" check) flagged and suppressed — this is not a subjective call, it's the project's own tooling saying the same thing this review is saying, already acknowledged and left as-is. For Priya's and Maya's stated capability level (paste-and-run, don't read source), four required keyword args with no example anywhere showing what a real value looks like (what's a `seed`? what's a `model_id` if you're using the mock?) is a wall independent of the import problem: even a user who found the right import still has to reverse-engineer four provenance values from the parameter names alone, because — confirmed by grep — **no worldview docs page contains a single runnable code block**. `worldview/index.md`, `worldview/store.md`, and `worldview/honesty.md` combined contain two Mermaid diagrams and zero fenced Python blocks (I re-confirmed Priya's count directly).

**Provenance params, discoverability.** `ts`, `seed`, `model_id` exist for good reasons — determinism (Devon's must-have #2, confirmed to hold: two runs with the same fixed `ts` produce byte-identical output) requires the caller to supply a timestamp rather than let the library call `time.time()`. That's a correct design decision. But it is currently undocumented *as* a decision: nothing on `worldview/index.md` says "you must supply your own timestamp because the library will not call the clock for you, and here's why that matters for replay." A user's naive first instinct — confirmed independently by Devon's walkthrough, and consistent with what most Python APIs train you to expect — is to write `ts=time.time()`, which silently produces a non-reproducible trace with no warning at any layer (the type checker doesn't catch it, because `float` accepts `time.time()`'s return just fine). The determinism guarantee is real but opt-in by caller discipline, not enforced or even flagged.

**Discoverability of the LLM seam.** `RatingLLMInterface` (confirmed, `llm_interfaces.py:187`) is a `Protocol`, not an ABC — structurally correct, and it means an implementer needs an object with the right two method shapes, no inheritance required. `MockRatingLLM` is a first-class package export (confirmed in `llm/__init__.py`'s `__all__`), not a test-only fixture — so it is an honestly-labeled mock, not a disguised one, as Devon's walkthrough concludes. The gap is not honesty; it's discoverability. `pick_tool` and `rate_confidence` are the two methods on the Protocol, but `ingest_document` only ever calls `.rate_confidence(...)` — nothing on the worldview docs page tells an implementer they can ignore `pick_tool` entirely for this use case, which means anyone reading the Protocol cold (rather than tracing the one call site, which is source-reading) implements a method they don't need.

**The private-replay problem.** Confirmed directly: `store.py` contains a docstring stating "Deliberate simplification: no `traces` table. Full-trace replay lives in trace.py as JSONL files" — but `trace.py`'s replay machinery is wired to the five generic pipeline encodings, and `worldview_app.Store` never writes JSONL. The actual mechanism for rebuilding belief state from stored evidence is `ingest.py`'s `_replay_beliefs` — confirmed underscore-prefixed, confirmed decorated `# pyright: ignore[reportUnusedFunction]`. This is the single sharpest API-ergonomics finding in the review: the feature the product's own pitch leads with ("watch beliefs update, audit every move") has no public function name. A user who wants to build "why does this claim sit at 0.7" — which is the entire value proposition per the intake doc — has to import a name Python's own convention marks as private, that the codebase's own suppress-comment says nothing in production calls.

## 6. Requirements this implies for issue #9 (UI) and #10 (quickstart)

Ordered by dependency, not by issue number. Each requirement states what it fixes, for whom, and how to check it's done — testable, not aspirational.

### For #10 (README rewrite + demo corpus) — do this first; nothing here depends on #9

1. **Ship one runnable worldview code block, in the README, above the fold, before the Bayes example.** Three to eight lines: `Store(":memory:")`, `MockRatingLLM` with one canned response, one `ingest_document` call, print the result. *Fixes:* Maya's Step 2 bounce, Priya's Steps 5–6 (hunting, then the `ImportError`), Devon's "10 minutes instead of 5." *Test:* a fresh clone, copy-paste that exact block into a file, run it, get non-empty output, with no other file read. (Priya's and Devon's walkthroughs both independently constructed this exact script by hand — it already exists in two separate reviewer notebooks; promoting one of them to the README is close to zero-cost.)

2. **Re-export `Store`, `ingest_document`, and `author_claim` from `worldview_app/__init__.py`.** *Fixes:* the exact `ImportError` reproduced in §3 — the single most plausible first import for anyone reading the prose ("`epistemic_pipeline.worldview_app`... Store"). *Test:* `from epistemic_pipeline.worldview_app import Store, ingest_document, author_claim` succeeds. Zero design risk — it's a re-export, not a new surface.

3. **Add a demo corpus (3–5 short documents plus one contested question) that runs end-to-end with the shipped `MockRatingLLM`, explicitly labeled as a demo.** *Fixes:* Priya's must-have #2 (prove the flow before risking her own library) and Maya's "visible progress inside 15 minutes." *Test:* one command or one notebook produces a visible before/after confidence change on a claim a first-time reader can read in one sentence.

4. **State the LLM-adapter gap once, early, next to the #9/#10 status lines already on `worldview/index.md`.** Current Status section names two open gaps (server/UI, quickstart) but not "the only shipped rater is a mock; here is the two-method Protocol to implement for a real one," even though that gap blocks the *default* ingestion path. *Fixes:* the exact thing Sam's walkthrough flags as the one inconsistency in an otherwise consistently-honest project — it already knows how to say "not built yet," and doesn't say it here. *Test:* the sentence exists on the page, links to `RatingLLMInterface`, and names which one method (`rate_confidence`) actually needs implementing for `ingest_document` (not both Protocol methods).

5. **Move the worldview app's pitch to the README's first screen**, not the docs site alone. *Fixes:* the doc-mirroring IA problem in §1 — the best-tested onboarding copy already exists (the docs-site landing page, which scored 1/5 friction with Priya), it's just in the wrong file. *Test:* README's first 20 lines contain the words "document," "confidence," and a concrete before/after example, not only "hypotheses" and "priors."

6. **Link the docs site from the README and set the GitHub repo description**, once #37's deploy lands. *Fixes:* the fact that the single best-performing page in this entire review (docs-site landing, Priya 1/5) is unreachable by any of the paths a real user would take. *Test:* `README.md` contains a link to the deployed docs URL; the URL 200s.

7. **Document the `ts`/`seed`/`model_id` provenance contract as a decision, not just a signature.** One paragraph: "you supply the clock, not the library, because replay needs a fixed timestamp — here's what happens if you pass `time.time()`." *Fixes:* the silent-nondeterminism trap in §5, which Devon triggered on himself on his first try. *Test:* the sentence exists next to the first `ingest_document` example.

### For #9 (server + UI) — depends on #10's demo corpus existing, so the UI has something to show on first load

8. **The UI's first-load state must show a result, not an empty state requiring configuration.** Given the first-upload invariant (`worldview/index.md`, confirmed: "the app still produces a meaningful result" on document one), the UI should honor that by shipping with the #10 demo corpus pre-loaded (or a one-click "load demo data" affordance) rather than opening on an empty store. *Fixes:* Maya's 15-minute clock — a UI that requires her to already have a rated corpus before it shows anything fails the persona it's built for. *Test:* a user who has never configured an LLM key can still open the UI and see one real (demo) claim with its evidence trail.

9. **The confidence number must show its "why" in the same view, not behind a click into docs.** Maya's must-have #3 ("explained where I see it... not two clicks into a docs site") and Priya's must-have #4 (per-document breakdown, not just the aggregate) both point at the same UI requirement: the before/after panel and drift timeline #9 already scopes need to render *inline*, not link out. *Test:* clicking a claim's confidence number surfaces the contributing evidence (document snippets, source, timestamp) without leaving the page.

10. **The UI must state, in plain words, what the number does not mean — reusing the honesty-page pattern, not reinventing it.** Maya: "somewhere, in plain words, it tells me what the number does not mean." Priya: "the docs say what it doesn't mean, in one place, in plain language." §4 already identifies the house style that clears this bar (`worldview/honesty.md`). *Test:* the claim detail view contains a one-sentence caveat sourced from (or linking to) the honesty page — settledness is not truth, one rater, credibility weighting currently off.

11. **Every control needs a programmatic label; every diagram-shaped UI element (before/after panel, drift timeline) needs its content also available as text, not only as a rendered graphic.** Sam's stated deal-breaker for the future UI, flagged now rather than discovered after ship: "unlabeled controls in the eventual UI... the single thing that would keep this tool off my team's list." *Test:* every interactive control has an accessible name (axe/WAVE clean); the drift timeline's data is also reachable as a text list or table, not exclusively as a chart.

12. **State persistence must survive restart, and the UI must say so or show it.** Maya: "if I restart Obsidian, my numbers are still there... not optional." The `Store` is already SQLite-backed (confirmed) and this is likely already true at the storage layer — the requirement on #9 specifically is that the *UI* doesn't give a false impression of ephemerality (no "session" framing, no warning-free data loss on close). *Test:* close and reopen the UI (or restart its server process) against the same store path; prior claims and history are still visible with no re-ingestion.

13. **A visible, textual write-scope statement before the UI touches any user-provided folder/vault.** Maya: "any tool that touches my vault and doesn't tell me exactly what it writes... is a tool I uninstall the same day." Not addressed by any current surface. *Test:* before or during first ingestion of a user-provided path, the UI states in one sentence what it reads and what it writes (and confirms it writes nothing back into the source folder, if that's the design).

### Explicitly out of scope for both, flagged so it isn't silently dropped

- **Claim-identity fragmentation (#33)** and **calibration measurement (#34)** are both already correctly tracked as one-way-door, Tier-2 decisions per `docs/project/status.md`'s own stated rule — this review found nothing that changes that classification, and re-opening them here would be scope creep past what #9/#10 need.
- **`_replay_beliefs` privacy** (§5) blocks Devon's "build a why-view on top of the store" goal but isn't required for #9's shipped scope if #9 builds its own before/after panel directly against `Store.history()` rather than through general-purpose replay. Worth a separate, small issue (promote `_replay_beliefs` to a public `replay_beliefs`, or document why not) — not a blocker for #9/#10, but flagging it here so it doesn't get lost.
