"""Tests for LLM integration interfaces.

Covers LLMResponse, MockLLM, LLMEvidenceAdapter, and the end-to-end
path from LLM invocation to Observation.
"""

import pytest

from epistemic_pipeline.llm import (
    LLMEvidenceAdapter,
    LLMResponse,
    MockLLM,
)
from epistemic_pipeline.state import EvidenceType


class TestLLMResponse:
    """LLMResponse is a frozen dataclass."""

    def test_frozen(self) -> None:
        """Assigning to a field must raise FrozenInstanceError."""
        response = LLMResponse(content="some text", confidence=0.9)
        with pytest.raises(Exception):
            response.content = "other"  # type: ignore[misc]

    def test_fields_accessible(self) -> None:
        """Both fields must be readable after construction."""
        response = LLMResponse(content="hello", confidence=0.7)
        assert response.content == "hello"
        assert response.confidence == 0.7


class TestMockLLM:
    """MockLLM returns canned responses and raises on unknown inputs."""

    def test_propose_ontology_returns_canned(self) -> None:
        """propose_ontology returns the pre-loaded LLMResponse for a known input."""
        expected = LLMResponse(content="variables: fever, cough", confidence=0.8)
        llm = MockLLM(responses={"diagnose flu": expected})
        result = llm.propose_ontology("diagnose flu")
        assert result is expected

    def test_unknown_input_raises_key_error(self) -> None:
        """All four methods raise KeyError when the input has no canned response."""
        llm = MockLLM(responses={})
        with pytest.raises(KeyError):
            llm.propose_ontology("unknown")
        with pytest.raises(KeyError):
            llm.decompose("unknown")
        with pytest.raises(KeyError):
            llm.propose_strategy("unknown")
        with pytest.raises(KeyError):
            llm.generate_explanation("unknown")


class TestLLMEvidenceAdapter:
    """LLMEvidenceAdapter maps LLMResponse fields to Observation fields."""

    def test_converts_to_observation(self) -> None:
        """Response content becomes value; modality='llm'; etype=REPORT."""
        adapter = LLMEvidenceAdapter()
        response = LLMResponse(content="use bayesian reasoning", confidence=0.85)
        obs = adapter.adapt(response, variable="strategy", timestamp=1234.0)
        assert obs.modality == "llm"
        assert obs.etype == EvidenceType.REPORT
        assert obs.confidence == 0.85
        assert obs.value == "use bayesian reasoning"
        assert obs.timestamp == 1234.0

    def test_variable_from_caller(self) -> None:
        """The variable field is set by the caller, not derived from the response."""
        adapter = LLMEvidenceAdapter()
        response = LLMResponse(content="...", confidence=0.5)
        obs_a = adapter.adapt(response, variable="ontology", timestamp=0.0)
        obs_b = adapter.adapt(response, variable="explanation", timestamp=0.0)
        assert obs_a.variable == "ontology"
        assert obs_b.variable == "explanation"


class TestLLMIntegration:
    """End-to-end: MockLLM -> LLMEvidenceAdapter -> Observation."""

    def test_end_to_end_mock_to_observation(self) -> None:
        """Invoke a mock LLM and adapt the response; verify all Observation fields."""
        canned = LLMResponse(
            content="variables: temperature, humidity", confidence=0.9
        )
        llm = MockLLM(responses={"weather prediction": canned})
        adapter = LLMEvidenceAdapter()

        response = llm.propose_ontology("weather prediction")
        obs = adapter.adapt(response, variable="ontology", timestamp=999.0)

        assert obs.variable == "ontology"
        assert obs.value == "variables: temperature, humidity"
        assert obs.source == "llm"
        assert obs.timestamp == 999.0
        assert obs.confidence == 0.9
        assert obs.etype == EvidenceType.REPORT
        assert obs.modality == "llm"
