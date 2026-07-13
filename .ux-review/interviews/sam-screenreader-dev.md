# Interview — Sam, blind developer, screen-reader user

Before touching the tool. Reacting cold to the pitch: "auditable belief revision over your documents."

## Who I am, for this review

37, backend developer, blind since birth. NVDA on Firefox, Windows. Terminal-first — I live in a shell more than a browser, because a shell is text and text is the one interface class that was built accessible before anyone had to ask. I evaluate every dev tool the same two ways: can I read the docs without a sighted colleague narrating a diagram to me, and can I drive the thing from a keyboard and a screen reader without hitting a wall the sighted reviewer never saw.

I'm not evaluating this as a personal user. I'm evaluating it to decide whether I can put "epistemic-pipeline" in front of my team without someone on my team — me — hitting friction nobody budgeted time to fix.

## What "auditable belief revision over your documents" means to me, walking in

I read "auditable" the same way Maya's notes (which I was shown, for calibration) read it: as a promise that every number traces to a reason I can inspect, not just a log file I'm "welcome to parse." I don't have a second reading of that word — it's a fine pitch.

What I add that a sighted reviewer wouldn't: "auditable" only helps me if the audit trail is *readable*, not just *present*. A confidence score with a receipts trail that's rendered as a picture of a graph is not auditable to me — it's auditable to whoever's next to me. So my bar for this pitch is one click stricter than Maya's: not just "does a number explain itself," but "does it explain itself in something my screen reader can get to."

## Expectations

- Every diagram on the docs site has its content stated in prose nearby — not "alt text describing a picture of a flowchart," full prose that carries the same information the picture does. A caption that says "Figure 3: the five layers" tells me nothing a diagram already couldn't.
- Math renders as real MathJax or MathML, not a PNG of a LaTeX equation. A screen reader can walk a MathML tree term by term. It cannot read a raster image, and alt text on a formula image is almost always "equation" or absent.
- Tables read as tables — `<table>` markup NVDA can navigate cell by cell — not `<div>` soup styled to look tabular.
- Skip-to-content, so I don't re-hear the same nav on every page.
- Headings are actual heading elements (`<h1>`–`<h6>`), including for anything that's visually styled like a callout or a warning box. I navigate long docs by jumping heading to heading (NVDA's `H` key) far more than by reading top to bottom — if a section is only a heading *visually*, it doesn't exist for that navigation mode.
- The CLI and any Python API read linearly in a terminal: plain text output, no information conveyed only by color or by a spinner/progress bar with no text equivalent.

## Must-haves

1. **Every diagram's content also stated in prose.** Not a caption — the actual information.
2. **MathJax (or equivalent accessible math), never math-as-image.**
3. **Tables that linearize sensibly** — real `<table>` markup, sensible reading order cell by cell.
4. **Skip-to-content**, present and working, on every page.
5. **Headings are headings**, including anything a sighted user would recognize as a section by its visual weight — a bolded, colored, icon-prefixed callout box included. If it looks like a landmark to the eye, it has to register as one to `H`-key navigation.

## Concerns, going in

- Diagram-heavy technical docs are the single most common place accessibility work gets skipped, because the sighted author tests by looking at the picture and never re-checks with a screen reader. A project can have excellent prose everywhere else and still fail here, because the diagram *feels* self-explanatory to the person who can see it.
- Admonition/callout boxes ("Note," "Warning") are a known trap: most static-site themes style them distinctively (icon, colored border, bold title) but render the title as a styled paragraph, not a real heading. Sighted users still see the visual landmark. Screen-reader users navigating by heading don't — the box is invisible to the one navigation mode built for skimming a long page. I'd bet money this project has at least one of those, because almost every docs site running Material for MkDocs does, and nobody fixes it unless someone with a screen reader files the bug.
- This project's own pitch is that it doesn't hide its limits — "Honest status" warnings, stated plainly. If those warnings live inside a callout box that isn't heading-navigable, the project's signature honesty feature is, for me, less discoverable than its ordinary paragraphs. That would be a genuinely funny failure mode for a tool whose whole premise is "nothing important should be invisible."
- The library ships only a mock LLM rater, per what I was told going in. That's not an accessibility problem — it's the same wall a sighted developer would hit — but it does mean the "primary goal" test (drive the library from the terminal, get a real number on a real document) may not be completable by anyone yet, sighted or not. I'll still document exactly where *my specific* road ends, separate from where everyone's road ends.

## Deal-breakers

- **Any diagram whose content exists nowhere but the picture.** Full stop — if I can't get the information any other way, the docs have a hole I can't route around, no matter how good the surrounding prose is.
- **Math as a rendered image with no text/MathML fallback.** Same category as above: information that exists in exactly one modality I don't have.
- **A CLI or library error that only communicates via a non-text signal** — a bare traceback with no message, output that depends on terminal color to convey meaning, a hang with no text indicating what it's waiting on.
- **Unlabeled controls in the eventual UI (#9).** Not live yet, so not something I can fail today — but it's the single thing that would keep this tool off my team's list once that surface ships, so I'm flagging it now rather than waiting to be surprised later.

## How I'll judge this review

Not a 15-minute clock — I'm a developer evaluating a dev tool, and I expect to spend real time in the docs and the code either way. My bar is narrower and more mechanical: at every diagram, every math block, every callout, every terminal command, does the *information* reach me, and does it reach me through the *right channel* (heading nav finds it, table nav finds it, linear read finds it — not "it's technically in the DOM somewhere if you read every character"). I'll rate each friction point 1–5 like the rest of this review, but I'm also going to say plainly, for each one, what it would cost the maintainer to fix — because that's the part a sighted QA pass never tells them.
