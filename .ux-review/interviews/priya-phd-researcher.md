# Interview — Priya, PhD researcher with a reading corpus

Before touching the tool. Reacting cold to the pitch: "auditable belief revision over your documents."

## Who I am, for this review

28, fourth-year public health PhD. 300+ papers in Zotero. My dissertation has three or four claims that the literature actually disputes — one drug's cardiovascular effect, one policy's causal claim — and every week I read new papers that bear on them. Right now I track "did this paper move me" in a spreadsheet I update by hand and half-trust. I write Python in notebooks: I can run someone else's cell, change a variable, rerun. I copy quickstart code and adapt it. I do not open a library's source to figure out how it works, and I do not write a class that implements an interface — that's a different job than mine.

## What "auditable belief revision over your documents" means to me, walking in

I read this as: I feed it a paper, it tells me how much that paper moved my confidence in a specific claim, and it can show its work later when I'm writing the methods section and a reviewer asks "why do you believe that." The word doing the work is "auditable" — not the update itself (I already informally do that in my head every time I read a paper) but the fact that I could point to it and say *this is why*, with a citation trail, six months from now when I've forgotten which of forty papers moved the needle.

"Belief revision" makes me brace slightly. If it means Bayesian updating with priors I have to specify per claim, that's a stats-methods conversation I don't want to have this week. If it means "reads roughly like: ten papers said yes, two said no, here's where that nets out, and here's the ten and the two" — that I can use immediately, and use honestly in a footnote.

## Expectations

- I can go from "I heard about this" to "I saw it rate one real paragraph" without writing a class or reading a spec. A notebook cell I paste and run is my ceiling.
- It tells me, per claim, which documents moved it and by how much — not just a final number. That's the difference between a citable audit trail and a black box with a confidence label.
- It does not require me to pre-seed a corpus or configure an ontology before it does anything useful. My corpus grows one paper at a time, same as my reading does.
- If it needs an LLM to do the rating, either it ships a working one behind a config line (API key in an env var, not a class I implement), or it says plainly, up front, that I have to bring my own — before I've invested twenty minutes.
- Whatever a "confidence" number means, the docs say what it doesn't mean, in one place, in plain language — not just in a footnote to a spec. I've been burned before by tools that dress up "one model's opinion" as evidence.
- Some way to get a citation-shaped output — the source document, or at minimum something I can trace back to a DOI or a URL, attached to each move. A number with no traceable source is not a footnote, it's a guess with decimals.

## Must-haves

1. **A copy-paste quickstart that produces a visible result on the first try.** One command or one notebook cell, stated input, stated output. If step two requires me to read a docstring to know what to pass, that's already a second tool.
2. **A demo corpus that proves the flow before I risk my own library.** I want to see it work on someone else's three papers before I point it at Zotero.
3. **API keys as config, not code.** If "connect it to an LLM" means implementing a method, that's a job for someone who ships the library, not someone who uses it.
4. **Confidence is explained per document, not just per claim.** The aggregate number is the headline; the per-source breakdown is the citation.
5. **Nothing touches my Zotero library without me being told exactly what it reads and writes.** I do not re-risk four years of a reference manager for a demo.

## Concerns, going in

- Every "confidence score from an LLM reading your sources" tool I've tried is one model's read of the literature wearing a number. If the tool doesn't say that about itself, I don't trust the rest of what it tells me.
- A tool built by researchers, for researchers, tends to ship the math before it ships the on-ramp. "Spec is publishable, code is pip-installable" is a great sentence for a paper and a bad promise for someone who wants a result in twenty minutes.
- "Auditable" gets used loosely. If the audit trail turns out to be a log file or a database table I'd need to query myself, that is not auditable to me — it's auditable to whoever wrote the query.
- I've had exactly one bad experience with a tool that silently re-processed my whole Zotero export and left me unsure what state it was in. I will stop at the first sign this tool could do the same.

## Deal-breakers

- **"Implement this interface to connect an LLM."** I know what a Python class is. I don't write ones that satisfy someone else's protocol on a Tuesday night between grading and a chapter draft.
- **No demo data — the first thing I try is my own corpus.** I will not risk 300 papers of citation metadata on a tool's first run.
- **More than about 30 minutes between landing on the README and seeing one real result.** Literature-review fatigue means I have a short list of tools I'll actually finish evaluating.
- **A confidence number with no path back to which document produced it.** If I can't turn it into a footnote, it doesn't serve my actual task, no matter how principled the math behind it is.

## How I'll judge the first 30 minutes

Timer starts on landing. I'm looking for: did I see a real claim move, with a real (or at least demo) document attached, without writing a class or reading source? If at minute 30 I'm still looking for the command that produces a result — or I've hit a line telling me to implement something — I close the tab and go back to my spreadsheet, which is ugly but mine.
