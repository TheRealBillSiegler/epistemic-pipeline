# Walkthrough — Sam, blind developer, screen-reader user

Goal: read the docs site end-to-end with NVDA, then drive the CLI and the library from the terminal, and hit no information that exists only in a picture. No 15-minute clock — I'm evaluating a dev tool the way I'd evaluate any dependency for my team. Friction 1–5 (5 = would abandon / would not recommend on this point alone).

## Step 0 — how I'd actually get here

I clone the repo rather than browse GitHub in a tab, because a local checkout is faster to search with my own tools than a rendered web page is to navigate with a screen reader. `git clone`, then I read `README.md` as plain text first — a raw markdown file is close to the ideal medium for me: no CSS, no SVG, no JS-rendered anything, just characters in order.

**Friction: 1.** This step is a strength of being a developer, not a property of this project — worth saying up front so it doesn't get credited to the docs.

## Step 1 — README, read linearly

I read what Maya's review already quotes: the status badge, "a formal system for making reasoning explicit and auditable," the `(O, E, B, R)` table, then the Bayesian `API Example` with `BayesProblem`, hand-aligned `likelihoods` dict, `Observation(...)` calls.

**Friction: 1, where Maya logged a 5.** A Python code block is exactly my working medium — NVDA reads it character-for-character in a code font, indentation and all. The manual column-alignment in the likelihoods dict (extra spaces to line up the colons) is a sighted-only nicety that costs me nothing; NVDA collapses the whitespace and I hear the same key-value pairs either way. I don't share Maya's "this is the wrong audience" reaction to code — I *am* the audience for a page that shows me a class definition. My complaint about this section is orthogonal to accessibility: it's still true, independent of who's reading it, that the flagship example is Bayesian diagnosis, not the worldview app, and the worldview row in the frameworks table says "In progress" with no path in. That's a content gap, not a screen-reader gap — I'm noting it once and then judging the rest of this walkthrough on my own axis.

> *Inner monologue: nothing here excludes me. Whoever is excluded by this README, it isn't the guy who can read a Python dict.*

## Step 2 — Quick Start, and I actually run it

Unlike a non-programmer reviewer, I don't stop at reading these commands — I run them.

```
uv pip install -e .
uv run pytest
uv run pyright
```

**Friction: 1.** All three produce plain-text terminal output. `pytest`'s dot-per-test and final summary line read fine linearly; a long green wall of dots is mildly uninformative by ear (I can't "glance" at a bar the way a sighted dev glances at a progress indicator), but the pass/fail count at the end is exactly what I need and it's plain text, not a color-only signal. No complaint here — this is what "terminal-first tooling" buys for free.

`uv run epc replay trace.jsonl` and siblings require a trace file I don't have yet. Same gap Maya found (nothing in the README shows how to produce one from the worldview path) — I confirm it independently below, in Step 7.

## Step 3 — the docs site, landing page

Handed the link directly, same caveat Maya's review logged and that I re-confirm: `https://therealbillsiegler.github.io/epistemic-pipeline/` returns a 404 today (checked live), and nothing in the README or the GitHub repo page links to the local docs build. A real Sam, browsing cold, would never land here. I'm reviewing it anyway because it's clearly meant to be the front door eventually, and because it's the surface where the screen-reader-specific questions actually live — the README has almost no diagrams or math to test against.

I check the skip link first, because it's the first thing I'd press `Tab` into on any new site:

```html
<a href="#epistemic-pipeline" class="md-skip">Skip to content</a>
```

**Friction: 1.** Present, and it targets the real `h1` id, not a dead anchor. Landmark structure is clean too — `<nav aria-label="Header">`, `<nav aria-label="Tabs">`, `<nav aria-label="Navigation">`, two `<nav aria-label="Table of contents">` regions, `<nav aria-label="Footer">`. NVDA's landmark navigation (`D` key) gets a sensible, distinct set of regions on every page I checked. This is Material for MkDocs doing its job — genuinely no complaint.

## Step 4 — the diagrams

The landing page opens with a mermaid flowchart (`O`/`E`/`B`/`R` and how they connect). I go looking for what a screen reader actually gets from it.

The page source ships the diagram as literal mermaid syntax, rendered to an SVG entirely by client-side JavaScript:

```html
<pre class="mermaid"><code>flowchart LR
    subgraph state ["Epistemic state"]
    ...
```

I checked every diagram in the docs (seven pages use mermaid: the landing page, `concepts/pipeline.md`, `concepts/layers.md`, `worldview/index.md`, `worldview/store.md`, `beliefs/fusion.md`) for `accTitle` / `accDescr` — mermaid's own directives for giving a diagram an accessible name and description. Zero hits, on any of the seven. Left as-is, the rendered SVG carries whatever generic `aria-roledescription` mermaid.js assigns by default (something like "flowchart-v2") and no meaningful label — NVDA either announces a bare, contentless graphic or skips it entirely depending on how the SVG's role resolves in the accessibility tree. Either way, the picture itself tells me nothing.

**Friction: 2, not 5 — and here's the must-have check that actually matters.** My must-have was never "diagrams must be accessible objects" — it was "every diagram's content is *also* stated in prose." I read past each diagram to check, and on every single page, it is:

- `concepts/pipeline.md` — the six-stage flowchart is immediately followed by a table with one row per stage, in prose.
- `concepts/layers.md` — a denser diagram (five layers × four state slots, twelve labeled edges) is followed by five full paragraphs, one per layer, each restating exactly which slots that layer reads or writes and why — I checked this one edge by edge and every arrow in the diagram has a sentence match in the prose.
- `worldview/index.md` — the three-ingestion-paths diagram is restated as a three-item bullet list right above it.
- `worldview/store.md` — the four-table ER diagram is restated as one paragraph per table, in more detail than the diagram shows.
- `beliefs/fusion.md` — the two-tier fusion diagram is restated as a worked numeric example with the actual arithmetic.

So the diagrams are not accessible *as diagrams*, but the *information* reaches me every time, through prose that was clearly written to stand on its own rather than as alt text for a picture. That's the must-have satisfied by discipline, not by structure — nothing enforces it (no lint checks "every mermaid block has adjacent prose," it's just been true every time so far). I'm logging that as a process risk for whoever adds diagram eight, not a defect in what exists today.

> *Inner monologue: this is what I expected to fail, and it's the one thing that didn't. Someone here is actually writing for a reader, not captioning a picture for themselves after the fact.*

## Step 5 — the math

`beliefs/fusion.md` has the most math on the site: fusion formulas, then three worked numerical examples. Config check: `mkdocs.yml` wires `pymdownx.arithmatex` (generic mode) to MathJax's `tex-mml-chtml.js` bundle — the CHTML-plus-assistive-MathML output, not a LaTeX-to-PNG renderer. That's the correct choice: this bundle emits a hidden MathML tree alongside the visual rendering specifically so assistive tech has something to read, on by default, nothing extra to configure.

**Friction: 2, with a caveat I have to be honest about.** This is a plausible pass, not a confirmed one — I don't have NVDA running against a live Firefox session in this environment, so I checked the *configuration* (right choice, right bundle, no image fallback anywhere) but I did not hear a formula spoken. Real-world MathML support varies by NVDA version and by whether the user has the newer math-viewer support enabled, and I'd want to actually hear `u = W / (r + s + W)` before I'd call this fully verified. Flagging it as "configured correctly, unverified in practice" rather than either a pass or a fail.

## Step 6 — the admonitions, and the honesty page

Every "Honest status" warning box — the project's own name for the parts of itself it won't oversell — is a Material admonition. I check the actual markup on `concepts/pipeline.md`:

```html
<div class="admonition warning">
  <p class="admonition-title">Honest status: replay uses today's revision rule, not the one that made the trace</p>
  ...
</div>
```

**Friction: 4.** The title is a `<p>`, not an `<h2>`–`<h6>`. The wrapping `<div>` carries no ARIA role — not `role="note"`, not `role="doc-notice"`, nothing. Two concrete consequences for me:

1. `H`-key navigation and NVDA's Elements List (filtered to headings) skip every admonition entirely. Heading-to-heading skimming is how I triage a long docs page before deciding what to read closely — it's the accessibility-parallel of a sighted reader's eye jumping to bold text and colored boxes. On `worldview/honesty.md`, the six numbered "known walls" are real `###` headings (good, I find those fine) — but two of them end in a further "Honest status" admonition that sits *below* the heading, invisible to the same navigation mode that got me to the heading in the first place. I only find those boxes by reading the section start to finish, not by skimming.
2. No role means no audible framing. When I do read one linearly, NVDA reads the title text with the same inflection as a plain paragraph — no "warning," no "note," nothing distinguishing it from body text except word choice. A sighted reader gets an icon, a colored left border, and bold type telling them "this one's different, pay attention." I get identical prosody to the sentence before it.

This is the finding my interview predicted, and it lands on exactly the content this project would least want to lose: the honesty callouts are the feature that makes "auditable" more than a marketing word, and they're the one thing on the page styled to be *found first* — for a sighted skimmer. For a heading-first screen-reader skim, they're the easiest thing on the page to miss entirely.

**What it would cost to fix:** cheap, in two tiers. Zero-engineering-cost stopgap: nothing stops the existing convention (`!!! warning "Honest status: ..."`) from putting "Warning:" in the visible title text itself, so linear reading always announces it, without touching markup — that's a wording change, not a code change. The real fix is a small template override on the Material admonition partial: add `role="note"` (or DPUB-ARIA `role="doc-notice"`) to the wrapping `div`, or promote the title to a heading at the appropriate depth. That's a few lines in a theme override, not a redesign — Material supports partial template overrides for exactly this kind of thing.

> *Inner monologue: everything on this page is telling me the truth. I just have to already be reading the paragraph to hear it — the one navigation shortcut built for finding "the important part fast" walks right past the important part.*

## Step 7 — driving the library from the terminal

This is my actual primary goal, not a side check: get a real number on a real document, from Python, no browser.

I read `worldview/index.md`'s "Three ways a belief enters the store" and go to the source instead of a tutorial, because there isn't one — `src/epistemic_pipeline/worldview_app/ingest.py`, `store.py`, and the test files under `tests/worldview_app/`.

**The `author_claim` path works today, no LLM required.** `author_claim(store, "the sky is blue", 0.95, ts=1.0)` writes a claim and a concept directly — I can self-assert a claim and a confidence right now, in one function call, and it persists in the SQLite-backed `Store`. Friction here: **1.** This is the one worldview capability I can actually exercise end to end today, and it works exactly as documented.

**The `ingest_document` path — "an LLM reads a document and rates the claims" — needs a `RatingLLMInterface`.** The only implementation that ships is `MockRatingLLM` (`src/epistemic_pipeline/llm/llm_interfaces.py`), which returns pre-scripted canned responses you hand it in the constructor — useful for the test suite, useless for rating a document I actually care about. To get a real rating on a real document, I'd have to implement `RatingLLMInterface.rate_confidence` myself, wiring up whatever LLM I want to call.

**Friction: 3.** Not a wall the way it is for Maya — I can write that adapter, it's an evening's work for a backend developer, not a skill I lack. What costs me time specifically: nothing in `worldview/index.md`'s **Status** section names this gap. It lists two open items — the server/UI (#9) and README/demo copy (#10) — but not "even from Python, you need to write your own rater before this does anything with a real document." I only found that by reading `llm_interfaces.py` and the test fixtures, not by being told. For a sighted developer that's a five-minute `grep`. For me it's the same `grep`, run from the same terminal — genuinely no accessibility delta here, just a documentation gap that happens to land on the one path I, specifically, was trying to complete. I'm logging it because "primary goal end to end" means I don't get to stop at "found the function," I have to notice it doesn't do the thing without more work, same as anyone would.

> *Inner monologue: I can build the missing piece. I just want the status section to tell me it's missing before I go looking for it in the source, the same way it already tells me the UI is missing. It knows how to say "not built yet" — it says it twice already on this exact page.*

## Step 8 — the CLI, for completeness

`uv run epc --help` and its three subcommands (`replay`, `diff`, `score`) are plain argparse text — linear, well-formed, no complaints. **Friction: 1.** Confirmed independently of Maya's review: none of the three take a document, a note, or a folder; all three require a `trace.jsonl` that nothing in the worldview path currently produces a CLI command to generate. This matches what the source already told me in Step 7 — there is no `epc` surface for the worldview app at all, only for the five pipeline-encoding frameworks.

## Where the road ends for Sam

Not at a hard wall — that's the real difference from Maya's review. I can read the whole docs site (the diagrams don't block me, because the prose carries their content every time), the math is configured the accessible way, and the one piece of the primary goal that isn't finished (a real rater) is something I have the skill to build myself. What actually stops me from calling this "usable by a screen-reader-using developer" without qualification:

1. **The honesty admonitions are invisible to heading navigation.** This is the concrete, fixable defect in this review — a real accessibility bug, not a content gap, and it specifically hides the project's own signature feature from the one skimming strategy I default to.
2. **No accessibility statement anywhere** — not in the README, not on the docs site (checked both for "accessib," "screen reader," "WCAG," "a11y" — zero hits). Nothing tells a screen-reader user "we thought about you" or gives them a place to report exactly the kind of gap I found in Step 6. For a project this deliberate about stating its own limits out loud, that silence is out of character.
3. **The diagram-prose parity is a habit, not a rule.** Good today, unenforced, so it's one busy pull request away from breaking on diagram eight.

## Scorecard

| Step | What I was doing | Friction | Blocking? |
|---|---|---|---|
| 0 | Clone + read README as text | 1 | No |
| 1 | README top + Bayes example | 1 | No |
| 2 | Quick Start commands, actually run | 1 | No |
| 3 | Docs site landing, skip link, landmarks | 1 | No |
| 4 | Mermaid diagrams (7 pages, no accTitle, full prose parity) | 2 | No |
| 5 | MathJax config (accessible bundle, unverified live) | 2 | No |
| 6 | Admonition titles not headings, no ARIA role | 4 | Real bug, not blocking |
| 7 | `author_claim` (works) vs `ingest_document` (needs own rater, undocumented gap) | 1 / 3 | Partial |
| 8 | `epc` CLI, zero worldview commands | 1 | No (content gap, known) |

**Overall: I'd recommend this to my team with one specific bug filed and one specific documentation gap named** — not a rejection, not a clean pass. The docs are genuinely well-built for a screen-reader user in every place I expected them to fail (diagrams, math) and fail in the one place a sighted QA pass would never catch (heading semantics on styled callouts).

## What would change my answer

- Fix the admonition markup (role + heading semantics) — small, template-level, closes the one real accessibility bug I found.
- Add a one-line accessibility statement somewhere findable — even just "diagrams are captioned in prose; math uses accessible MathJax; file issues for anything that isn't" — costs a sentence, signals the project has actually thought about this class of user rather than passing by accident.
- Name the "you need your own rater" gap in `worldview/index.md`'s Status section, next to the two gaps already listed there — same honesty this project already applies to the UI and the README, extended to the one path a Python-literate user would actually try first.
- A lint or CI check that every `mermaid` fence has prose coverage nearby would turn today's good habit into a guarantee — lower priority than the other three, since nothing is broken yet.
