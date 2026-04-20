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


def test_schema_generation():
    registry = ToolRegistry()

    @registry.tool(description="Say hello", parameters={"name": {"type": "string"}})
    def greet(name):
        return f"Hello {name}"

    schemas = registry.get_schemas()
    assert len(schemas) == 1
    assert schemas[0]["type"] == "function"
    assert schemas[0]["function"]["name"] == "greet"
    assert schemas[0]["function"]["description"] == "Say hello"
    assert "name" in schemas[0]["function"]["parameters"]["properties"]


def test_has_tool():
    registry = ToolRegistry()

    @registry.tool(description="test", parameters={})
    def foo():
        return "bar"

    assert registry.has_tool("foo")
    assert not registry.has_tool("baz")


def test_tool_names():
    registry = ToolRegistry()

    @registry.tool(description="func a", parameters={})
    def alpha():
        return "a"

    @registry.tool(description="func b", parameters={})
    def beta():
        return "b"

    names = registry.tool_names
    assert "alpha" in names
    assert "beta" in names


def test_execute_exception_returns_error():
    registry = ToolRegistry()

    @registry.tool(description="boom", parameters={})
    def boom():
        raise ValueError("exploded")

    result = registry.execute("boom", {})
    assert "[ERROR]" in result
    assert "failed" in result
    assert "exploded" in result
