from tool_registry import ToolRegistry
import hashlib

registry = ToolRegistry()

@registry.tool(description="Test tool", parameters={"type": "object", "properties": {}})
def test_tool():
    return "Sovereign Test Success"

print(f"Tools in registry: {registry.tool_names}")
