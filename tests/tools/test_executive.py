import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "cortex"))

from tools.executive import register_executive_tools
from tool_registry import ToolRegistry
from unittest.mock import MagicMock


def test_executive_tools_register():
    registry = ToolRegistry()
    mock_client = MagicMock()
    mock_state = MagicMock()
    register_executive_tools(registry, mock_client, mock_state)
    assert registry.has_tool("set_focus")
    assert registry.has_tool("resolve_focus")
    assert registry.has_tool("fold_context")
    assert registry.has_tool("reflect")
