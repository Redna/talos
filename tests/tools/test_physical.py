import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "cortex"))

from tools.physical import register_physical_tools
from tool_registry import ToolRegistry
from unittest.mock import MagicMock


def test_physical_tools_register():
    registry = ToolRegistry()
    mock_client = MagicMock()
    register_physical_tools(registry, mock_client)
    assert registry.has_tool("bash_command")
    assert registry.has_tool("send_message")
    assert registry.has_tool("request_restart")
