"""Worldview encoding: revise beliefs over a personal corpus.

Sixth expressiveness use: a reader's worldview as an (O, E, B, R) tuple.

- O (ontology): the set of *concepts* the corpus knows about. Concepts
  are claim identifiers — stable handles for the things the reader holds
  beliefs about. O grows as new documents introduce new concepts.
- E (evidence): recorded LLM confidence vectors, one per document the
  reader takes in. Each is an Observation whose value is a JSON object
  mapping concept -> confidence in [0, 1].
- B (beliefs): the reader's current confidence in each concept.
- R (revision): parse the latest confidence vector, keep the concepts O
  knows, and renormalize so they sum to 1.0.

Empty-prior case: with no prior beliefs, R returns the normalized
likelihood unchanged -- posterior equals likelihood. So a brand-new
reader's first document produces a complete result with no setup step.
This is the same normalize-over-a-closed-set update the Bayesian and
LLM-agent encodings use; the worldview difference is that O (and thus
the claim set) grows from the documents themselves.

The LLM is non-deterministic, but R is pure: the LLM's confidence vector
is recorded as an Observation before R runs, and R only ever reads from
that recorded text. Replay is deterministic given the recorded trace.

ponytail: claims are treated as one normalized distribution, reusing the
proven Bayesian/LLM-agent update. If independent per-claim beliefs (two
claims both true at once) start to matter, switch B to per-claim
Bernoulli and drop the renormalize.
"""

from __future__ import annotations

import json
from dataclasses import dataclass

from epistemic_pipeline.state import EvidenceType, Observation

_FLOAT_TOLERANCE = 1e-9


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
            for name in _parse_confidence_vector(obs.value):
                if name not in self.concepts:
                    return False
        return True


@dataclass(frozen=True)
class WorldviewBeliefs:
    """Confidence distribution over concepts.

    confidences: maps each concept (claim id) to a confidence in [0, 1].
    Invariant: the values sum to 1.0 within float tolerance, or the map
    is empty (a brand-new reader with no beliefs yet).
    """

    confidences: dict[str, float]


def worldview_argmax(beliefs: WorldviewBeliefs) -> str:
    """Return the concept with the highest confidence (empty string if none)."""
    if not beliefs.confidences:
        return ""
    return max(beliefs.confidences, key=lambda c: beliefs.confidences[c])


def _parse_confidence_vector(text: str) -> dict[str, float]:
    """Parse a JSON object mapping concept -> confidence.

    Returns an empty dict if the text is not a JSON object or holds no
    usable numbers. Non-numeric values are skipped.
    """
    try:
        payload = json.loads(text)
    except (json.JSONDecodeError, ValueError):
        return {}
    if not isinstance(payload, dict):
        return {}
    result: dict[str, float] = {}
    for name, value in payload.items():
        if not isinstance(name, str):
            continue
        try:
            result[name] = float(value)
        except (TypeError, ValueError):
            continue
    return result


def worldview_update(
    beliefs: WorldviewBeliefs,
    evidence: Observation,
    ontology: WorldviewOntology,
) -> WorldviewBeliefs:
    """Apply a recorded confidence vector to current beliefs: R(B, e, O) -> B'.

    The LLM has already rated each concept given the new document; that
    rating is recorded in ``evidence.value`` as JSON. R parses it, drops
    concepts O does not know and negative values, and renormalizes the
    rest to sum to 1.0. With an empty or uniform prior this returns the
    normalized likelihood, so posterior equals likelihood.

    Only confidence-vector observations carry a rating; any other
    observation (a raw document chunk, say) leaves beliefs unchanged. If
    nothing survives filtering, beliefs are returned unchanged.

    Args:
        beliefs: current confidence distribution over concepts.
        evidence: the recorded observation. Its ``value`` is the LLM's
            JSON confidence vector when ``variable == "confidence_vector"``.
        ontology: the known concept set used to filter the vector.

    Returns:
        Updated WorldviewBeliefs with normalized confidences.
    """
    if evidence.variable != "confidence_vector":
        return beliefs
    parsed = _parse_confidence_vector(evidence.value)
    filtered = {
        name: max(0.0, value)
        for name, value in parsed.items()
        if name in ontology.concepts
    }
    total = sum(filtered.values())
    if total <= _FLOAT_TOLERANCE:
        return beliefs
    return WorldviewBeliefs(
        confidences={name: value / total for name, value in filtered.items()},
    )


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
