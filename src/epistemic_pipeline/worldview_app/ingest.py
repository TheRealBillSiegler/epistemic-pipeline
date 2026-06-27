"""Three ways beliefs enter the worldview store.

All three write to the same store (#6) and route ratings through the
worldview encoding (#7). They differ only in where the rating comes from:

- inferred: an LLM reads a document and rates the claims in it.
  ``ingest_document``.
- user: a person states a claim and its confidence directly.
  ``author_claim``. This is almost the bare store API; the only extra is
  registering the claim as a concept so the ontology knows it.
- derived: a note is ingested whenever it changes. ``NoteIngester``
  wraps the inferred path with content-hash dedupe so re-saving an
  unchanged note does not thrash the store.

A claim's id is its text: the sentence *is* the claim (e.g.
``"Fiscal Q4 2024 = $2.1B"``). The LLM emits a JSON object mapping each
such sentence to a confidence. So no separate text-extraction step is
needed.

Ingestion grows the ontology from the documents: every rated claim is
added as a concept before the revision policy runs. The Power-norm
"unknown concept" signal (WorldviewOntology.adequate) is therefore for a
future locked-ontology mode, not this auto-growing one.
"""

from __future__ import annotations

import hashlib
import math
from typing import TYPE_CHECKING

from epistemic_pipeline.encodings._confidence import parse_confidence_vector
from epistemic_pipeline.encodings.worldview import (
    DEFAULT_BASE_RATE,
    WorldviewBeliefs,
    WorldviewOntology,
    aggregate_beliefs,
    extraction_observation,
)
from epistemic_pipeline.worldview_app.provenance import canonicalize_origin

if TYPE_CHECKING:
    from epistemic_pipeline.llm.llm_interfaces import RatingLLMInterface
    from epistemic_pipeline.worldview_app.store import Store


def author_claim(
    store: Store,
    claim: str,
    confidence: float,
    ts: float,
) -> None:
    """Record a claim the user states directly (source_type 'user').

    A user assertion is not driven by document evidence, so it writes no
    observation or evidence link -- just the claim and its concept. It is
    therefore outside the Subjective-Logic evidence trail. If a later
    document rates the same claim (claim id is the text, so they collide),
    the document evidence takes over: the stored confidence becomes the
    document-derived projected probability, the source_type becomes the
    document's, and the drift link records the change from the user's last
    displayed value. User assertions and document-derived opinions are kept
    as separate kinds of belief for now; folding user assertions into the
    evidence trail is future work.

    Args:
        store: the belief store to write to.
        claim: the claim text, which is also its id.
        confidence: the user's confidence in [0, 1].
        ts: caller-supplied timestamp (never wall clock).
    """
    store.add_concept(claim, "user")
    store.put_claim(claim, claim, confidence, "user", ts)


def _prompt_hash(*parts: str) -> str:
    """Return a stable short hash of the prompt material."""
    joined = "\x1f".join(parts)
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()[:16]


def _ratings_from_store(store: Store) -> list[tuple[str, dict[str, float]]]:
    """Read the trail as (root_id, confidence-vector) pairs.

    The root id is the recorded ``root_id``; legacy rows that predate it
    fall back to ``source`` so each still counts as its own root.
    """
    ratings: list[tuple[str, dict[str, float]]] = []
    for row in store.observations():
        if row["variable"] != "confidence_vector":
            continue
        root = row["root_id"] or row["source"]
        ratings.append((root, parse_confidence_vector(row["value"])))
    return ratings


def _replay_beliefs(store: Store) -> WorldviewBeliefs:  # pyright: ignore[reportUnusedFunction]
    """Rebuild opinions by replaying R (two-tier fusion) over the trail.

    Groups each concept's evidence by root id: averaging within a root,
    cumulative across distinct roots. The ontology is read here (the full,
    current concept set) so a stale ontology cannot silently drop concepts.
    """
    ontology = WorldviewOntology(concepts=frozenset(store.concepts()))
    return aggregate_beliefs(_ratings_from_store(store), ontology)


def ingest_rating(  # noqa: PLR0913
    store: Store,
    confidences: dict[str, float],
    *,
    source_type: str,
    ts: float,
    model_id: str,
    prompt_hash: str,
    seed: int,
    reason: str,
    root_id: str | None = None,
) -> dict[str, float]:
    """Persist an LLM rating: grow O, accumulate evidence, link the drift.

    Steps:
    1. Add every rated claim to the ontology as a concept.
    2. Build the observation; derive the root (the canonical source this
       rating traces to; None falls back to the provenance source, so an
       unrooted rating counts as one root).
    3. Fuse the full trail plus this rating via aggregate_beliefs.
    4. Write the confidence-vector observation once.
    5. For each rated concept, cache its new projected probability on the
       claims row and link the projected-probability change (the drift)
       to the observation.

    Args:
        store: the belief store.
        confidences: the LLM's claim -> confidence rating.
        source_type: 'inferred' or 'derived' (who triggered the rating).
        ts: caller-supplied timestamp.
        model_id: the model that produced the rating.
        prompt_hash: hash of the exact prompt sent.
        seed: the sampling seed used.
        reason: short human-readable cause, shown in the drift timeline.
        root_id: the canonical source this rating traces to; None falls back
            to the provenance source, so an unrooted rating counts as one root.

    Returns:
        A map from each moved concept to its new projected probability
        (empty if the rating moved nothing).
    """
    # Drop non-finite ratings before touching the store, so a value the
    # encoding would discard (NaN/Infinity) cannot leave an orphan concept
    # in the ontology with no belief behind it.
    rated = {c: v for c, v in confidences.items() if math.isfinite(v)}
    if not rated:
        return {}
    for claim in rated:
        store.add_concept(claim, source_type)

    # Build the observation first: its provenance source doubles as the root
    # when the caller gives none. That is the same fallback replay uses for
    # legacy rows (row["root_id"] or row["source"]), so a direct rating still
    # counts as exactly one root, and the cached projected probabilities here
    # match what _replay_beliefs will later derive.
    obs = extraction_observation(rated, ts, model_id, prompt_hash, seed)
    root = root_id or obs.source

    ontology = WorldviewOntology(concepts=frozenset(store.concepts()))
    after = aggregate_beliefs([*_ratings_from_store(store), (root, rated)], ontology)

    # Only the concepts this rating actually moved. A concept enters
    # ``after.opinions`` only when R fused evidence for it, so this both
    # skips unrelated beliefs and is empty when nothing survived parsing.
    moved = [c for c in rated if c in after.opinions]
    if not moved:
        return {}

    obs_id = store.add_observation(
        obs.variable,
        obs.value,
        obs.source,
        obs.confidence,
        obs.timestamp,
        modality=obs.modality,
        root_id=root_id,
    )
    result: dict[str, float] = {}
    for claim in moved:
        p_after = after.opinions[claim].projected
        # Drift is measured from the value the user last saw -- the cached
        # confidence on the claims row -- so the link reconciles with the
        # displayed trajectory even for a claim a user authored directly
        # (which has a row but no opinion in the evidence trail). A
        # brand-new claim has no row, so it starts from the base rate.
        existing = store.get_claim(claim)
        p_before = existing["confidence"] if existing is not None else DEFAULT_BASE_RATE
        store.put_claim(claim, claim, p_after, source_type, ts)
        store.add_link(claim, obs_id, p_after - p_before, reason, ts)
        result[claim] = p_after
    return result


def ingest_document(  # noqa: PLR0913
    store: Store,
    llm: RatingLLMInterface,
    question: str,
    document: str,
    *,
    ts: float,
    seed: int,
    model_id: str,
    origin: str,
    reason: str | None = None,
    source_type: str = "inferred",
) -> dict[str, float]:
    """Have the LLM rate the claims in a document, then persist them.

    The known concepts are passed to the LLM so it can re-rate claims it
    has seen and add new ones. Every returned claim is then registered, so
    the ontology grows to cover the document.

    Args:
        store: the belief store.
        llm: a rating-capable LLM.
        question: the reader's standing question.
        document: the document text to rate against.
        ts: caller-supplied timestamp.
        seed: the sampling seed used (for the provenance record).
        model_id: the model identifier (for the provenance record).
        origin: the canonical source the document came from (a URL, DOI, or
            note path). Resolved to a root id so re-imports of one source
            are not double-counted.
        reason: drift-timeline label; defaults to a document digest.
        source_type: 'inferred' (one-shot) or 'derived' (continuous).

    Returns:
        The map of moved concepts to their new projected probabilities.
    """
    known = tuple(store.concepts())
    response = llm.rate_confidence(question, known, document)
    confidences = parse_confidence_vector(response.content)
    return ingest_rating(
        store,
        confidences,
        source_type=source_type,
        ts=ts,
        model_id=model_id,
        # Hash the full prompt the LLM saw -- question, known concepts, and
        # document -- so two prompts that differ only in the known set do
        # not collide to the same provenance record.
        prompt_hash=_prompt_hash(question, *known, document),
        seed=seed,
        reason=reason or f"doc:{_prompt_hash(document)}",
        root_id=canonicalize_origin(origin),
    )


class NoteIngester:
    """Continuous ingestion of notes, with content-hash dedupe.

    A file watcher fires many events per save, and most "changes" leave
    content identical. This wraps ``ingest_document`` (as source_type
    'derived') and skips a note whose content has not changed since it was
    last ingested.

    ponytail: dedupe state is in-memory per instance, so it resets when
    the process restarts. Persist the hashes (e.g. in the store) only if
    cross-session dedupe ever matters.
    """

    def __init__(
        self,
        store: Store,
        llm: RatingLLMInterface,
        question: str,
        *,
        model_id: str,
    ) -> None:
        """Bind the store, LLM, standing question, and model id."""
        self.store = store
        self.llm = llm
        self.question = question
        self.model_id = model_id
        self._seen: dict[str, str] = {}

    def ingest(
        self,
        path: str,
        content: str,
        *,
        ts: float,
        seed: int,
    ) -> dict[str, float] | None:
        """Ingest a note unless its content is unchanged since last time.

        Args:
            path: the note's path, used as its dedupe key and link reason.
            content: the note's current text.
            ts: caller-supplied timestamp.
            seed: the sampling seed used.

        Returns:
            The map of moved concepts to their new projected probabilities,
            or None if the note was skipped because its content was unchanged.
        """
        digest = hashlib.sha256(content.encode("utf-8")).hexdigest()
        if self._seen.get(path) == digest:
            return None
        # Record the hash only after a successful ingest. If the LLM call
        # raises, the note stays un-seen so the next attempt retries it
        # instead of silently skipping a never-ingested note.
        result = ingest_document(
            self.store,
            self.llm,
            self.question,
            content,
            ts=ts,
            seed=seed,
            model_id=self.model_id,
            origin=path,
            reason=path,
            source_type="derived",
        )
        self._seen[path] = digest
        return result
