"""Worldview encoding: revise beliefs over a personal corpus, in Subjective Logic.

Sixth expressiveness use: a reader's worldview as an (O, E, B, R) tuple.

- O (ontology): the set of *concepts* the corpus knows about. Concepts
  are claim identifiers -- stable handles for the things the reader holds
  beliefs about. O grows as new documents introduce new concepts.
- E (evidence): recorded LLM confidence vectors, one per document the
  reader takes in. Each is an Observation whose value is a JSON object
  mapping concept -> confidence in [0, 1].
- B (beliefs): one Subjective-Logic ``Opinion`` per concept, stored as
  evidence counts. Independent per concept; no shared normalization.
- R (revision): turn the latest confidence vector into evidence,
  discount it by source reliability, and *accumulate* it into each
  mentioned concept's opinion. Concepts the vector omits are carried
  forward unchanged.

This replaces the v1.1 "renormalize the latest vector" revision, which
forgot any concept a new document failed to mention and could not tell "I
have no evidence" from "the evidence is balanced". An Opinion carries an
explicit uncertainty mass, so a vacuous concept reports `u = 1` (and
projects to its base rate) instead of a fabricated 0.5.

How a confidence becomes evidence (the mapping Unit 1 left to the
encoding): one document contributes ``EVIDENCE_PER_DOC`` units of
evidence about each concept it rates, split for/against by the stated
confidence ``p`` -- ``Opinion(E*p, E*(1-p))`` -- then scaled by the
source's reliability. With ``E = 2`` and ``W = 2``, one fully-confident
source at reliability 1.0 yields ``b = u = 0.5``: believed, but still
uncertain after a single source. This is the same mechanism as the
design's worked example (§4.3); that example additionally applies a
``P_R = 0.95`` reliability discount, which this version disables, so its
numbers are ``b ~ 0.49`` / ``u ~ 0.51`` rather than 0.5 / 0.5.

Source reliability is fixed at ``DEFAULT_RELIABILITY`` for now: credibility
weighting is disabled and labelled as such until it can be grounded in
something auditable (design Unit 3). At reliability 1.0 the discount is a
no-op, so belief tracks evidence directly and nothing fakes credibility.

The LLM is non-deterministic, but R is pure: the LLM's confidence vector
is recorded as an Observation before R runs, and R only ever reads from
that recorded text. Cumulative fusion is count addition, so replaying the
recorded evidence trail reproduces beliefs exactly.
"""

from __future__ import annotations

import json
from dataclasses import dataclass

from epistemic_pipeline.encodings._confidence import parse_confidence_vector
from epistemic_pipeline.encodings._subjective_logic import (
    Opinion,
    discount,
    fuse_cumulative,
)
from epistemic_pipeline.state import EvidenceType, Observation

# Evidence units one document contributes about each concept it rates.
# E = 2 pairs with the SL prior weight W = 2: one fully-confident source
# leaves belief and uncertainty equal (b = u = 0.5).
EVIDENCE_PER_DOC = 2.0

# Source reliability used by R. 1.0 = credibility weighting disabled
# (the discount is a no-op). Grounding this per-source is design Unit 3.
DEFAULT_RELIABILITY = 1.0

# Base rate for a concept with no evidence yet. 0.5 = a vacuous opinion
# projects to one-half, the neutral prior.
DEFAULT_BASE_RATE = 0.5


@dataclass(frozen=True)
class WorldviewOntology:
    """The concepts (claim identifiers) the corpus knows about.

    concepts: the closed set of claim ids the reader holds beliefs over.
        Grows as documents introduce new claims (done by the ingestion
        layer before R runs).
    """

    concepts: frozenset[str]

    def adequate(self, evidence: tuple[Observation, ...]) -> bool:
        """Return False if any recorded vector names a concept O lacks.

        This is the Power norm for the worldview encoding: the ontology
        is adequate only if it already covers every concept the evidence
        talks about. A confidence vector that mentions an unknown concept
        means a document introduced something O has not accounted for, so
        the meta layer should REFRAME (grow O) before trusting the run.

        Args:
            evidence: the observations gathered so far. Only confidence
                vectors (variable == "confidence_vector") are inspected.

        Returns:
            True if every concept mentioned in evidence is in
            ``concepts``; False otherwise.
        """
        for obs in evidence:
            if obs.variable != "confidence_vector":
                continue
            for name in parse_confidence_vector(obs.value):
                if name not in self.concepts:
                    return False
        return True


@dataclass(frozen=True)
class WorldviewBeliefs:
    """One Subjective-Logic opinion per concept.

    opinions: maps each concept (claim id) to its ``Opinion``. A concept
        with no opinion yet is treated as vacuous (``Opinion(0, 0)``):
        uncertainty 1, projecting to its base rate. Opinions are
        independent -- they do not sum to anything.
    """

    opinions: dict[str, Opinion]


def worldview_argmax(beliefs: WorldviewBeliefs) -> str:
    """Return the concept with the highest projected probability.

    Ranks by projected probability ``P`` (belief plus base-rate-weighted
    uncertainty), which is the quantity calibration scores against. Empty
    string if there are no opinions.
    """
    if not beliefs.opinions:
        return ""
    return max(beliefs.opinions, key=lambda c: beliefs.opinions[c].projected)


def _evidence_increment(confidence: float) -> Opinion:
    """Turn one stated confidence into a discounted evidence increment.

    Splits ``EVIDENCE_PER_DOC`` units for/against by the confidence
    (clamped to [0, 1]), then scales by ``DEFAULT_RELIABILITY``.
    """
    p = min(1.0, max(0.0, confidence))
    raw = Opinion(EVIDENCE_PER_DOC * p, EVIDENCE_PER_DOC * (1.0 - p), DEFAULT_BASE_RATE)
    return discount(raw, DEFAULT_RELIABILITY)


def worldview_update(
    beliefs: WorldviewBeliefs,
    evidence: Observation,
    ontology: WorldviewOntology,
) -> WorldviewBeliefs:
    """Accumulate a recorded confidence vector into beliefs: R(B, e, O) -> B'.

    For each concept the vector rates that O knows, turn the confidence
    into a discounted evidence increment and fuse it (cumulatively, i.e.
    by adding counts) into that concept's opinion. Every other concept is
    carried forward unchanged -- there is no renormalize and no amnesia.

    Only confidence-vector observations carry evidence; any other
    observation (a raw document chunk, say) leaves beliefs unchanged.

    Args:
        beliefs: current opinions, one per concept.
        evidence: the recorded observation. Its ``value`` is the LLM's
            JSON confidence vector when ``variable == "confidence_vector"``.
        ontology: the known concept set used to filter the vector.

    Returns:
        Updated WorldviewBeliefs. Unmentioned concepts are unchanged.
    """
    if evidence.variable != "confidence_vector":
        return beliefs
    parsed = parse_confidence_vector(evidence.value)
    updates = {
        name: confidence
        for name, confidence in parsed.items()
        if name in ontology.concepts
    }
    if not updates:
        return beliefs

    new_opinions = dict(beliefs.opinions)
    for name, confidence in updates.items():
        prior = new_opinions.get(name, Opinion(0.0, 0.0, DEFAULT_BASE_RATE))
        new_opinions[name] = fuse_cumulative([prior, _evidence_increment(confidence)])
    return WorldviewBeliefs(opinions=new_opinions)


def extraction_observation(
    confidences: dict[str, float],
    timestamp: float,
    model_id: str,
    prompt_hash: str,
    seed: int,
) -> Observation:
    """Build a confidence-vector Observation that records its provenance.

    The (model_id, prompt_hash, seed) triple rides in ``source`` so the
    trace shows exactly which model and prompt produced the rating. Same
    inputs always produce the same Observation, which is what keeps a
    replay byte-identical.

    Args:
        confidences: the LLM's concept -> confidence rating.
        timestamp: caller-supplied time (never wall clock).
        model_id: the model that produced the rating.
        prompt_hash: hash of the exact prompt sent.
        seed: the sampling seed used.

    Returns:
        An Observation ready to append to evidence and feed to R.
    """
    return Observation(
        variable="confidence_vector",
        value=json.dumps(confidences, sort_keys=True),
        source=f"{model_id}@{prompt_hash}#{seed}",
        timestamp=timestamp,
        confidence=1.0,
        etype=EvidenceType.REPORT,
        modality="llm",
    )
