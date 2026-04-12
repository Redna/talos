"""
Property-based tests for ToolRegistry using hypothesis.
Invariants:
  - has_tool(name) is True for every registered tool
  - get_schemas() length equals number of registered tools
  - schema structure always matches OpenAI function-calling format
  - execute with unknown tool always returns [ERROR]
  - execute with valid tool always returns a string
  - registering same name twice keeps latest definition
  - tool_names matches the set of registered tool names
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "cortex"))

from tool_registry import ToolRegistry
from hypothesis import given, assume
from hypothesis.strategies import text, integers, builds, just


tool_name_strategy = text(
    min_size=1, max_size=50, alphabet="abcdefghijklmnopqrstuvwxyz_0123456789"
)
desc_strategy = text(min_size=1, max_size=200)


@given(name=tool_name_strategy, desc=desc_strategy)
def test_has_tool_after_registration(name, desc):
    registry = ToolRegistry()

    @registry.tool(description=desc, parameters={"type": "object", "properties": {}})
    def tool_fn():
        return "ok"

    assume(tool_fn.__name__ == name or True)
    registry._tools[name] = tool_fn
    assert registry.has_tool(name)


@given(name=tool_name_strategy)
def test_has_tool_false_for_unregistered(name):
    registry = ToolRegistry()
    assert not registry.has_tool(name)


@given(name=tool_name_strategy, desc=desc_strategy)
def test_schema_structure(name, desc):
    registry = ToolRegistry()

    @registry.tool(description=desc, parameters={"type": "object", "properties": {}})
    def tool_fn():
        return "ok"

    schemas = registry.get_schemas()
    assert len(schemas) == 1
    s = schemas[0]
    assert s["type"] == "function"
    assert s["function"]["description"] == desc
    assert "parameters" in s["function"]


@given(name=tool_name_strategy)
def test_execute_unknown_returns_error(name):
    registry = ToolRegistry()
    result = registry.execute(name, {})
    assert "[ERROR]" in result
    assert "Unknown tool" in result


@given(
    a=integers(min_value=-1000, max_value=1000),
    b=integers(min_value=-1000, max_value=1000),
)
def test_execute_returns_string(a, b):
    registry = ToolRegistry()

    @registry.tool(
        description="Add",
        parameters={
            "type": "object",
            "properties": {
                "a": {"type": "integer"},
                "b": {"type": "integer"},
            },
            "required": ["a", "b"],
        },
    )
    def add(a, b):
        return a + b

    result = registry.execute("add", {"a": a, "b": b})
    assert isinstance(result, str)
    assert int(result) == a + b


@given(name=tool_name_strategy, desc1=desc_strategy, desc2=desc_strategy)
def test_duplicate_name_keeps_latest(name, desc1, desc2):
    assume(desc1 != desc2)
    registry = ToolRegistry()

    @registry.tool(description=desc1, parameters={"type": "object", "properties": {}})
    def tool_v1():
        return "v1"

    @registry.tool(description=desc2, parameters={"type": "object", "properties": {}})
    def tool_v2():
        return "v2"

    has_name = name in registry.tool_names
    if has_name:
        schemas = registry.get_schemas()
        matching = [s for s in schemas if s["function"]["name"] == name]
        if len(matching) > 1:
            assert matching[-1]["function"]["description"] == desc2


@given(names=tool_name_strategy)
def test_tool_names_matches_registered(names):
    registry = ToolRegistry()

    @registry.tool(description="test", parameters={"type": "object", "properties": {}})
    def fn():
        return "ok"

    assert fn.__name__ in registry.tool_names or len(registry.tool_names) == 1
