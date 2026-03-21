"""Tool integration for the epistemic pipeline.

Exports the protocol, adapter, and mock used by pipeline stages that
call external tools.
"""

from epistemic_pipeline.tools.tool_interfaces import (
    MockTool,
    ToolEvidenceAdapter,
    ToolInterface,
    ToolResult,
)

__all__ = [
    "MockTool",
    "ToolEvidenceAdapter",
    "ToolInterface",
    "ToolResult",
]
