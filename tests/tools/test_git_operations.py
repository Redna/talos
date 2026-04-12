import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "cortex"))

from tools.git_operations import register_git_tools
from tool_registry import ToolRegistry
from unittest.mock import MagicMock


def test_git_tools_register():
    registry = ToolRegistry()
    mock_client = MagicMock()
    register_git_tools(registry, mock_client)
    assert registry.has_tool("git_commit")
    assert registry.has_tool("git_diff")
