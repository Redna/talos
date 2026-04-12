import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "cortex"))

from tools.code_surgery import register_code_surgery_tools
from tool_registry import ToolRegistry
from unittest.mock import MagicMock


def test_code_surgery_tools_register():
    registry = ToolRegistry()
    mock_client = MagicMock()
    register_code_surgery_tools(registry, mock_client)
    assert registry.has_tool("generate_repo_map")
    assert registry.has_tool("replace_symbol")
    assert registry.has_tool("write_file")
    assert registry.has_tool("read_file")
    assert registry.has_tool("patch_file")
