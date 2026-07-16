"""Dogfood experiment: this repo's own review history as an epistemic ledger.

The question being tested (2026-07-12): does a belief ledger over a
project's claims answer questions the GitHub issue list cannot? If yes,
the "belief layer of intent-driven development" framing earns a design
pass. If no, the framing dies here, cheaply.

Every claim and evidence event below is real. They come from the
2026-07-11 blind-spot review, the code verifications that followed, and
the deep-research passes. Timestamps are ordinal event order, not wall
clock. Roots are evidence channels: one LLM lens is `agent:fable/<lens>`,
a direct code read is `check:code-read`, a pytest run is `check:pytest`,
a measurement is `measure:<name>`, a deep-research run is
`research:<id>`.

ponytail: experiment script, not product code. One file, stdlib + the
library under test, prints a markdown report to stdout.
"""

from __future__ import annotations

from epistemic_pipeline.encodings._confidence import parse_confidence_vector
from epistemic_pipeline.encodings.worldview import (
    WorldviewBeliefs,
    WorldviewOntology,
    aggregate_beliefs,
)
from epistemic_pipeline.worldview_app.ingest import ingest_rating
from epistemic_pipeline.worldview_app.store import Store

# --- The real history, as (timestamp, root, reason, {claim: confidence}) ---
# Confidence = how strongly this evidence supports the claim (1.0 = strong
# support, 0.0 = strong disconfirmation), as stated in the session record.

C_REPLAY = "Replay path fuses without root grouping; replaying reproduces the #25 inflation (#30)"
C_IDENTITY = "Claim identity is unexamined: evidence fragments and contradictions coexist (#33)"
C_RATER = "One rater's prior is a shared upstream source root-keying cannot see (#35)"
C_TAUTOLOGY = "The s8 validation tests except calibration are true by construction (#34)"
C_N34 = "The n=34 measurement shows the faithfulness gate would fire on ~0%, so deferral is safe (#26)"
C_AUTHOR = "author_claim leaves no record in the drift timeline (#31)"
C_AVOIDANCE = "Research effort systematically substitutes for shipping user-facing surfaces"
C_NOVEL = "The parametric-knowledge encoding is novel as a combination (#41)"

EVENTS: list[tuple[float, str, str, dict[str, float]]] = [
    # 2026-07-01: the faithfulness measurement and its original reading.
    (1.0, "measure:n34", "n34 original interpretation", {C_N34: 0.9}),
    # 2026-07-11: the five blind-spot lenses (one model, five prompts).
    (2.0, "agent:fable/bayesian", "lens: Bayesian reviewer", {C_RATER: 0.85, C_TAUTOLOGY: 0.9, C_IDENTITY: 0.85}),
    (3.0, "agent:fable/product", "lens: product skeptic", {C_AVOIDANCE: 0.8}),
    (4.0, "agent:fable/eval", "lens: eval methodologist", {C_TAUTOLOGY: 0.8, C_N34: 0.15}),
    (5.0, "agent:fable/epistemologist", "lens: formal epistemologist", {C_IDENTITY: 0.9}),
    (6.0, "agent:fable/systems", "lens: systems realist", {C_REPLAY: 0.9, C_IDENTITY: 0.9, C_AUTHOR: 0.9}),
    # Same day: direct code verification of the two code-level findings.
    (7.0, "check:code-read", "read worldview.py and ingest.py directly", {C_REPLAY: 0.95, C_AUTHOR: 0.95}),
    # PR #38: regression tests pin the author_claim fix.
    (8.0, "check:pytest", "PR #38 regression tests pass", {C_AUTHOR: 0.98}),
    # 2026-07-12: deep-research pass, adversarially verified.
    (9.0, "research:wf_843e043f", "prior-art sweep, 3-vote verified", {C_NOVEL: 0.9, C_RATER: 0.7}),
]

SHORT = {
    C_REPLAY: "#30 replay divergence",
    C_IDENTITY: "#33 claim identity",
    C_RATER: "#35 rater correlation",
    C_TAUTOLOGY: "#34 tautological validation",
    C_N34: "#26 'deferral is safe' (n=34)",
    C_AUTHOR: "#31 author_claim gap",
    C_AVOIDANCE: "research-as-avoidance",
    C_NOVEL: "#41 novelty verdict",
}

DISCREDITED_REASON = "n34 original interpretation"


def build(store: Store) -> None:
    """Ingest the session history through the real write path."""
    for ts, root, reason, ratings in EVENTS:
        ingest_rating(
            store, ratings, source_type="inferred", ts=ts,
            model_id="session-record", prompt_hash=reason[:16], seed=0,
            reason=reason, root_id=root,
        )


def trail(store: Store, *, exclude_obs: set[int] | None = None) -> list[tuple[str, dict[str, float]]]:
    """Read (root, vector) pairs back from the store, optionally excluding rows."""
    pairs: list[tuple[str, dict[str, float]]] = []
    for row in store.observations():
        if row["variable"] != "confidence_vector":
            continue
        if exclude_obs and row["id"] in exclude_obs:
            continue
        pairs.append((row["root_id"] or row["source"], parse_confidence_vector(row["value"])))
    return pairs


def fold(store: Store, pairs: list[tuple[str, dict[str, float]]]) -> WorldviewBeliefs:
    """The pure R fold over a (possibly filtered/remapped) trail."""
    return aggregate_beliefs(pairs, WorldviewOntology(concepts=frozenset(store.concepts())))


def discredited_ids(store: Store, reason: str) -> set[int]:
    """Find observation ids whose drift links carry the given reason."""
    ids: set[int] = set()
    for claim_row in store.claims():
        for link in store.history(claim_row["id"]):
            if link["reason"] == reason:
                ids.add(link["observation_id"])
    return ids


SHIFT_THRESHOLD = 0.05


def main() -> None:
    """Build the ledger from the session record and print the five answers."""
    with Store(":memory:") as store:
        build(store)

        base = fold(store, trail(store))
        merged = fold(store, [
            ("agent:fable" if r.startswith("agent:fable/") else r, v)
            for r, v in trail(store)
        ])
        retracted = fold(store, trail(store, exclude_obs=discredited_ids(store, DISCREDITED_REASON)))

        roots: dict[str, set[str]] = {}
        for _ts, root, _reason, ratings in EVENTS:
            for c in ratings:
                roots.setdefault(c, set()).add(root)

        print("## Q1 — How settled is each finding? (the issue list says only 'Open')\n")
        print("| Claim | P | settledness | distinct roots |")
        print("|---|---|---|---|")
        ordered = sorted(SHORT, key=lambda c: base.opinions[c].uncertainty)
        for claim in ordered:
            op = base.opinions[claim]
            print(f"| {SHORT[claim]} | {op.projected:.2f} | {1 - op.uncertainty:.2f} | {len(roots[claim])} |")

        print("\n## Q2 — Which findings rest on a single evidence root?\n")
        for claim in ordered:
            if len(roots[claim]) == 1:
                op = base.opinions[claim]
                only = next(iter(roots[claim]))
                print(f"- {SHORT[claim]}: one root ({only}), settledness {1 - op.uncertainty:.2f}")

        print("\n## Q3 — Drift timeline of the corrected claim (#26 deferral)\n")
        for link in store.history(C_N34):
            print(f"- ts={link['timestamp']:.0f}: delta {link['delta']:+.2f} — {link['reason']}")
        print(f"- today: P={base.opinions[C_N34].projected:.2f}")

        print("\n## Q4 — Simulated retraction (#42): discredit the original n=34 reading\n")
        print(f"- with the discredited row:   P={base.opinions[C_N34].projected:.2f}")
        print(f"- after retraction (re-fold): P={retracted.opinions[C_N34].projected:.2f}")

        print("\n## Q5 — Sensitivity: treat the 5 lenses as one root instead of five\n")
        any_shift = False
        for claim in ordered:
            s1 = 1 - base.opinions[claim].uncertainty
            s2 = 1 - merged.opinions[claim].uncertainty
            if abs(s1 - s2) > SHIFT_THRESHOLD:
                any_shift = True
                print(f"- {SHORT[claim]}: settledness {s1:.2f} -> {s2:.2f}")
        if not any_shift:
            print("- no claim shifts by more than 0.05")


if __name__ == "__main__":
    main()
