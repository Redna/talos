import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "cortex"))

from tools.memory import register_memory_tools
from tool_registry import ToolRegistry
from unittest.mock import MagicMock


def test_memory_tools_register():
    registry = ToolRegistry()
    mock_memory = MagicMock()
    register_memory_tools(registry, mock_memory)
    assert registry.has_tool("store_fact")
    assert registry.has_tool("recall_fact")
    assert registry.has_tool("list_memory_keys")
    assert registry.has_tool("search_memory")
