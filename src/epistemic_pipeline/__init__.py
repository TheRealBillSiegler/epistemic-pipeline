"""Epistemic Pipeline: a general-purpose reasoning architecture."""

from epistemic_pipeline.meta import (
    MetaController,
    MetaDecision,
    MetaResult,
    MetaThresholds,
)
from epistemic_pipeline.norms import NormScore, score_pipeline_run
from epistemic_pipeline.pipeline import PipelineResult, run_pipeline
from epistemic_pipeline.state import (
    EpistemicState,
    EvidenceType,
    Metadata,
    Observation,
)

__all__ = [
    "EpistemicState",
    "EvidenceType",
    "MetaController",
    "MetaDecision",
    "MetaResult",
    "MetaThresholds",
    "Metadata",
    "NormScore",
    "Observation",
    "PipelineResult",
    "run_pipeline",
    "score_pipeline_run",
]
