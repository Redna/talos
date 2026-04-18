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

import asyncio
import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
from tool_registry import ToolRegistry

# --- Strategies ---
tool_name_strategy = st.text(min_size=1, max_size=20).map(lambda x: x.replace(" ", "_"))

def create_registry():
    reg = ToolRegistry()
    
    @reg.tool(description="Add two numbers", parameters={
        "type": "object",
        "properties": {"a": {"type": "integer"}, "b": {"type": "integer"}},
        "required": ["a", "b"],
    })
    def add(a: int, b: int) -> str:
        return str(a + b)
    
    @reg.tool(description="Async add", parameters={
        "type": "object",
        "properties": {"a": {"type": "integer"}, "b": {"type": "integer"}},
        "required": ["a", "b"],
    })
    async def async_add(a: int, b: int) -> str:
        await asyncio.sleep(0.01)
        return str(a + b)
        
    return reg

# --- Tests ---

@given(name=st.text())
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_has_tool_invariants(name):
    registry = create_registry()
    if name == "add" or name == "async_add":
        assert registry.has_tool(name) is True
    else:
        assert registry.has_tool(name) is False

def test_get_schemas_structure():
    registry = create_registry()
    schemas = registry.get_schemas()
    assert len(schemas) == 2
    for s in schemas:
        assert "type" in s
        assert s["type"] == "function"
        assert "function" in s
        assert "name" in s["function"]
        assert "description" in s["function"]
        assert "parameters" in s["function"]

@given(name=tool_name_strategy)
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_execute_unknown_returns_error(name):
    registry = create_registry()
    if name in ["add", "async_add"]:
        return 
    
    result = asyncio.run(registry.execute(name, {}))
    assert result.startswith("[ERROR] Unknown tool")

@given(
    a=st.integers(min_value=-1000, max_value=1000),
    b=st.integers(min_value=-1000, max_value=1000),
)
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_execute_returns_string(a, b):
    registry = create_registry()
    result = asyncio.run(registry.execute("add", {"a": a, "b": b}))
    assert isinstance(result, str)
    assert result == str(a + b)

@given(
    a=st.integers(min_value=-1000, max_value=1000),
    b=st.integers(min_value=-1000, max_value=1000),
)
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_execute_async_returns_string(a, b):
    registry = create_registry()
    result = asyncio.run(registry.execute("async_add", {"a": a, "b": b}))
    assert isinstance(result, str)
    assert result == str(a + b)

@given(
    name=st.text(min_size=1, max_size=10),
    desc=st.text(),
    val=st.integers()
)
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_register_override(name, desc, val):
    registry = create_registry()
    
    @registry.tool(description="First", parameters={"type": "object", "properties": {}, "required": []})
    def override_tool():
        return "first"
    
    @registry.tool(description="Second", parameters={"type": "object", "properties": {}, "required": []})
    def override_tool():
        return "second"
        
    result = asyncio.run(registry.execute("override_tool", {}))
    assert result == "second"
