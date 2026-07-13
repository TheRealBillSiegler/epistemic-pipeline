# Walkthrough — Maya, Obsidian curator

Goal: point the tool at my documents, see a per-claim confidence with receipts. Judged on my own clock: 15 minutes, then I close the tab. Friction scale 1-5 (5 = would abandon here).

## Step 0 — how I'd actually get here

I heard "auditable belief revision over your documents" somewhere and went looking. That means GitHub first — that's where an open-source tool lives, and it's the only address I'd actually have.

`https://github.com/TheRealBillSiegler/epistemic-pipeline`

**Friction: 2.** The repo has no description and no topics on the GitHub page itself — just a bare file listing. Not a dealbreaker by itself, plenty of good tools have thin GitHub metadata. But it's the first small "nobody polished this for a stranger" signal.

> *Inner monologue: Okay, no tagline, no "for note-takers" badge, nothing. Let's see the README.*

## Step 1 — the README, top to bottom

First line: a status badge about "five reasoning frameworks," "norm scoring," "adaptive meta-layer," "JSONL trace persistence." Then: "A formal system for making reasoning explicit and auditable. It tracks four things: the vocabulary of a problem, what has been observed, how confident the system is in each hypothesis, and the rule it uses to update that confidence."

Then, in bold, the line that answers my question before I finish asking it:

> **Who is this for?** Researchers and engineers who build systems that reason — and need to inspect, replay, and evaluate that reasoning after the fact.

**Friction: 4.** That line is doing me a favor, honestly — it's telling me flat out I'm not the audience. But I came here because someone told me this does what I do by hand every night with a note and a confidence tag. Nothing in the first screen says "documents," "notes," or "vault." It says "hypotheses," "priors," "posterior." I scan for my words and don't find them.

> *Inner monologue: "Vocabulary of a problem." "Priors." This reads like a stats course syllabus. I want to know if I misheard the pitch, or if I'm three clicks from the actual thing.*

I keep scrolling in case the app is further down.

## Step 2 — the API Example

A code block. `BayesProblem`, `hypotheses=("flu", "cold", "covid")`, `likelihoods={...}`, `Observation(variable="fever", ...)`.

**Friction: 5 — this is where I'd close the tab on a bad day.** This is Python. I don't write Python. The example is a medical diagnosis toy problem with hand-written probability tables, which is precisely the kind of thing that tells me: *this tool wants you to author your own math model before it does anything.* That's the opposite of "drop in a document."

I don't quit yet only because the task said to check the whole surface. A version of me with a normal 15-minute budget stops here.

> *Inner monologue: If step one of using this is writing a dict of likelihoods by hand, we are nowhere near "point it at my vault." This is a different product than what I was told about.*

## Step 3 — searching the README for my use case

I search the page for "worldview" (the word that, per the intake notes, is supposed to be the document-facing app). It appears five times, always as one line in a table of six research frameworks: "Worldview | Tracking graded beliefs about claims as new documents arrive | ... | In progress." No section of its own. No example. No mention of Obsidian, notes, a vault, or a plugin anywhere in the file.

**Friction: 4.** The one feature that matches my goal is a single table row, status "in progress," with no path in from here.

## Step 4 — Quick Start

```bash
uv pip install -e .        # install the package locally
uv run pytest              # run the test suite
uv run pyright             # run the type checker
```

**Friction: 5.** `uv pip install -e .` assumes I have `uv`, a Python toolchain, and a cloned repo already. That's not "one command I can paste" — that's three, and the payoff of running them is a test suite passing, not a number on my screen. There is nothing here for someone who wants to see the tool work, only for someone who wants to verify the code is correct. I do not know if my computer even has `uv`. I do not know what "the type checker" is for.

The next block:

```bash
uv run epc replay trace.jsonl
uv run epc diff a.jsonl b.jsonl
uv run epc score trace.jsonl
```

These all take a `trace.jsonl` as a *given* — a file I'm supposed to already have from somewhere. Nothing tells me how to make one from my own notes.

> *Inner monologue: I paste the first line into a terminal for tools that promise "one command." This promises three, and none of them show me anything I'd recognize as the product. I would have stopped at Step 2. I'm continuing because I said I'd give it the full look.*

## Step 5 — spec links

Under the architecture section, the README points to `docs/superpowers/specs/` for the "current design." I click through out of thoroughness. It's a formal design document, dense, written for implementers.

**Friction: 5 (deal-breaker, confirmed).** "Any workflow that requires reading a spec" was on my list before I started. This confirms it. A tool whose own README defers the real explanation to a spec has told me who it's for, and it isn't me.

## Step 6 — the docs site (only reachable because the reviewer handed me the link)

Worth being honest about how I got here: `http://127.0.0.1:8123/epistemic-pipeline/` is a `127.0.0.1` address — a developer's own machine. Nothing on GitHub or in the README links to a public docs site, and a check of GitHub Pages for this repo returns 404 — there is no deployed site yet. The real Maya, browsing this repo cold, would never find this page. I'm only seeing it because it was handed to me directly for this review. I'm logging it anyway, because it's clearly meant to become the onboarding surface, and it's worth knowing whether it fixes what the README gets wrong.

**Landing page.** This is a different tone entirely — better. "A reasoning system that shows its work... You can always ask: what did it believe, when, and why? — and get a checkable answer." A "Where to go" card literally says: **"The worldview app — The first application: drop in documents, watch beliefs update, audit every move."**

**Friction: 2.** That card is exactly my pitch, word for word. If this were the front door, Step 1 would have gone very differently.

> *Inner monologue: This is the page that should have been the README. Whoever wrote this understands what I want. Why did I have to be handed a localhost link to find it?*

## Step 7 — the worldview page

I click through. It explains the three ways a belief enters the store (inferred from a document, stated by a user, derived from a note that changed), and the "first-upload invariant" — a brand-new install with zero history still produces a meaningful result on the very first document. That's a good, honest answer to "do I need to seed this with a big corpus first" (no).

Then, under **Status**:

> "The server and browser UI (#9) — right now the app is a library you drive from Python. A local server and a UI for the before/after panel, conflict surfacing, and the belief-drift timeline are not built yet."
>
> "README and demo copy (#10) — a quickstart with a seed corpus, one per ingestion path, is not written yet."

**Friction: 5 — this is the wall.** Not a bug, not a bad explanation — a plainly stated fact. "You drive it from Python" is my first deal-breaker, restated without the word "adapter" but meaning the same thing: there is no surface I can operate. No plugin. No app. No form. Nothing to point at my vault. The road ends here, and it ends honestly — the page doesn't pretend otherwise — but it still ends.

I do not attempt to run Python. I can't, and the page just told me nobody's pretending I could.

> *Inner monologue: I appreciate that it says this straight out instead of letting me discover it by failing at something. That's rare and I'd remember it fondly — if I were the kind of user who was going to come back in six months to check. I'm not. I give a tool fifteen minutes, and the honest "not built yet" still means: not built.*

## Step 8 — checking whether the CLI has a side door (reviewer thoroughness, not something Maya would do)

For completeness, I confirmed `uv run epc --help` lists exactly three commands — `replay`, `diff`, `score` — all of which operate on an existing trace file. None ingest a document, a note, or a folder. There is no `epc worldview` or `epc ingest` command. This matches what the worldview page already told me. It also matches the intake note that the library ships only `MockRatingLLM` — even a person who *could* write Python would need to implement their own real rating model before a single one of their own documents got a real number. That's the literal "write your own LLM adapter" deal-breaker, just spelled `RatingLLMInterface.rate_confidence` instead.

## Where the road ends for Maya

At Step 7. Not because the tool is bad — the honesty page and the worldview page are the best-written things I found, and they say exactly what the numbers do and don't mean, unprompted, which is more candor than most tools manage. It ends because there is currently no surface a non-programmer can operate: no plugin, no app, no server, no form, no file to drop notes into and get a number back. Everything past the docs pages requires writing Python, and one specific piece of Python (a working rating model) doesn't exist yet even for someone who can code.

## Scorecard

| Step | What I was doing | Friction | Would I still be here? |
|---|---|---|---|
| 0 | GitHub repo page | 2 | Yes |
| 1 | README top | 4 | Marginal |
| 2 | API example (Python/Bayes) | 5 | No — real Maya closes here |
| 3 | Searching for "worldview" | 4 | — |
| 4 | Quick Start commands | 5 | — |
| 5 | Spec link | 5 (confirmed deal-breaker) | — |
| 6 | Docs site landing (not publicly reachable) | 2 | — |
| 7 | Worldview page — "drive it from Python," no UI | 5 (wall) | — |
| 8 | CLI / MockRatingLLM check | 5 (confirmed deal-breaker) | — |

**Overall: would abandon by minute 3-4, at Step 2**, on the strength of the README alone — before ever finding the one page (the docs site's worldview page) that actually speaks to her. That page is only reachable today via a link nobody outside this review has.

## What would change my answer

- A landing surface (even just a repositioned README section) that opens with "drop in a document, see a confidence number, here's why" — the docs-site pitch — before any Python.
- The docs site actually deployed and linked from the README and the GitHub repo description. Right now the best answer to my exact question exists and isn't findable.
- Literally anything I can operate without Python: a hosted demo, a single script I run with one pasted command that ingests a sample folder and prints results, or (the real ask) an Obsidian plugin. Absent that, "for researchers and engineers" is the accurate audience line, and the worldview page should say so as plainly as the README does, instead of implying with "drop in a document" that I'm closer than I am.
