import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "talos" / "cortex"))

from tool_registry import ToolRegistry


def test_register_and_execute():
    registry = ToolRegistry()

    @registry.tool(
        description="Add two numbers",
        parameters={"a": {"type": "integer"}, "b": {"type": "integer"}},
    )
    def add(a, b):
        return a + b

    result = registry.execute("add", {"a": 2, "b": 3})
    assert result == "5"


def test_type_error_reports_missing_args():
    registry = ToolRegistry()

    @registry.tool(
        description="Add two numbers",
        parameters={"a": {"type": "integer"}, "b": {"type": "integer"}},
    )
    def add(a, b):
        return a + b

    result = registry.execute("add", {"a": 2})
    assert "[ERROR]" in result
    assert "add" in result
    assert "wrong arguments" in result
    assert "Required:" in result
    assert "missing:" in result


def test_unknown_tool_error():
    registry = ToolRegistry()
    result = registry.execute("nonexistent", {})
    assert result == "[ERROR] Unknown tool: nonexistent"
