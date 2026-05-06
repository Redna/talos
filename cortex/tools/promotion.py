import os
import json
from cortex.tool_registry import ToolRegistry

def promote_tool(name: str, code: str, description: str, parameters: dict):
    """
    Promotes a dynamically installed tool to a permanent source-code tool.
    """
    promoted_path = "/app/cortex/tools/promoted_tools.py"
    
    # Ensure the file exists with the basic structure
    if not os.path.exists(promoted_path):
        content = "def register_promoted_tools(registry, client, state):\n    pass\n"
        with open(promoted_path, 'w') as f:
            f.write(content)

    # Construct the tool definition
    # We define the function inside register_promoted_tools to have access to the registry
    tool_entry = f"\n    def {name}(**kwargs):\n"
    # Indent the code
    lines = code.splitlines()
    indented_code = "\n".join(["        " + line for line in lines])
    tool_entry += indented_code + "\n\n"
    tool_entry += f"    registry.register_dynamic_tool(\n"
    tool_entry += f"        '{name}',\n"
    tool_entry += f"        {name},\n"
    tool_entry += f"        {repr(description)},\n"
    tool_entry += f"        {json.dumps(parameters)}\n"
    tool_entry += f"    )\n"

    with open(promoted_path, 'r') as f:
        lines = f.readlines()
    
    # Insert the tool before the end of the function
    # Find the 'pass' or the end of the function
    new_lines = []
    found_pass = False
    for line in lines:
        if line.strip() == "pass":
            new_lines.append(tool_entry)
            found_pass = True
        else:
            new_lines.append(line)
    
    if not found_pass:
        new_lines.append(tool_entry)

    with open(promoted_path, 'w') as f:
        f.writelines(new_lines)

    return f"Tool {name} promoted to {promoted_path}. Please ensure register_promoted_tools is called in seed_agent.py."

def register_promotion_tools(registry, client, state):
    registry.register_dynamic_tool(
        "promote_tool",
        promote_tool,
        "Promotes a dynamically installed tool to a permanent source-code tool.",
        {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "code": {"type": "string"},
                "description": {"type": "string"},
                "parameters": {"type": "object"}
            },
            "required": ["name", "code", "description", "parameters"]
        }
    )
