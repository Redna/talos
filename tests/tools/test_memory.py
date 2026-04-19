import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "cortex"))

from tools.memory import register_memory_tools
from tool_registry import ToolRegistry
from unittest.mock import MagicMock


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
    assert registry.has_tool("store_memory")
    assert registry.has_tool("recall_memory")
    assert registry.has_tool("list_memory_keys")
    assert registry.has_tool("search_memory")
    assert registry.has_tool("forget_memory")
    assert registry.has_tool("consolidate_memory")
    assert registry.has_tool("analyze_memory_telemetry")
