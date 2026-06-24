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
from typing import TYPE_CHECKING

from epistemic_pipeline.encodings._confidence import parse_confidence_vector
from epistemic_pipeline.encodings.worldview import (
    WorldviewBeliefs,
    WorldviewOntology,
    extraction_observation,
    worldview_update,
)

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
    observation or evidence link -- just the claim and its concept.

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
) -> dict[str, float]:
    """Persist an LLM rating: grow O, revise B, link the evidence.

    Steps:
    1. Add every rated claim to the ontology as a concept.
    2. Apply the revision policy to the recorded confidence vector.
    3. Write the confidence-vector observation once.
    4. For each claim in the posterior, update its stored confidence and
       link it to the observation with the delta from its prior value.

    Args:
        store: the belief store.
        confidences: the LLM's claim -> confidence rating.
        source_type: 'inferred' or 'derived' (who triggered the rating).
        ts: caller-supplied timestamp.
        model_id: the model that produced the rating.
        prompt_hash: hash of the exact prompt sent.
        seed: the sampling seed used.
        reason: short human-readable cause, shown in the drift timeline.

    Returns:
        The posterior confidence map that was persisted (empty if the
        rating had nothing usable).
    """
    if not confidences:
        return {}
    for claim in confidences:
        store.add_concept(claim, source_type)

    ontology = WorldviewOntology(concepts=frozenset(store.concepts()))
    prior = {row["id"]: row["confidence"] for row in store.claims()}
    obs = extraction_observation(confidences, ts, model_id, prompt_hash, seed)
    posterior = worldview_update(WorldviewBeliefs(prior), obs, ontology)

    # Persist only what this rating produced. A degenerate (all <= 0)
    # rating makes worldview_update echo the prior unchanged; intersect
    # with the incoming claims so we never re-stamp or relink unrelated
    # beliefs, and skip the observation entirely when nothing survives.
    updated = {c: v for c, v in posterior.confidences.items() if c in confidences}
    if not updated:
        return {}
    obs_id = store.add_observation(
        obs.variable, obs.value, obs.source, obs.confidence, obs.timestamp,
        modality=obs.modality,
    )
    for claim, conf in updated.items():
        delta = conf - prior.get(claim, 0.0)
        store.put_claim(claim, claim, conf, source_type, ts)
        store.add_link(claim, obs_id, delta, reason, ts)
    return updated


def ingest_document(  # noqa: PLR0913
    store: Store,
    llm: RatingLLMInterface,
    question: str,
    document: str,
    *,
    ts: float,
    seed: int,
    model_id: str,
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
        reason: drift-timeline label; defaults to a document digest.
        source_type: 'inferred' (one-shot) or 'derived' (continuous).

    Returns:
        The posterior confidence map that was persisted.
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
            The persisted posterior map, or None if the note was skipped
            because its content had not changed.
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
            reason=path,
            source_type="derived",
        )
        self._seen[path] = digest
        return result
