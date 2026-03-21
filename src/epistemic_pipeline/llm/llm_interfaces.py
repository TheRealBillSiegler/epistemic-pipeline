"""LLM integration interfaces for the epistemic pipeline.

An LLM is a model the pipeline can query for reasoning support — proposing
an ontology, decomposing a problem, or generating an explanation. LLM
responses are text paired with a self-assessed confidence score.
This module defines the protocol, an adapter to convert responses into
Observations, and a mock for testing.
"""

from dataclasses import dataclass
from typing import Protocol

from epistemic_pipeline.state import EvidenceType, Observation


@dataclass(frozen=True)
class LLMResponse:
    """Output from an LLM call.

    content: the generated text or structured response.
    confidence: model's self-assessed confidence in [0, 1].
    """

    content: str
    confidence: float


class LLMInterface(Protocol):
    """Protocol for LLM implementations.

    Any object with all four methods matching these signatures satisfies
    the protocol. No base class is required.
    """

    def propose_ontology(self, problem: str) -> LLMResponse:
        """Suggest an ontology (variable set) for the given problem.

        Args:
            problem: A plain-text description of the problem.

        Returns:
            An LLMResponse with proposed ontology text and confidence.
        """
        ...

    def decompose(self, problem: str) -> LLMResponse:
        """Break a problem into sub-problems.

        Args:
            problem: A plain-text description of the problem.

        Returns:
            An LLMResponse listing sub-problems and confidence.
        """
        ...

    def propose_strategy(self, state_description: str) -> LLMResponse:
        """Suggest a reasoning strategy given the current state.

        Args:
            state_description: A plain-text summary of the epistemic state.

        Returns:
            An LLMResponse naming a strategy and confidence.
        """
        ...

    def generate_explanation(self, state_description: str) -> LLMResponse:
        """Produce a human-readable explanation of the current state.

        Args:
            state_description: A plain-text summary of the epistemic state.

        Returns:
            An LLMResponse with the explanation text and confidence.
        """
        ...


class LLMEvidenceAdapter:
    """Converts LLMResponse to Observation with modality='llm'.

    Sets etype to REPORT, confidence from response.confidence,
    variable from caller, value to response.content.
    """

    def adapt(
        self, response: LLMResponse, variable: str, timestamp: float
    ) -> Observation:
        """Convert an LLMResponse into an Observation.

        The caller names the variable because one LLM method can serve
        multiple pipeline roles (e.g. "ontology", "strategy").

        Args:
            response: The LLM response to convert.
            variable: The role name for this observation (e.g. "ontology").
            timestamp: When the LLM was queried (seconds since epoch).

        Returns:
            An Observation with modality='llm' and etype=REPORT.
        """
        return Observation(
            variable=variable,
            value=response.content,
            source="llm",
            timestamp=timestamp,
            confidence=response.confidence,
            etype=EvidenceType.REPORT,
            modality="llm",
        )


class MockLLM:
    """Test implementation. Returns canned responses keyed by input string.

    Pass a dict of ``{input_string: LLMResponse}`` at construction time.
    All four interface methods look up the input in the same dict.
    """

    def __init__(self, responses: dict[str, LLMResponse]) -> None:
        """Initialize with a dict of canned responses.

        Args:
            responses: Maps input string to the LLMResponse to return.
        """
        self._responses = responses

    def propose_ontology(self, problem: str) -> LLMResponse:
        """Return the canned response for ``problem``.

        Args:
            problem: The problem string to look up.

        Returns:
            The canned LLMResponse.

        Raises:
            KeyError: If ``problem`` has no canned response.
        """
        return self._responses[problem]

    def decompose(self, problem: str) -> LLMResponse:
        """Return the canned response for ``problem``.

        Args:
            problem: The problem string to look up.

        Returns:
            The canned LLMResponse.

        Raises:
            KeyError: If ``problem`` has no canned response.
        """
        return self._responses[problem]

    def propose_strategy(self, state_description: str) -> LLMResponse:
        """Return the canned response for ``state_description``.

        Args:
            state_description: The state description to look up.

        Returns:
            The canned LLMResponse.

        Raises:
            KeyError: If ``state_description`` has no canned response.
        """
        return self._responses[state_description]

    def generate_explanation(self, state_description: str) -> LLMResponse:
        """Return the canned response for ``state_description``.

        Args:
            state_description: The state description to look up.

        Returns:
            The canned LLMResponse.

        Raises:
            KeyError: If ``state_description`` has no canned response.
        """
        return self._responses[state_description]
