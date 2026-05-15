"""Tool integration interfaces for the epistemic pipeline.

A tool is any external function the pipeline can call — a calculator,
a database lookup, a web search. Tools return structured results.
This module defines the protocol, an adapter to convert results into
Observations, and a mock for testing.
"""

from dataclasses import dataclass
from typing import Protocol

from epistemic_pipeline.state import EvidenceType, Observation


@dataclass(frozen=True)
class ToolResult:
    """Output from a tool invocation.

    name: which tool was called.
    output: structured output data.
    success: True if the tool call succeeded.
    """

    name: str
    output: dict[str, object]
    success: bool


class ToolInterface(Protocol):
    """Protocol for tool implementations.

    Any object with an ``invoke`` method matching this signature satisfies
    the protocol. No base class is required.
    """

    def invoke(self, name: str, args: dict[str, object]) -> ToolResult:
        """Call a tool by name with the given arguments.

        Args:
            name: The tool to invoke.
            args: Key-value arguments for the tool.

        Returns:
            The tool's result.
        """
        ...


class ToolEvidenceAdapter:
    """Converts ToolResult to Observation with modality='tool'.

    Sets etype to MEASUREMENT, confidence to 1.0 if success else 0.5,
    variable to tool name, value to str(output).
    """

    def adapt(self, result: ToolResult, timestamp: float) -> Observation:
        """Convert a ToolResult into an Observation.

        A successful tool call gets confidence 1.0. A failed call gets 0.5:
        the output may still contain useful partial information.

        Args:
            result: The tool result to convert.
            timestamp: When the tool was invoked (seconds since epoch).

        Returns:
            An Observation with modality='tool' and etype=MEASUREMENT.
        """
        confidence = 1.0 if result.success else 0.5
        return Observation(
            variable=result.name,
            value=str(result.output),
            source=result.name,
            timestamp=timestamp,
            confidence=confidence,
            etype=EvidenceType.MEASUREMENT,
            modality="tool",
        )


class MockTool:
    """Test implementation. Returns canned responses keyed by tool name.

    Pass a dict of ``{tool_name: ToolResult}`` at construction time.
    ``invoke`` returns the matching result or raises KeyError.
    """

    def __init__(self, responses: dict[str, ToolResult]) -> None:
        """Initialize with a dict of canned responses.

        Args:
            responses: Maps tool name to the ToolResult to return.
        """
        self._responses = responses

    def invoke(
        self, name: str, args: dict[str, object],
    ) -> ToolResult:
        """Return the canned response for ``name``.

        Args:
            name: The tool name to look up.
            args: Ignored in mock implementation.

        Returns:
            The canned ToolResult for this name.

        Raises:
            KeyError: If ``name`` has no canned response.
        """
        _ = args
        return self._responses[name]
