"""Tests for tool integration interfaces.

Covers ToolResult, MockTool, ToolEvidenceAdapter, and the end-to-end
path from tool invocation to Observation.
"""

import pytest

from epistemic_pipeline.state import EvidenceType
from epistemic_pipeline.tools import (
    MockTool,
    ToolEvidenceAdapter,
    ToolResult,
)


class TestToolResult:
    """ToolResult is a frozen dataclass."""

    def test_frozen(self) -> None:
        """Assigning to a field must raise FrozenInstanceError."""
        result = ToolResult(name="calc", output={"value": 42}, success=True)
        with pytest.raises(Exception):
            result.name = "other"  # type: ignore[misc]

    def test_fields_accessible(self) -> None:
        """All three fields must be readable after construction."""
        result = ToolResult(name="lookup", output={"key": "val"}, success=False)
        assert result.name == "lookup"
        assert result.output == {"key": "val"}
        assert result.success is False


class TestMockTool:
    """MockTool returns canned responses and raises on unknown names."""

    def test_returns_canned_response(self) -> None:
        """invoke returns the pre-loaded ToolResult for a known name."""
        expected = ToolResult(name="search", output={"hits": 3}, success=True)
        tool = MockTool(responses={"search": expected})
        result = tool.invoke("search", {})
        assert result is expected

    def test_unknown_tool_raises_key_error(self) -> None:
        """invoke raises KeyError when the name has no canned response."""
        tool = MockTool(responses={})
        with pytest.raises(KeyError):
            tool.invoke("unknown", {})


class TestToolEvidenceAdapter:
    """ToolEvidenceAdapter maps ToolResult fields to Observation fields."""

    def test_converts_success_to_observation(self) -> None:
        """A successful result produces confidence=1.0, modality='tool', etype=MEASUREMENT."""
        adapter = ToolEvidenceAdapter()
        result = ToolResult(name="thermometer", output={"temp": 102}, success=True)
        obs = adapter.adapt(result, timestamp=1000.0)
        assert obs.modality == "tool"
        assert obs.etype == EvidenceType.MEASUREMENT
        assert obs.confidence == 1.0
        assert obs.variable == "thermometer"
        assert obs.value == str({"temp": 102})
        assert obs.timestamp == 1000.0

    def test_converts_failure_to_low_confidence(self) -> None:
        """A failed result produces confidence=0.5."""
        adapter = ToolEvidenceAdapter()
        result = ToolResult(name="sensor", output={"error": "timeout"}, success=False)
        obs = adapter.adapt(result, timestamp=2000.0)
        assert obs.confidence == 0.5
        assert obs.modality == "tool"
        assert obs.etype == EvidenceType.MEASUREMENT


class TestToolIntegration:
    """End-to-end: MockTool -> ToolEvidenceAdapter -> Observation."""

    def test_end_to_end_mock_to_observation(self) -> None:
        """Invoke a mock tool and adapt the result; verify all Observation fields."""
        canned = ToolResult(name="calculator", output={"result": 7}, success=True)
        tool = MockTool(responses={"calculator": canned})
        adapter = ToolEvidenceAdapter()

        raw = tool.invoke("calculator", {"a": 3, "b": 4})
        obs = adapter.adapt(raw, timestamp=500.0)

        assert obs.variable == "calculator"
        assert obs.value == str({"result": 7})
        assert obs.source == "calculator"
        assert obs.timestamp == 500.0
        assert obs.confidence == 1.0
        assert obs.etype == EvidenceType.MEASUREMENT
        assert obs.modality == "tool"
