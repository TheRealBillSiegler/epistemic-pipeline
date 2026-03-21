"""LLM integration for the epistemic pipeline.

Exports the protocol, adapter, and mock used by pipeline stages that
query language models.
"""

from epistemic_pipeline.llm.llm_interfaces import (
    LLMEvidenceAdapter,
    LLMInterface,
    LLMResponse,
    MockLLM,
)

__all__ = [
    "LLMEvidenceAdapter",
    "LLMInterface",
    "LLMResponse",
    "MockLLM",
]
