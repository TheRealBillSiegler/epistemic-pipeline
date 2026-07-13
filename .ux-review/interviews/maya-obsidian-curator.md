# Interview — Maya, Obsidian curator

Before touching the tool. Reacting cold to the pitch: "auditable belief revision over your documents."

## Who I am, for this review

34, policy analyst. 2,400 notes in Obsidian, Dataview and Zotero wired in. I read 5-15 things a day for work — reports, papers, news — and save the ones that matter. I am good with software. I am not a programmer. I have never run a `for` loop on purpose. I can paste one command into a terminal if a README tells me exactly what to paste and what I should see after. Two commands, or a command whose output I have to interpret myself, and I'm already behind.

## What "auditable belief revision over your documents" means to me, walking in

I already do a version of this by hand: a note per claim, a running "how sure am I" tag, links to the three articles that moved it. It's manual and it drifts — I forget to update the tag, I forget which article moved it and by how much. So the pitch reads to me as: *point this at my vault, and it keeps that tag current and shows its work.* That's the whole ask. Not a new belief system, not a new note format — an engine under the note format I already have.

"Auditable" is the word that got my attention, not "belief revision." Half the PKM plugins I've tried show me a confidence score with no way to ask *why*. If this one can answer "why does this claim sit at 0.7" with a list of the actual passages that moved it, that's the differentiator. If "auditable" turns out to mean "there's a log file somewhere," that's not what I heard.

## Expectations

- I install it the way I install any Obsidian plugin: from the community plugin browser, or at worst one documented command, and it works inside the vault I already have — not a new folder structure I have to migrate into.
- I point it at a folder (or my whole vault) and it starts rating claims without me writing anything. If it needs an LLM, it either ships a working default or asks me for an API key through a settings box — not a Python class I implement.
- The first thing I see is a number attached to a claim I actually wrote, with a one-click path to the sentence(s) that produced it. Not a schema. Not a CLI flag list.
- If I restart Obsidian, my numbers are still there. This is not optional — it's the same bar as "did my notes survive a crash."
- Somewhere, in plain words, it tells me what the number does *not* mean. I don't need a hedge on every screen, but I want the tool to admit "settled" isn't "true," the same way a good source-critical historian would.

## Must-haves

1. **No terminal, or exactly one command I can copy-paste with a stated expected result.** Anything past that is a different product for a different user.
2. **Works with notes I already have.** Markdown files, plain text, whatever's already in the vault. I will not restructure 2,400 notes to feed a tool.
3. **The confidence number is explained where I see it**, not two clicks into a docs site. A tooltip, a hover, something in-app.
4. **State persists.** My belief store is not a scratch buffer — it's the point. If it resets on restart or on every re-run, it has failed the one thing it promised.
5. **Visible progress inside 15 minutes.** I don't need the whole vault ingested — I need to see it work once, on one document, unattended.

## Concerns, going in

- PKM tooling has a bad track record of promising "auditable" and delivering "a JSON blob you're welcome to parse yourself." I've been burned by this exact pitch before (Zotero plugins that log everything and surface nothing).
- "Belief revision" is a term with real math behind it (Bayesian updating, Dempster-Shafer, whatever). If the tool expects me to understand that math to read my own numbers, it has failed the audience it's naming — a note-taker, not a statistician.
- Confidence scoring from one model reading my own reading list is confirmation bias wearing a number. I want the tool to know this about itself. If it presents "0.83 settled" as if that's an external check on truth, I don't trust the rest of it either.
- Any tool that touches my vault and doesn't tell me exactly what it writes, and where, is a tool I uninstall the same day. Obsidian vaults are precious; I don't grant write access lightly.

## Deal-breakers

- **"Write your own LLM adapter."** I don't know what an adapter is in this context, and I'm not going to learn on a Tuesday night to use a note-taking tool.
- **Any workflow that requires reading a spec.** A spec is a document for the people who build the tool, not the people who use it. If the README's answer to "how do I start" is "see the design doc," I'm gone.
- **Losing state on restart.** Covered above — this isn't a nice-to-have, it's the product's entire premise (accumulation over time) failing on contact.
- **A CLI as the only interface.** I can run one pasted command. I cannot debug one. If the "quick start" assumes I'll notice and fix an error message, that's a wall, not a step.

## How I'll judge the first 15 minutes

Timer starts when I land on the README or the plugin page. I'm looking for: can I get from "I heard about this" to "I saw a real number on a real claim of mine, and I understood in one sentence what produced it"? If at minute 15 I'm still reading about the architecture, or I've hit a line that says "write your own X," I close the tab. I've done this with three other tools this year already.
