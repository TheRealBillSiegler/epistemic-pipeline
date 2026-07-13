# UX backlog — draft (pending Billy's priority pass)

Effort is agent-execution scope (files touched / blast radius), not clock time. Items grouped by the issue that should own them. Status: DRAFT — priorities not yet confirmed by the maintainer.

## Own issue exists

| # | Item | Owner issue | Effort | Depends on |
|---|---|---|---|---|
| 1 | Deploy docs site; link from README + repo description | #37/#39 | merge + 2 lines | #39 merged |
| 2 | Demo corpus running on the mock rater | #10 | new `examples/` or `docs/` assets | — |
| 3 | README: worldview pitch + runnable block above Bayes example | #10 | 1 file | — |
| 4 | Rater-gap sentence in worldview Status section | #10 | 1 paragraph | — |
| 5 | Provenance contract (`ts`/`seed`) documented as a decision | #10 | 1 paragraph | — |
| 6 | UI first-load = demo data; inline "why"; honesty copy; labeled controls; text timeline; write-scope statement; visible persistence | #9 | design constraints, recorded before build | #10 items 2 |

## Needs a new (small) issue each

| # | Item | Effort | Note |
|---|---|---|---|
| 7 | Re-export public API from `worldview_app/__init__.py` | 1 line + test | cheapest fix in the review; kills a reproduced ImportError |
| 8 | Mermaid a11y: `accTitle`/`accDescr` ×7 + prose parity ×2 | content-only | WCAG 1.1.1 Level A |
| 9 | Admonition semantics (role/heading) via Material partial override | ~10 lines template | the honesty callouts are invisible to heading nav |
| 10 | `honesty` admonition custom style + rename ×9 | ~10 lines CSS + find/replace | mockup: `.ux-review/mockups/honesty-admonition.html` |
| 11 | Mermaid mobile scroll container (match table behavior) | 1 CSS rule | text illegible at 375px today |
| 12 | Accessibility statement (one line, site + README) | 1 sentence | |
| 13 | Promote `_replay_beliefs` → public `replay_beliefs` (or document intended pattern) | small API decision | pitch's flagship capability has no public name |

## Explicitly not reopened by this review

- #33 (claim identity), #34 (calibration) — remain Tier-2 as classified; nothing here changes that.
- Real-LLM adapter shipping: a product decision (BYO-key adapter was v1 scope in #5); this review only demands the gap be *stated*, which is item 4.
