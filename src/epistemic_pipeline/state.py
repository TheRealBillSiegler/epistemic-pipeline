"""Core epistemic state model: the (O, E, B, R) tuple.

Every pipeline step reads one immutable state and produces a new one.
The state is generic over ontology type O and beliefs type B.
Evidence is always a tuple of Observations. The revision policy R
is a callable: R(B, e, O) -> B'.
"""

from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum


class EvidenceType(Enum):
    """Type of evidence: how the observation was obtained.

    OBSERVATION: direct sensory input (e.g. seeing a symptom).
    REPORT: secondhand testimony (e.g. patient says "I feel sick").
    MEASUREMENT: instrument reading (e.g. thermometer shows 102F).
    """

    OBSERVATION = "observation"
    REPORT = "report"
    MEASUREMENT = "measurement"


@dataclass(frozen=True)
class Observation:
    """One piece of evidence: what was observed, its value, where it came from, and when.

    variable: the name of the thing measured (e.g. "fever").
    value: the observed outcome (e.g. "high").
    source: where the observation came from (e.g. "thermometer").
    timestamp: when the observation happened (seconds since epoch or ordinal).
    confidence: how reliable this observation is, from 0.0 to 1.0. Default is 1.0 (fully trusted).
    etype: how the observation was obtained. Default is EvidenceType.OBSERVATION.
    """

    variable: str
    value: str
    source: str
    timestamp: float
    confidence: float = 1.0
    etype: EvidenceType = EvidenceType.OBSERVATION


@dataclass(frozen=True)
class Metadata:
    """Immutable pipeline metadata carried through each stage.

    decomposition: sub-problems identified by the Decompose stage.
    strategy: the reasoning strategy name (e.g. "bayesian").
    evidence_order: the order in which evidence will be processed.
    anomalies: any anomalies detected during the pipeline run.
    pending_observations: observations waiting to be processed by Test.
    anomaly_checks: names of anomaly checks to run during the Test stage.
    heuristics: names of heuristics in use for the current strategy.
    strategy_switches: number of times the strategy has changed during this run.
    """

    decomposition: tuple[str, ...] = ()
    strategy: str = ""
    evidence_order: tuple[str, ...] = ()
    anomalies: tuple[str, ...] = ()
    pending_observations: tuple[Observation, ...] = ()
    anomaly_checks: tuple[str, ...] = ()
    heuristics: tuple[str, ...] = ()
    strategy_switches: int = 0


@dataclass(frozen=True)
class EpistemicState[O, B]:
    """Immutable epistemic state: (O, E, B, R) plus metadata.

    Generic over ontology type O and beliefs type B.
    Evidence is always a tuple of Observations (append-only).
    R is a callable: R(beliefs, observation, ontology) -> updated beliefs.
    Frozen: no field can be reassigned after construction.
    """

    ontology: O
    evidence: tuple[Observation, ...]
    beliefs: B
    revision_policy: Callable[[B, Observation, O], B]
    metadata: Metadata = field(default_factory=Metadata)
