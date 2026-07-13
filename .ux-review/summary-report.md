# UX review — summary report

Date: 2026-07-12. Scope: current surfaces only (README, `epc` CLI, Python library, local docs site). Method: 4 simulated personas (interview + walkthrough each), 2 specialist reviews (technical UX; visual + accessibility), all claims marked "confirmed" reproduced live by the reviewer, not assumed. Confidence: high for findings verified by command output or accessibility-tree snapshots; medium for persona-behavior predictions (simulated users, single model family).

## Executive summary — top 5 findings

1. **The onboarding funnel dead-ends before the product for 3 of 4 personas.** There is no runnable worldview example anywhere — README, docs site, or `examples/`. The only correct call sequence in the repo lives in the test suite. The non-programmer abandons at the README's Bayes example (~minute 3); the notebook user dies on `ImportError` (the package `__init__.py` re-exports nothing); even the expert took 10 minutes of source-reading to write his own first example. **Zero non-expert personas reach a first result.**
2. **The best onboarding surface in the project is unreachable.** The docs-site landing page scored the best friction rating of anything in this review (1/5), and its worldview page pitch ("drop in documents, watch beliefs update") is exactly what two personas came for — but the site isn't deployed (PR #39 unmerged), and nothing in the README or the GitHub repo description links to it. The answer to a stranger's exact question exists and cannot be found.
3. **The default ingestion path requires writing your own LLM adapter, and no doc says so.** `MockRatingLLM` is the only rater that ships (honestly labeled, first-class export — not a disguised mock). The `worldview/index.md` Status section names two gaps (#9, #10) but not this one, which blocks the *default* path even for Python users. It's the researcher persona's stated deal-breaker, verified against code.
4. **Two real accessibility defects, both landing on the project's signature feature.** (a) Mermaid diagrams contribute zero nodes to the accessibility tree (WCAG 1.1.1 Level A; verified by `ariaSnapshot()` — empty string; no `accTitle`/`accDescr` on any of 7 diagram pages). Prose parity currently saves the content, by discipline, not by rule. (b) "Honest status" admonition titles are `<p>` with no ARIA role — invisible to screen-reader heading navigation, which is precisely how a screen-reader user skims for the important parts. The honesty callouts are the feature; they are the easiest thing on the page to miss.
5. **The honesty identity is the project's strongest UX asset — and its chrome undersells it.** Every persona who reached `worldview/honesty.md` (3 of 4) independently called it the best thing in the repo; the hostile expert said it, not the code sample, decides adoption. Visually, those callouts are stock amber warnings, indistinguishable from routine caveats on any Material site. Cheap fix: a custom `honesty` admonition style (mockup in `.ux-review/mockups/honesty-admonition.html`).

**Counterweight, stated plainly:** determinism held under the expert's adversarial test; CLI error messages are good; color contrast, heading structure, MathJax accessibility, skip links, and dark mode all pass verified checks. The core is sound. The failures are almost all *path-to-the-product* failures, not product failures.

## Persona outcomes

| Persona | Reached a first result? | Died at | Best moment | Verdict |
|---|---|---|---|---|
| Maya (non-programmer, Obsidian) | No | README code example (min ~3); wall re-confirmed at "drive it from Python" | Docs-site landing pitch (unreachable in real life) | Not the audience today; docs should say so or give her one operable surface |
| Priya (notebook user, no source-reading) | No | `ImportError` on the only guessable import | Worldview page pitch (1/5 friction) | Would return for a copy-paste quickstart + config-key LLM |
| Devon (expert, adversarial) | Yes (wrote his own example, <10 min) | Nothing; stalled at private `_replay_beliefs` | Honesty page; determinism surviving his attack | "Come back in a few PRs" — would file 3 precise issues |
| Sam (blind developer) | Yes (via `author_claim`, no LLM needed) | Nothing hard; friction at undocumented rater gap | Diagram-prose parity everywhere he tested | Recommend-with-one-bug-filed (admonition semantics) |

## Prioritized recommendations

### P0 — unblocks everything, near-zero cost
1. Merge #39, enable Pages, **link the site from the README first screen and the GitHub repo description**.
2. **Re-export `Store`, `ingest_document`, `author_claim`, `NoteIngester` from `worldview_app/__init__.py`** — one line kills the reproduced ImportError.
3. **One runnable worldview code block in the README, above the Bayes example** (3–8 lines, mock LLM, prints a result). Test: fresh clone, paste, run, non-empty output.

### P1 — the #10 work, informed
4. Demo corpus (3–5 short docs + one contested question) running on the shipped mock, labeled as a demo.
5. Add the rater gap to `worldview/index.md` Status: "only a mock rater ships; implement `rate_confidence` (one method, not both) for a real LLM."
6. Document the `ts`/`seed`/`model_id` provenance contract as a decision ("you supply the clock; `time.time()` silently breaks replay").
7. README first screen: lead with the worldview pitch (reuse the docs-site landing copy — the best-tested copy in the project).

### P2 — docs-site page fixes (post-#39, small PRs)
8. `accTitle`/`accDescr` on all 7 Mermaid fences; add prose parity for the two diagrams lacking it (home O/E/B/R, fusion two-tier).
9. Admonition semantics: role (`note`/`doc-notice`) or heading-level titles via a small Material partial override.
10. Custom `honesty` admonition style (10 lines CSS + find/replace `!!! warning "Honest status` → `!!! honesty`); mockup exists.
11. Mermaid mobile fix: wrap diagrams in the same `overflow-x: auto` scroll container tables already get (one CSS rule, all 7 pages).
12. One-line accessibility statement on the site.

### P3 — requirements recorded for #9 (UI), so they're designed-in, not retrofitted
13. First load shows the demo corpus result, never an empty state needing configuration.
14. A claim's "why" (evidence, sources, timestamps) renders inline with the number, not behind a docs link.
15. UI restates what the number does not mean, sourced from the honesty page.
16. Every control programmatically labeled; the drift timeline's data also available as text/table (screen-reader deal-breaker, flagged pre-build).
17. Restart persistence visible (SQLite already provides it; the UI must not imply ephemerality).
18. A one-sentence write-scope statement before touching any user folder/vault.
19. Small separate issue: promote `_replay_beliefs` to public `replay_beliefs` (or document the intended pattern) — the pitch's flagship capability currently has no public function name.

## Artifacts

- Intake: `.ux-review/interviews/intake.md` (assumption-flagged; no live interview)
- Personas: `.ux-review/personas/*.md` (4)
- Interviews: `.ux-review/interviews/*.md` (4)
- Walkthroughs: `.ux-review/walkthroughs/*.md` (4)
- Specialists: `.ux-review/specialist-reports/technical-ux.md`, `visual-ux.md`
- Mockup: `.ux-review/mockups/honesty-admonition.html`
- Backlog: `.ux-review/backlog.md`

Caveat on method: personas are simulated by one model family; treat their *behavioral* predictions (abandonment timing) as directional, and their *factual* findings (reproduced errors, verified markup) as solid — the two specialists re-verified every load-bearing factual claim live.
