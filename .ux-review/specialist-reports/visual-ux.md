# Visual + accessibility UX review — epistemic-pipeline docs site

Reviewer: visual + accessibility UX specialist. Scope: the docs site as the product's face —
visual hierarchy, typography/density, diagram legibility, WCAG 2.1 AA. Not in scope: content
IA, onboarding funnel, CLI/library UX (see `technical-ux.md` for those).

Method: fetched rendered HTML directly (`curl`) for heading/landmark structure, then used a
headless Chromium instance (Playwright) to inspect what actually reaches the accessibility
tree — `page.locator(...).ariaSnapshot()`, the same tree assistive tech consumes — because
this site's diagrams and math are rendered client-side by JavaScript and a static HTML fetch
alone cannot tell you what a screen reader will announce. Every finding below is reproduced
with commands, not inferred from source reading. Six pages inspected in depth: home,
`concepts/pipeline`, `beliefs/fusion`, `worldview/honesty`, `concepts/layers`, plus spot
checks on others. Screenshots taken at 1280×900 (desktop) and 375×812 (mobile), light and
dark, via a headless Chromium instance.

---

## Finding 1 — Mermaid diagrams are invisible to screen readers (WCAG 1.1.1, Level A)

**Severity: high.** This is not a missing-alt-text nit — the diagrams contribute *zero* nodes
to the accessibility tree. A screen reader user does not get an unlabeled graphic they can at
least know exists; they get nothing, not even a gap. The surrounding text flows as if the
diagram were never there.

Verified two ways, on two pages:

1. `page.locator('.mermaid').first().ariaSnapshot()` on the homepage (the "whole idea in one
   diagram" O/E/B/R diagram — the single most load-bearing visual on the site) returns an
   **empty string**. Same result on `concepts/pipeline` (the six-stage flowchart).
2. A full `article` ariaSnapshot on `concepts/pipeline` jumps directly from the paragraph
   above the diagram to the "The six stages" heading's sibling table — no image, group, or
   figure node in between, at any accessibility-tree depth.

For contrast, the same page's MathJax formulas *are* done correctly: each renders an
`mjx-assistive-mml` block with real MathML, and `ariaSnapshot()` reports `role: math, name:
"r"` etc. — exactly what a screen reader needs. This isolates the defect to Mermaid
specifically; it is not a site-wide accessibility gap.

Root cause is not fully diagnosable from outside the render pipeline (the rendered SVG paints
correctly on screen — confirmed by cropped screenshot — but is absent from `document.
querySelectorAll('svg')`, `innerHTML`, and the accessibility tree simultaneously, across five
independent timing checks up to 5 seconds after load). What's checkable and actionable from
the content side: **zero of the 7 pages that embed Mermaid diagrams use Mermaid's own
`accTitle` / `accDescr` directives** (confirmed by grep across `docs/`), which is the
first, cheapest fix regardless of the underlying rendering issue.

Fix, in order of effort:

- Add `accTitle` / `accDescr` to every `mermaid` fence (Mermaid's native accessibility
  API — two lines per diagram, no CSS/JS changes).
- Better: follow the pattern `concepts/pipeline.md` *already* uses for its own diagram — it
  restates the exact same flow as a full data table immediately below the flowchart, so a
  screen reader user loses only the "at a glance" view, not the content. The homepage's O/E/B/R
  diagram and `beliefs/fusion`'s two-tier-fusion diagram have no such equivalent nearby; those
  two are the ones where fixing this actually matters most.

## Finding 2 — Diagrams scale to fit narrow viewports instead of scrolling; text becomes illegible on mobile

**Severity: medium-high.** Verified by screenshot at a 375px viewport (`beliefs/fusion`, the
two-tier-fusion architecture diagram): every internal box label is well under a legible size —
smaller than the browser's own minimum comfortable reading size, not just "small."

The cause is a real, checkable inconsistency in how this site's two kinds of wide content
behave on mobile:

- **Tables** get Material's `.md-typeset__scrollwrap` treatment: `overflow-x: auto`, table
  stays at native width (confirmed: the fusion-rules comparison table has `scrollWidth: 515`
  inside a `clientWidth: 375` wrapper — it scrolls, text stays full-size).
- **Diagrams** get no equivalent wrapper: the `.mermaid` SVG's `scrollWidth` exactly equals
  its rendered `width` (343px, matching the viewport) — it isn't clipped, it's *scaled down*
  to fit, taking all its internal text down with it.

Fix: wrap Mermaid output in the same scroll-container pattern already used for tables
(`overflow-x: auto` on the container, remove any `width: 100%` / `max-width: 100%` forcing
the SVG to shrink). This is a CSS change, not a per-diagram content change — one fix covers
all 7 pages.

## Finding 3 — The site's core trust device has no visual identity of its own

**Severity: medium — this is the one that speaks to "rigorous instrument vs. generic docs."**
"Honest status" callouts are the site's defining rhetorical move: 9 of ~14 pages use one to
name exactly where a number or a replay guarantee falls short. That is a genuinely
distinctive, well-executed pattern (see `beliefs/fusion.md`'s callout naming the
shared-source blind spot, or `concepts/pipeline.md`'s on replay-rule drift) — but visually,
every one of them is MkDocs Material's completely generic `!!! warning` admonition: the same
amber triangle used for any "heads up, unfinished" note anywhere on the web (confirmed:
grep shows all 9 use `!!! warning "Honest status`; the compiled CSS shows this is exactly
Material's stock `#ff9100` warning color, not a custom one).

The content already does the hard part — it's specific, numbered (cross-references real
issue numbers and test files), and consistent in voice. The styling doesn't signal "this is a
first-class, load-bearing feature of the system" — it signals "routine caveat," which
undersells the one thing this project is actually trying to be known for.

Fix: this repo uses the plain `admonition` extension (confirmed: `mkdocs.yml` line 49 —
not `pymdownx.blocks.admonition`), which means any type name works immediately — writing
`!!! honesty "Title"` today already emits `<div class="admonition honesty">`, no config change
needed. It just has no icon/color yet because nothing targets `.md-typeset .honesty` in CSS.
So the fix is two small, independent pieces: ~10 lines of hand-rolled CSS keyed to
`.md-typeset .honesty` (mirroring how Material's own stylesheet styles `.warning`/`.failure` —
border color, title background, icon mask) added via `extra_css`, then a find-and-replace of
the opening line across the 9 files. A visual
mockup of current vs. proposed is at `.ux-review/mockups/honesty-admonition.html` — this is
the one recommendation where a static screenshot of the *existing* site can't show what the
fix would look like, so it gets a mockup rather than a description.

---

## What's already solid (verified, not assumed)

Worth stating plainly so the above three findings don't read as "the site is broken" — they
aren't representative of the whole. What passed:

- **Color contrast.** Computed WCAG contrast ratios with proper alpha-compositing (Material's
  text colors are `rgba` over layered backgrounds — a naive check that ignores alpha
  under/over-states contrast, so this was done by resolving the actual composited RGB at each
  layer) for body text, in-content links, sidebar nav, inline code, admonitions, footer, and
  the header/tab bar, in both light and dark. Every pair checked clears AA (≥4.5:1 normal
  text, ≥3:1 large text/UI). No violations found. The indigo palette is not a contrast risk.
- **Heading structure.** Six pages checked: exactly one `h1`, sequential `h2`/`h3` nesting, no
  skipped levels, on every one.
- **MathJax accessibility.** Correct: real MathML fallback, proper `role="math"` exposure —
  see Finding 1's contrast with Mermaid.
- **Skip-to-content link** present, targets the `h1`, first focusable element.
- **Dark mode** is a real second theme, not a body-text-only palette swap: Mermaid diagrams
  re-theme their fills, borders, and text color correctly for dark mode (verified by
  screenshot) — the diagram legibility problem in Finding 2 is orthogonal to this and present
  in both themes equally.
- **Tables** get correct responsive scroll behavior on mobile (the thing Finding 2 says
  diagrams should also get).

## On "rigorous instrument vs. generic docs"

Mixed, and the split runs along a clean line: **content says rigorous instrument, chrome says
generic MkDocs Material.** The honest-status admonitions, the worked numeric examples with
real formulas, the direct links to the test files that back a claim, and the "honest status"
box that literally exists to admit where the math can't see — none of that reads as marketing
copy, and none of it is common on a typical docs site. But the *look* — indigo primary color,
default Material chrome, stock admonition icons — is visually indistinguishable from
thousands of other MkDocs Material sites (FastAPI, Pydantic, Traefik, etc.). Nothing in the
palette or type system itself signals "formal instrument" one way or the other; it's a solid,
correctly-executed default, not a distinctive one. Finding 3 is the cheapest lever available
to close that gap, because it targets the one component that's genuinely unique to this
project's identity rather than asking for a full reskin.

## Artifacts

- Mockup: `.ux-review/mockups/honesty-admonition.html` (current vs. proposed admonition
  styling, light + dark aware, self-contained).
- Screenshots referenced above were taken to a scratch directory during this review and are
  not checked into the repo; re-run against the live site to reproduce (commands available on
  request — all used a headless Chromium instance via Playwright, `waitUntil: 'load'` +
  1.5–2.5s settle, `page.locator(...).ariaSnapshot()` for accessibility-tree checks).
